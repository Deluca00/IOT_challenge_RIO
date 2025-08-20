from flask import Flask, Response, render_template,request, redirect, url_for, session
import cv2
import threading
import time
import firebase_admin
from firebase_admin import credentials, db
import numpy as np
import base64
from pyzbar.pyzbar import decode

app = Flask(__name__)
app.secret_key = "supersecretkey" 
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024  # 30 MB

cred = credentials.Certificate("aiforlife-12891-firebase-adminsdk-9g1al-4b9118fe29.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://flaskapphn-default-rtdb.firebaseio.com/"  # thay URL của bạn
})
###############################################################################
# CẤU HÌNH NGUỒN CAMERA
# - Có thể là chỉ số webcam (0,1,2,3) hoặc URL RTSP/HTTP.
# - Ví dụ thay bằng rtsp/HTTP: "rtsp://user:pass@192.168.1.10/stream1"
###############################################################################
CAMERA_SOURCES = [
    1,  # Camera 1
    0,  # Camera 2
    2,  # Camera 3
    3   # Camera 4
]

# Nếu bạn chỉ có 1-2 webcam, có thể tạm copy nguồn:
# CAMERA_SOURCES = [0, 0, 0, 0]

###############################################################################
# LỚP QUẢN LÝ CAMERA: mở cv2.VideoCapture và chạy thread đọc khung hình
###############################################################################
class CameraStream:
    def __init__(self, src, cam_name="cam"):
        self.src = src
        self.cam_name = cam_name
        self.cap = cv2.VideoCapture(self.src)
        self.lock = threading.Lock()
        self.running = False
        self.frame = None
        self.thread = None

        # Tùy chọn (nếu là webcam USB): đặt độ phân giải/ FPS
        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        # self.cap.set(cv2.CAP_PROP_FPS, 25)

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

@app.route("/login", methods=["POST"])
def login():
    # Tạm thời hardcode user/pass để test
    email = request.form.get("email")
    password = request.form.get("password")
    if email == "admin@test.com" and password == "123456":
        session["uid"] = email
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
    return render_template("index.html", cameras=cameras)
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

@app.route("/nhapthuoc")
def nhapthuoc():
    barcode = request.args.get('barcode', '')  # <--- dùng đúng tên query param
    return render_template('nhapthuoc.html', barcode=barcode)

@app.route("/save_medicine", methods=["POST"])
def save_medicine():
    if "uid" not in session:
        return {"success": False, "error": "Chưa đăng nhập"}, 403

    try:
        data = request.get_json()
        ref = db.reference("medicines")
        new_ref = ref.push(data)  # push vào Firebase
        return {"success": True, "id": new_ref.key}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route("/list_medicine", methods=["GET"])
def list_medicine():
    if "uid" not in session:
        return {"error": "Chưa đăng nhập"}, 403

    try:
        ref = db.reference("medicines")
        medicines = ref.get()
        return medicines if medicines else {}
    except Exception as e:
        return {"error": str(e)}

@app.route("/delete_medicine/<string:med_id>", methods=["DELETE"])
def delete_medicine(med_id):
    if "uid" not in session:
        return {"success": False, "error": "Chưa đăng nhập"}, 403

    try:
        ref = db.reference(f"medicines/{med_id}")
        ref.delete()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}




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
        port=5000,
        ssl_context=("192.168.1.9.pem", "192.168.1.9-key.pem"))
    # app.run(host="0.0.0.0", port=5000, debug=True)

