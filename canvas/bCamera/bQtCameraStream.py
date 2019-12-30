# Rbert Cudmore
# 20191228

"""
Important, this is using imageio.imsave instead of the older scipy.misc.imwrite
I think imageio is getting imported/installed by napari?
"""

import os, sys, time

from PyQt5 import QtCore, QtWidgets, QtGui
import numpy as np
import cv2
import imageio

# todo: create this kind of thread for PointGray camera on Olympus scope
class myVideoThread(QtCore.QThread):
	changePixmap2 = QtCore.pyqtSignal(np.ndarray)

	def run(self):
		cap = cv2.VideoCapture(0)
		while True:
			ret, frame = cap.read() # frame is np.ndarray
			if ret:
				self.changePixmap2.emit(frame)
			time.sleep(.02)

# todo: this will always be used by canvas
class myVideoWidget(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()
		#[...]
		self.title = 'myVideoWidget'
		self.myleft = 100
		self.mytop = 100
		self.mywidth = 640
		self.myheight = 480

		# put this in so parent app (e.g. bCanvasApp) can grab the last image!
		#self.mypixmap = None
		self.myCurrentImage = None
		self.aspectRatio = 640/480

		self.saveImageAtInterval = True
		self.saveIntervalSeconds = 1
		self.lastSaveSeconds = None
		
		# save oneimage.tif in the same folder as source code
		myPath = os.path.dirname(os.path.abspath(__file__))
		self.mySaveFilePath = os.path.join(myPath, 'oneimage.tif')
	
		print('myVideoWidget.mySaveFilePath:', self.mySaveFilePath)
	
		self.initUI()

		#self.show()

	def resizeEvent(self, event):
		"""
		Maintain aspect ratio of window/widget to match aspect ration of video images
		"""
		if self.width() / self.height() > self.aspectRatio: # too wide
			w = self.height() * self.aspectRatio
			h = self.height()
			self.resize(w, h)
		else: # too tall
			w = self.width()
			h = self.width() / self.aspectRatio
			self.resize(w, h)

	@QtCore.pyqtSlot(np.ndarray)
	def setImage2(self, image):
		"""
		We got a new image from the camera.
		
		Parameters:
			image: type is numpy.ndarray, shape is (height,width,3), dtype is 'uint8'
		"""
		# convert to Qt
		# https://stackoverflow.com/a/55468544/6622587
		rgbImage = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		h, w, ch = rgbImage.shape
		bytesPerLine = ch * w
		myQtImage = QtGui.QImage(rgbImage.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888)
			
		
		# this does not work, i think because my webcam has 3 image planes, roughly RGB
		'''
		width = image.shape[1]
		height = image.shape[0]
		myQtImage = QtGui.QImage(image[:,:,0], width, height, QtGui.QImage.Format_Indexed8)
		'''
		
		# update qt interface
		pixmap = QtGui.QPixmap.fromImage(myQtImage)
		# scale pixmap
		pixmap = pixmap.scaled(self.width(), self.height(), QtCore.Qt.KeepAspectRatio)
		# set label
		self.label.setPixmap(pixmap)
		# scale label
		self.label.resize(self.width(), self.height())

		# this can be grabbed by other code
		self.myCurrentImage = image

		if self.saveImageAtInterval:
			now = time.time()
			if self.lastSaveSeconds is None or ((now-self.lastSaveSeconds) > self.saveIntervalSeconds):
				print(now, 'saving type(image)', type(image), image.shape, image.dtype, self.mySaveFilePath)
				self.lastSaveSeconds = now
				# todo: make it so we receive a single plane grayscale image?
				#cv2.imwrite(self.mySaveFilePath, image[:,:,0])
				imageio.imwrite(self.mySaveFilePath, image[:,:,0])
					
	def initUI(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.myleft, self.mytop, self.mywidth, self.myheight)
		#self.resize(640, 480)
		# create a label
		self.label = QtWidgets.QLabel(self)
		self.label.move(0, 0)
		self.label.resize(640, 480)
		th = myVideoThread(self)
		#th.changePixmap.connect(self.setImage)
		th.changePixmap2.connect(self.setImage2)
		th.start()

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	mvw = myVideoWidget()
	mvw.show()
	sys.exit(app.exec_())
