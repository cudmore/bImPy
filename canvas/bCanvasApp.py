# Author: Robert Cudmore
# Date: 20190630

import os, sys, json, traceback
import copy # to do deepcopy of (dict, OrderedDict)
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
	"""
	One main 'window' for the canvas appication.
		- One instance of video (canvas.bCamera.myVideoWidget)
		- One instance of motor (canvas.bMotor)
		- Keep a list of canvas (bCanvasWidget) in canvasDict.
	"""
	def __init__(self, loadIgorCanvas=None, path=None, parent=None):
		"""
		loadIgorCanvas: path to folder of converted Igor canvas
		path: path to text file of a saved Python canvas
		"""
		super(bCanvasApp, self).__init__()

		bLogger.info(f'path: {path}')

		self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

		# size of singleton 'QApplication' window on MS Windows
		w = 500
		h = 200
		self.resize(w, h)

		self.myApp = parent # to use activeWindow() or focusWidget()

		self.optionsFile = self.defaultOptionsFile()
		self.optionsLoad()

		self.myMenu = canvas.bMenu(self)

		# todo: do this after user modifies options, so they can set motor on fly
		#useMotor = self._optionsDict['motor']['useMotor']
		motorName = self._optionsDict['motor']['motorName'] # = 'bPrior'
		port = self._optionsDict['motor']['port']
		self.assignMotor(motorName, port)

		# dictionary of bCanvasWidget
		# each key is file name with no extension
		self.canvasDict = OrderedDict()

		# abb removed baltimore 20200916
		'''
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
		'''

		# todo: only needed on windows
		#self.show()

		# todo: self.camera = None and then create it when user first opens it
		# start a camera Thread
		self.camera = None #bCamera.myVideoWidget()
		self.showingCamera = False
		#self.camera.show()

	def closeEvent(self, event):
		# added this on windows, what does it do on mac? There is no main window?
		print('bCanvasApp.closeEvent()')

		# close canvas windows
		print('  closing canvas widgets/windows')
		for k in self.canvasDict.keys():
			self.canvasDict[k].close()

		# shutdown videothread#

		# tell the app to quit?
		print('  calling self.myApp.quit()')
		self.myApp.quit()
		event.accept()

	def toggleVideo(self):
		self.showingCamera = not self.showingCamera
		if self.showingCamera:
			if self.camera is None:
				saveAtInterval = self._optionsDict['video']['saveAtInterval'] # Boolean
				saveIntervalSeconds = self._optionsDict['video']['saveIntervalSeconds']
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
					scaleMult = scaleMult,
					saveAtInterval = saveAtInterval,
					saveIntervalSeconds = saveIntervalSeconds)
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

	def assignMotor(self, motorName, motorPort):
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
		class_ = getattr(canvas.bMotor, motorName) # class_ is a module
		#print('class_:', class_)
		#class_ = getattr(class_, motorName) # class_ is a class
		self.xyzMotor = class_(motorPort)

	def mousePressEvent(self, event):
		print('=== bCanvasApp.mousePressEvent()')
		bLogger.info('===')
		super().mousePressEvent(event)
		#event.setAccepted(False)

	'''
	def keyPressEvent(self, event):
		print('myApp.keyPressEvent() event:', event)
		bLogger.info(f'event:{event}')
		# todo: abb hopkins, why is this here?
		self.myGraphicsView.keyPressEvent(event)
	'''

	def bringCanvasToFront(self, fileNameNoExtension):
		print('bCanvasApp.bringCanvasToFront() fileNameNoExtension:', fileNameNoExtension)
		for canvas in self.canvasDict.keys():
			if canvas == fileNameNoExtension:
				self.canvasDict[canvas].activateWindow()
				self.canvasDict[canvas].raise_() # raise is a keyword and can't be used

	def activateCanvas(self, path):
		self.myMenu.buildCanvasMenu(self.canvasDict)

	def closeCanvas(self, path):
		fileNameNoExt = os.path.split(path)[1]
		fileNameNoExt = os.path.splitext(fileNameNoExt)[0]

		#self.canvasDict[fileNameNoExt]
		removed = self.canvasDict.pop(fileNameNoExt, None)
		if removed is None:
			print('warning: bCanvasApp.closeCanvas() did not remove', fileNameNoExt)
		else:
			self.myMenu.buildCanvasMenu(self.canvasDict)

	def newCanvas(self, shortName=''):
		"""
		new canvas(s) are always saved in options['Canvas']['savePath']
			options['Canvas']['savePath']/<date>_<name>
		"""

		# path where we will save on new
		savePath = self._optionsDict['Canvas']['savePath']

		if shortName=='':
			# if our savePath is bogus then abort
			if not os.path.isdir(savePath):
				# savepath from options is bogus
				print('bCanvasApp.newCanvas() error')
				print('  save path folder does not exist, savePath:', savePath)
				print('  Please specify a valid folder in main interface with menu "Options - Set Data Path ..."')

				msgBox = QtWidgets.QMessageBox()
				msgBox.setWindowTitle('Save Path Not Found')
				msgBox.setText('Did not find data path folder:\n  ' + savePath)
				msgBox.setInformativeText('Please specify a valid folder in main interface with menu "Options - Set Data Path ..."')
				retval = msgBox.exec_()
				return

			# ask user for the name of the canvas
			text, ok = QtWidgets.QInputDialog.getText(self,
							'New Canvas', 'Enter a new canvas name (no spaces):')
			text = text.replace(' ', '')
			if ok:
				shortName = str(text)

		if shortName == '':
			return

		dateStr = datetime.today().strftime('%Y%m%d')

		#datePath = os.path.join(savePath, dateStr)

		folderName = dateStr + '_' + shortName
		#folderPath = os.path.join(datePath, folderName)
		folderPath = os.path.join(savePath, folderName)
		#print('  folderPath:', folderPath)

		videoFolderPath = os.path.join(folderPath, folderName + '_video')

		fileName = dateStr + '_' + shortName + '_canvas.txt'
		filePath = os.path.join(folderPath, fileName)

		print('  bCanvasApp.newCanvas() filePath:', filePath)
		if os.path.isfile(filePath):
			print('   error: newCanvas() file exists:', filePath)

			text = f'Canvas "{shortName}" Already Exists'
			informativeText = 'Please choose a different name'
			tmp = canvas.okDialog(text, informativeText=informativeText)
			'''
			msg = QtWidgets.QMessageBox()
			msg.setIcon(QtWidgets.QMessageBox.Information)

			msg.setText(f'Canvas "{shortName}" Already Exists')
			msg.setInformativeText("Please choose a different name")
			msg.setWindowTitle("Canvas Already Exists")
			msg.setDetailedText(f'Existing path is:\n {filePath}')
			msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
			#msg.buttonClicked.connect(msgbtn)

			retval = msg.exec_()
			'''
		else:
			print('   making new canvas:', filePath)
			# todo: defer these until we actually save !!!
			'''
			if not os.path.isdir(datePath):
				os.mkdir(datePath)
			'''
			if not os.path.isdir(folderPath):
				print('  making dir folderPath:', folderPath)
				os.mkdir(folderPath)

			# made when we actually acquire a video
			#if not os.path.isdir(videoFolderPath):
			#	os.mkdir(videoFolderPath)

			# finally, make the canvas
			newCanvas = canvas.bCanvasWidget(filePath, self, isNew=True)

			# add to list
			fileNameNoExt, ext = os.path.splitext(fileName)
			self.canvasDict[fileNameNoExt] = newCanvas

			# update menus
			self.myMenu.buildCanvasMenu(self.canvasDict)

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
			dataFolder = self.options['Canvas']['savePath']
			# '/Users/cudmore/data/canvas' #os.path.join(self._getCodeFolder(), 'config')
			if not os.path.isdir(dataFolder):
				dataFolder = ''
			filePath = QtWidgets.QFileDialog.getOpenFileName(caption='Load a _canvas.txt file',
							directory=dataFolder, filter="Canvas Files (*.txt)")
			filePath = filePath[0] # filePath is a tuple
			print('bCanvasApp.load() got user file:', filePath)

		if os.path.isfile(filePath):
			# load
			loadedCanvas = canvas.bCanvasWidget(filePath, self, isNew=False) #bCanvas(filePath=filePath)

			basename = os.path.split(filePath)[1]
			basename = os.path.splitext(basename)[0]
			self.canvasDict[basename] = loadedCanvas

			self.myMenu.buildCanvasMenu(self.canvasDict)

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
		return 0.24

	def optionsDefault(self):
		self._optionsDict = OrderedDict()

		self._optionsDict['motor'] = OrderedDict()
		self._optionsDict['motor']['motorNameList'] = [motor for motor in dir(canvas.bMotor) if not (motor.endswith('__') or motor=='bMotor')]
		self._optionsDict['motor']['motorName'] = 'mp285' #'fakeMotor' #'mp285' #'bPrior' # the name of the class derived from bMotor
		self._optionsDict['motor']['portList'] = [f'COM{x+1}' for x in range(20)]
		self._optionsDict['motor']['port'] = 'COM4'
		#self._optionsDict['motor']['isReal'] = False

		# on olympus, camera is 1920 x 1200
		self._optionsDict['video'] = OrderedDict()
		self._optionsDict['video']['saveAtInterval'] = False
		self._optionsDict['video']['saveIntervalSeconds'] = 2
		#self._optionsDict['video']['oneimage'] = 'bCamera/oneimage.tif'
		self._optionsDict['video']['left'] = 100
		self._optionsDict['video']['top'] = 100
		self._optionsDict['video']['width'] = 640 #1280 # set this to actual video pixels
		self._optionsDict['video']['height'] = 480 #720
		self._optionsDict['video']['scaleMult'] = 1.0 # as user resizes window
		self._optionsDict['video']['umWidth'] = 455.2 #693
		self._optionsDict['video']['umHeight'] = 341.4 #433
		self._optionsDict['video']['motorStepFraction'] = 0.15 # for motor moves

		self._optionsDict['Scope'] = OrderedDict()
		self._optionsDict['Scope']['zoomOneWidthHeight'] = 509.116882454314
		self._optionsDict['Scope']['motorStepFraction'] = 0.15 # for motor moves
		self._optionsDict['Scope']['useWatchFolder'] = False # Olympus needs this

		self._optionsDict['Canvas'] = OrderedDict()
		self._optionsDict['Canvas']['wheelZoom'] = 1.1
		self._optionsDict['Canvas']['maxProjectChannel'] = 1 #
		self._optionsDict['Canvas']['useNapariViewer'] = True
		if sys.platform.startswith('win'):
			self._optionsDict['Canvas']['savePath'] = 'c:/Users/LindenLab/Desktop/cudmore/data'
		else:
			self._optionsDict['Canvas']['savePath'] = '/Users/cudmore/data/canvas'

		self._optionsDict['version'] = OrderedDict()
		self._optionsDict['version']['version'] = self.optionsVersion() #0.1


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
					self._optionsDict = json.load(f, object_pairs_hook=OrderedDict)
				# check if it is old
				loadedVersion = self._optionsDict['version']['version']
				if self.optionsVersion() > loadedVersion:
					print('  optionsLoad() loaded older options file, making new one')
					print('  loadedVersion:', loadedVersion)
					print('  self.optionsVersion()', self.optionsVersion())
					self.optionsDefault()

	def optionsSave(self):
		print('bCanvasApp.optionsSave() self.optionsFile:', self.optionsFile)
		# abb ubuntu
		tmpPath, tmpFile = os.path.split(self.optionsFile)
		if not os.path.isdir(tmpPath):
			print('  making folder:', tmpPath)
			os.mkdir(tmpPath)
		with open(self.optionsFile, 'w') as outfile:
			json.dump(self._optionsDict, outfile, indent=4, sort_keys=True)

	def optionsSetSavePath(self, savePath):
		if not os.path.isdir(savePath):
			print('warning: bCanvasApp.optionsSetSavePath() got bad save path:', savePath)
		else:
			self._optionsDict['Canvas']['savePath'] = savePath
			self.optionsSave()

	def slot_UpdateOptions(self, optionsDict):
		print('bCanvasApp.slot_UpdateOptions()')

		# grab existing and compare to new to find changes
		oldMotorName = self._optionsDict['motor']['motorName']
		oldPort = self._optionsDict['motor']['port']

		# make sure motor name is in list
		#self._optionsDict['motor']['motorNameList']

		# update
		self._optionsDict = copy.deepcopy(optionsDict)
		#self._optionsDict = optionsDict
		self.optionsSave()

		# update the motore
		# todo: check if it has changed
		# todo: do this after user modifies options, so they can set motor on fly
		newMotorName = self._optionsDict['motor']['motorName'] # = 'bPrior'
		newPort = self._optionsDict['motor']['port']
		#isReal = self._optionsDict['motor']['isReal'] #= False
		if oldMotorName != newMotorName or oldPort != newPort:
			print('  slot_UpdateOptions() calling self.assignMotor() with new motor')
			self.assignMotor(newMotorName, newPort)


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
		iconPath = os.path.join(iconsFolderPath, 'canvas-color-64.png')
		print('bCanvasApp() iconPath:', iconPath)
		appIcon = QtGui.QIcon(iconPath)
		# todo: on windows we need to set a bunch of sizes??? not sure if this is needed
		'''
		appIcon.addFile('gui/icons/16x16.png', QtCore.QSize(16,16))
		appIcon.addFile('gui/icons/24x24.png', QtCore.QSize(24,24))
		appIcon.addFile('gui/icons/32x32.png', QtCore.QSize(32,32))
		appIcon.addFile('gui/icons/48x48.png', QtCore.QSize(48,48))
		appIcon.addFile('gui/icons/256x256.png', QtCore.QSize(256,256))
		'''
		app.setWindowIcon(appIcon)

		myCanvasApp = bCanvasApp(parent=app)

		# todo: could also use platform.system() which returns 'Windows'
		if sys.platform.startswith('win') or sys.platform.startswith('linux'):
			# linden windows machine isreporting 'win32'
			myCanvasApp.show()

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

	okGo = True
	if len(sys.argv) > 1:
		if sys.argv[1] == 'javabridge':
			withJavaBridge = True
		else:
			okGo = False
			print('ERROR: did not understand command line:', sys.argv[1])

	if okGo:
		main(withJavaBridge)
