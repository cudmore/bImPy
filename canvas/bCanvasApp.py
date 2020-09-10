# Author: Robert Cudmore
# Date: 20190630

import os, sys, json
from collections import OrderedDict
from datetime import datetime

from PyQt5 import QtCore, QtWidgets, QtGui

import qdarkstyle

import bimpy

import canvas
import bCanvas
import bMotor
import bCamera

#from bCameraStream import VideoStreamWidget

# todo: put this in scope config json (along with motor name like 'Prior')
#gMotorIsReal = False

#class bCanvasApp(QtWidgets.QMainWindow):
#class bCanvasApp(QtWidgets.QApplication):
# was this
# widget do not have menus
#class bCanvasApp(QtWidgets.QWidget):
# on windows, this needs to be a qmain window so we get menus
# todo: have the canvas app open stackbrowser (so we get a main window)
class bCanvasApp(QtWidgets.QMainWindow):
	def __init__(self, loadIgorCanvas=None, path=None, parent=None):
		"""
		loadIgorCanvas: path to folder of converted Igor canvas
		path: path to text file of a saved Python canvas
		"""
		print('bCanvasApp.__init__() path:', path)
		super(bCanvasApp, self).__init__()

		self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

		self.myApp = parent

		self.optionsFile = ''
		self.optionsLoad()

		self.myMenu = canvas.bMenu(self)

		motorName = self._optionsDict['motor']['name'] # = 'bPrior'
		isReal = self._optionsDict['motor']['isReal'] #= False
		#motorName = 'bPrior'
		self.assignMotor(motorName, isReal)

		self.canvasDict = {}

		if loadIgorCanvas is not None:
			#tmpCanvasFolderPath = '/Users/cudmore/Dropbox/data/20190429/20190429_tst2'
			#tmpCanvasFolderPath = '/Users/cudmore/box/data/nathan/canvas/20190429_tst2'
			self.canvas = bCanvas.bCanvas(folderPath=loadIgorCanvas)

			# this is only for import from igor
			self.canvas.importIgorCanvas()

			self.canvas.buildFromScratch()
		else:
			self.canvas = bCanvas.bCanvas(filePath=path)

		# todo: only needed on windows
		self.show()

		# start a camera Thread
		self.camera = bCamera.myVideoWidget()
		self.showingCamera = False
		#self.camera.show()

	def toggleVideo(self):
		self.showingCamera = not self.showingCamera
		if self.showingCamera:
			self.camera.show()
		else:
			self.camera.hide()

	def getCurentImage(self):
		return self.camera.getCurentImage()

	def assignMotor(self, motorName, isReal):
		"""
		Create a motor controller from a class name

		Parameters:
			motorName: A string corresponding to a derived class of bMotor. File is in bimpy/bMotor folder
		"""
		# we will import user defined motor class using a string
		# see: https://stackoverflow.com/questions/4821104/dynamic-instantiation-from-string-name-of-a-class-in-dynamically-imported-module
		# on sutter this is x/y/x !!!
		class_ = getattr(bMotor, motorName) # class_ is a module
		#print('class_:', class_)
		#class_ = getattr(class_, motorName) # class_ is a class
		self.xyzMotor = class_(isReal=isReal)


	def mousePressEvent(self, event):
		print('=== bCanvasApp.mousePressEvent()')
		super().mousePressEvent(event)
		#event.setAccepted(False)

	def keyPressEvent(self, event):
		print('myApp.keyPressEvent() event:', event)
		self.myGraphicsView.keyPressEvent(event)

	def newCanvas(self, shortName=''):
		if shortName=='':
			text, ok = QtWidgets.QInputDialog.getText(self, 'Text Input Dialog', 'Enter your name:')
			if ok:
				shortName = str(text)

		if shortName == '':
			return

		savePath = self._optionsDict['savePath']
		dateStr = datetime.today().strftime('%Y%m%d')

		datePath = os.path.join(savePath, dateStr)

		folderName = dateStr + '_' + shortName
		folderPath = os.path.join(datePath, folderName)

		videoFolderPath = os.path.join(folderPath, folderName + '_video')

		fileName = dateStr + '_' + shortName + '_canvas.txt'
		filePath = os.path.join(folderPath, fileName)

		print('bCanvasApp.newCanvas() filePath:', filePath)
		if os.path.isfile(filePath):
			print('   error: newCanvas() file exists:', filePath)
		else:
			if not os.path.isdir(datePath):
				os.mkdir(datePath)
			if not os.path.isdir(folderPath):
				os.mkdir(folderPath)

			if not os.path.isdir(videoFolderPath):
				os.mkdir(videoFolderPath)

			# finally, make the canvas
			self.canvasDict[fileName] = canvas.bCanvasWidget(filePath, self) #bCanvas(filePath=filePath)

	def save(self):
		"""
		Save the canvas
		"""
		self.canvas.save()

	def load(self, filePath='', askUser=False):
		"""
		Load a canvas
		"""
		if askUser:
			dataFolder = '/Users/cudmore/box/data/canvas' #os.path.join(self._getCodeFolder(), 'config')
			if not os.path.isdir(dataFolder):
				dataFolder = ''
			filePath = QtWidgets.QFileDialog.getOpenFileName(caption='xxx load canvas file', directory=dataFolder, filter="Canvas Files (*.txt)")
			filePath = filePath[0] # filePath is a tuple
			print('optionsLoad() got user file:', filePath)

		if os.path.isfile(filePath):
			#self.canvas.load(thisFile=thisFile)
			basename = os.path.basename(filePath)

			# this is causing waste of time problems
			# if I pass self to constructor, the canvas widget end up with multiple copies of its sub widgets?
			loadedCanvas = canvas.bCanvasWidget(filePath, self) #bCanvas(filePath=filePath)
			#loadedCanvas = bCanvasWidget(filePath) #bCanvas(filePath=filePath)

			#loadedCanvas.buildUI()
			self.canvasDict[basename] = loadedCanvas

		else:
			print('Warning: bCanvasApp.load() did not find file:', filePath)
			return


	@property
	def options(self):
		return self._optionsDict

	def defaultOptionsFile(self):
		if getattr(sys, 'frozen', False):
			# we are running in a bundle (frozen)
			bundle_dir = sys._MEIPASS
		else:
			# we are running in a normal Python environment
			bundle_dir = os.path.dirname(os.path.abspath(__file__))
		optionsFilePath = os.path.join(bundle_dir, 'config', 'Default_Options.json')
		return optionsFilePath

	'''
	@property
	def optionsFile(self):
		"""
		Return the options .json file name
		"""

		if getattr(sys, 'frozen', False):
			# we are running in a bundle (frozen)
			bundle_dir = sys._MEIPASS
		else:
			# we are running in a normal Python environment
			bundle_dir = os.path.dirname(os.path.abspath(__file__))
		optionsFilePath = os.path.join(bundle_dir, 'config', 'bCanvasApp_Options.json')
		return optionsFilePath
	'''

	def optionsDefault(self):
		self._optionsDict = OrderedDict()
		self._optionsDict['version'] = 0.1
		self._optionsDict['savePath'] = '/Users/cudmore/box/data/canvas'

		self._optionsDict['motor'] = OrderedDict()
		self._optionsDict['motor']['name'] = 'bPrior' # the name of the class derived from bMotor
		self._optionsDict['motor']['isReal'] = False

		# on olympus, camera is 1920 x 1200
		self._optionsDict['video'] = OrderedDict()
		self._optionsDict['video']['oneimage'] = 'bCamera/oneimage.tif'
		self._optionsDict['video']['umWidth'] = 693
		self._optionsDict['video']['umHeight'] = 433
		self._optionsDict['video']['stepFraction'] = 0.1

		self._optionsDict['scanning'] = OrderedDict()
		self._optionsDict['scanning']['zoomOneWidthHeight'] = 509.116882454314
		self._optionsDict['scanning']['stepFraction'] = 0.2

	def optionsLoad(self, askUser=False):
		if askUser:
			optionsFolder = os.path.join(self._getCodeFolder(), 'config')
			fname = QtWidgets.QFileDialog.getOpenFileName(caption='xxx load options file', directory=optionsFolder, filter="Options Files (*.json)")
			fname = fname[0]
			#dialog.setNameFilter("*.cpp *.cc *.C *.cxx *.c++");
			print('optionsLoad() got user file selection:', fname)
			if os.path.isfile(fname):
				with open(fname) as f:
					self._optionsDict = json.load(f)
				self.optionsFile = fname
		else:
			if not os.path.isfile(self.optionsFile):
				self.optionsFile = self.defaultOptionsFile()
				print('bCanvasApp.optionsLoad() is creating defaults options and saving them in:', self.optionsFile)
				self.optionsDefault()
				self.optionsSave()
			else:
				print('bCanvasApp.optionsLoad() loading:', self.optionsFile)
				with open(self.optionsFile) as f:
					self._optionsDict = json.load(f)

	def optionsSave(self):
		with open(self.optionsFile, 'w') as outfile:
			json.dump(self._optionsDict, outfile, indent=4, sort_keys=True)

	def _getCodeFolder(self):
		""" get full path to the folder where this file of code lives

		We are using this to
		1) Store single image file snapshot off video camera
		2) Place to store icons
		"""
		if getattr(sys, 'frozen', False):
			# we are running in a bundle (frozen)
			bundle_dir = sys._MEIPASS
		else:
			# we are running in a normal Python environment
			bundle_dir = os.path.dirname(os.path.abspath(__file__))
		return bundle_dir


if __name__ == '__main__':
	print('bCanvasApp __main__')
	import sys
	import logging
	import traceback

	try:

		print('bCanvasApp __main__ intantiation bimpy.bJavaBridge()')
		myJavaBridge = bimpy.bJavaBridge()
		print('bCanvasApp __main__ starting bimpy.bJavaBridge() with start()')
		myJavaBridge.start()

		app = QtWidgets.QApplication(sys.argv)
		app.setQuitOnLastWindowClosed(False)

		if 0:
			loadIgorCanvas = '/Users/cudmore/box/data/nathan/canvas/20190429_tst2'
			w = bCanvasApp(loadIgorCanvas=loadIgorCanvas)
			w.resize(640, 480)
			w.show()
			w.save()

		if 1:
			# make a new canvas and load what we just saved
			#savedCanvasPath = '/Users/cudmore/box/data/nathan/canvas/20190429_tst2/20190429_tst2_canvas.txt'
			#savedCanvasPath = 'd:/Users/cudmore/data/canvas/20190429_tst2/20190429_tst2_canvas.txt'
			#w2 = bCanvasApp(path=savedCanvasPath)
			myCanvasApp = bCanvasApp(parent=app)
			#w2.load(thisFile=savedCanvasPath)
			#print('bCanvasApp.__main__() myCanvasApp.optionsFile:', myCanvasApp.optionsFile)
			#myCanvasApp.resize(1024, 768)

		# working
		#w2.newCanvas('tst2')
		#w2.newCanvas('')

		'''
		myCanvasApp.optionsFile = 'C:/Users/cudmore/Sites/bImPy/canvas/config/Olympus_Options.json'
		myCanvasApp.optionsLoad()
		'''

		# 20200909 working
		'''
		path = '/Users/cudmore/box/data/canvas/20191226/20191226_tst1/20191226_tst1_canvas.txt'
		if os.path.isfile(path):
			myCanvasApp.load(path)
		'''

		# start a thread with videoFolderPath
		#bCamera.myVideoWidget()

		#video_stream_widget = VideoStreamWidget()

		sys.exit(app.exec_())
	except Exception as e:
		print('bCanvasApp __main__ exception')
		print(traceback.format_exc())
		#logging.error(traceback.format_exc())
		myJavaBridge.stop()
		#sys.exit(app.exec_())
		#raise
	finally:
		print('bCanvasApp __main__ finally')
		myJavaBridge.stop()
		#sys.exit(app.exec_())
	print('bCanvasApp __main__ last line')
