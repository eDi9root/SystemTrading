# dart 
import requests
import zipfile
import xmltodict
import json
import pandas as pd
from io import BytesIO

class Dart():
    def __init__(self, api_key):
        self.API_KEY = api_key
        self.CORPORATE_CODE = self._get_corporate_code()

    # 기업 고유번호
    def _get_corporate_code(self):
        PARAMS = {
            'crtfc_key': self.API_KEY 
        }
        URL = 'https://opendart.fss.or.kr/api/corpCode.xml'
        res = requests.get(URL, params = PARAMS)

        if res.status_code == 200:
            code_file = zipfile.ZipFile(BytesIO(res.content))
            code_data = code_file.read('CORPCODE.xml').decode('utf-8')
            code_dict = xmltodict.parse(code_data)['result']['list']
            df = pd.DataFrame(code_dict)
            df = df[df['stock_code'].notnull()].reset_index(drop = True)     # 비상장 주식회사 제거 
            return df
        
        else:
            print('*** request failed ***')
        
    # 재무제표
    def get_balance_sheet(self, corp_code, year, reprt_code = '11011'):
        '''
        input:
            - corp_code: corporate code (not stock code)
            - year: business year (available from 2015)
            - reprt_code: report code (1Q: 11013, 2Q: 11012, 3Q: 11014, 4Q: 11011 (cumulative))

        output: 
            - balance_sheet(DataFrame)
        '''
        PARAMS = {
            'crtfc_key': self.API_KEY,
            'corp_code': str(corp_code),
            'bsns_year': str(year),
            'reprt_code': str(reprt_code)
        }
        URL = 'https://opendart.fss.or.kr/api/fnlttSinglAcnt.json'
        res = requests.get(URL, params = PARAMS)   
        
        if res.status_code == 200:
            data_dict = json.loads(res.content)
            
            # if there are no data to get
            if data_dict['status'] == '013':
                return

            df = pd.DataFrame(data_dict['list'])
            return df
        else:
            print('*** request failed ***')

    # 기준시점부터 재무데이터 모두 불러오는 함수 
    def get_all_balance_sheet(self, corp_code, year, reprt_code = '11011'): 
        '''
        input:
            - corp_code: corporate code (not stock code)
            - year: business year (available from 2015)
            - reprt_code: report code (1Q: 11013, 2Q: 11012, 3Q: 11014, 4Q: 11011 (cumulative))

        output: 
            - balance_sheet(DataFrame)
        '''
        if not isinstance(year, int): 
            year = int(year)
            years = range(year, 2024)
            years = map(str, years)
        
        df = pd.DataFrame(None)
        for y in years: 
            tmp_df = self.get_balance_sheet(corp_code, y, reprt_code)

            # 조회된 데이터가 없는 경우 
            if tmp_df is None:
                continue

            # preprocess dataframe
            # TODO: Consolidated financial statements VS. Seperated financial statements
            cfs_df = tmp_df[tmp_df['fs_div'] == 'CFS']
            
            data = {}
            for k, v in zip(cfs_df.account_nm.values, cfs_df.thstrm_amount.values):
                data.update({k: v})

            df = pd.concat([df, pd.DataFrame(data, index = [y])])
        
        return df


# test 
if __name__ == '__main__':
    API_KEY = None # your key
    dart = Dart(API_KEY)
    
    ### test: _get_corporate_code ### 
    # print(dart.CORPORATE_CODE)

    ### test: get_balance_sheet ### 
    # df = dart.get_balance_sheet('00126380', '2020', '11011')
    # print(df)

    ### test: get_all_balance_sheet ### 
    # df = dart.get_all_balance_sheet('00126380', '2016', '11011')
    # print(df)