import sqlite3

DB_NAME = "database.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def add_tray(name,x, y, z):
    """Thêm 1 khay mới vào database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO trays (name,x, y, z) VALUES (?,?, ?, ?)", (name,x, y, z))
    conn.commit()
    tray_id = c.lastrowid
    conn.close()
    return tray_id

def delete_trays_by_id_range(start_id, end_id):
    """
    Xóa các khay có ID từ start_id đến end_id (bao gồm cả start_id và end_id)
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM trays WHERE id BETWEEN ? AND ?", (start_id, end_id))
    conn.commit()
    deleted_count = c.rowcount
    conn.close()
    return deleted_count

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
    # t1 = add_tray('A1',35,0,30)
    # t2 = add_tray('A2',42,0,185)
    # t3 = add_tray('A3',39,0,267)   
    # t4 = add_tray('A4',43,0,415)   
    # t5 = add_tray('B1',75,0,32)     
    # t6 = add_tray('B2',75,0,185)           
    # t7 = add_tray('B3',76,0,267)
    # t8 = add_tray('B4',76,0,415)
    # t9 = add_tray('C1',62,0,515)
    # t10 = add_tray('C2',0,0,300)

    # print("✅ Đã thêm các khay:", t1, t2, t3, t4, t5, t6, t7, t8, t9, t10)

    # In ra danh sách khay

    # deleted = delete_trays_by_id_range(11, 20)
    # print(f"✅ Đã xóa {deleted} khay có ID từ 11 đến 20")
    print("\n=== Danh sách khay hiện có ===")
    for tray in list_trays():
        print(dict(tray))
