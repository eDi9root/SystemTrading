# dart 
import requests
import zipfile
import xmltodict
import pandas as pd
from io import BytesIO

class Dart():
    def __init__(self, api_key):
        self.API_KEY = api_key
        self.CORPORATE_CODE = self._get_company_code()

    # 기업 고유번호
    def _get_company_code(self):
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
        
            

# test 
if __name__ == '__main__':
    API_KEY = None # your key
    dart = Dart(API_KEY)
    print(dart.CORPORATE_CODE)