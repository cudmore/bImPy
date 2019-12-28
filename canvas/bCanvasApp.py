# Author: Robert Cudmore
# Date: 20190630

import os, sys, json #, subprocess
#from functools import partial
from collections import OrderedDict
from datetime import datetime

from PyQt5 import QtCore, QtWidgets, QtGui

import bimpy
from canvas import bCanvasWidget, bMenu
import bMotor

#class bCanvasApp(QtWidgets.QMainWindow):
#class bCanvasApp(QtWidgets.QApplication):
# was this
#class bCanvasApp(QtWidgets.QMainWindow):
class bCanvasApp(QtWidgets.QWidget):
	def __init__(self, loadIgorCanvas=None, path=None, parent=None):
		"""
		loadIgorCanvas: path to folder of converted Igor canvas
		path: path to text file of a saved Python canvas
		"""
		print('bCanvasApp.__init__()')
		super(bCanvasApp, self).__init__()

		self.optionsLoad()

		self.myMenu = bMenu(self)

		motorName = 'bPrior'
		self.assignMotor(motorName)

		self.canvasDict = {}
		'''
		if loadIgorCanvas is not None:
			#tmpCanvasFolderPath = '/Users/cudmore/Dropbox/data/20190429/20190429_tst2'
			#tmpCanvasFolderPath = '/Users/cudmore/box/data/nathan/canvas/20190429_tst2'
			self.canvas = bimpy.bCanvas(folderPath=loadIgorCanvas)

			# this is only for import from igor
			self.canvas.importIgorCanvas()

			self.canvas.buildFromScratch()
		else:
			self.canvas = bCanvas(filePath=path)
		'''


	def assignMotor(self, motorName):
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
		self.xyzMotor = class_(isReal=gMotorIsReal)


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
			self.canvasDict[fileName] = bCanvasWidget(filePath, self) #bCanvas(filePath=filePath)

	def save(self):
		"""
		Save the canvas
		"""
		self.canvas.save()

	def load(self, filePath):
		"""
		Load a canvas
		"""
		if os.path.isfile(filePath):
			#self.canvas.load(thisFile=thisFile)
			basename = os.path.basename(filePath)

			# this is causing waste of time problems
			# if I pass self to constructor, the canvas widget end up with multiple copies of its sub widgets?
			loadedCanvas = bCanvasWidget(filePath, self) #bCanvas(filePath=filePath)
			#loadedCanvas = bCanvasWidget(filePath) #bCanvas(filePath=filePath)

			#loadedCanvas.buildUI()
			self.canvasDict[basename] = loadedCanvas

		else:
			print('Warning: bCanvasApp.load() did not find file:', filePath)

	@property
	def options(self):
		return self._optionsDict

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

	def optionsDefault(self):
		self._optionsDict = OrderedDict()
		self._optionsDict['version'] = 0.1
		self._optionsDict['savePath'] = '/Users/cudmore/box/data/canvas'

		self._optionsDict['video'] = OrderedDict()
		self._optionsDict['video']['oneimage'] = 'oneimage.tif'
		self._optionsDict['video']['umWidth'] = 693
		self._optionsDict['video']['umHeight'] = 433

	def optionsLoad(self):
		if not os.path.isfile(self.optionsFile):
			self.optionsDefault()
			self.optionsSave()
		else:
			print('bCanvasApp.optionsLoad() loading:', self.optionsFile)
			with open(self.optionsFile) as f:
				self._optionsDict = json.load(f)

	def optionsSave(self):
		with open(self.optionsFile, 'w') as outfile:
			json.dump(self._optionsDict, outfile, indent=4, sort_keys=True)


if __name__ == '__main__':
	import sys
	#import bJavaBridge

	import logging
	import traceback

	try:
		gMotorIsReal = False

		#from bJavaBridge import bJavaBridge
		myJavaBridge = bimpy.bJavaBridge()
		myJavaBridge.start()

		app = QtWidgets.QApplication(sys.argv)
		app.setQuitOnLastWindowClosed(False)

		'''
		loadIgorCanvas = '/Users/cudmore/box/data/nathan/canvas/20190429_tst2'
		w = bCanvasApp(loadIgorCanvas=loadIgorCanvas)
		w.resize(640, 480)
		w.show()

		w.save()
		'''

		# make a new canvas and load what we just saved
		#savedCanvasPath = '/Users/cudmore/box/data/nathan/canvas/20190429_tst2/20190429_tst2_canvas.txt'
		#savedCanvasPath = 'd:/Users/cudmore/data/canvas/20190429_tst2/20190429_tst2_canvas.txt'
		#w2 = bCanvasApp(path=savedCanvasPath)
		w2 = bCanvasApp()
		#w2.load(thisFile=savedCanvasPath)
		print('bCanvasApp.__main__() w2.optionsFile:', w2.optionsFile)
		w2.resize(1024, 768)

		# working
		#w2.newCanvas('tst2')
		#w2.newCanvas('')

		path = '/Users/cudmore/box/data/canvas/20191226/20191226_tst1/20191226_tst1_canvas.txt'
		w2.load(path)

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
