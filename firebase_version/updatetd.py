import sqlite3

DB_NAME = "database.db"

def get_connection():
    """Kết nối đến cơ sở dữ liệu SQLite"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def update_tray(tray_id, x, y, z):
    """Cập nhật tọa độ của khay theo tray_id"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE trays SET x = ?, y = ?, z = ? WHERE id = ?", (x, y, z, tray_id))
    conn.commit()
    conn.close()

def list_trays():
    """Hiển thị tất cả khay"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM trays")
    rows = c.fetchall()
    conn.close()
    return rows

def display_trays():
    """Hiển thị danh sách các khay"""
    trays = list_trays()
    if trays:
        print("\n=== Danh sách khay hiện có ===")
        for tray in trays:
            print(f"ID: {tray['id']} - Name: {tray['name']} - X: {tray['x']} Y: {tray['y']} Z: {tray['z']}")
    else:
        print("Không có khay nào!")

def update_tray_coordinates():
    """Chỉnh sửa tọa độ của khay"""
    display_trays()
    try:
        tray_id = int(input("Nhập ID khay muốn cập nhật tọa độ: "))
        x = int(input("Nhập tọa độ X mới: "))
        y = int(input("Nhập tọa độ Y mới: "))
        z = int(input("Nhập tọa độ Z mới: "))
        
        # Cập nhật tọa độ khay
        update_tray(tray_id, x, y, z)
        print(f"✅ Đã cập nhật tọa độ của khay ID {tray_id} thành X: {x}, Y: {y}, Z: {z}")
    except ValueError:
        print("Lỗi: Vui lòng nhập ID và tọa độ hợp lệ!")

if __name__ == "__main__":
    update_tray_coordinates()
