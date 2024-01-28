import pymysql
from sqlalchemy import create_engine

HOSTNAME = '127.0.0.1'
USER = 'root'
PASSWORD = 'systemtradingpy0'


def check_table_exist(db_name, table_name):
    conn = pymysql.connect(host=HOSTNAME, user=USER,
                           password=PASSWORD,
                           db=db_name, charset='utf8')
    cur = conn.cursor()
    check = "SHOW TABLES LIKE '{}'".format(table_name)
    cur.execute(check)
    result = cur.fetchall()

    # print(len(result))
    if len(result) > 0:
        return True
    else:
        return False


def insert_df_to_db(db_name, table_name, df, index, option="replace"):
    db_connection_str = f'mysql+pymysql://{USER}:{PASSWORD}@{HOSTNAME}/{db_name}'
    db_connection = create_engine(db_connection_str)
    conn = db_connection
    df.to_sql(table_name, conn, index=index, if_exists=option)


def execute_sql(db_name, sql, param={}):
    conn = pymysql.connect(host=HOSTNAME, user=USER,
                           password=PASSWORD,
                           db=db_name, charset='utf8')
    cur = conn.cursor()
    cur.execute(sql, param)
    return cur


"""
Data insert: INSERT
cur.execute("INSERT INTO balance VALUES('007700', 70000, 10, '20201222', 'today')")

Data check: SELECT
cur.execute('SELECT * FROM balance')
cur.execute('SELECT code, created_at FROM balance')
row = cur.fetchone()
row = cur.fetchall()
print(row)

Data update: UPDATE
cur.execute("UPDATE balance SET will_clear_at=: ... where ...")
print(cur.rowcount)

Data delete: DELETE
# if you want to delete whole table, then use DROP
cur.execute("DELETE FROM balance where will_clear_at ...")

"""
# conn.close()
# conn.commit()
