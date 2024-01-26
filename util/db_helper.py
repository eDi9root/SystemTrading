import pymysql


def check_table_exist(db_name, table_name):
    conn = pymysql.connect(host='127.0.0.1', user='root',
                           password='systemtradingpy0',
                           db='{}'.format(db_name), charset='utf8')
    cur = conn.cursor()
    check = "SHOW TABLES LIKE '{}'".format(table_name)
    cur.execute(check)
    print(check)
    result = cur.fetchall()

    if len(result) > 0:
        return True
    else:
        return False



# conn.close()

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

# conn.commit()


