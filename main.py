
from api.Kiwoom import *
import sys

app = QApplication(sys.argv)
kiwoom = Kiwoom()

"""
orders = kiwoom.get_order()
print(orders)
"""

"""
order_result = kiwoom.send_order('send_buy_order',
                                 '1001', 1,
                                 '007700', 1,
                                 37600, '00')

print(order_result)
"""

# kiwoom.get_account_number()

# deposit = kiwoom.get_deposit()

"""
order_result = kiwoom.send_order('send_buy_order', '1001', 1,
                                 '007700', 1, 35000, '00')
print(order_result)
"""

"""
df = kiwoom.get_price_data("005930") # SAMSUNG information
print(df)


Kospi_code_list = kiwoom.get_code_list_by_market("0")  # KOSPI number
print(Kospi_code_list)
for code in Kospi_code_list:
    code_name = kiwoom.get_master_code_name(code)
    print(code, code_name)

Kosdaq_code_list = kiwoom.get_code_list_by_market("10") # KOSDAP number
print(Kosdaq_code_list)
for code in Kosdaq_code_list:
    code_name = kiwoom.get_master_code_name(code)
    print(code, code_name)
"""

app.exec_()
# Auto login
