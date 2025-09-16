import sqlite3

DB_NAME = "database.db"

def get_connection():
    """Trả về connection mới đến database"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Trả về dict-like thay vì tuple
    return conn
def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table});")}
    return column in cols

def init_db():
    """Tạo bảng nếu chưa có"""
    conn = get_connection()
    c = conn.cursor()

    # Bảng khay (tray)
    c.execute("""
    CREATE TABLE IF NOT EXISTS trays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,                       -- tên khay
        x REAL,                        -- tọa độ X
        y REAL,                        -- tọa độ Y
        z REAL,                        -- tọa độ Z
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    type TEXT,
    code TEXT,
    quantity TEXT,
    price TEXT,
    strip TEXT,
    pill TEXT,
    left_strip INTEGER DEFAULT 0, -- vỉ lẻ còn lại của hộp đang bán
    left_pill INTEGER DEFAULT 0,  -- viên lẻ còn lại của vỉ đang bán
    manu_date TEXT,
    exp_date TEXT,
    tray_id INTEGER,
    tray_id2 INTEGER,  -- khay phụ (nếu có)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tray_id) REFERENCES trays(id)
)
    
    """)
    if not column_exists(conn, "medicines", "tray_id2"):
        conn.execute("ALTER TABLE medicines ADD COLUMN tray_id2 INTEGER;")
    c.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER,
        customer_name TEXT,
        hometown TEXT,
        dob TEXT,
        unit TEXT,              -- Hộp / Vỉ / Viên
        quantity INTEGER,
        total_price REAL,
        advice TEXT,
        purchase_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
