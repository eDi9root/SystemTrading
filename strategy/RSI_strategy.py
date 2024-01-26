from api.Kiwoom import *
from util.RSI_universe import *
from util.db_helper import *


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

    def run(self):
        pass


'''
Need to make a function for check universe database is up-to-date for each month to update
'''