import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from datetime import datetime

BASE_URL = 'https://finance.naver.com/sise/sise_market_sum.nhn?sosok='
START_PAGE = 1
fields = []
CODES = [0, 1]  # KOSPI:0, KOSDAQ:1

now = datetime.now()
formattedDate = now.strftime("%Y%m%d")


def execute_crawler():
    # Variable used to combine KOSPI, KOSDAQ into one
    df_total = []

    # KOSPI, KOSDAQ items in CODES
    for code in CODES:
        # Get the total number of pages
        res = requests.get(BASE_URL + str(CODES[0]))
        page_soup = BeautifulSoup(res.text, 'lxml')

        # Extract the total number of pages based on tag 'last'
        total_page_num = page_soup.select_one('td.pgRR > a')
        total_page_num = int(total_page_num.get('href').split('=')[-1])

        # Extract item information can be searched
        ipt_html = page_soup.select_one('div.subcnt_sise_item_top')

        # Put items in the global variable, can be accessed from other functions
        global fields
        fields = [item.get('value') for item in ipt_html.select('input')]

        # Crawl the information of all items exist on each page and store it
        result = [crawler(code, str(page)) for page in range(1, total_page_num + 1)]

        # Create data frame of the result of the entire page
        df = pd.concat(result, axis=0, ignore_index=True)

        # append to df_total to combine into one
        df_total.append(df)

    # Create merged data frame of df_total
    df_total = pd.concat(df_total)

    # Re-number the index of the merged data frame
    df_total.reset_index(inplace=True, drop=True)

    # Output entire crawl results to Excel
    df_total.to_excel('NaverFinance.xlsx')

    return df_total


def crawler(code, page):
    global fields

    # Setting the values to be delivered to Naver finance
    data = {'menu': 'market_sum',
            'fieldIds': fields,
            'returnUrl': BASE_URL + str(code) + "&page=" + str(page)}

    # Send request using post method
    res = requests.post('https://finance.naver.com/sise/field_submit.nhn', data=data)

    page_soup = BeautifulSoup(res.text, 'lxml')

    # Retrieve the HTML of the table (check the class of the element in the browser)
    table_html = page_soup.select_one('div.box_type_l')

    # Process the column name
    header_data = [item.get_text().strip() for item in table_html.select('thead th')][1:-1]

    # Extract Stock name + numerical value (a.title = stock name, td.number = other numerical values)
    inner_data = [item.get_text().strip() for item in table_html.find_all(lambda x:
                                                                          (x.name == 'a' and
                                                                           'tltle' in x.get('class', [])) or
                                                                          (x.name == 'td' and
                                                                           'number' in x.get('class', []))
                                                                          )]

    # Get the order number of items on each page
    no_data = [item.get_text().strip() for item in table_html.select('td.no')]
    number_data = np.array(inner_data)

    # Re size Matrix to fit horizontal x vertical
    number_data.resize(len(no_data), len(header_data))

    # Collect info obtained from one page and return it
    df = pd.DataFrame(data=number_data, columns=header_data)
    return df
