import requests
import json
import datetime as dt
import pandas as pd
import time

class KIS():
    def __init__(self, app_key, app_secret, mock = True):
        self.app_key = app_key
        self.app_secret = app_secret
        self.url_base = 'https://openapivts.koreainvestment.com:29443' if mock else 'https://openapi.koreainvestment.com:9443'
        self.access_token = self._get_access_token()

    # access token 발급
    def _get_access_token(self):
        path = 'oauth2/tokenP'
        url = f'{self.url_base}/{path}'
        headers = {
            'content-type': 'application/json'
        }
        body = {
            'grant_type': 'client_credentials',
            'appkey': app_key,
            'appsecret': app_secret
        }

        res = requests.post(url, headers = headers, data = json.dumps(body))
        access_token = res.json()['access_token']

        return access_token

    # 해쉬키 발급
    def _get_hashkey(self, body):
        path = 'uapi/hashkey'
        url = f'{self.url_base}/{path}'
        headers = {
            'content-type': 'application/json',
            'appkey': self.app_key,
            'appsecret': self.app_secret
        }

        res = requests.post(url, headers = headers, data = json.dumps(body))
        hashkey = res.json()['HASH']

        return hashkey

    # 주식 현재가 시세 조회
    def get_current_price(self, code):
        path = 'uapi/domestic-stock/v1/quotations/inquire-price'
        url = f'{self.url_base}/{path}'
        headers = {
            'content-type': 'application/json',
            'authorization': f'Bearer {self.access_token}',
            'appkey': self.app_key,
            'appsecret': self.app_secret,
            'tr_id': 'FHKST01010100'
        }
        params = {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': str(code)
        }

        res = requests.get(url, headers = headers, params = params)
        # TODO: preprocess response output
        return res
    
    # 국내주식기간별시세
    def get_periodic_price(self, code, start, end, period = 'D'):
        path = 'uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice'
        url = f'{self.url_base}/{path}'
        headers = {
            'content-type': 'application/json',
            'authorization': f'Bearer {self.access_token}',
            'appkey': self.app_key,
            'appsecret': self.app_secret,
            'tr_id': 'FHKST03010100',
        }
        
        df = pd.DataFrame(None)
        s = dt.datetime.strptime(start, '%Y%m%d')
        isin = True
        while isin:
            e = s + dt.timedelta(days = 100)
            
            if e > dt.datetime.strptime(end, '%Y%m%d'):
                e = dt.datetime.strptime(end, '%Y%m%d')
                isin = False
                
            params = {
                'FID_COND_MRKT_DIV_CODE': 'J',
                'FID_INPUT_ISCD': str(code),
                'FID_INPUT_DATE_1': dt.datetime.strftime(s, '%Y%m%d'),
                'FID_INPUT_DATE_2': dt.datetime.strftime(e, '%Y%m%d'),
                'FID_PERIOD_DIV_CODE': 'D',
                'FID_ORG_ADJ_PRC': '0'
            }
            
            res = requests.get(url, headers = headers, params = params)

            s = e
            data = res.json()['output2']
            df = pd.concat([pd.DataFrame(data), df])
            time.sleep(0.1)
        
        # preprocess dataframe: TODO
        df['stck_bsop_date'] = pd.to_datetime(df['stck_bsop_date'])
        df.set_index('stck_bsop_date', inplace = True)
        df.dropna(inplace = True)
        
        return df
    
# test
if __name__ == '__main__':
    app_key =  None # your appkey
    app_secret = None # your appsecret
    kis = KIS(app_key, app_secret)

    # test get_current_price
    res = kis.get_current_price('005930') # samsung electronics
    print(res)

    # test periodic_price
    df = kis.get_periodic_price('005930', '20130101', '20231231')
    print(df)