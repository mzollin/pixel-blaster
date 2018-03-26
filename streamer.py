#!/usr/bin/env python3

import cv2
import numpy as np
import serial
import time

#url = 'rick.mp4'
url = 'foo'
#url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ?action=stream?dummy=param.mjpg'
#url = 0 # webcam

print('starting...')
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0)
cap = cv2.VideoCapture(url)
fps = cap.get(cv2.CAP_PROP_FPS)
start = True
while True:
    ret, frame = cap.read()
    if ret:
        # convert the image to grayscale
        frame_bw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # determine threshold if it is the first frame
        if start:
            _, thresh = cv2.threshold(frame_bw, 1, 255, cv2.THRESH_BINARY)
            _, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            x, y, w, h = cv2.boundingRect(contours[0])
            print(x, y, w, h)

	# crop image using threshold
        frame_crop = frame_bw[y:y+h, x:x+w]

	# resize image to 32x32 pixel
	# TODO: preserve aspect ratio
        frame_native = cv2.resize(frame_crop, (32, 32))

	# perform histogram equalization
        frame_equ = cv2.equalizeHist(frame_native)

        outdata = bytearray([0xFF])

	# replace value 0xFF (reserved for frame sync value) with 0xFE
        data = [line.tobytes().replace(b'\xFF', b'\xFE') for line in frame_equ]

	# rearrange image buffer to match the format expected by the out-of-sync hardware
        for outline in range(16):
            outdata += bytes(data[outline][:16])
            outdata += bytes(data[16 + outline][:16])
            outdata += bytes(data[outline][16:])
            outdata += bytes(data[16 + outline][16:])

        ser.write(outdata)
        start = False
    else:
        cap = cv2.VideoCapture(url)
        print('video restarted')
    try:
        time.sleep(1.0/fps)
    except ZeroDivisionError:
        fps = 25
ser.close()
cap.release()
print('done!')
