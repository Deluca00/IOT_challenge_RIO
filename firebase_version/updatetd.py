import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB_NAME = "database.db"

# -------------------- DB Helpers --------------------

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_trays():
    """Chỉ đọc dữ liệu, KHÔNG tạo bảng tự động."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, x, y, z FROM trays ORDER BY id ASC")
        return cur.fetchall()

def update_tray(tray_id: int, x: float, y: float, z: float):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE trays SET x = ?, y = ?, z = ? WHERE id = ?", (x, y, z, tray_id))
        if cur.rowcount == 0:
            raise ValueError(f"Không tìm thấy khay với ID {tray_id}")

# -------------------- UI --------------------

class TrayApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.master = master
        self.master.title("Cập nhật tọa độ khay (SQLite)")
        self.pack(fill=tk.BOTH, expand=True)

        self._build_widgets()
        self._load_trays()

    # ---------- Build ----------
    def _build_widgets(self):
        # Top controls
        top = ttk.Frame(self)
        top.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(top, text="Danh sách khay").pack(side=tk.LEFT)
        ttk.Button(top, text="Làm mới", command=self._load_trays).pack(side=tk.RIGHT)

        # Treeview
        cols = ("id", "name", "x", "y", "z")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c, w in zip(cols, (60, 180, 100, 100, 100)):
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, width=w, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Form
        form = ttk.LabelFrame(self, text="Chỉnh sửa tọa độ")
        form.pack(fill=tk.X, pady=8)

        # ID (readonly)
        ttk.Label(form, text="ID:").grid(row=0, column=0, sticky=tk.W, padx=8, pady=6)
        self.var_id = tk.StringVar()
        self.ent_id = ttk.Entry(form, textvariable=self.var_id, width=12, state="readonly")
        self.ent_id.grid(row=0, column=1, sticky=tk.W, padx=(0, 16))

        # Name (readonly)
        ttk.Label(form, text="Tên:").grid(row=0, column=2, sticky=tk.W, padx=8)
        self.var_name = tk.StringVar()
        self.ent_name = ttk.Entry(form, textvariable=self.var_name, width=24, state="readonly")
        self.ent_name.grid(row=0, column=3, sticky=tk.W, padx=(0, 16))

        # Float validators
        vcmd = (self.register(self._validate_float), "%P")

        # X
        ttk.Label(form, text="X:").grid(row=1, column=0, sticky=tk.W, padx=8)
        self.var_x = tk.StringVar()
        self.ent_x = ttk.Entry(form, textvariable=self.var_x, width=12, validate="key", validatecommand=vcmd)
        self.ent_x.grid(row=1, column=1, sticky=tk.W, padx=(0, 16))

        # Y
        ttk.Label(form, text="Y:").grid(row=1, column=2, sticky=tk.W, padx=8)
        self.var_y = tk.StringVar()
        self.ent_y = ttk.Entry(form, textvariable=self.var_y, width=12, validate="key", validatecommand=vcmd)
        self.ent_y.grid(row=1, column=3, sticky=tk.W, padx=(0, 16))

        # Z
        ttk.Label(form, text="Z:").grid(row=1, column=4, sticky=tk.W, padx=8)
        self.var_z = tk.StringVar()
        self.ent_z = ttk.Entry(form, textvariable=self.var_z, width=12, validate="key", validatecommand=vcmd)
        self.ent_z.grid(row=1, column=5, sticky=tk.W, padx=(0, 16))

        # Buttons
        btns = ttk.Frame(form)
        btns.grid(row=2, column=0, columnspan=6, sticky=tk.EW, pady=(6, 8))
        btns.columnconfigure(0, weight=1)
        ttk.Button(btns, text="Lưu cập nhật", command=self._save).grid(row=0, column=1, sticky=tk.E, padx=6)
        ttk.Button(btns, text="Bỏ chọn", command=self._clear_form).grid(row=0, column=2, sticky=tk.E)

        # Status bar
        self.status = tk.StringVar(value="Sẵn sàng")
        ttk.Label(self, textvariable=self.status, anchor=tk.W).pack(fill=tk.X, pady=(4, 0))

        # Style tweaks for nicer look
        style = ttk.Style()
        try:
            self.master.call("source", "azure.tcl")  # If you have a Tk theme file
            style.theme_use("azure")
        except Exception:
            pass

    # ---------- Data Ops ----------
    def _load_trays(self):
        self.tree.delete(*self.tree.get_children())
        try:
            rows = fetch_trays()
            for row in rows:
                self.tree.insert("", tk.END, values=(row["id"], row["name"], row["x"], row["y"], row["z"]))
            self.status.set("Đã tải danh sách khay")
        except sqlite3.OperationalError as e:
            messagebox.showerror("Lỗi cơ sở dữ liệu", f"Không thể đọc bảng 'trays': {e}\nHãy tự tạo bảng và dữ liệu trước khi chạy.")
            self.status.set("Lỗi: thiếu bảng 'trays'")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu: {e}")
            self.status.set("Không thể tải dữ liệu")

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        tray_id, name, x, y, z = vals
        self.var_id.set(str(tray_id))
        self.var_name.set(str(name))
        self.var_x.set(str(x))
        self.var_y.set(str(y))
        self.var_z.set(str(z))
        self.status.set(f"Đang chọn khay ID {tray_id}")

    def _clear_form(self):
        self.var_id.set("")
        self.var_name.set("")
        self.var_x.set("")
        self.var_y.set("")
        self.var_z.set("")
        self.tree.selection_remove(self.tree.selection())
        self.status.set("Đã bỏ chọn")

    def _validate_float(self, proposed: str) -> bool:
        # allow empty during editing, enforce float on save
        if proposed in ("", "-", "."):
            return True
        try:
            float(proposed)
            return True
        except ValueError:
            self.bell()
            return False

    def _save(self):
        if not self.var_id.get():
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng chọn một khay trong danh sách.")
            return
        try:
            tray_id = int(self.var_id.get())
            x = float(self.var_x.get())
            y = float(self.var_y.get())
            z = float(self.var_z.get())
            update_tray(tray_id, x, y, z)
            self._load_trays()
            self.status.set(f"✅ Đã cập nhật tọa độ khay ID {tray_id} -> X:{x} Y:{y} Z:{z}")
        except ValueError as e:
            messagebox.showerror("Lỗi", f"Giá trị không hợp lệ hoặc không tìm thấy: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật: {e}")


def main():
    root = tk.Tk()
    root.minsize(640, 480)
    TrayApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
