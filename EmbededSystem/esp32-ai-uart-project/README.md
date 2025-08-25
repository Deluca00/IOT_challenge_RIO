# ESP32 AI UART Project

## Cấu trúc
- `esp32-camera/`: ESP32-CAM gửi ảnh qua UART
- `esp32-ai/`: ESP32 nhận ảnh, chạy AI nhỏ, gửi kết quả qua UART cho PC
- `pc-uart-reader/`: Máy tính đọc kết quả từ ESP32-AI qua UART

## Hướng dẫn sử dụng
1. Nạp code cho từng ESP32 theo từng folder.
2. Kết nối UART giữa các thiết bị:
   - ESP32-CAM TX -> ESP32-AI RX
   - ESP32-AI TX (Serial1) -> Máy tính RX
3. Chạy script Python trên máy tính để xem kết quả AI.

## Lưu ý
- Đảm bảo tốc độ baud giống nhau (115200).
- Đổi đúng cổng COM trong file Python.
- Cần cài đặt thư viện `pyserial` cho Python: `pip install pyserial`
- Cần cấu hình đúng thư viện camera cho ESP32-CAM.
