import sqlite3

DB_NAME = "database.db"

def get_connection():
    """Trả về connection mới đến database"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Trả về dict-like thay vì tuple
    return conn

def init_db():
    """Tạo bảng nếu chưa có"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    type TEXT,
    code TEXT,
    manu_date TEXT,
    exp_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

    """)
    conn.commit()
    conn.close()
