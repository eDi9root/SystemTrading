# Python_project_SystemTrading with Bank API

## About

### 1. Strategy
- Counter-trend Strategy Based On `RSI`
    ```
    RSI = 100 * AU / (AU+AD)
    RS = AU / AD
    RSI Signal = moving average line of RSI
  
    # Assuming mean reversion effect
    # Used RSI(2), judged based on the closing prices of the last two days for short term
    # USed RSI Signal (20 or 60) for mid-term trend
    ```
- Conditions
    ```python
    if RSI_Signal(20) > RSI_Signal(60) and
       RSI(2) < 5 and
       Current stock price change rate compared to two days ago < -2%:
       
       Result = Buy at the current highest bid price
  
    if RSI(2) > 80 and
       Current price > Buying Price:
  
       Result = Sell at the current best ask price
    ```
- Universe Composition
    ```
    1. Excluding ETF, preferred stock 
    2. Excluding holding companies
    3. Selecting companies with a sales growth rate greater than 0
    4. Selecting companies with an ROE greater than 0
    5. Sorting ROE and 1/PER in descending order, 
        extracting 200 companies by calculating the average of the two ranks
    ```
- Backtesting


### How To Run
  ```
  Development Tools:    # PyCharm 2023.2.3  # Anaconda3
  Programming Language: # Python
  API:                  # Kiwoom Open API+
  Database:             # sqlite3
  ```

### Logical Structure (initialization phase)
<img src="https://github.com/eDi9root/SystemTrading/blob/main/Documents/Logical%20structure.png" 
alt="Logical Structure" width=300>

### Logical Structure (post)
<img src="https://github.com/eDi9root/SystemTrading/blob/main/Documents/post%20logical%20structure.png" 
alt="Logical Structure" width=300>

### Continous Development
  ```
  This project continues to progress and further implements the strategy.
  ```

