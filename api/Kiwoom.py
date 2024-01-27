from PyQt5.QAxContainer import *
from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time
import pandas as pd
from util.const import *


class Kiwoom(QAxWidget):

    def __init__(self):
        super().__init__()
        self._make_kiwoom_instance()
        self._set_signal_slots()
        self._comm_connect()

        self.account_number = self.get_account_number()
        # Automatically call once when initialize

        self.tr_event_loop = QEventLoop()
        # Variable, waiting for response to TR request

        self.order = {}
        # dictionary containing the order information for the item from stock code
        # dictionary of dictionary
        self.balance = {}
        # dictionary containing purchase information for the stock from stock code
        self.universe_realtime_transaction_info = {}
        # dictionary containing real time transaction information

    def _make_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        # Update API identifier to function to get Open API Control Function

    def _set_signal_slots(self):                                # Slot function to get a response from API
        self.OnEventConnect.connect(self._login_slot)           # Get login response to _login_slot
        self.OnReceiveTrData.connect(self._on_receive_tr_data)  # Set getting response result from TR
        self.OnReceiveMsg.connect(self._on_receive_msg)         # Set receiving TR message to _on_receive_msg
        self.OnReceiveChejanData.connect(self._on_chejan_slot)  # Set receiving conclusion to _on_chejan_slot
        self.OnReceiveRealData.connect(self._on_receive_real_data)  # Set receiving real time transaction data

    def _login_slot(self, err_code):  # Get response of trying login
        if err_code == 0:
            print("JS connected")
        else:
            print("JS NOT connected")
        # Refer from KOA
        self.login_event_loop.exit()  # Exit response loop

    def _comm_connect(self):  # Login Function 
        self.dynamicCall("CommConnect()")

        self.login_event_loop = QEventLoop()  # Begin waiting response for trying login
        self.login_event_loop.exec_()

    def get_account_number(self, tag="ACCNO"):  # Function for getting Account Number
        account_list = self.dynamicCall("GetLoginInfo(QString)", tag)
        account_number = account_list.split(';')[0]  # Environment for simulate
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

    def get_code_list_by_market(self, market_type):  # Function for getting code list
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

    def get_master_code_name(self, code):  # Function for return name from code
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_price_data(self, code):  # Function, retrieves daily information from
        # the stock's listing data to the most recent date
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 0, "0001")

        self.tr_event_loop.exec_()

        ohlcv = self.tr_data

        while self.has_next_tr_data:
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 2, "0001")
            self.tr_event_loop.exec_()

            for key, val in self.tr_data.items():
                ohlcv[key][-1:] = val

        df = pd.DataFrame(ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=ohlcv['date'])
        # Save imported data in Matrix form

        return df[::-1]

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        # Print what response of TR
        # print("[Kiwoom] _on_receive_tr_data is called {} / {} / {}".format(screen_no, rqname, trcode))
        # Get number of response of this request
        tr_data_cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

        if next == '2':
            self.has_next_tr_data = True
        else:
            self.has_next_tr_data = False

        if rqname == "opt10081_req":
            ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

            for i in range(tr_data_cnt):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "일자")
                open = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시가")
                high = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "고가")
                low = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "저가")
                close = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "거래량")

                ohlcv['date'].append(date.strip())
                ohlcv['open'].append(int(open))
                ohlcv['high'].append(int(high))
                ohlcv['low'].append(int(low))
                ohlcv['close'].append(int(close))
                ohlcv['volume'].append(int(volume))

            self.tr_data = ohlcv

        elif rqname == "opw00001_req":
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, 0, "주문가능금액")
            self.tr_data = int(deposit)
            print(self.tr_data)

        elif rqname == "opt10075_req":
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목코드")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목명")
                order_number = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문상태")
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                  "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문가격")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                order_type = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문구분")
                left_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                 "미체결수량")
                executed_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                     "체결량")
                ordered_at = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시간")
                fee = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "당일매매수수료")
                tax = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "당일매매세금")

                # Data conversion and processing
                code = code.strip()
                code_name = code_name.strip()
                order_number = str(int(order_number.strip()))
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())

                current_price = int(current_price.strip().lstrip('+').lstrip('-'))
                order_type = order_type.strip().lstrip('+').lstrip('-')  # Remove plus and minus
                left_quantity = int(left_quantity.strip())
                executed_quantity = int(executed_quantity.strip())
                ordered_at = ordered_at.strip()
                fee = int(fee)
                tax = int(tax)

                # Dictionary conversion with code as key value
                self.order[code] = {
                    '종목코드': code,
                    '종목명': code_name,
                    '주문번호': order_number,
                    '주문상태': order_status,
                    '주문수량': order_quantity,
                    '주문가격': order_price,
                    '현재가': current_price,
                    '주문구분': order_type,
                    '미체결수량': left_quantity,
                    '체결량': executed_quantity,
                    '주문시간': ordered_at,
                    '당일매매수수료': fee,
                    '당일매매세금': tax
                }

            self.tr_data = self.order

        elif rqname == "opw00018_req":
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목번호")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목명")
                quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "보유수량")
                purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                  "매입가")
                return_rate = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                               "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                total_purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                        "매입금액")
                available_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                      "매매가능수량")

                # Data conversion and processing
                code = code.strip()[1:]
                code_name = code_name.strip()
                quantity = int(quantity)
                purchase_price = int(purchase_price)
                return_rate = float(return_rate)
                current_price = int(current_price)
                total_purchase_price = int(total_purchase_price)
                available_quantity = int(available_quantity)

                # Dictionary conversion with code as key value
                self.balance[code] = {
                    '종목명': code_name,
                    '보유수량': quantity,
                    '매입가': purchase_price,
                    '수익률': return_rate,
                    '현재가': current_price,
                    '매입금액': total_purchase_price,
                    '매매가능수량': available_quantity
                }

            self.tr_data = self.balance

        self.tr_event_loop.exit()
        time.sleep(0.5)  # Kiwoom API only allows up to 5 requests per second (0.2 but set 0.5)

    def get_deposit(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00001_req", "opw00001", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    # Get the Cash information you have in the account (investment amount)

    def send_order(self, rqname, screen_no, order_type, code, order_quantity, order_price, order_classification,
                   origin_order_number=""):
        order_result = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [rqname, screen_no, self.account_number, order_type, code, order_quantity,
             order_price, order_classification, origin_order_number])
        return order_result

    '''
    The order processing flow occurs within a program using the API is as follows
    1. SendOrder (order Occurrence)
    2. OnReceiveTrData (After receiving the order, create an order number response)
    3. OnReceiveMsg (Receive order message)
        Function for receiving Korean response (optional function)
    4. OnReceiveChejan (Order reception/conclusion)
    order_classification = 00: Limit order, 03: Market order (only these two can be used in stock market simulator)
    '''

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        print("[Kiwoom] _on_receive_msg is called {} / {}/ {}/ {}".format(screen_no, rqname, trcode, msg))

    def _on_chejan_slot(self, s_gubun, n_item_cnt, s_fid_list):
        print("[Kiwoom] _on_chejan_slot is called {} / {} / {}".format(s_gubun, n_item_cnt, s_fid_list))

        for fid in s_fid_list.split(";"):  # Get fid from list with ";"
            if fid in FID_CODES:  # Confirm the fid codes are in our FID_CODES
                code = self.dynamicCall("GetChejanData(int)", '9001')[1:]  # Remove first character from code
                data = self.dynamicCall("GetChejanData(int)", fid)  # Get data by fid
                data = data.strip().lstrip('+').lstrip('-')  # Remove plus or minus, lstrip -> left strip
                if data.isdigit():
                    data = int(data)
                item_name = FID_CODES[fid]  # Find the item name according to the fid code

                print("{}: {}".format(item_name, data))  # Print data ex)주문 가격:35000
                if int(s_gubun) == 0:  # Submission/Conclusion (0) -> self.order or Balance transfer -> self.balance
                    if code not in self.order.keys():  # If there is no code in order yet, create new one
                        self.order[code] = {}
                    self.order[code].update({item_name: data})  # Save data to order dictionary
                elif int(s_gubun) == 1:
                    if code not in self.balance.keys():  # If there is no code in balance yet, create new one
                        self.balance[code] = {}
                    self.balance[code].update({item_name: data})  # Save data to balance dictionary

        if int(s_gubun) == 0:  # Print result according to s_gubun
            print("* 주문 출력(self.order)")
            print(self.order)
        elif int(s_gubun) == 1:
            print("* 잔고 출력(self.balance)")
            print(self.balance)

    def get_order(self):  # Check today order information
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "0")  # 0:All, 1:Unfinished, 2:Conclude
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")  # 0:All, 1:Sell, 2:Buy
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10075_req", "opt10075", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    """
    1. Run program
    2. Check today order information (confirm received order)
    3. Receive order
    4. Execute _on_chejan_slot function
    5. Save order data
    6. Program termination situation occurs
    7. Rerun program
    8. Order information inquiry
    9. confirm order information and do not reorder
    """

    def get_balance(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00018_req", "opw00018", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    def set_real_reg(self, str_screen_no, str_code_list, str_fid_list, str_opt_type):
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", str_screen_no,
                         str_code_list, str_fid_list, str_opt_type)
        time.sleep(0.5)

    """
    If register (SetRealReg) the items for which you which to receive real-time trading information,
    you can receive continuously from the API server
    """

    def _on_receive_real_data(self, s_code, real_type, real_data):
        if real_type == "장시작시간":
            pass

        elif real_type == "주식체결":
            signed_at = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("체결시간"))

            close = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("현재가"))
            close = abs(int(close))

            high = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('고가'))
            high = abs(int(high))

            open = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('시가'))
            open = abs(int(open))

            low = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('저가'))
            low = abs(int(low))

            top_priority_ask = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('(최우선)매도호가'))
            top_priority_ask = abs(int(top_priority_ask))

            top_priority_bid = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('(최우선)매수호가'))
            top_priority_bid = abs(int(top_priority_bid))

            accum_volume = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('누적거래량'))
            accum_volume = abs(int(accum_volume))

            # print(s_code, signed_at, close, high, open, low, top_priority_ask, top_priority_bid, accum_volume)

            # If the item code does not exist as a key value in the universe_realtime_transaction_info dictionary,
            # create it (when receiving real-time data for the item for the first time)
            if s_code not in self.universe_realtime_transaction_info:
                self.universe_realtime_transaction_info.update({s_code: {}})

            # Data that continues to be received after initial reception is updated using 'update'.
            self.universe_realtime_transaction_info[s_code].update({
                "체결시간": signed_at,
                "시가": open,
                "고가": high,
                "저가": low,
                "현재가": close,
                "(최우선)매도호가": top_priority_ask,
                "(최우선)매수호가": top_priority_bid,
                "누적거래량": accum_volume
            })
