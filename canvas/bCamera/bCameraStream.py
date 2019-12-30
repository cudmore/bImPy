# Robert Cudmore
# 20191229

from threading import Thread
import cv2, time

class VideoStreamWidget(object):
	def __init__(self, src=0):
		"""
		src: 0 is the first usb camera (not a fancy camera like pointgrey etc but a dead simple cheap webcam
		"""
		self.windowTitle = 'Camera Stream'

		self.capture = cv2.VideoCapture(src)

		# grab one frame to get width/height
		(self.status, self.frame) = self.capture.read()
		#print(self.frame.shape)
		#self.frame.shape is (height, width, rgb)
		self.winWidth = self.frame.shape[1]
		self.winHeight = self.frame.shape[0]

		cv2.namedWindow(self.windowTitle,cv2.WINDOW_NORMAL) # needed to dynamically resize window
		cv2.moveWindow(self.windowTitle, 50, 20)
		cv2.resizeWindow(self.windowTitle, self.winWidth, self.winHeight)

		# Start the thread to read frames from the video stream
		self.thread = Thread(target=self.update, args=())
		self.thread.daemon = True
		self.thread.start()


	def update(self):
		# Read the next frame from the stream in a different thread
		while True:
			if self.capture.isOpened():
				(self.status, self.frame) = self.capture.read()
				#self.show_frame()
			time.sleep(.02)

	def show_frame(self):
		# Display frames in main program
		cv2.imshow(self.windowTitle, self.frame)
		key = cv2.waitKey(20) & 0xFF
		if key == ord('q'):
			self.capture.release()
			cv2.destroyAllWindows()
			exit(1)
		if key == ord('-'):
			self.winWidth = int(self.winWidth * 0.8)
			self.winHeight = int(self.winHeight * 0.8)
			cv2.resizeWindow(self.windowTitle, self.winWidth, self.winHeight)
			print('-', self.winWidth, self.winHeight)
		if key in [ord('+'), ord('=')]:
			self.winWidth = int(self.winWidth * 1.2)
			self.winHeight = int(self.winHeight * 1.2)
			cv2.resizeWindow(self.windowTitle, self.winWidth, self.winHeight)
			print('+', self.winWidth, self.winHeight)

if __name__ == '__main__':
	video_stream_widget = VideoStreamWidget()
	while True:
		try:
			video_stream_widget.show_frame()
			time.sleep(.02)
		except AttributeError:
			pass
