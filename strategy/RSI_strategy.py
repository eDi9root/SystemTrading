from api.Kiwoom import *
from util.RSI_universe import *
from util.db_helper import *
from util.time_helper import *
import math


class RSIStrategy(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.strategy_name = "RSIStrategy"
        self.kiwoom = Kiwoom()
        self.universe = {}

        self.init_strategy()

    def init_strategy(self):
        """
        Performs strategy initialization function
        """
        self.check_and_get_universe()
        self.check_and_get_price_data()

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
    def run(self):
        pass


'''
Need to make a function for check universe database is up-to-date for each month to update
'''