from PyQt5.QAxContainer import *
from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


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
