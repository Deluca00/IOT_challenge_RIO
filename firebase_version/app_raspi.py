from flask import Flask, Response, render_template,request, redirect, url_for, session, jsonify, send_file
import io
import datetime 
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import cv2
import threading
import time
import numpy as np
import base64
from pyzbar.pyzbar import decode
from database import get_connection, init_db
from collections import defaultdict

import os
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"


app = Flask(__name__)
app.secret_key = "supersecretkey" 
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024  # 30 MB

init_db()
###############################################################################
# CẤU HÌNH NGUỒN CAMERA
# - Có thể là chỉ số webcam (0,1,2,3) hoặc URL RTSP/HTTP.
# - Ví dụ thay bằng rtsp/HTTP: "rtsp://user:pass@192.168.1.10/stream1"
###############################################################################
CAMERA_SOURCES = [
    {"type": "usb", "index": 3},   # /dev/video0
    {"type": "usb", "index": 0},   # /dev/video1
    # {"type": "usb", "index": 6}  # Pi Camera
]

# Nếu bạn chỉ có 1-2 webcam, có thể tạm copy nguồn:
# CAMERA_SOURCES = [0, 0, 0, 0]

###############################################################################
# LỚP QUẢN LÝ CAMERA: mở cv2.VideoCapture và chạy thread đọc khung hình
###############################################################################
class CameraStream:
    def __init__(self, source, cam_name="Camera"):
        self.cam_name = cam_name
        self.running = False
        self.frame = None
        self.lock = threading.Lock()

        if isinstance(source, dict):
            if source["type"] == "usb":
                self.src = int(source["index"])
            elif source["type"] == "csi":
                self.src = int(source["index"])
            elif source["type"] == "ip":
                self.src = source["url"]
            else:
                raise ValueError("❌ Unknown camera type")
        else:
            self.src = source

        # mở camera
        self.cap = cv2.VideoCapture(self.src)
        if not self.cap.isOpened():
            print(f"❌ Không mở được camera: {self.src}")

    def start(self):
        if self.running:
            return
        if not self.cap.isOpened():
            # thử mở lại
            self.cap.release()
            self.cap = cv2.VideoCapture(self.src)

        self.running = True
        self.thread = threading.Thread(target=self.update, name=f"Reader-{self.cam_name}", daemon=True)
        self.thread.start()

    def update(self):
        # vòng lặp đọc khung
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                # chờ một chút rồi thử lại (đặc biệt với RTSP)
                time.sleep(0.2)
                # thử reopen
                self.cap.release()
                self.cap = cv2.VideoCapture(self.src)
                continue

            # (Tuỳ chọn) xử lý ảnh, vẽ overlay...
            # cv2.putText(frame, self.cam_name, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            

            with self.lock:
                self.frame = frame

        # khi dừng
        self.cap.release()

    def get_jpeg(self):
        # Lấy frame hiện tại và mã hoá JPEG
        with self.lock:
            frame = None if self.frame is None else self.frame.copy()
        if frame is None:
            return None
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ok:
            return None
        return buf.tobytes()

    def stop(self):
        self.running = False
        # không join ở đây để không block shutdown
        # stream vẫn có thể chạy xuyên suốt nếu bạn không gọi stop()


# Khởi tạo 4 camera
streams = []
for idx, src in enumerate(CAMERA_SOURCES, start=1):
    streams.append(CameraStream(src, cam_name=f"Camera {idx}"))


###############################################################################
# ROUTES
###############################################################################

@app.route("/")
def root():
    # Nếu chưa login → render login.html
    if "uid" not in session:
        return render_template("login.html")
    return redirect(url_for("dashboard"))

# Users demo (có thể thay bằng bảng users sau này)
USERS = {
    "admin@test.com": {"password": "123456", "role": "admin"},
    "staff@test.com": {"password": "123456", "role": "staff"},
}


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    user = USERS.get(email)
    if user and user["password"] == password:
        session["uid"] = email
        session["role"] = user["role"]  # <-- lưu role
        return redirect(url_for("dashboard"))
    return render_template("login.html", error="Sai tài khoản hoặc mật khẩu")



@app.route("/dashboard")
def dashboard():
    if "uid" not in session:
        return redirect(url_for("root"))
    cameras = [
        {"id": 1, "name": "Camera 1: Cổng trước"},
        {"id": 2, "name": "Camera 2: Cổng sau"},
        {"id": 3, "name": "Camera 3: Nhà kho"},
        {"id": 4, "name": "Camera 4: Văn phòng"},
    ]
    return render_template("index.html", cameras=cameras,role=session.get("role"))
# @app.route("/nhapthuoc")
# def nhapthuoc():
#     if "uid" not in session:   # bắt buộc login
#         return redirect(url_for("root"))
#     return render_template("nhapthuoc.html")
@app.route("/scan_barcode", methods=["POST"])
def scan_barcode():
    if "uid" not in session:  # Ensure the user is logged in
        return redirect(url_for("root"))

    if "image" not in request.files:  # Ensure an image is uploaded
        return "No image uploaded", 400

    # Get the uploaded image
    file = request.files['image']
    data = file.read()

    # Save the image for debugging (optional)
    with open("debug_upload.jpg", "wb") as f:
        f.write(data)

    # Decode the image
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)

    if img is None:
        return "Invalid or empty image", 400

    scanned_barcodes = set()

    # ===== Xử lý ảnh để quét barcode =====
    # 1. Chuyển ảnh sang màu xám
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Làm sắc nét ảnh
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(gray, -1, kernel)

    # 3. Giảm nhiễu nhẹ
    denoised = cv2.GaussianBlur(sharpened, (3, 3), 0)

    # 4. Phân ngưỡng thích nghi để làm nổi bật barcode
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)

    # 5. Quét barcode từ cả ảnh gốc và ảnh đã xử lý
    barcodes = decode(denoised) + decode(thresh)

    # Kiểm tra nếu có mã vạch được phát hiện
    barcode_data = ""
    if barcodes:
        for barcode in barcodes:
            (x, y, w, h) = barcode.rect
            barcode_data = barcode.data.decode("utf-8")
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, barcode_data, (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            if barcode_data not in scanned_barcodes:
                print(f"Đã quét: {barcode_data}")
                scanned_barcodes.add(barcode_data)
    else:
        print("No barcode detected in this image")

    # Redirect về trang nhập thuốc với dữ liệu barcode
    return redirect(url_for("nhapthuoc", barcode=barcode_data))

@app.route("/get_trays", methods=["GET"])
def get_trays():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM trays ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    trays = [dict(row) for row in rows]
    return {"trays": trays}


# --- Tham số xác nhận ---
REQUIRED_COUNT = 5       # cần đọc 5 lần trong cửa sổ thời gian
TIME_WINDOW = 0.5        # trong 0.5 giây
REQUIRED_FRAMES = 3      # hoặc 3 frame liên tiếp

def gen_barcode_frames(cam_index: int):
    if cam_index < 0 or cam_index >= len(streams):
        return

    stream = streams[cam_index]
    stream.start()


    # Trạng thái cho stream này (mỗi camera độc lập)
    detected_barcodes = set()
    count_buffer      = defaultdict(int)
    start_time        = defaultdict(float)
    confirmed         = set()
    frame_seen_count  = defaultdict(int)
    last_seen_frame   = defaultdict(int)
    frame_idx = 0

    try:
        while True:
            frame_bytes = stream.get_jpeg()
            if frame_bytes is None:
                continue

            frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
            frame_idx += 1


            # Tạo các phiên bản ảnh
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_eq = cv2.equalizeHist(gray)
            _, thresh = cv2.threshold(
                gray_eq, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Thử decode trên nhiều phiên bản
            versions = [("thresh", thresh), ("gray_eq", gray_eq), ("orig", frame)]
            seen_this_frame = set()
            results = []
            for _, img in versions:
                results = decode(img)
                if results:
                    break  # ưu tiên phiên bản đầu tiên decode được

            for bc in results:
                data = bc.data.decode("utf-8", errors="ignore").strip()
                if not data or data in seen_this_frame:
                    continue
                seen_this_frame.add(data)

                # --- Xử lý logic đếm ---
                if last_seen_frame[data] == frame_idx - 1:
                    frame_seen_count[data] += 1
                else:
                    frame_seen_count[data] = 1
                last_seen_frame[data] = frame_idx

                now = time.time()
                if data not in confirmed:
                    if count_buffer[data] == 0:
                        start_time[data] = now
                        count_buffer[data] = 1
                    else:
                        if now - start_time[data] <= TIME_WINDOW:
                            count_buffer[data] += 1
                        else:
                            start_time[data] = now
                            count_buffer[data] = 1

                    just = (count_buffer[data] >= REQUIRED_COUNT) or \
                           (frame_seen_count[data] >= REQUIRED_FRAMES)
                    if just:
                        confirmed.add(data)

                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("SELECT tray_id FROM medicines WHERE code = ?", (data,))
                        row = c.fetchone()
                        if row:
                            tray_id = row[0]
                            c.execute("SELECT x, y, z FROM trays WHERE id = ?", (tray_id,))
                            tray = c.fetchone()
                            if tray:
                                cx, cy, cz = tray
                            else:
                                cx = cy = cz = 0
                        else:
                            cx = cy = cz = 0

                        print(f"[CAM {cam_index}] ✅ XÁC NHẬN: {data} tại tọa độ từ SQL (x={cx}, y={cy}, z={cz})", flush=True)
                        color = (0, 255, 0)      # xanh lá
                        label = f"{data} ✓"
                    else:
                        color = (0, 255, 255)    # vàng
                        label = f"{data}"
                else:
                    color = (0, 0, 255)          # đỏ
                    label = f"{data} ✓"

                # --- Vẽ bounding box ---
                if bc.polygon and len(bc.polygon) >= 4:
                    pts = [(int(p.x), int(p.y)) for p in bc.polygon]
                    for i in range(len(pts)):
                        cv2.line(frame, pts[i], pts[(i + 1) % len(pts)], color, 2)
                    tx, ty = pts[0]
                else:
                    x, y, w, h = bc.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    tx, ty = x, y - 10
                safe_label = label.encode('ascii', errors='ignore').decode('ascii')

                cv2.putText(frame, f"[CAM {cam_index}] {safe_label}",
                            (tx, max(20, ty - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # Encode JPEG để stream
            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                continue
            jpg = buf.tobytes()
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
                   jpg + b"\r\n")
    finally:
        cap.release()


@app.route('/')
def barcode_page():
    return render_template("index.html")

# Mỗi camera một feed: /barcode_feed/0 và /barcode_feed/1
@app.route("/barcode_feed/<int:cam_index>")
def barcode_feed(cam_index: int):
    return Response(gen_barcode_frames(cam_index),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/nhapthuoc")
def nhapthuoc():
    barcode = request.args.get('barcode', '')
    return render_template('nhapthuoc.html', barcode=barcode, role=session.get("role"))

@app.route("/get_medicine/<code>", methods=["GET"])
def get_medicine(code):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM medicines WHERE code=?", (code,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"exists": True, "medicine": dict(row)}
    return {"exists": False}


@app.route("/save_medicine", methods=["POST"])
def save_medicine():
    data = request.get_json()
    conn = get_connection()
    c = conn.cursor()

    # kiểm tra mã thuốc có tồn tại không
    c.execute("SELECT * FROM medicines WHERE code=?", (data.get("code"),))
    row = c.fetchone()

    if row:
        # cập nhật số lượng (cộng dồn)
        current_qty = int(row["quantity"] or 0)
        add_qty = int(data.get("quantity") or 0)
        new_qty = current_qty + add_qty
        c.execute("UPDATE medicines SET quantity=? WHERE code=?", (str(new_qty), data.get("code")))
        conn.commit()
        conn.close()
        return {"success": True, "updated": True, "new_quantity": new_qty}
    else:
        # thêm thuốc mới
        c.execute("""
            INSERT INTO medicines (name, type, code, quantity,price,strip,pill, manu_date, exp_date, tray_id)
            VALUES (?, ?, ?, ?, ?, ?,?,?,?,?)
        """, (
            data.get("name"),
            data.get("type"),
            data.get("code"),
            data.get("quantity"),
            data.get("price"),
            data.get("strips"),
            data.get("pills"),
            data.get("manuDate"),
            data.get("expDate"),
            data.get("trayid"),
        ))
        conn.commit()
        new_id = c.lastrowid
        conn.close()
        return {"success": True, "id": new_id, "updated": False}


@app.route("/list_medicine", methods=["GET"])
def list_medicine():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM medicines")
    rows = c.fetchall()
    conn.close()
    medicines = [dict(row) for row in rows]
    return {"success": True, "data": medicines}


@app.route("/delete_medicine/<int:med_id>", methods=["DELETE"])
def delete_medicine(med_id):
    if "uid" not in session:
        return {"success": False, "error": "Chưa đăng nhập"}, 403
    if session.get("role") != "admin":
        return {"success": False, "error": "Không có quyền xoá"}, 403

    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM medicines WHERE id=?", (med_id,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route("/update_medicine/<int:med_id>", methods=["POST"])
def update_medicine(med_id):
    if "uid" not in session:
        return {"success": False, "error": "Chưa đăng nhập"}, 403
    try:
        data = request.get_json()
        print("DEBUG JSON:", data)   # ✅ log dữ liệu nhận được
        if not data:
            return {"success": False, "error": "Không nhận được dữ liệu JSON"}

        name = data.get("name")
        type_ = data.get("type")
        code = data.get("code")
        quantity = data.get("quantity")  # Số lượng, mặc định là 0 nếu không có
        price = data.get("price")
        strips = data.get("strips")
        pills = data.get("pills")
        manuDate = data.get("manuDate")
        expDate = data.get("expDate")

        conn = get_connection()
        c = conn.cursor()
        c.execute(
            """
            UPDATE medicines
            SET name=?, type=?, code=?,quantity=?,price=?,strip=?,pill=?, manu_date=?, exp_date=?
            WHERE id=?
            """,
            (name, type_, code,quantity,price,strips,pills, manuDate, expDate, med_id),
        )
        conn.commit()
        print("DEBUG rowcount:", c.rowcount)  # ✅ số dòng bị ảnh hưởng
        conn.close()
        return {"success": True, "updated": c.rowcount}
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"success": False, "error": str(e)}
    
@app.route("/banthuoc")
def banthuoc_page():
    if "uid" not in session:  # bắt buộc login
        return redirect(url_for("root"))
    return render_template("banthuoc.html")


@app.route("/autocomplete")
def autocomplete():
    query = request.args.get("query", "").strip().lower()
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT name, quantity, strip, pill, price, left_strip, left_pill,id
        FROM medicines
        WHERE LOWER(name) LIKE ?
    """, (f"%{query}%",))
    rows = c.fetchall()
    conn.close()

    results = [
        {
            "name": row["name"],           
            "quantity": row["quantity"],
            "strip": row["strip"],
            "pill": row["pill"],
            "left_strip": row["left_strip"],
            "left_pill": row["left_pill"],
            "price": row["price"],
            "id": row["id"]
        }
        for row in rows
    ]
    return jsonify(results)


def process_sale(medicine, unit, qty):
    """
    medicine: row lấy từ bảng medicines (sqlite Row)
    unit: 'Hộp' / 'Vỉ' / 'Viên'
    qty: số lượng cần bán
    """
    quantity = int(medicine["quantity"])      # số hộp nguyên
    strip = int(medicine["strip"])            # số vỉ / hộp
    pill = int(medicine["pill"])              # số viên / vỉ
    left_strip = int(medicine["left_strip"])  # vỉ dư hộp đang bán
    left_pill = int(medicine["left_pill"])    # viên dư vỉ đang bán

    # ---- Case 1: Bán theo HỘP ----
    if unit == "Hộp":
        if quantity < qty:
            raise ValueError("Không đủ hộp trong kho")
        quantity -= qty

    # ---- Case 2: Bán theo VỈ ----
    elif unit == "Vỉ":
        need = qty

        # dùng vỉ dư trước
        if left_strip >= need:
            left_strip -= need
            need = 0
        else:
            need -= left_strip
            left_strip = 0

        # nếu vẫn cần → khui hộp mới (-1 hộp)
        while need > 0:
            if quantity <= 0:
                raise ValueError("Không đủ vỉ trong kho")
            quantity -= 1
            total_v = strip
            if total_v >= need:
                # bán số vỉ cần, dư thì cộng lại
                left_strip += total_v - need
                need = 0
            else:
                # bán hết hộp, vẫn chưa đủ
                need -= total_v

    # ---- Case 3: Bán theo VIÊN ----
    elif unit == "Viên":
        need = qty

        # dùng viên dư trước
        if left_pill >= need:
            left_pill -= need
            need = 0
        else:
            need -= left_pill
            left_pill = 0

        # nếu vẫn cần → lấy từ vỉ dư trước
        if need > 0 and left_strip > 0:
            while need > 0 and left_strip > 0:
                if pill >= need:
                    left_pill += pill - need
                    need = 0
                    left_strip -= 1
                else:
                    need -= pill
                    left_strip -= 1

        # nếu vẫn cần → khui hộp mới (-1 hộp)
        while need > 0:
            if quantity <= 0:
                raise ValueError("Không đủ viên trong kho")
            quantity -= 1
            total_v = strip * pill  # tổng số viên trong hộp
            if total_v >= need:
                # bán số viên cần, dư thì chia lại thành vỉ + viên
                full_strip, remain_pill = divmod(total_v - need, pill)
                left_strip += full_strip
                left_pill += remain_pill
                need = 0
            else:
                # bán hết hộp vẫn chưa đủ
                need -= total_v

    else:
        raise ValueError("Đơn vị không hợp lệ")

    return quantity, left_strip, left_pill

pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))

def generate_invoice_pdf(customer_name, hometown, dob, purchase_date, medicines, total_price_all):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ---- Header ----
    p.setFont("DejaVu", 16)
    p.drawString(200, height - 50, "HÓA ĐƠN MUA THUỐC")

    p.setFont("DejaVu", 10)
    p.drawString(50, height - 80, f"Tên khách hàng: {customer_name}")
    p.drawString(50, height - 100, f"Quê quán: {hometown}")
    p.drawString(50, height - 120, f"Ngày sinh: {dob}")
    p.drawString(50, height - 140, f"Ngày mua: {purchase_date or datetime.date.today().isoformat()}")

    # ---- Table header ----
    y = height - 180
    p.setFont("DejaVu", 10)
    p.drawString(50, y, "Tên thuốc")
    p.drawString(200, y, "Đơn vị")
    p.drawString(260, y, "Số lượng")
    p.drawString(330, y, "Thành tiền")

    # ---- Medicines ----
    p.setFont("DejaVu", 10)
    y -= 20
    for m in medicines:
        p.drawString(50, y, m["name"])
        p.drawString(200, y, m["unit"])
        p.drawString(260, y, str(m["qty"]))
        p.drawString(330, y, f"{m['total_price']:.0f} VND")
        y -= 20

    # ---- Total ----
    p.setFont("DejaVu", 12)
    p.drawString(50, y - 20, f"Tổng cộng: {total_price_all:.0f} VND")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


@app.route("/sell", methods=["POST"])
def sell():
    data = request.get_json()
    customer_name = data.get("customer_name", "")
    hometown = data.get("hometown", "")
    dob = data.get("dob", "")
    advice = data.get("advice", "")
    purchase_date = data.get("purchase_date", "")
    medicines = data.get("medicines", [])

    if not medicines:
        return jsonify({"error": "Chưa chọn thuốc"}), 400

    conn = get_connection()
    c = conn.cursor()
    total_price_all = 0
    sold_items = []
    try:
        for item in medicines:
            medicine_id = item["medicine_id"]
            qty = int(item["qty"])
            unit = item["unit"]

            med = c.execute("SELECT * FROM medicines WHERE id=?", (medicine_id,)).fetchone()
            if med is None:
                raise ValueError(f"Không tìm thấy thuốc id={medicine_id}")

            new_quantity, new_left_strip, new_left_pill = process_sale(med, unit, qty)

            # Tính giá
            price_per_box = float(med["price"])
            strip = int(med["strip"])
            pill = int(med["pill"])

            if unit == "Hộp":
                total_price = price_per_box * qty
            elif unit == "Vỉ":
                total_price = (price_per_box / strip) * qty
            elif unit == "Viên":
                total_price = (price_per_box / (strip * pill)) * qty
            else:
                total_price = 0

            total_price_all += total_price

            # Cập nhật kho
            c.execute("""
                UPDATE medicines 
                SET quantity=?, left_strip=?, left_pill=? 
                WHERE id=?
            """, (new_quantity, new_left_strip, new_left_pill, medicine_id))

            # Ghi vào sales
            c.execute("""
                INSERT INTO sales (medicine_id, customer_name, hometown, dob, unit, quantity, total_price, advice, purchase_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (medicine_id, customer_name, hometown, dob, unit, qty, total_price, advice, purchase_date))

            sold_items.append({
                "name": med["name"],
                "unit": unit,
                "qty": qty,
                "total_price": total_price
            })

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()
    rpdf_buffer = generate_invoice_pdf(customer_name, hometown, dob, purchase_date, sold_items, total_price_all)

    # Lưu file vào static/invoices
    return send_file(
        rpdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="hoadon.pdf"   # tên file khi tải về
    )





@app.route("/me")
def me():
    if "uid" not in session:
        return {"logged_in": False}
    return {"logged_in": True, "email": session["uid"], "role": session.get("role")}





def mjpeg_generator(cam: CameraStream):
    """
    Trả về luồng MJPEG từ một CameraStream
    """
    # Đảm bảo đã start reader
    cam.start()

    # Luồng vô hạn
    while True:
        frame = cam.get_jpeg()
        if frame is None:
            time.sleep(0.05)
            continue

        # multipart/x-mixed-replace
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n"
               b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n" +
               frame + b"\r\n")
        # throttling nhẹ nhàng (tùy ý)
        # time.sleep(0.01)


@app.route("/video_feed/<int:cam_id>")
def video_feed(cam_id):
    if cam_id < 1 or cam_id > len(streams):
        return "Camera not found", 404
    stream = streams[cam_id - 1]
    return Response(mjpeg_generator(stream),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    # Nếu bạn đã làm HTTPS bằng mkcert, truyền ssl_context vào đây
    # ssl_context = ("192.168.1.2.pem", "192.168.1.2-key.pem")
    # app.run(host="0.0.0.0", port=5000, ssl_context=ssl_context)

    # Tạm thời HTTP (chỉ chạy trong LAN hoặc khi bạn không cần getUserMedia nữa)
    
    
    app.run( 
        host="0.0.0.0",
        port=5002,
        ssl_context=("server.pem", "server-key.pem"))
    # app.run(host="0.0.0.0", port=5000, debug=True)

