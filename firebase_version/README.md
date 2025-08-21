# Ứng dụng Quản lý Thuốc - Phiên bản Firebase

Ứng dụng Flask để quản lý thuốc với camera giám sát và quét mã vạch, sử dụng Firebase Realtime Database.

## 🚀 Tính năng

- **Quản lý thuốc**: Thêm, sửa, xóa, tìm kiếm thuốc
- **Quét mã vạch**: Tự động quét mã vạch từ ảnh upload
- **Camera giám sát**: 4 camera streams real-time
- **Authentication**: Hệ thống đăng nhập đơn giản
- **Database cloud**: Firebase Realtime Database - cần internet

## 📋 Yêu cầu hệ thống

- Python 3.7+
- Webcam (tối thiểu 1 cái)
- Windows/Linux/macOS
- Kết nối internet

## 🛠️ Cài đặt

1. **Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

2. **Cấu hình Firebase**
- Đảm bảo file `aiforlife-12891-firebase-adminsdk-9g1al-4b9118fe29.json` có trong thư mục
- Cập nhật URL database trong file `app.py` nếu cần

3. **Chạy ứng dụng**
```bash
python app.py
```

## 🌐 Truy cập

- **Local**: http://localhost:5000
- **Tài khoản mặc định**: admin@test.com / 123456

## 📊 Cấu trúc Database (Firebase)

### Node `medicines`
- `id`: ID duy nhất (tự động tạo)
- `name`: Tên thuốc
- `barcode`: Mã vạch
- `quantity`: Số lượng
- `unit`: Đơn vị
- `price`: Giá
- `manufacturer`: Nhà sản xuất
- `expiry_date`: Ngày hết hạn
- `location`: Vị trí lưu trữ
- `notes`: Ghi chú

## 🔧 API Endpoints

### Authentication
- `POST /login` - Đăng nhập
- `GET /logout` - Đăng xuất

### Medicine Management
- `GET /list_medicine` - Lấy danh sách thuốc
- `POST /save_medicine` - Thêm thuốc mới
- `DELETE /delete_medicine/<id>` - Xóa thuốc

### Camera
- `GET /video_feed/<cam_id>` - Stream camera

### Barcode Scanning
- `POST /scan_barcode` - Quét mã vạch từ ảnh

## 📷 Cấu hình Camera

Chỉnh sửa `CAMERA_SOURCES` trong file `app.py`:

```python
CAMERA_SOURCES = [
    0,  # Camera 1 (webcam đầu tiên)
    1,  # Camera 2 (webcam thứ hai)
    2,  # Camera 3
    3   # Camera 4
]
```

## 🔒 Bảo mật

- **Session-based authentication**
- **Firebase security rules**
- **File upload validation**

## 📁 Cấu trúc thư mục

```
firebase_version/
├── app.py                                    # Ứng dụng chính (Firebase)
├── aiforlife-12891-firebase-adminsdk-9g1al-4b9118fe29.json  # Firebase credentials
├── requirements.txt                          # Dependencies
├── README.md                                # Hướng dẫn này
├── static/                                  # CSS, JS, images
└── templates/                               # HTML templates
```

## 🔧 Troubleshooting

### Lỗi Firebase
- Kiểm tra kết nối internet
- Kiểm tra file credentials Firebase
- Kiểm tra URL database

### Lỗi camera không hoạt động
- Kiểm tra quyền truy cập camera
- Thử thay đổi index camera (0, 1, 2...)
- Kiểm tra driver webcam

### Lỗi quét mã vạch
- Đảm bảo ảnh rõ nét
- Kiểm tra định dạng mã vạch (Code128, EAN, UPC...)
- Thử với ảnh khác

## 📞 Hỗ trợ

Nếu gặp vấn đề, hãy kiểm tra:
1. Log console khi chạy ứng dụng
2. File `debug_upload.jpg` để xem ảnh upload
3. Firebase Console để kiểm tra database

---

**Lưu ý**: Ứng dụng này cần kết nối internet để hoạt động với Firebase Realtime Database.
