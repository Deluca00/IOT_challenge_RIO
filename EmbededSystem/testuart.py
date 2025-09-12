import serial

ser = serial.Serial('Com3', 115200, timeout=1)

print("🔌 Đang đọc dữ liệu từ /dev/ttyUSB0 ... (Ctrl+C để thoát)")

try:
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print(f"[RX] {line}")
except KeyboardInterrupt:
    print("\n⏹ Dừng lại.")
finally:
    ser.close()
