import serial
import time

PORT = "/dev/ttyACM0"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # đợi Arduino reset khi mở cổng

print(f"🔌 Đang đọc dữ liệu từ {PORT} ... (Ctrl+C để thoát)")

try:
    while True:
        # Đọc dữ liệu từ Arduino
        if ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                print(f"[RX] {line}")

        # Nhập bất cứ gì muốn gửi
        msg = input("Nhập tin nhắn gửi Arduino (hoặc 'exit' để thoát): ")
        if msg.lower() == 'exit':
            break

        # Gửi trực tiếp
        ser.write((msg + "\r\n").encode())
        print(f"[TX] {msg}")

except KeyboardInterrupt:
    print("\n⏹ Dừng lại.")
finally:
    ser.close()
