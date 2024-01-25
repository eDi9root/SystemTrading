from util.RSI_crawling import *
def get_universe():
    # Get crawling results
    df = execute_crawler()

    mapping = {',': '', 'N/A': '0'}
    df.replace(mapping, regex=True, inplace=True)

    # Setting columns to use
    cols = ['거래량', '매출액', '매출액증가율', 'ROE', 'PER']

    # Convert columns to numeric type (string to float)
    df[cols] = df[cols].astype(float)

    # Import data satisfies universe composition conditions (included in docs)
    df = df[(df['거래량'] > 0) & (df['매출액'] > 0) & (df['매출액증가율'] > 0) & (df['ROE'] > 0) & (df['PER'] > 0) & (
        ~df.종목명.str.contains("지주")) & (~df.종목명.str.contains("홀딩스"))]

    # Inverse of PER
    df['1/PER'] = 1 / df['PER']

    # Rank ROE, max = method of handling tie rank
    df['RANK_ROE'] = df['ROE'].rank(method='max', ascending=False)

    # Rank inverse of PER
    df['RANK_1/PER'] = df['1/PER'].rank(method='max', ascending=False)

    # Combined two rank by average
    df['RANK_VALUE'] = (df['RANK_ROE'] + df['RANK_1/PER']) / 2

    # Sort by RANK_VALUE, Smaller RANK_VALUE Larger rank
    df = df.sort_values(by=['RANK_VALUE'])

    # Renew index number of filtered data frame
    df.reset_index(inplace=True, drop=True)

    # Extract the top 200
    df = df.loc[:199]

    # Output universe results to Excel
    df.to_excel('universe.xlsx')
    return df['종목명'].tolist()


if __name__ == "__main__":
    print('Start')
    universe = get_universe()
    print(universe)
    print('End')
