import sqlite3

conn = sqlite3.connect("database.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Xem danh sách bảng
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [row[0] for row in c.fetchall()])

# Xem dữ liệu trong bảng medicines
c.execute("SELECT * FROM sales")

rows = c.fetchall()

for row in rows:
    print(dict(row))

conn.close()
