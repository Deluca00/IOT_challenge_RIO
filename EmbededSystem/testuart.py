import serial, time

PORT = "/dev/ttyACM0"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # đợi Arduino reset khi mở cổng

print(f"🔌 Đang đọc dữ liệu từ {PORT} ... (Ctrl+C để thoát)")

# Gửi lệnh test
ser.write(b"MODE IMPORT\r\n")
ser.write(b"X30Y0Z0\r\n")
# ser.write(b"mode import x30y0z0")

try:
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print(f"[RX] {line}")
except KeyboardInterrupt:
    print("\n⏹ Dừng lại.")
finally:
    ser.close()
