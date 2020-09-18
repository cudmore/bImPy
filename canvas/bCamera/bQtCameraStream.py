# Rbert Cudmore
# 20191228

"""
Important, this is using imageio.imsave instead of the older scipy.misc.imwrite
I think imageio is getting imported/installed by napari?

newer opencv give conflicit with versions of PyQt5.
DO NOT use python-opencv but use 'opencv-python-headless' instead

    pip install opencv-python-headless
"""

import os, sys, time

#from PyQt5 import QtCore, QtWidgets, QtGui
from qtpy import QtCore, QtWidgets, QtGui
import numpy as np

#print('bQtCameraStream importing cv2')
import cv2
#print('cv2.__version__:', cv2.__version__)

import imageio

import qdarkstyle

# todo: create this kind of thread for PointGray camera on Olympus scope
class myVideoThread(QtCore.QThread):
	changePixmap2 = QtCore.Signal(np.ndarray)

	def run(self):
		cap = cv2.VideoCapture(0)
		while True:
			ret, frame = cap.read() # frame is np.ndarray
			if ret:
				self.changePixmap2.emit(frame)
			time.sleep(.02)

# todo: this will always be used by canvas
class myVideoWidget(QtWidgets.QWidget):

	videoWindowSignal = QtCore.Signal(object)

	def getVideoDict():
		"""
		pass this in self.videoWindowSignal.emit()
		"""
		theRet = {
		'event': ''
		}
		return theRet

	def __init__(self, parent=None, videoSize=None, videoPos=None, scaleMult=1.0,
					saveIntervalSeconds=None):
		"""
		videoSize: (w,h) of actual video (pixels)
		videoPos: (left,top) position on screen
		scaleMult: final width is w * scaleMult
		"""

		# this is causing error on quit
		# WARNING: QThread: Destroyed while thread is still running
		#super().__init__(parent)
		super().__init__()

		self.title = 'myVideoWidget'

		self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

		#self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		self.setWindowFlags(QtCore.Qt.Tool)

		if videoSize is not None:
			self.myWidth = videoSize[0]
			self.myHeight = videoSize[1]
		else:
			self.myWidth = 640
			self.myHeight = 480

		self.aspectRatio = self.myWidth / self.myHeight #640/480

		# set on self.moveEvent
		if videoPos is not None:
			self.videoPos = videoPos
		else:
			self.videoPos = (100,100)

		self.scaleMult = scaleMult # set on self.resizeEvent

		self.myCurrentImage = None # updated with new images (in thread)

		# save an image at an interval
		#self.saveImageAtInterval = True
		self.saveIntervalSeconds = saveIntervalSeconds #1
		self.lastSaveSeconds = None
		# save oneimage.tif in the same folder as source code
		myPath = os.path.dirname(os.path.abspath(__file__))
		self.mySaveFilePath = os.path.join(myPath, 'oneimage.tif')

		print('  saveIntervalSeconds:', self.saveIntervalSeconds)
		print('  mySaveFilePath:', self.mySaveFilePath)

		self.initUI()

		#self.show()

	def getCurentImage(self):
		return self.myCurrentImage

	def moveEvent(self, event):
		#print('myVideoWidget.moveEvent()')
		left = self.frameGeometry().left()
		top = self.frameGeometry().top()
		#w = self.frameGeometry().width()
		#h = self.frameGeometry().height()

		# emit
		videoDict = myVideoWidget.getVideoDict()
		videoDict['event'] = 'Move Window'
		videoDict['left'] = left
		videoDict['top'] = top
		self.videoWindowSignal.emit(videoDict)

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

		# emit
		videoDict = myVideoWidget.getVideoDict()
		videoDict['event'] = 'Resize Window'
		videoDict['scaleMult'] = w / self.myWidth # myWidth does not change
		self.videoWindowSignal.emit(videoDict)

	#@QtCore.Slot(np.ndarray)
	def setImage2(self, image):
		"""
		We got a new image from the camera.

		Parameters:
			image: type is numpy.ndarray, shape is (height,width,3), dtype is 'uint8'
		"""

		# (720, 1280, 3)
		#print('setImage2() image:', image.shape)

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

		if self.saveIntervalSeconds is not None:
			now = time.time()
			if self.lastSaveSeconds is None or ((now-self.lastSaveSeconds) > self.saveIntervalSeconds):
				#print(now, 'saving type(image)', type(image), image.shape, image.dtype, self.mySaveFilePath)
				self.lastSaveSeconds = now
				# todo: make it so we receive a single plane grayscale image?
				#cv2.imwrite(self.mySaveFilePath, image[:,:,0])
				imageio.imwrite(self.mySaveFilePath, image[:,:,0])

	def closeEvent(self, event):
		"""
		called when video window is closed
		"""
		#print('  bQtCameraStream.closeEvent()')
		videoDict = myVideoWidget.getVideoDict()
		videoDict['event'] = 'Close Window'
		self.videoWindowSignal.emit(videoDict)
		#if self.canvasApp is not None:
		#	self.canvasApp.closeVideo()

	def _getScaledWithHeight(self):
		scaledWidth = self.myWidth * self.scaleMult
		scaledHeight = self.myHeight * self.scaleMult
		return scaledWidth, scaledHeight

	def initUI(self):
		self.setWindowTitle(self.title)

		scaledWith, scaledHeight = self._getScaledWithHeight()
		self.setGeometry(self.videoPos[0], self.videoPos[1], scaledWith, scaledHeight)
		#self.resize(640, 480)
		# create a label
		self.label = QtWidgets.QLabel(self)
		self.label.move(0, 0)
		#self.label.resize(640, 480)
		self.label.resize(scaledWith, scaledHeight)

		print('  myVideoWidget.initUI() creating myVideoThread()')

		# by having the thread as a member (Self.th)
		# it gets garbage collected on quit and stops dreaded
		# WARNING: QThread: Destroyed while thread is still running
		self.th = myVideoThread()
		self.th.changePixmap2.connect(self.setImage2)
		self.th.start()

if __name__ == '__main__':
	w = 1280 #640
	h = 720 #480

	app = QtWidgets.QApplication(sys.argv)
	mvw = myVideoWidget(videoSize=(w,h),
						videoPos=(100,500),
						scaleMult=0.5)
	mvw.show()

	def slot_test(videoDict):
		print('slot_test() videoDict:', videoDict)
	mvw.videoWindowSignal.connect(slot_test)

	sys.exit(app.exec_())
