from PyQt5.QAxContainer import *
from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time


class Kiwoom(QAxWidget):

    def __init__(self):
        super().__init__()
        self._make_kiwoom_instance()
        self._set_signal_slots()
        self._comm_connect()

        self.account_number = self.get_account_number()
        # Automatically call once when initialize

    def _make_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        # Update API identifier to function to get Open API Control Function

    def _set_signal_slots(self): # Slot function to get a response from API
        self.OnEventConnect.connect(self._login_slot) # Get login response to _login_slot

        self.OnReceiveTrData.connect(self._on_receive_tr_data) # Set getting response result from TR

    def _login_slot(self, err_code): # Get response of trying login
        if err_code == 0:
            print("JS connected")
        else:
            print("JS NOT connected")
        # Refer from KOA
        self.login_event_loop.exit() # Exit response loop

    def _comm_connect(self):  # Login Function 
        self.dynamicCall("CommConnect()")

        self.login_event_loop = QEventLoop()  # Begin waiting response for trying login
        self.login_event_loop.exec_()

    def get_account_number(self, tag="ACCNO"): # Function for getting Account Number
        account_list = self.dynamicCall("GetLoginInfo(QString)", tag)
        account_number = account_list.split(';')[0] # Environment for simulate
        print(account_number)
        return account_number
    """ 
    "ACCOUNT_CNT" : Number of own accounts
    "ACCLIST" or "ACCNO" : List of accounts with ';'
    "USER_ID" : Return user ID
    "USER_NAME" : Return user name
    "GetServerGubun" : Return connected server (1 : Simulated Investment, others : Real world server)
    "KEY_BSECGB" : Return Whether to disable keyboard security (0 : Normal, 1: Disable)
    "FIREW_SECGB" : Return Whether Firewall settings (0 : Not set, 1: Set, 2: Disable)
    """

    def get_code_list_by_market(self, market_type): # Function for getting code list
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_type)
        code_list = code_list.split(';')[:-1]
        return code_list
    '''
    Get List by Market
    KOA Developing Guide -> other functions -> Functions related to Stock information
    KOA의 개발 가이드 -> 기타 함수 -> 종목 정보 관련 함수
    0: KOSPI
    10: KOSDAQ
    3: ELW
    8: ETF
    50: KONEX
    4: Mutual Fund
    5: New stock warrant
    6: Ritz
    9: Haier Fund
    30: K-OTC
    '''

    def get_master_code_name(self, code): # Function for return name from code
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        print("[Kiwoom] _on_receive_tr_data is called {} / {} / {}".format(screen_no, rqname, trcode)) # Print what response of TR
        tr_data_cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname) # Get number of response of this request

        if next == '2':
            self.has_next_tr_data = True
        else:
            self.has_next_tr_data = False

        if rqname == "opt10081_req":
            oh1cv = {'data': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

            for i in range(tr_data_cnt):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "일자")
                open = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시가")
                high = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "고가")
                low = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "저가")
                close = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "거래량")

                oh1cv['data'].append(data.strip())
                oh1cv['open'].append(int(open))
                oh1cv['high'].append(int(high))
                oh1cv['low'].append(int(low))
                oh1cv['close'].append(int(close))
                oh1cv['volume'].append(int(volume))

            self.tr_data = oh1cv

        self.tr_event_loop.exit()
        time.sleep(0.5) # Kiwoom API only allows up to 5 requests per second (0.2 but set 0.5)




    self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 0, "0001")
    # Function CommRqData -> return 0 is normal, rest is an error
    """
    Get Price Information
    일봉이란 1일 거래 동안의 주가 변동을 캔들 차트로 표현한 것
    당일 장 마감때 가격(종가)이 시작 가격(시가)보다 상승하면 양봉, 반대면 음봉이라 한다
    양봉은 빨간색, 음봉은 파란색
    가격 정보란 '시가, 저가, 종가, 고가'를 의미한다
    """

