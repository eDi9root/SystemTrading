from api.Kiwoom import *
from util.RSI_universe import *
from util.db_helper import *
from util.time_helper import *
import math
import traceback


class RSIStrategy(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.strategy_name = "RSIStrategy"
        self.kiwoom = Kiwoom()

        self.universe = {}
        self.deposit = 0
        self.is_init_success = False

        self.init_strategy()

    def init_strategy(self):
        """
        Performs strategy initialization function
        """
        try:
            self.check_and_get_universe()
            self.check_and_get_price_data()
            self.kiwoom.get_order()
            self.kiwoom.get_balance()
            self.deposit = self.kiwoom.get_deposit()
            self.set_universe_real_time()

            self.is_init_success = True

        except Exception as e:
            print(traceback.format_exc())

    def check_and_get_universe(self):
        """
        Check if the universe exists and create it
        """
        if not check_table_exist(self.strategy_name, 'universe'):
            universe_list = get_universe()
            print(universe_list)
            universe = {}
            now = datetime.now().strftime("%Y%m%d")

            # Get all stock codes listed on KOSPI(0)
            kospi_code_list = self.kiwoom.get_code_list_by_market("0")

            # Get all stock codes listed on KOSDAQ(10)
            kosdaq_code_list = self.kiwoom.get_code_list_by_market("10")

            for code in kospi_code_list + kosdaq_code_list:
                # Perform loop based on all items codes to get code name
                code_name = self.kiwoom.get_master_code_name(code)

                if code_name in universe_list:
                    universe[code] = code_name

            # Create dataframe with code, code_name, and created_at as columns
            universe_df = pd.DataFrame({
                'code': universe.keys(),
                'code_name': universe.values(),
                'created_at': [now] * len(universe.keys())
            })

            # Save in DB with table name 'universe'
            insert_df_to_db(self.strategy_name, 'universe', universe_df)

        sql = "select * from universe"
        cur = execute_sql(self.strategy_name, sql)
        universe_list = cur.fetchall()
        for item in universe_list:
            idx, code, code_name, created_at = item
            self.universe[code] = {
                'code_name': code_name
            }
        print(self.universe)

    def check_and_get_price_data(self):
        """
        Check if candle data exists and create it
        :return:
        """
        for idx, code in enumerate(self.universe.keys()):
            print("({}/{}) {}".format(idx + 1, len(self.universe), code))

            # Case 1: Whether there is any daily data (after market close)
            if check_transaction_closed() and not check_table_exist(self.strategy_name, code):
                # Save price data using API
                price_df = self.kiwoom.get_price_data(code)
                # Save to the database (code -> table name)
                insert_df_to_db(self.strategy_name, code, price_df)
            else:
                # Case 2, 3 ,4: Now we have daily data
                # Case 2: The stock market is closed, then save the data obtained by API
                if check_transaction_closed():
                    # Check the most recent date of saved data
                    sql = "select max(`{}`) from `{}`".format('index', code)
                    cur = execute_sql(self.strategy_name, sql)
                    last_date = cur.fetchone()

                    now = datetime.now().strftime("%Y%m%d")

                    # Check if the most recent save date is today
                    if last_date[0] != now:
                        price_df = self.kiwoom.get_price_data(code)
                        # Save to the database (code -> table name)
                        insert_df_to_db(self.strategy_name, code, price_df)

                # Case 3, 4: Extract data stored in the database before or during the market
                # But, candle data extracted is data from the previous day, excluding today
                else:
                    sql = "select * from `{}`".format(code)
                    cur = execute_sql(self.strategy_name, sql)
                    # ['index', 'open', 'high', 'low', 'close', 'volume']
                    cols = [column[0] for column in cur.description]

                    # Convert data from database into DataFrame
                    price_df = pd.DataFrame.from_records(data=cur.fetchall(), columns=cols)
                    price_df = price_df.set_index('index')
                    # store price data to self.universe to access
                    self.universe[code]['price_df'] = price_df

    def set_universe_real_time(self):
        """
        Register to receive universe real-time trading information
        :return:
        """
        # Pass one random fid (must pass at least one fid of any value)
        fids = get_fid("체결시간")

        # Use if want to check market operation classification
        # self.kiwoom.set_real_reg("1000", "", get_fid("장운영구분"), "0")

        # key values mean stock codes
        codes = self.universe.keys()

        # grouping stock codes based on ';'
        codes = ";".join(map(str, codes))

        # Request to receive real-time trading information
        self.kiwoom.set_real_reg("9999", codes, fids, "0")

    def run(self):
        """
        Run a practical role
        :return:
        """
        while self.is_init_success:
            try:
                # Check if the market is opened
                if not check_transaction_open():
                    print("장시간이 아니므로 5분간 대기합니다.")
                    time.sleep(5 * 60)
                    continue

                for idx, code in enumerate(self.universe.keys()):
                    print('[{}/{}_{}]'.format(idx + 1, len(self.universe), self.universe[code]['code_name']))
                    time.sleep(0.5)

                    # Check whether any orders have been received
                    if code in self.kiwoom.order.keys():
                        # There is an order
                        print('접수 주문', self.kiwoom.order[code])

                        # Check the 'untraded quantity'
                        if self.kiwoom.order[code]['미체결수량'] > 0:
                            pass

                    # Check whether it is an item you own
                    elif code in self.kiwoom.balance.keys():
                        print('보유 종목', self.kiwoom.balance[code])
                        # Check of sale target
                        if self.check_sell_signal(code):
                            self.order_sell(code)

                    else:
                        # Whether it is a purchase target and then submit the order
                        self.check_buy_signal_and_order(code)
            except Exception as e:
                print(traceback.format_exc())
                # LINE
                # send_message(traceback.format_exc(), RSI_STRATEGY_MESSAGE_TOKEN)

    def check_sell_signal(self, code):
        """
        Check sell signal
        :param code:
        :return:
        """
        universe_item = self.universe[code]

        # 1. Check whether current transaction info exists
        if code not in self.kiwoom.universe_realtime_transaction_info.keys():
            # If there is no info, function ends
            print("매도대상 확인 과정에서 아직 체결정보가 없습니다.")
            return

        # If exists, Store current market price/high price/low price/current price/cumulative volume
        open = self.kiwoom.universe_realtime_transaction_info[code]['시가']
        high = self.kiwoom.universe_realtime_transaction_info[code]['고가']
        low = self.kiwoom.universe_realtime_transaction_info[code]['저가']
        close = self.kiwoom.universe_realtime_transaction_info[code]['현재가']
        volume = self.kiwoom.universe_realtime_transaction_info[code]['누적거래량']

        # Create a list to add to DataFrame
        today_price_data = [open, high, low, close, volume]

        df = universe_item['price_df'].copy()

        # Add today's date to price data
        df.loc[datetime.now().strftime('%Y%m%d')] = today_price_data

        # RSI(N) Calculation
        period = 2  # Base date setting
        date_index = df.index.astype('str')

        U = np.where(df['close'].diff(1) > 0, df['close'].diff(1), 0)
        D = np.where(df['close'].diff(1) < 0, df['close'].diff(1) * (-1), 0)

        AU = pd.DataFrame(U, index=date_index).rolling(window=period).mean()
        AD = pd.DataFrame(D, index=date_index).rolling(window=period).mean()

        RSI = AU / (AD + AU) * 100
        df['RSI(2)'] = RSI

        # Check the purchase price of stocks
        purchase_price = self.kiwoom.balance[code]['매입가']
        # Find today's RSI(2)
        rsi = df[-1:]['RSI(2)'].values[0]

        # Selling conditions are met -> True
        if rsi > 80 and close > purchase_price:
            return True
        else:
            return False


    def order_sell(self, code):
        """
        Sell order reception
        :param code:
        :return:
        """
        quantity = self.kiwoom.balance[code]['보유수량']
        ask = self.kiwoom.universe_realtime_transaction_info[code]['(최우선)매도호가']

        order_result = self.kiwoom.send_order('send_sell_order', '1001', 2, code, quantity, ask, '00')

        # LINE
        # message = "[{}]sell order is done! quantity:{}, ask:{}, order_result:{}".format(code, quantity, ask,
        #                                                                                order_result)
        # send_message(message, RSI_STRATEGY_MESSAGE_TOKEN)


    def check_buy_signal_and_order(self, code):
        """
        Checks whether the purchase target is available and accepts the order
        :param code:
        :return:
        """
        if not check_adjacent_transaction_closed():
            return False

        universe_item = self.universe[code]

        # Check whether current transaction info exists
        if code not in self.kiwoom.universe_realtime_transaction_info.keys():
            print("매수대상 확인 과정에서 아직 체결정보가 없습니다.")
            return

        open = self.kiwoom.universe_realtime_transaction_info[code]['시가']
        high = self.kiwoom.universe_realtime_transaction_info[code]['고가']
        low = self.kiwoom.universe_realtime_transaction_info[code]['저가']
        close = self.kiwoom.universe_realtime_transaction_info[code]['현재가']
        volume = self.kiwoom.universe_realtime_transaction_info[code]['누적거래량']

        today_price_data = [open, high, low, close, volume]

        df = universe_item['price_df'].copy()

        df.loc[datetime.now().strftime('%Y%m%d')] = today_price_data

        # RSI(N) Calculation
        period = 2
        date_index = df.index.astype('str')

        U = np.where(df['close'].diff(1) > 0, df['close'].diff(1), 0)
        D = np.where(df['close'].diff(1) < 0, df['close'].diff(1) * (-1), 0)
        AU = pd.DataFrame(U, index=date_index).rolling(window=period).mean()
        AD = pd.DataFrame(D, index=date_index).rolling(window=period).mean()

        RSI = AU / (AD + AU) * 100
        df['RSI(2)'] = RSI

        # Calculate moving average based on closing price
        df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean()
        df['ma60'] = df['close'].rolling(window=60, min_periods=1).mean()

        rsi = df[-1:]['RSI(2)'].values[0]
        ma20 = df[-1:]['ma20'].values[0]
        ma60 = df[-1:]['ma60'].values[0]

        idx = df.index.get_loc(datetime.now().strftime('%Y%m%d')) - 2

        close_2days_ago = df.iloc[idx]['close']

        price_diff = (close - close_2days_ago) / close_2days_ago * 100

        # Confirm buy signal (Get order if conditions are met)
        if ma20 > ma60 and rsi < 5 and price_diff < -2:
            # If the total sum of the items already maximum number, then no more puchases
            if (self.get_balance_count() + self.get_buy_order_count()) >= 10:
                return

            # Amount of money calculation
            budget = self.deposit / (10 - (self.get_balance_count() + self.get_buy_order_count()))

            bid = self.kiwoom.universe_realtime_transaction_info[code]['(최우선)매수호가']

            # Order quantity calculation
            quantity = math.floor(budget / bid)

            if quantity < 1:
                return

            # Fee calculation
            amount = quantity * bid
            self.deposit = math.floor(self.deposit - amount * 1.00035)
            # 1.00015 -> real, 1.00035 -> virtual

            if self.deposit < 0:
                return

            order_result = self.kiwoom.send_order('send_buy_order', '1001', 1, code, quantity, bid, '00')

            self.kiwoom.order[code] = {'주문구분': '매수', '미체결수량': quantity}

            # LINE
            """
            message = "[{}]buy order is done! quantity:{}, bid:{}, order_result:{}, deposit:{}, get_balance_count:{}, get_buy_order_count:{}, balance_len:{}".format(
                code, quantity, bid, order_result, self.deposit, self.get_balance_count(), self.get_buy_order_count(),
                len(self.kiwoom.balance))
            send_message(message, RSI_STRATEGY_MESSAGE_TOKEN)
            """

        else:
            return


    def get_balance_count(self):
        """
        Calculate the number of stocks held for which no sell order has been received
        :return:
        """
        balance_count = len(self.kiwoom.balance)
        for code in self.kiwoom.order.keys():
            if code in self.kiwoom.balance and self.kiwoom.order[code]['주문구분'] == "매도" and self.kiwoom.order[code]['미체결수량'] == 0:
                balance_count = balance_count - 1
        return balance_count

    def get_buy_order_count(self):
        """
        Calculate the number of stocks buy order
        :return:
        """
        buy_order_count = 0
        for code in self.kiwoom.order.keys():
            if code not in self.kiwoom.balance and self.kiwoom.order[code]['주문구분'] == "매수":
                buy_order_count = buy_order_count + 1
        return buy_order_count

'''
Need to make a function for check universe database is up-to-date for each month to update
'''