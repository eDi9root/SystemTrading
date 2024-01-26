from strategy.RSI_strategy import *
import sys

app = QApplication(sys.argv)


rsi_strategy = RSIStrategy()
rsi_strategy.start()

app.exec_()
# Auto login
