# migrate_trayid2_simple.py
# Thêm cột tray_id2 nếu thiếu, backfill = copy từ tray_id,
# và cung cấp hàm update_medicine() để cập nhật dữ liệu.

import sqlite3

DB_NAME = "database.db"

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def table_exists(conn, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,)
    ).fetchone() is not None

def column_exists(conn, table: str, column: str) -> bool:
    cols = conn.execute(f"PRAGMA table_info({table});").fetchall()
    return any(c["name"] == column for c in cols)

def add_trayid2_and_backfill():
    """Thêm cột tray_id2 nếu thiếu và backfill = copy từ tray_id."""
    with get_conn() as conn:
        if not table_exists(conn, "medicines"):
            raise SystemExit("❌ Không tìm thấy bảng 'medicines' trong DB.")

        # 1) Thêm cột tray_id2 nếu thiếu
        if not column_exists(conn, "medicines", "tray_id2"):
            conn.execute("ALTER TABLE medicines ADD COLUMN tray_id2 INTEGER;")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_medicines_tray2 ON medicines(tray_id2);")
            print("✅ Đã thêm cột tray_id2.")
        else:
            print("= Cột tray_id2 đã tồn tại, bỏ qua bước thêm cột.")

        # 2) Backfill: tray_id2 = tray_id cho các dòng còn NULL và tray_id có giá trị
        cur = conn.execute("""
            UPDATE medicines
            SET tray_id2 = tray_id
            WHERE tray_id2 IS NULL
              AND tray_id IS NOT NULL
        """)
        conn.commit()
        print(f"✅ Đã cập nhật {cur.rowcount} dòng (tray_id2 = tray_id cho dòng còn NULL).")

def update_medicine(med_id: int, **fields) -> int:
    """
    Cập nhật các cột của 1 thuốc theo id.
    Dùng:
        update_medicine(3, price="180000", left_strip=1, left_pill=5)
        update_medicine(5, name="Paracetamol 500", tray_id=2, tray_id2=8)

    Trả về: số dòng được cập nhật (0 hoặc 1). Ném lỗi nếu không có cột hợp lệ.
    """
    allowed = {
        "name", "type", "code", "quantity", "price", "strip", "pill",
        "left_strip", "left_pill", "manu_date", "exp_date", "tray_id", "tray_id2"
    }
    sets, params = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k} = ?")
            params.append(v)

    if not sets:
        raise ValueError("Không có cột hợp lệ để cập nhật.")

    params.append(med_id)
    sql = f"UPDATE medicines SET {', '.join(sets)} WHERE id = ?"

    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"Không tìm thấy thuốc với ID {med_id}")
        return cur.rowcount

def preview(limit: int = 10):
    """In nhanh vài dòng để kiểm tra."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, name, tray_id, tray_id2, price, left_strip, left_pill
            FROM medicines
            ORDER BY id ASC
            LIMIT ?
        """, (limit,)).fetchall()

    if not rows:
        print("(Bảng medicines trống)")
        return

    # In đơn giản
    print("id | name                | tray_id | tray_id2 | price   | left_strip | left_pill")
    print("---+----------------------+---------+---------+---------+------------+----------")
    for r in rows:
        print(f"{str(r['id']).ljust(2)} | {str(r['name'] or '')[:20].ljust(20)} | "
              f"{str(r['tray_id']).ljust(7)} | {str(r['tray_id2']).ljust(7)} | "
              f"{str(r['price']).ljust(7)} | {str(r['left_strip']).ljust(10)} | {str(r['left_pill']).ljust(8)}")

if __name__ == "__main__":
    # Bước 1: đảm bảo có tray_id2 và backfill
    add_trayid2_and_backfill()

    # Bước 2: ví dụ cập nhật (bỏ comment để chạy thử)
    update_medicine(2, tray_id2="4")
    update_medicine(1, tray_id2="2")
    update_medicine(3, tray_id2="6")
    update_medicine(4, tray_id2="8")
        

    # Xem nhanh kết quả
    preview(10)
