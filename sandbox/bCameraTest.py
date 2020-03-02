# "(534d:0021) ???? - AV TO USB2.0"

import cv2

i=1
camera = cv2.VideoCapture(i)
ret, frame = camera.read() # frame is np.ndarray
print(ret, frame.shape)