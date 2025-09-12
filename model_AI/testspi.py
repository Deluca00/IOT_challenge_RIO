import serial
import numpy as np
import cv2

ser = serial.Serial("COM10", 115200)  # chỉnh COM cho đúng
data = bytearray()

# nhận 19200 byte
while len(data) < 19200:
    data.extend(ser.read(19200 - len(data)))

# chuyển thành ảnh 160x120 grayscale
img = np.frombuffer(data, dtype=np.uint8).reshape((120, 160))

# hiển thị
cv2.imshow("Grayscale Image", img)
cv2.waitKey(0)
