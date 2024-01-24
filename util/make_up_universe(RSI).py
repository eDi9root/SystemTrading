import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from datetime import datetime

BASE_URL = 'https://finance.naver.com/sise/sise_market_sum.nhn?sosok='
START_PAGE = 1
fields = []

CODES = [0, 1] # KOSPI:0, KOSDAQ:1


# Extract total number of pages based on the tag 'last'
res = requests.get(BASE_URL + str(CODES[0]))
page_soup = BeautifulSoup(res.text,'lxml')

total_page_num = page_soup.select_one('td.pgRR > a')
total_page_num = int(total_page_num.get('href').split('=')[-1])

# Extract searchable item names
ipt_html = page_soup.select_one('div.subcnt_sise_item_top')
fields = [item.get('value') for item in ipt_html.select('input')]
print(fields)



"""
43 pg, 50 each, 2149 total (2024-01-23)
"""