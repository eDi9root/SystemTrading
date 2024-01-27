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
                send_message(traceback.format_exc(), RSI_STRATEGY_MESSAGE_TOKEN)

    def check_sell_signal(self, code):
        """
        Check sell signal
        :param code:
        :return:
        """



    def order_sell(self, code):
        """
        Sell order reception
        :param code:
        :return:
        """


    def check_buy_signal_and_order(self, code):
        """
        Checks whether the purchase target is available and accepts the order
        :param code:
        :return:
        """


    def get_balance_count(self):
        """
        Calculate the number of stocks held for which no sell order has been received
        :return:
        """

'''
Need to make a function for check universe database is up-to-date for each month to update
'''