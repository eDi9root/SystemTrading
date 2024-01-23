import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root',
                       password='systemtradingpy0',
                       db='universe_price', charset='utf8')

cur = conn.cursor()

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




conn.commit()

conn.close()
