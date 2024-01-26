import datetime as dt
import pandas as pd 

class Momentum(): 
    def __init__(self, period = '12'):
        
        # TODO: 데이터베이스 쿼리
        # row: 최근 m개월 종가
        # column: 각 종목명(종목코드)
        self.stock_list = None
        self.data = None 
        self.period = period
        self.momentum_rank = None

    def get_momentum_rank(self, rank = 30):
        # calculate rate of return
        ret = pd.DataFrame(data = (self.data.iloc[-1] / self.data.iloc[0]) - 1, columns = ['return'])
        ret.index.names = ['Code']
        
        # merge stock_code, stock_name, return
        data = self.stock_list[['Code', 'Name']].merge(ret, how = 'left', on = 'Code')
        data.sort_values(['return'], ascending = False)

        self.momentum_rank = data.iloc[0:rank,]

        return self.momentum_rank
    
    def get_k_ratio_momentum(self, rank = 30):
        # TODO
        pass

    def plot_momentum(self):
        if self.momentum_rank is None:
            print('You must call get_momentum_rank before plotting')
            pass
        
        # TODO
        pass