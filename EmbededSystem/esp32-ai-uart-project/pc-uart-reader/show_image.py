import serial
import numpy as np
from PIL import Image

ser = serial.Serial('COM3', 115200)  # Thay COM3 bằng cổng của bạn
frame_size = 160 * 120 * 2           # QQVGA RGB565

while True:
    data = ser.read(frame_size)
    img = np.zeros((120, 160, 3), dtype=np.uint8)
    for i in range(0, frame_size, 2):
        pixel = data[i] | (data[i+1] << 8)
        r = ((pixel >> 11) & 0x1F) << 3
        g = ((pixel >> 5) & 0x3F) << 2
        b = (pixel & 0x1F) << 3
        y = (i // 2) // 160
        x = (i // 2) % 160
        img[y, x] = [r, g, b]
    Image.fromarray(img).show()
    break  # Hiển thị 1 frame, bỏ break để xem liên tục
