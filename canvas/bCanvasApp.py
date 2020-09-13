# Author: Robert Cudmore
# Date: 20190630

import os, sys, json, traceback
from collections import OrderedDict
from datetime import datetime

from PyQt5 import QtCore, QtWidgets, QtGui

import qdarkstyle

from bLogger import bLogger

import logging
bLogger = logging.getLogger('canvasApp')

import bimpy

import canvas # for (bCanvs, bMotor, bCamera)

class bCanvasApp(QtWidgets.QMainWindow):
	def __init__(self, loadIgorCanvas=None, path=None, parent=None):
		"""
		loadIgorCanvas: path to folder of converted Igor canvas
		path: path to text file of a saved Python canvas
		"""
		super(bCanvasApp, self).__init__()

		bLogger.info(f'path: {path}')

		self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

		self.myApp = parent # to use activeWindow() or focusWidget()

		self.optionsFile = self.defaultOptionsFile()
		self.optionsLoad()

		self.myMenu = canvas.bMenu(self)

		useMotor = self._optionsDict['motor']['useMotor']
		motorName = self._optionsDict['motor']['name'] # = 'bPrior'
		isReal = self._optionsDict['motor']['isReal'] #= False
		self.assignMotor(useMotor, motorName, isReal)

		self.canvasDict = {}

		self.canvas = None
		if loadIgorCanvas is not None:
			#tmpCanvasFolderPath = '/Users/cudmore/Dropbox/data/20190429/20190429_tst2'
			#tmpCanvasFolderPath = '/Users/cudmore/box/data/nathan/canvas/20190429_tst2'
			self.canvas = canvas.bCanvas(folderPath=loadIgorCanvas)

			# this is only for import from igor
			self.canvas.importIgorCanvas()

			self.canvas.buildFromScratch()
		else:
			self.canvas = canvas.bCanvas(filePath=path)

		# todo: only needed on windows
		#self.show()

		# todo: self.camera = None and then create it when user first opens it
		# start a camera Thread
		self.camera = None #bCamera.myVideoWidget()
		self.showingCamera = False
		#self.camera.show()

	def toggleVideo(self):
		self.showingCamera = not self.showingCamera
		if self.showingCamera:
			if self.camera is None:
				left = self._optionsDict['video']['left']
				top  = self._optionsDict['video']['top']
				pos = (left,top)
				w = self._optionsDict['video']['width'] # actual video pixels
				h = self._optionsDict['video']['height']
				videoSize = (w,h)
				scaleMult = self._optionsDict['video']['scaleMult']
				self.camera = canvas.bCamera.myVideoWidget(parent=self,
					videoSize=videoSize,
					videoPos = pos,
					scaleMult = scaleMult)
				self.camera.videoWindowSignal.connect(self.slot_VideoChanged)
			self.camera.show()
		else:
			if self.camera is not None:
				self.camera.hide()

	def slot_VideoChanged(self, videoDict):
		#print('bCanvasApp.slot_VideoChanged() videoDict:', videoDict)
		event = videoDict['event']
		if event == 'Close Window':
			# actual video window is already closed (thread is still running)
			self.showingCamera = False
		elif event == 'Resize Window':
			# save the scaleMult (never change w/h)
			scaleMult = videoDict['scaleMult']
			self._optionsDict['video']['scaleMult'] = scaleMult
		elif event == 'Move Window':
			# save the (t,l)
			self._optionsDict['video']['left'] = videoDict['left']
			self._optionsDict['video']['top'] = videoDict['top']

	def getCurentImage(self):
		if self.camera is not None:
			return self.camera.getCurentImage()
		else:
			return None

	def assignMotor(self, useMotor, motorName, isReal):
		"""
		Create a motor controller from a class name

		Parameters:
			useMotor: False for off scope analysis
			motorName: A string corresponding to a derived class of bMotor. File is in bimpy/bMotor folder
		"""
		# we will import user defined motor class using a string
		# see: https://stackoverflow.com/questions/4821104/dynamic-instantiation-from-string-name-of-a-class-in-dynamically-imported-module
		# on sutter this is x/y/x !!!
		self.xyzMotor = None
		if useMotor:
			class_ = getattr(canvas.bMotor, motorName) # class_ is a module
			#print('class_:', class_)
			#class_ = getattr(class_, motorName) # class_ is a class
			self.xyzMotor = class_(isReal=isReal)

	def mousePressEvent(self, event):
		print('=== bCanvasApp.mousePressEvent()')
		bLogger.info('===')
		super().mousePressEvent(event)
		#event.setAccepted(False)

	def keyPressEvent(self, event):
		print('myApp.keyPressEvent() event:', event)
		bLogger.info(f'event:{event}')
		self.myGraphicsView.keyPressEvent(event)

	def newCanvas(self, shortName=''):
		if shortName=='':
			text, ok = QtWidgets.QInputDialog.getText(self, 'Text Input Dialog', 'Enter your name:')
			if ok:
				shortName = str(text)

		if shortName == '':
			return

		savePath = self._optionsDict['userOptions']['savePath']
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

		print('=== bCanvasApp.save()')

		# need to get the active canvas window
		# use
		#self.myApp = parent # to use activeWindow() or focusWidget()
		activeWindow = self.myApp.activeWindow()
		#focusWidget = self.myApp.focusWidget()

		print('  activeWindow:', activeWindow)
		#print('  focusWidget:', focusWidget)

		#if focusWidget is not None:
		if activeWindow is not None:
			# todo: double bCanvasWidget.bCanvasWidget is required?
			if isinstance(activeWindow, canvas.bCanvasWidget):
				print('  bCanvasApp.save() calling .save() for bCanvasWidget')
				activeWindow.saveMyCanvas()
			else:
				print('  bCanvasApp.save() front window is not a bCanvasWidget.bCanvasWidget')
		else:
			print('  bCanvasApp.save() no front widget?')
		'''
		self.canvas.save()
		self.optionsSave()
		'''

	def load(self, filePath='', askUser=False):
		"""
		Load a canvas
		"""
		if askUser:
			dataFolder = self.options['userOptions']['savePath']
			# '/Users/cudmore/data/canvas' #os.path.join(self._getCodeFolder(), 'config')
			if not os.path.isdir(dataFolder):
				dataFolder = ''
			filePath = QtWidgets.QFileDialog.getOpenFileName(caption='Load a _canvas.txt file',
							directory=dataFolder, filter="Canvas Files (*.txt)")
			filePath = filePath[0] # filePath is a tuple
			print('bCanvasApp.load() got user file:', filePath)

		if os.path.isfile(filePath):
			loadedCanvas = canvas.bCanvasWidget(filePath, self) #bCanvas(filePath=filePath)
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

	def optionsVersion(self):
		return 0.23

	def optionsDefault(self):
		self._optionsDict = OrderedDict()

		self._optionsDict['userOptions'] = OrderedDict()
		self._optionsDict['userOptions']['savePath'] = '/Users/cudmore/data/canvas'

		self._optionsDict['scope'] = OrderedDict()
		self._optionsDict['scope']['useWatchFolder'] = False # Olympus needs this

		self._optionsDict['version'] = OrderedDict()
		self._optionsDict['version']['version'] = self.optionsVersion() #0.1

		self._optionsDict['motor'] = OrderedDict()
		self._optionsDict['motor']['useMotor'] = True
		self._optionsDict['motor']['name'] = 'mp285' #'bPrior' # the name of the class derived from bMotor
		self._optionsDict['motor']['isReal'] = False

		# on olympus, camera is 1920 x 1200
		self._optionsDict['video'] = OrderedDict()
		self._optionsDict['video']['oneimage'] = 'bCamera/oneimage.tif'
		self._optionsDict['video']['left'] = 100
		self._optionsDict['video']['top'] = 100
		self._optionsDict['video']['width'] = 1280 # set this to actual video pixels
		self._optionsDict['video']['height'] = 720
		self._optionsDict['video']['scaleMult'] = 1.0 # as user resizes window
		self._optionsDict['video']['umWidth'] = 693
		self._optionsDict['video']['umHeight'] = 433
		self._optionsDict['video']['stepFraction'] = 0.2 # for motor moves

		self._optionsDict['scanning'] = OrderedDict()
		self._optionsDict['scanning']['zoomOneWidthHeight'] = 509.116882454314
		self._optionsDict['scanning']['stepFraction'] = 0.2 # for motor moves

		self._optionsDict['Interface'] = OrderedDict()
		self._optionsDict['Interface']['wheelZoom'] = 1.1

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
				# check if it is old
				loadedVersion = self._optionsDict['version']['version']
				if self.optionsVersion() > loadedVersion:
					print('  optionsLoad() loaded older options file, making new one')
					print('  loadedVersion:', loadedVersion)
					print('  self.optionsVersion()', self.optionsVersion())
					self.optionsDefault()

	def optionsSave(self):
		print('bCanvasApp.optionsSave() self.optionsFile:', self.optionsFile)
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


def main(withJavaBridge=False):
	try:
		if withJavaBridge:
			myJavaBridge = bimpy.bJavaBridge()
			myJavaBridge.start()

		app = QtWidgets.QApplication(sys.argv)
		app.setQuitOnLastWindowClosed(False)

		# set the icon of the application
		tmpPath = os.path.dirname(os.path.abspath(__file__))
		iconsFolderPath = os.path.join(tmpPath, 'icons')
		iconPath = os.path.join(iconsFolderPath, 'canvas-64.png')
		print('bCanvasApp() iconPath:', iconPath)
		appIcon = QtGui.QIcon(iconPath)
		app.setWindowIcon(appIcon)

		myCanvasApp = bCanvasApp(parent=app)

		# load an existing canvas
		path = '/Users/cudmore/data/canvas/20200911/20200911_aaa/20200911_aaa_canvas.txt'
		path = ''
		if os.path.isfile(path):
			myCanvasApp.load(path)

		sys.exit(app.exec_())
	except Exception as e:
		print('EXCEPTION: bCanvasApp.main()')
		print(traceback.format_exc())
		if withJavaBridge:
			myJavaBridge.stop()
	finally:
		#bLogger.info('bCanvasApp.main() finally')
		if withJavaBridge:
			myJavaBridge.stop()
	bLogger.info('bCanvasApp.main() last line .. bye bye')


if __name__ == '__main__':
	"""
	call main() with or without javabridge
	"""

	withJavaBridge = False

	if len(sys.argv) > 1:
		if sys.argv[1] == 'javabridge':
			withJavaBridge = True

	main(withJavaBridge)
