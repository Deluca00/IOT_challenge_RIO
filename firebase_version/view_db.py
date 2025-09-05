import sqlite3

DB_NAME = "database.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def add_tray(x, y, z):
    """Thêm 1 khay mới vào database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO trays (x, y, z) VALUES (?, ?, ?)", (x, y, z))
    conn.commit()
    tray_id = c.lastrowid
    conn.close()
    return tray_id

def list_trays():
    """Hiển thị tất cả khay"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM trays")
    rows = c.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    # Thêm nhanh vài khay mẫu
    t1 = add_tray(10.5, 20.2, 5.0)
    t2 = add_tray(15.0, 25.0, 7.5)
    t3 = add_tray(5.0, 12.0, 3.5)

    print("✅ Đã thêm các khay:", t1, t2, t3)

    # In ra danh sách khay
    print("\n=== Danh sách khay hiện có ===")
    for tray in list_trays():
        print(dict(tray))
