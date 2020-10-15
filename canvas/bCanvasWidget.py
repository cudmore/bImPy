# Robert H Cudmore
# 20191224

import os, sys, time, subprocess
from datetime import datetime
from functools import partial
from collections import OrderedDict

import numpy as np

from PyQt5 import QtCore, QtWidgets, QtGui

import bimpy
import canvas
import bToolbar

# I want this to inherit from QWidget, but that does not have addToolbar ???
#class bCanvasWidget(QtWidgets.QWidget):
class bCanvasWidget(QtWidgets.QMainWindow):
	def __init__(self, filePath, parent=None, isNew=True):
		"""
		filePath:
		parent: bCanvasApp
		"""
		print('bCanvasWidget.__init__() filePath:', filePath)
		super(bCanvasWidget, self).__init__(parent)
		self.filePath = filePath
		self.myCanvasApp = parent
		self.isNew = isNew # if False then was loaded

		# if filePath exists then will load, otherwise will make new and save
		self.myCanvas = canvas.bCanvas(filePath=filePath)

		self.myStackList = [] # a list of open bStack

		# on olympus we watch for new files to log motor position from Prior controller
		self.myLogFilePositon = None
		useWatchFolder = self.appOptions()['Scope']['useWatchFolder']
		if useWatchFolder:
			folderPath = os.path.dirname(self.filePath)
			self.myLogFilePositon = canvas.bLogFilePosition(folderPath, self.myCanvasApp.xyzMotor)

		self.buildUI()

		# do this after interface is created
		if self.isNew: # and self.getOptions()['motor']['useMotor']:
			print('bCanvasWidget is reading initial motor position')
			self.userEvent('read motor position')

		self.show()

		# has to be done after self.show()
		# center existing video/tiff
		self.myGraphicsView.centerOnCrosshair()

	def event(self, event):
		"""
		implemented to catch window activate
		"""
		#print('bCanvasWidget.event()', event.type() )
		if (event.type() == QtCore.QEvent.WindowActivate):
			#// window was activated
			print('bCanvasWidget.event() QtCore.QEvent.WindowActivate')
			self.myCanvasApp.activateCanvas(self.filePath)
		# see self.closeEvent()
		#if (event.type() == QtCore.QEvent.Close):
		#	print('bCanvasWidget.event() QtCore.QEvent.Close')

		return super().event(event)

	def closeEvent(self, event):
		"""
		called when window is closed
		"""
		# ask user if it is ok
		fileName = os.path.split(self.filePath)[1]
		fileName = os.path.splitext(fileName)[0]
		fileNameStr = f'Canvas name is "{fileName}"'

		close = canvas.okCancelDialog('Do You Want To Close The Canvas?',
									informativeText=fileNameStr)
		'''
		close = QtWidgets.QMessageBox()
		close.setText("Do You Want To Close The Canvas?")
		close.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
		close = close.exec()
		'''
		#if close == QtWidgets.QMessageBox.Yes:
		if close:
			# remove
			self.myCanvasApp.closeCanvas(self.filePath)
			#
			event.accept()
		else:
			event.ignore()

	def appOptions(self):
		return self.myCanvasApp.options

	def saveMyCanvas(self):
		"""
		save canvas as one text file
		"""
		if self.myCanvas is not None:
			self.myCanvas.save()

	def getCanvas(self):
		return self.myCanvas

	def getGraphicsView(self):
		return self.myGraphicsView

	def getStatusToolbar(self):
		return self.statusToolbarWidget

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

	def _getIcon(self, name):
		"""
		get full path to an icon file (usually a .png)
		"""
		codeFolder = self._getCodeFolder()
		iconPath = os.path.join(codeFolder, 'icons', name)
		return iconPath

	def selectInFileList(self, filename):
		"""
		User click on canvas image will select in file list
		"""
		print('bCanvasWidget.selectInFileList() filename:', filename)
		self.toolbarWidget.setSelectedItem(filename)

	def toggleVisibleCheck(self, filename, doShow):
		"""
		toggle checkbox in list on/off
		"""
		self.toolbarWidget.setCheckedState(filename, doShow)

	def openStack(self, filename, layer, channel=1):
		"""
		open a stack from the canvas
		"""
		print('=== bCanvasApp.openStack() filename:', filename)

		canvasPath = self.myCanvas._folderPath

		if layer == 'Video Layer':
			#canvasPath = os.path.join(canvasPath, 'video')
			canvasPath = self.myCanvas.videoFolderPath

		print('   canvasPath:', canvasPath)

		stackPath = os.path.join(canvasPath, filename)
		print('   bCanvasWidget.openStack() is opening viewer for stackPath:', stackPath)

		#todo: fix the logic here, using stack after loop
		# add something like *thisStac
		doNapari = self.myCanvasApp.options['Canvas']['useNapariViewer']
		alreadyOpen = False
		for stack in self.myStackList:
			if stack.path == stackPath:
				# bring to front
				alreadyOpen = True
				break
		print('  alreadyOpen:', alreadyOpen)
		if alreadyOpen:
			#doNapari = True
			if doNapari:
				# todo: add this to class bNapari
				stack.viewer.window._qt_window.show()
				stack.viewer.window._qt_window.activateWindow()
				stack.viewer.window._qt_window.raise_()
			else:
				# works for qwidget
				stack.show()
				stack.activateWindow()
				stack.raise_()
		else:
			# if I pass parent=self, all hell break loos (todo: fix this)
			# when i don't pass parent=self then closing the last stack window quits the application?

			"""
			we should keep a list of open stack (and function to close them)
			on double-clikc throw loaded data (load if necc) to a viewer
			"""
			#doNapari = True
			print('  bCanvasWidget.openStack() opening fresh')
			print('    doNapari:', doNapari)
			if doNapari:
				bStackObject = self.myCanvas.findStackByName(filename)
				# make sure channels are load
				print('  todo: loading stack data each time, fix this ... bStackObject.loadStack2()')
				bStackObject.loadStack2()

				tmp = canvas.bNapari(bStackObject, self)
			else:
				tmp = bimpy.interface.bStackWidget(path=stackPath)
				tmp.show()

			#tmp = bimpy.interface.bStackWidget(path=stackPath, parent=self)

			#print('done creating bStackWidget')
			self.myStackList.append(tmp)

	def grabImage(self):
		"""
		this grabs from a data stream
		we also need to grab from a file like with a point-gray camera

		todo:
			1) grab image
			2) make header with (motor, um size, date/time)
			3) tell backend bCanvas to .newVideoStack(imageData, imageHeader)
			"""

		print('=== bCanvasWidget.grabImage()')

		# grab single image from camera
		imageData = self.myCanvasApp.getCurentImage()
		if imageData is None:
			return

		# user speciified video with/height (um)
		umWidth = self.myCanvasApp.options['video']['umWidth']
		umHeight = self.myCanvasApp.options['video']['umHeight']

		# todo: do we need to swap x/y here?
		# maybe add readPosiitonn(preSwap=True) to get swapped

		# get the current motor position
		#xMotor, yMotor, zMotor = self.myCanvasApp.xyzMotor.readPosition()
		xMotor, yMotor, zMotor = self.readMotorPosition()
		if xMotor is None or yMotor is None: # or zMotor is None:
			print('error: bCanvasWidget.grabImage() got bad motor position')
			return False

		imageHeader = {
			'date': time.strftime('%Y%m%d'),
			'time': datetime.now().strftime("%H:%M:%S.%f")[:-4],
			'seconds': time.time(),
			'xMotor': xMotor,
			'yMotor': yMotor,
			'zMotor': zMotor,
			'umWidth': umWidth,
			'umHeight': umHeight,
		}
		# abb southwest
		newVideoStack = self.myCanvas.newVideoStack(imageData, imageHeader)

		if newVideoStack is not None:
			# append to graphics view
			self.myGraphicsView.appendVideo(newVideoStack)
			# append to toolbar widget (list of files)
			self.toolbarWidget.appendVideo(newVideoStack)

		return True

	def userEvent(self, event):
		print('=== myCanvasWidget.userEvent() event:', event)

		'''
		xStep = yStep = None
		if self.appOptions()['motor']['useMotor']:
			xStep, yStep = self.motorToolbarWidget.getStepSize()
		'''

		if event == 'move stage right':
			# todo: read current x/y move distance
			xStep, yStep = self.motorToolbarWidget.getStepSize()
			thePos = self.myCanvasApp.xyzMotor.move('right', xStep) # the pos is (x,y)
			self.userEvent('read motor position')
		elif event == 'move stage left':
			# todo: read current x/y move distance
			xStep, yStep = self.motorToolbarWidget.getStepSize()
			thePos = self.myCanvasApp.xyzMotor.move('left', xStep) # the pos is (x,y)
			self.userEvent('read motor position')
		elif event == 'move stage front':
			# todo: read current x/y move distance
			xStep, yStep = self.motorToolbarWidget.getStepSize()
			thePos = self.myCanvasApp.xyzMotor.move('front', yStep) # the pos is (x,y)
			self.userEvent('read motor position')
		elif event == 'move stage back':
			# todo: read current x/y move distance
			xStep, yStep = self.motorToolbarWidget.getStepSize()
			thePos = self.myCanvasApp.xyzMotor.move('back', yStep) # the pos is (x,y)
			self.userEvent('read motor position')
		elif event == 'read motor position':
			self.readMotorPosition()

			'''
			# update the interface
			x,y,z = self.myCanvasApp.xyzMotor.readPosition()

			# for mp285 swap x/y for diaply
			xDisplay = x
			yDisplay = y
			if self.myCanvasApp.xyzMotor.swapxy:
				tmp = xDisplay
				xDisplay = yDisplay
				yDisplay = tmp

			if xDisplay is not None:
				xDisplay = round(xDisplay,1)
			if yDisplay is not None:
				yDisplay = round(yDisplay,1)

			if xDisplay is None:
				self.motorToolbarWidget.xStagePositionLabel.setStyleSheet("color: red;")
				self.motorToolbarWidget.xStagePositionLabel.repaint()
			else:
				self.motorToolbarWidget.xStagePositionLabel.setStyleSheet("color: white;")
				self.motorToolbarWidget.xStagePositionLabel.setText(str(xDisplay))
				self.motorToolbarWidget.xStagePositionLabel.repaint()
			if yDisplay is None:
				self.motorToolbarWidget.yStagePositionLabel.setStyleSheet("color: red;")
				self.motorToolbarWidget.yStagePositionLabel.repaint()
			else:
				self.motorToolbarWidget.yStagePositionLabel.setStyleSheet("color: white;")
				self.motorToolbarWidget.yStagePositionLabel.setText(str(yDisplay))
				self.motorToolbarWidget.yStagePositionLabel.repaint()

			#self.motorToolbarWidget.setStepSize(x,y)

			# x/y coords are not updating???
			#self.motorToolbarWidget.xStagePositionLabel.update()

			# set red crosshair
			if xDisplay is not None and yDisplay is not None:
				self.myGraphicsView.myCrosshair.setMotorPosition(xDisplay, yDisplay)
			'''
		elif event == 'Canvas Folder':
			#print('sys.platform:', sys.platform)
			path = self.myCanvas._folderPath
			print('open folder on hdd', path)
			if sys.platform.startswith('darwin'):
				subprocess.Popen(["open", path])
			elif sys.platform.startswith('win'):
				windowsPath = os.path.abspath(path)
				#print('windowsPath:', windowsPath)
				os.startfile(windowsPath)
			else:
				subprocess.Popen(["xdg-open", path])

		elif event == 'Live Video':
			# toggle video on/offset
			print('=== bCanvasWidget.userEvent() event:', event)
			self.myCanvasApp.toggleVideo()

		elif event == 'Grab Image':
			self.grabImage()

		elif event =='Import From Scope':
			print('=== bCanvasWidget.userEvent() event:', event)

			# todo: build a list of all (.tif and folder)
			# pass this to self.myCanvas.addNEwScopeFile()
			# that will return a list of files actually added
			#
			# option 2: pass importNEwScope file
			#	- a dict of log file positions
			#	- try and swap x/y of motor when we display?

			# abb southwest
			useWatchFolder = self.appOptions()['Scope']['useWatchFolder']
			if useWatchFolder:
				watchDict = self.myLogFilePositon.getPositionDict()
			else:
				watchDict = None
			newScopeFileList = self.myCanvas.importNewScopeFiles(watchDict=watchDict)

			for newScopeFile in newScopeFileList:
				# append to view
				self.myGraphicsView.appendScopeFile(newScopeFile)

				# append to list
				self.toolbarWidget.appendScopeFile(newScopeFile)
			if len(newScopeFileList) > 0:
				self.saveMyCanvas()
				#self.myCanvas.save()

		elif event == 'print stack info':
			selectedItem = self.myGraphicsView.getSelectedItem()
			if selectedItem is not None:
				selectedItem.myStack.print()

		elif event == 'center canvas on motor position':
			self.getGraphicsView().centerOnCrosshair()

		else:
			print('bCanvasWidget.userEvent() not understood:', event)

	def readMotorPosition(self):
		# update the interface
		x,y,z = self.myCanvasApp.xyzMotor.readPosition()

		# for mp285 swap x/y for diaply
		xDisplay = x
		yDisplay = y
		if self.myCanvasApp.xyzMotor.swapxy:
			tmp = xDisplay
			xDisplay = yDisplay
			yDisplay = tmp

		if xDisplay is not None:
			xDisplay = round(xDisplay,1)
		if yDisplay is not None:
			yDisplay = round(yDisplay,1)

		if xDisplay is None:
			self.motorToolbarWidget.xStagePositionLabel.setStyleSheet("color: red;")
			self.motorToolbarWidget.xStagePositionLabel.repaint()
		else:
			self.motorToolbarWidget.xStagePositionLabel.setStyleSheet("color: white;")
			self.motorToolbarWidget.xStagePositionLabel.setText(str(xDisplay))
			self.motorToolbarWidget.xStagePositionLabel.repaint()
		if yDisplay is None:
			self.motorToolbarWidget.yStagePositionLabel.setStyleSheet("color: red;")
			self.motorToolbarWidget.yStagePositionLabel.repaint()
		else:
			self.motorToolbarWidget.yStagePositionLabel.setStyleSheet("color: white;")
			self.motorToolbarWidget.yStagePositionLabel.setText(str(yDisplay))
			self.motorToolbarWidget.yStagePositionLabel.repaint()

		#self.motorToolbarWidget.setStepSize(x,y)

		# x/y coords are not updating???
		#self.motorToolbarWidget.xStagePositionLabel.update()

		# set red crosshair
		if xDisplay is not None and yDisplay is not None:
			self.myGraphicsView.myCrosshair.setMotorPosition(xDisplay, yDisplay)

		return x,y,z

	def getOptions(self):
		return self.myCanvasApp._optionsDict

	def buildUI(self):
		self.centralwidget = QtWidgets.QWidget()
		#self.centralwidget = QtWidgets.QWidget(parent)
		#self.centralwidget.setObjectName("centralwidget")

		# V Layout for | canvas | one line feedback
		self.myQVBoxLayout = QtWidgets.QVBoxLayout(self.centralwidget)

		self.title = self.filePath
		self.left = 50
		self.top = 50
		self.width = 800
		self.height = 700

		self.setMinimumSize(640, 640)
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)

		#
		#
		# 201912, need to load canvas first, ow myQGraphicsView will not populate
		#tmpPath = '/Users/cudmore/box/data/nathan/canvas/20190429_tst2/20190429_tst2_canvas.txt'
		#self.load(thisFile=tmpPath)
		#
		#

		# main view to hold images
		# leave at end, it is using self.motorToolbarWidget
		self.myGraphicsView = myQGraphicsView(self)
		self.myQVBoxLayout.addWidget(self.myGraphicsView)

		# todo: 20191217, add a status bar !!!
		self.statusToolbarWidget = bToolbar.myStatusToolbarWidget(parent=self)
		self.addToolBar(QtCore.Qt.BottomToolBarArea, self.statusToolbarWidget)

		# here I am linking the toolbar to the graphics view
		# i can't figure out how to use QAction !!!!!!
		self.motorToolbarWidget = bToolbar.myScopeToolbarWidget(parent=self)
		self.addToolBar(QtCore.Qt.LeftToolBarArea, self.motorToolbarWidget)
		#useMotor = self.getOptions()['motor']['useMotor']
		#if useMotor:
		if self.isNew:
			pass
		else:
			self.motorToolbarWidget.hide()

		self.toolbarWidget = bToolbar.myToolbarWidget(self)
		self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbarWidget)

		self.setCentralWidget(self.centralwidget)

		#self.myStackList = [] # a list of open bStack

	def toggleMotor(self):
		if self.motorToolbarWidget.isVisible():
			self.motorToolbarWidget.hide()
			self.myGraphicsView.myCrosshair.hide()
		else:
			self.motorToolbarWidget.show()
			self.myGraphicsView.myCrosshair.show()

	def keyPressEvent(self, event):
		#print('\n=== bCanvasWidget.keyPressEvent()', event.text())

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		isControl = modifiers == QtCore.Qt.ControlModifier

		'''
		if isControl and event.key() == QtCore.Qt.Key_S:
			#event.accept(True)
			print('  ... save canvas ...')
			print('  TODO: reactivate bMenu Save by having canvas window signal app when window takes focus')
		'''

		if event.key() == QtCore.Qt.Key_M:
			self.toggleMotor()

		elif isControl and event.key() == QtCore.Qt.Key_W:
			self.close() # should trigger self.closeEvent()

globalSquare = {
	'pen': QtCore.Qt.SolidLine, # could be QtCore.Qt.DotLine
	'penColor': QtCore.Qt.blue,
	'penWidth': 4,
}
globalSelectionSquare = {
	'pen': QtCore.Qt.SolidLine, # could be QtCore.Qt.DotLine
	'penColor': QtCore.Qt.yellow,
	'penWidth': 7,
}

class myQGraphicsPixmapItem(QtWidgets.QGraphicsPixmapItem):
	"""
	To display images in canvas

	Each item is added to a scene (QGraphicsScene)
	"""
	#def __init__(self, fileName, index, myLayer, myQGraphicsView, parent=None):
	def __init__(self, fileName, myLayer, theStack, parent=None):
		"""
		theStack: the underlying bStack, assuming it has at least its header loaded ???
		"""

		'''
		print('myQGraphicsPixmapItem.__init__')
		print('   fileName:', fileName)
		print('   index:', index)
		print('   myLayer:', myLayer)
		print('   theStack:', theStack)
		print('   parent:', parent)
		'''

		super(myQGraphicsPixmapItem, self).__init__(parent)
		#self.myQGraphicsView = myQGraphicsView
		self._fileName = fileName
		self.myLayer = myLayer
		self._isVisible = True
		# new 20191229
		self.myStack = theStack # underlying bStack

		# abb 20200913 baltimore
		self._drawSquare = True

		#self.hide()

	# was trying to not have ot use opacity 0.01
	'''
	def shape(self):
		print('myQGraphicsPixmapItem.shape()')
		self.setOpacity(0.1)
		super().shape()
		self.setOpacity(0.0)
	'''

	def paint(self, painter, option, widget=None):
		super().paint(painter, option, widget)
		"""
		painter.setBrush(self.brush)
		painter.setPen(self.pen)
		painter.drawEllipse(self.rect)
		"""

		#print('myQGraphicsPixmapItem.paint self.shapeMode():', self._fileName, self.shapeMode())

		self.drawMyRect(painter)
		#print('myQGraphicsPixmapItem.paint() isSelected', self.isSelected())
		if self.isSelected():
			self.drawFocusRect(painter)

	def drawMyRect(self, painter):
		#print('myQGraphicsPixmapItem.drawFocusRect() self.boundingRect():', self.boundingRect())
		if not self._drawSquare:
			return

		self.focusbrush = QtGui.QBrush()

		self.focuspen = QtGui.QPen(globalSquare['pen'])
		self.focuspen.setColor(globalSquare['penColor'])
		self.focuspen.setWidthF(globalSquare['penWidth'])
		#
		painter.setBrush(self.focusbrush)
		painter.setPen(self.focuspen)

		painter.setOpacity(1.0)

		#painter.drawRect(self.focusrect)
		# ???
		painter.drawRect(self.boundingRect())

	def drawFocusRect(self, painter):
		#print('myQGraphicsPixmapItem.drawFocusRect()')
		self.focusbrush = QtGui.QBrush()
		'''
		self.focuspen = QtGui.QPen(QtCore.Qt.SolidLine)
		self.focuspen.setColor(QtCore.Qt.yellow)
		self.focuspen.setWidthF(5)
		'''
		self.focuspen = QtGui.QPen(globalSelectionSquare['pen'])
		self.focuspen.setColor(globalSelectionSquare['penColor'])
		self.focuspen.setWidthF(globalSelectionSquare['penWidth'])
		#
		painter.setBrush(self.focusbrush)
		painter.setPen(self.focuspen)

		painter.setOpacity(1.0)

		painter.drawRect(self.boundingRect())

	'''
	def mousePressEvent(self, event):
		"""
		needed for mouse click+drag
		"""
		#print('   myQGraphicsPixmapItem.mousePressEvent()')
		super().mousePressEvent(event)
		#self.scene().mousePressEvent(event)
		#event.setAccepted(False)

	def mouseMoveEvent(self, event):
		"""
		needed for mouse click+drag
		"""
		#print('   myQGraphicsPixmapItem.mouseMoveEvent()')
		super().mouseMoveEvent(event)
		#self.scene().mouseMoveEvent(event)
		#event.setAccepted(False)

	def mouseReleaseEvent(self, event):
		"""
		needed for mouse click+drag
		"""
		#print('   myQGraphicsPixmapItem.mouseReleaseEvent()', 'motor position:', self.pos())
		super().mouseReleaseEvent(event)
		#self.scene().mouseReleaseEvent(event)
		#event.setAccepted(False)
	'''

	def bringForward(self):
		"""
		move this item before its previous sibling

		todo: don't ever move video in front of 2p!
		"""
		print('myQGraphicsPixmapItem.myQGraphicsPixmapItem.bringForward()')
		myScene = self.scene()
		previousItem = None

		# debug, list all items
		for idx, item in enumerate(self.scene().items(QtCore.Qt.DescendingOrder)):
			print(idx, item._fileName, item.zValue())

		for item in self.scene().items(QtCore.Qt.DescendingOrder):
			if item == self:
				break
			previousItem = item
		if previousItem is not None:
			print('    myQGraphicsPixmapItem.bringForward() is moving', self._fileName, 'before', previousItem._fileName)
			# this does not work !!!!
			#self.stackBefore(previousItem)
			previous_zvalue = previousItem.zValue()
			this_zvalue = self.zValue()
			print('previous_zvalue:', previous_zvalue, 'this_zvalue:', this_zvalue)
			previousItem.setZValue(this_zvalue)
			self.setZValue(previous_zvalue)
			#self.stackBefore(previousItem)
			#
			self.update()
		else:
			print('   myQGraphicsPixmapItem.bringToFront() item is already front most')

	def sendBackward(self):
		"""
		move this item after its next sibling

		todo: don't every move 2p behind video
		"""
		print('myQGraphicsPixmapItem.myQGraphicsPixmapItem.sendBackward()')
		myScene = self.scene()
		nextItem = None
		for item in self.scene().items(QtCore.Qt.AscendingOrder):
			if item == self:
				break
			nextItem = item
		if nextItem is not None:
			print('   myQGraphicsPixmapItem.sendBackward() is moving', self._fileName, 'after', nextItem._fileName)
			# this does not work !!!!
			#self.stackBefore(previousItem)
			next_zvalue = nextItem.zValue()
			this_zvalue = self.zValue()
			nextItem.setZValue(this_zvalue)
			self.setZValue(next_zvalue)
			self.update()
		else:
			print('   myQGraphicsPixmapItem.bringToFront() item is already front most')

class myQGraphicsView(QtWidgets.QGraphicsView):
	"""
	Main canvas widget
	"""
	def __init__(self, myCanvasWidget):
		super(myQGraphicsView, self).__init__(myCanvasWidget)

		self.myCanvasWidget = myCanvasWidget

		self.myMouse_x = None
		self.myMouse_y = None

		self.setBackgroundBrush(QtCore.Qt.darkGray)

		#20191217
		#self.myScene = QtWidgets.QGraphicsScene(self)
		#self.myScene = QtWidgets.QGraphicsScene()
		myScene = QtWidgets.QGraphicsScene(self)
		self.setScene(myScene)

		# visually turn off scroll bars
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

		# these work
		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

		numItems = 0 # used to stack items with item.setZValue()

		for idx, videoFile in enumerate(self.myCanvasWidget.getCanvas().videoFileList):
			self.appendVideo(videoFile)
			numItems += 1

		# this is to load 2p file ... put back in
		#for idx, image in enumerate(fakeTwoPImages.keys()):
		for idx, scopeFile in enumerate(self.myCanvasWidget.getCanvas().scopeFileList):
			self.appendScopeFile(scopeFile)
			numItems += 1


		# a cross hair and rectangle (size of zoom)
		#useMotor = self.myCanvasWidget.appOptions()['motor']['useMotor']
		#if useMotor:
		self.myCrosshair = myCrosshairRectItem(self)
		self.myCrosshair.setZValue(10000)
		self.scene().addItem(self.myCrosshair)
		# read initial position (might cause problems)
		# does not work, not all objects are initialized
		#print('myQGraphicsView.__init__ is asking myCanvasWidget to read initial motor position')
		#self.myCanvasWidget.userEvent('read motor position')
		if self.myCanvasWidget.isNew:
			pass
		else:
			self.myCrosshair.hide()

	def centerOnCrosshair(self):
		print('myQGraphicsView.centerOnCrosshair()')

		# trying to zoom to full view
		borderMult = 1.1

		bounds = self.scene().itemsBoundingRect()
		print('  1 bounds:', bounds)
		bounds.setWidth(bounds.width() * borderMult)
		bounds.setHeight(bounds.height() * borderMult)
		print('  2 bounds:', bounds)
		#self.ensureVisible ( bounds )
		self.fitInView( bounds, QtCore.Qt.KeepAspectRatio )

		#return

	def zoomSelectedItem(self, fileName):
		print('   myQGraphicsView.zoomSelectedItem() fileName:', fileName)
		zoomThisItem = None
		for item in self.scene().items():
			if item._fileName == fileName:
				zoomThisItem = item
		if zoomThisItem is not None:
			'''
			bounds = item.boundingRect() # local to item
			print('  1 type(bounds):', bounds)
			bounds = item.mapToScene(bounds)
			print('  2 type(bounds):', bounds)
			'''
			print('   myQGraphicsView.zoomSelectedItem:', zoomThisItem._fileName)
			self.fitInView( zoomThisItem, QtCore.Qt.KeepAspectRatio )

	def appendScopeFile(self, newScopeFile):
		"""
		"""

		# what about
		# pixMapItem.setZValue(numItems)

		# todo: on olympus the header will not have x/y motor, we need to look up in our watched folderPath
		# THESE ARE FUCKING STRINGS !!!!!!!!!!!!!!!!!!!!
		path = newScopeFile.path
		fileName = newScopeFile.getFileName()
		xMotor = newScopeFile.header.header['xMotor']
		yMotor = newScopeFile.header.header['yMotor']

		# abb 20200912, baltimore
		# IMPORTANT: If we do not know (umwidth, umHeight) WE CANNOT place iimage in canvas !!!
		umWidth = newScopeFile.header.header['umWidth']
		umHeight = newScopeFile.header.header['umHeight']
		#

		'''
		print('\n')
		print('bCanvasWidget.appendScopeFile() path:', path)
		print('  umWidth:', umWidth, 'umHeight:', umHeight)
		print('\n')
		'''

		if xMotor == 'None':
			xMotor = None
		if yMotor == 'None':
			yMotor = None

		#if xMotor is None or yMotor is None:
		#	print('bCanvasWidget.myQGraphicsView() not inserting scopeFile -->> xMotor or yMotor is None ???')
		#	#continue

		# stackMax can be None
		maxProjectChannel = self.myCanvasWidget.getOptions()['Canvas']['maxProjectChannel']
		stackMax = newScopeFile.getMax(channel=maxProjectChannel) # stackMax can be None
		if stackMax is None:
			print('\n\n')
			print('  myQGraphicsView.appendScopeFile() got stackMax None. path:', path)
			#print('    myQGraphicsView.appendScopeFile is not appending file')
			imageStackHeight = newScopeFile.header.header['xPixels']
			imageStackWidth = newScopeFile.header.header['yPixels']
			print(f'  imageStackWidth {imageStackWidth} imageStackHeight {imageStackHeight}')
			print('\n\n')
		else:
			imageStackHeight, imageStackWidth = stackMax.shape

		print('myQGraphicsView.appendScopeFile() path:', path)
		print('  xMotor:', xMotor, 'yMotor:', yMotor)
		print('  umWidth:', umWidth, 'umHeight:', umHeight)
		print('  imageStackHeight:', imageStackHeight, 'imageStackWidth:', imageStackWidth)

		if stackMax is None:
			print('  myQGraphicsView.appendScopeFile() is making zero max image for newScopeFile:', newScopeFile)
			stackMax = np.zeros((imageStackWidth, imageStackHeight), dtype=np.uint8)

		# always map to 8-bit (should work for 8/14/16, etc)
		stackMax_8Bit = ((stackMax - stackMax.min()) / (stackMax.ptp() / 255.0)).astype(np.uint8) # map the data range to 0 - 255

		myQImage = QtGui.QImage(stackMax_8Bit, imageStackWidth, imageStackHeight, QtGui.QImage.Format_Indexed8)

		#
		# try and set color
		colors=[]
		for i in range(256): colors.append(QtGui.qRgb(i/4,i,i/2))
		myQImage.setColorTable(colors)

		pixmap = QtGui.QPixmap(myQImage)
		pixmap = pixmap.scaled(umWidth, umHeight, QtCore.Qt.KeepAspectRatio)

		# insert
		#pixMapItem = myQGraphicsPixmapItem(fileName, idx, '2P Max Layer', self, parent=pixmap)
		pixMapItem = myQGraphicsPixmapItem(fileName, '2P Max Layer', newScopeFile, parent=pixmap)
		pixMapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
		pixMapItem.setToolTip(fileName)
		pixMapItem.setPos(xMotor,yMotor)
		#todo: this is important, self.myScene needs to keep all video BELOW 2p images!!!

		#pixMapItem.setZValue(200)
		numItems = len(self.scene().items())
		pixMapItem.setZValue(1000 + numItems) # do i use this???

		# this also effects bounding rect
		#pixMapItem.setOpacity(0.0) # 0.0 transparent 1.0 opaque

		pixMapItem.setShapeMode(QtWidgets.QGraphicsPixmapItem.BoundingRectShape)
		#print('appendScopeFile() setting pixMapItem.shapeMode():', pixMapItem.shapeMode())

		# add to scene
		self.scene().addItem(pixMapItem)

		#numItems += 1

	# todo: put this in __init__() as a function
	def appendVideo(self, newVideoStack):
		# what about
		# pixMapItem.setZValue(numItems)

		path = newVideoStack.path
		fileName = newVideoStack.getFileName()
		#videoFileHeader = videoFile.getHeader()
		xMotor = newVideoStack.getHeaderVal2('xMotor')
		yMotor = newVideoStack.getHeaderVal2('yMotor')
		umWidth = newVideoStack.getHeaderVal2('umWidth')
		umHeight = newVideoStack.getHeaderVal2('umHeight')

		if xMotor is None or yMotor is None:
			print('error: myQGraphicsView.appendVideo() got bad xMotor/yMotor')
			print('      -->> ABORTING')
			return
		if umWidth is None or umHeight is None:
			print('error: myQGraphicsView.appendVideo() got bad umWidth/umHeight')
			print('      -->> ABORTING')
			return

		xMotor = float(xMotor)
		yMotor = float(yMotor)

		channel = 1
		videoImage = newVideoStack.getStack('video', channel) # ndarray
		imageStackHeight, imageStackWidth = videoImage.shape

		print('myQGraphicsView.appendVideo() path:', path)
		print('  xMotor:', xMotor, 'yMotor:', yMotor)
		print('  umWidth:', umWidth, 'umHeight:', umHeight)
		print('  imageStackHeight:', imageStackHeight, 'imageStackWidth:', imageStackWidth)

		myQImage = QtGui.QImage(videoImage, imageStackWidth, imageStackHeight, QtGui.QImage.Format_Indexed8)
		#myQImage = QtGui.QImage(videoImage, imageStackWidth, imageStackHeight, QtGui.QImage.Format_RGB32)

		pixmap = QtGui.QPixmap(myQImage)
		pixmap = pixmap.scaled(umWidth, umHeight, QtCore.Qt.KeepAspectRatio)

		# insert
		#pixMapItem = myQGraphicsPixmapItem(fileName, idx, 'Video Layer', self, parent=pixmap)
		pixMapItem = myQGraphicsPixmapItem(fileName, 'Video Layer', newVideoStack, parent=pixmap)
		pixMapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
		pixMapItem.setToolTip(fileName)
		pixMapItem.setPos(xMotor,yMotor)
		#todo: this is important, self.myScene needs to keep all video BELOW 2p images!!!
		#tmpNumItems = 100
		numItems = len(self.scene().items())
		pixMapItem.setZValue(500 + numItems) # do i use this???

		# add to scene
		self.scene().addItem(pixMapItem)

	def setSelectedItem(self, fileName):
		"""
		Select the item at itemIndex.
		This is usually coming from toolbar file list selection
		"""
		print('   myQGraphicsView.setSelectedItem() fileName:', fileName)
		selectThisItem = None
		for item in self.scene().items():
			# I don't want to select rect when showing both 2p max and rect
			#print(item._fileName, isinstance(item, QtWidgets.QGraphicsPixmapItem)) # only select images, not rects
			#print('   item.flags():', item.flags())

			# if '2p max layer off' then we DO want to select 2p square
			# put the logic here rather than turning isSelectible(True/False)

			isSelectable = item.flags() & QtWidgets.QGraphicsItem.ItemIsSelectable
			item.setSelected(False) # as we iterate, make sure we turn off all selection
			if isSelectable and item._fileName == fileName:
				selectThisItem = item
		if selectThisItem is not None:
			print('   myQGraphicsView.setSelectedItem:', selectThisItem, selectThisItem._fileName, selectThisItem.pos())
		self.scene().setFocusItem(selectThisItem)
		selectThisItem.setSelected(True)

	def hideShowItem(self, fileName, doShow):
		"""
		Hide/Show individual items

		todo: if a layer is off then do not hide/show, better yet,
		when layer is off, disable checkboxes in myToolbarWidget
		"""
		for item in self.scene().items():
			if item._fileName == fileName:
				# todo: need to ask the self.myCanvas if the layer is on !!!

				if item.myLayer=='Video Layer':
					item.setOpacity(1.0 if doShow else 0)
				else:
					item.setOpacity(1.0 if doShow else 0.01)
				# keep track of this for each item so we can keep checked items in myToolbarWidget in sync
				#when user presses checkboxes to toggle layers on/off
				item._isVisible = doShow

	def hideShowLayer(self, thisLayer, isVisible):
		"""
		if hide/show thisLayer is '2p max layer' then set opacity of '2p max layer'

		layers:
			Video Layer
			Video Squares Layer
			2P Max Layer
			2P Squares Layer

		"""
		print('myQGraphicsView.hideShowLayer() thisLayer:', thisLayer, 'isVisible:', isVisible)

		doVideoSquares = False
		if thisLayer == 'Video Squares Layer':
			thisLayer = 'Video Layer'
			doVideoSquares= True

		doTwoPhotonSquares = False
		if thisLayer == '2P Squares Layer':
			thisLayer = '2P Max Layer'
			doTwoPhotonSquares= True

		for item in self.scene().items():
			#print(item._fileName, item.myLayer)
			if item.myLayer == thisLayer:
				# don't show items in this layer that are not visible
				# not visible are files that are checked off in myToolbarWidget
				if isVisible and not item._isVisible:
					continue
				if thisLayer=='Video Layer':
					# turn off both image and outline
					if doVideoSquares:
						item._drawSquare = isVisible
					else:
						item.setOpacity(1.0 if isVisible else 0.01)
				elif thisLayer == '2P Max Layer':
					# allow show/hide of both (max, square)
					if doTwoPhotonSquares:
						item._drawSquare = isVisible
					else:
						item.setOpacity(1.0 if isVisible else 0.01)
			else:
				pass
		#
		self.scene().update()

	def mouseDoubleClickEvent(self, event):
		"""
		open a stack on a double-click
		"""
		print('=== myQGraphicsView.mouseDoubleClickEvent')
		selectedItems = self.scene().selectedItems()
		if len(selectedItems) > 0:
			selectedItem = selectedItems[0]
			fileName = selectedItem._fileName
			layer = selectedItem.myLayer
			#print('   layer:', layer)
			self.myCanvasWidget.openStack(fileName, layer)

	'''
	def mousePressEvent(self, event):
		print('=== myQGraphicsView.mousePressEvent() x:', event.x(), 'y:', event.y())
		scenePoint = self.mapToScene(event.x(), event.y())
		#print('=== myQGraphicsView.mousePressEvent() scene_x:', scenePoint.x(), 'scene_y:', scenePoint.y())
		super().mousePressEvent(event)
		#event.setAccepted(False)
	'''

	def mouseMoveEvent(self, event):
		#print('=== myQGraphicsView.mouseMoveEvent() x:', event.x(), 'y:', event.y())

		# this is critical, allows dragging view/scene around
		#scenePoint = self.mapToScene(event.x(), event.y())
		#print(scenePoint)

		super().mouseMoveEvent(event)

		scenePoint = self.mapToScene(event.x(), event.y())

		item = self.scene().itemAt(scenePoint, QtGui.QTransform())
		filename = ''
		if item is not None:
			filename = item._fileName
		#print('mouseMoveEvent() item:', item._fileName)

		self.myCanvasWidget.getStatusToolbar().setMousePosition(scenePoint, filename=filename)

		# todo: what are these for ?
		self.myMouse_x = event.x() #scenePoint.x()
		self.myMouse_y = event.y() #scenePoint.y()

		# abb 20200914
		#event.setAccepted(True)

	def mouseReleaseEvent(self, event):
		#print('=== myQGraphicsView.mouseReleaseEvent() x:', event.x(), 'y:', event.y())
		super().mouseReleaseEvent(event)

		#print('   tell the parent self.myCanvasWidget to select this file in its file list')
		selectedItems = self.scene().selectedItems()
		#print('   selectedItems:', selectedItems)#event.setAccepted(False)
		if len(selectedItems) > 0:
			selectedItem = selectedItems[0]
			'''
			print('selectedItem._fileName:', selectedItem._fileName)
			print('selectedItem._index:', selectedItem._index)
			print('selectedItem.myLayer:', selectedItem.myLayer)
			'''
			fileName = selectedItem._fileName
			self.myCanvasWidget.selectInFileList(fileName)
	'''
	def mousePressEvent(self, event):
		print('=== myQGraphicsView.mousePressEvent()')
		print('   ', event.pos())
		xyPos = event.pos()
		item = self.itemAt(xyPos)
		print('   mouse selected item:', item)

		#super(QtWidgets.QGraphicsView, self).mousePressEvent(event)
		super().mousePressEvent(event)
	'''

	# I want to drag the scene around when click+drag on an image ?????
	# see:
	# https://stackoverflow.com/questions/55007339/allow-qgraphicsview-to-move-outside-scene
	'''
	def mouseMoveEvent(self, event):
		print('=== myQGraphicsView.mouseMoveEvent()')
		print('   ', event.pos())
		super().mouseMoveEvent(event)

		#self.scene.mouseMoveEvent(event) # this is an error because scene is wrong class???

		# C++ code
		# scene()->update(mapToScene(rect()).boundingRect());
		#
		# this almost works !!!!
		print('   self.rect():', self.rect())
		self.scene().update(self.mapToScene(self.rect()).boundingRect());

		#self.scene().mouseMoveEvent(event) # this is an error because scene is wrong class???
	'''

	def zoom(self, inout):
		oldPos = QtCore.QPoint(self.myMouse_x, self.myMouse_y) #
		oldPos = self.mapToScene(oldPos)
		'''
		oldPos = self.mapToScene(event.pos())
		'''
		if inout=='in':
			scale = 1.25
		else:
			scale = 1/1.25
		self.scale(scale,scale)

		newPos = QtCore.QPoint(self.myMouse_x, self.myMouse_y)
		newPos = self.mapToScene(newPos)
		delta = newPos - oldPos
		self.translate(delta.y(), delta.x())

	def wheelEvent(self, event):
		'''
		self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
		self.setResizeAnchor(QtGui.QGraphicsView.NoAnchor)
		'''

		wheelZoom = self.myCanvasWidget.getOptions()['Canvas']['wheelZoom'] # 1.25

		oldPos = self.mapToScene(event.pos())
		if event.angleDelta().y() > 0:
			#self.zoom('in')
			scale = 1 * wheelZoom
		elif event.angleDelta().y() < 0:
			#self.zoom('out')
			scale = 1 / wheelZoom
		else:
			return
		self.scale(scale,scale)
		newPos = self.mapToScene(event.pos())
		delta = newPos - oldPos

		#print('myQGraphicsView.wheelEvent() delta:', delta)

		self.translate(delta.y(), delta.x())
		'''
		if self._zoom > 0:
			self.scale(factor, factor)
		elif self._zoom == 0:
			self.fitInView()
		else:
			self._zoom = 0
		'''

	def pan(self, direction):
		stepSize = 500.0
		xOffset = 0.0
		yOffset = 0.0
		if direction == 'left':
			xOffset = stepSize
		elif direction == 'right':
			xOffset = -stepSize
		elif direction == 'up':
			yOffset = stepSize
		elif direction == 'down':
			yOffset = -stepSize

		print('pan() x:', xOffset, 'y:', yOffset)
		self.translate(xOffset,yOffset)

	def keyPressEvent(self, event):
		#print('\n=== myQGraphicsView.keyPressEvent()', event.text())

		# pan is handled by super
		'''
		if event.key() == QtCore.Qt.Key_Left:
			self._getBoundingRect()
			self.pan('left')
		if event.key() == QtCore.Qt.Key_Right:
			self.pan('right')
		if event.key() == QtCore.Qt.Key_Up:
			self.pan('up')
		if event.key() == QtCore.Qt.Key_Down:
			self.pan('down')
		'''

		# zoom
		if event.key() in [QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal]:
			self.zoom('in')
		elif event.key() == QtCore.Qt.Key_Minus:
			self.zoom('out')

		elif event.key() == QtCore.Qt.Key_F:
			#print('f for bring to front')
			self.changeOrder('bring to front')
		elif event.key() == QtCore.Qt.Key_B:
			#print('b for send to back')
			self.changeOrder('send to back')

		elif event.key() == QtCore.Qt.Key_H:
			# 'h' for show/hide
			selectedItem = self.getSelectedItem()
			if selectedItem is not None:
				filename = selectedItem._fileName
				doShow = False # if we get here, the item is visible, thus, doShow is always False
				self.hideShowItem(filename, doShow)
				# tell the toolbar widget to turn off checkbow
				#todo: this is a prime example of figuring out signal/slot
				self.myCanvasWidget.toggleVisibleCheck(filename, doShow)
				#setCheckedState(fileName, doSHow)
		elif event.key() == QtCore.Qt.Key_I:
			# 'i' is for info
			self.myCanvasWidget.userEvent('print stack info')

		elif event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
			#print('todo: set scene centered on crosshair, if no crosshair, center on all images')
			print('key calling centerOnCrosshair()')
			self.centerOnCrosshair()

		else:
			super(myQGraphicsView, self).keyPressEvent(event)

	def _getBoundingRect(self):
		leftMin = float('Inf')
		topMin = float('Inf')

		print(self.scene().sceneRect())

		'''
		for idx, item in enumerate(self.scene().items()):
			print(idx, item.sceneRect)
		'''

	def getSelectedItem(self):
		"""
		Get the currently selected item, return None if no selection
		"""
		selectedItems = self.scene().selectedItems()
		if len(selectedItems) > 0:
			return selectedItems[0]
		else:
			return None

	def changeOrder(self, this):
		"""
		this can be:
			'bring to front': Will bring the selected item BEFORE its previous item
			'send to back': Will put the selected item AFTER its next item

			This does not bring entirely to front or entirely to back???
		"""
		print('myQGraphicsView.changeOrder()', this)
		if this == 'bring to front':
			selectedItems = self.scene().selectedItems()
			if len(selectedItems) > 0:
				print('   bring item to front:', selectedItems)
				selectedItem = selectedItems[0]
				selectedItem.bringForward()
			else:
				print('myQGraphicsView.changeOrder() did not find a selected item???')
		elif this == 'send to back':
			selectedItems = self.scene().selectedItems()
			if len(selectedItems) > 0:
				print('   send item to back:', selectedItems)
				selectedItem = selectedItems[0]
				selectedItem.sendBackward()
			else:
				print('myQGraphicsView.changeOrder() did not find a selected item???')

# this was supposed to be an 'x' in the middle of the dotted red square
'''
class myCrosshair(QtWidgets.QGraphicsTextItem):
	def __init__(self, parent=None):
		super(myCrosshair, self).__init__(parent)
		self.fontSize = 50
		self._fileName = ''
		self.myLayer = 'crosshair'
		theFont = QtGui.QFont("Times", self.fontSize, QtGui.QFont.Bold)
		self.setFont(theFont)
		self.setPlainText('XXX')
		self.setDefaultTextColor(QtCore.Qt.red)
		self.document().setDocumentMargin(0)
		# hide until self.setMotorPosition
		self.hide()

	def setMotorPosition(self, x, y):
		if x is None or y is None:
			self.hide()
			print('myCrosshair.setMotorPosition() hid crosshair')
			return

		self.show()

		# offset so it is centered
		x = x
		y = y - self.fontSize/2

		print('myCrosshair.setMotorPosition() x:', x, 'y:', y)

		# 20200912, was this
		#newPnt = self.mapToScene(x, y)

		# 20200912, was this
		#print('  self.setPos() newPnt:', newPnt)

		# 20200912, was this
		#self.setPos(newPnt)

		# 20200912, NOW this
		self.setPos(x, y)
'''

class myCrosshairRectItem(QtWidgets.QGraphicsRectItem):
	"""
	To display rectangles in canvas.
	Used for 2p images so we can show/hide max project and still see square
	"""
	def __init__(self, parent=None):
		super(myCrosshairRectItem, self).__init__()

		self.myQGraphicsView = parent

		#-9815.6, -20083.0
		#self.fake_x = -4811.0 #-9811.7 #185
		#self.fake_y = -10079.0 #-20079.0 #-83
		self.penSize = 10

		self.xPos = None
		self.yPos = None
		self.width = 693.0
		self.height = 433.0

		#myRect = QtCore.QRectF(self.xPos, self.yPos, self.width, self.height)
		# I really do not understand use of parent ???
		# was this
		#super(QtWidgets.QGraphicsRectItem, self).__init__(myRect)

		self._fileName = ''
		self.myLayer = 'crosshair'

		# tryinig to make scene() itemAt() not report *this
		#self.setEnabled(False) # should be visible but not selectable

		# abb 20200914 removed self
		#self.myCrosshair2 = None
		'''
		self.myCrosshair2 = myCrosshair()
		self.myQGraphicsView.scene().addItem(self.myCrosshair2)
		self.myCrosshair2.setZValue(10001)
		'''

	def setWidthHeight(self, width, height):
		"""
		Called when user selects different 'Square Size'
		Use this to set different 2p zooms and video
		"""
		self.width = width
		self.height = height
		self.setMotorPosition(xMotor=None, yMotor=None) # don't adjust position, just size

	def setMotorPosition(self, xMotor=None, yMotor=None):
		"""
		update the crosshair to a new position

		also used when changing the size of the square (Video, 1x, 1.5x, etc)
		"""
		#print('myCrosshairRectItem.setMotorPosition() xMotor:', xMotor, 'yMotor:', yMotor)
		if xMotor is not None and yMotor is not None:
			self.xPos = xMotor #- self.width/2
			self.yPos = yMotor #- self.height/2

		# BINGO, DO NOT USE setPos !!! Only use setRect !!!
		#self.setPos(self.xPos, self.yPos)

		if self.xPos is not None and self.yPos is not None:
			self.setRect(self.xPos, self.yPos, self.width, self.height)

			'''
			if self.myCrosshair2 is not None:
				xCrosshair = self.xPos + (self.width/2)
				yCrosshair = self.yPos + (self.height/2)
				self.myCrosshair2.setMotorPosition(xCrosshair, yCrosshair)
			'''
		else:
			pass
			#print('setMotorPosition() did not set')

	def paint(self, painter, option, widget=None):
		super().paint(painter, option, widget)
		self.drawCrosshairRect(painter)

	def drawCrosshairRect(self, painter):
		#print('myCrosshairRectItem.drawCrosshairRect()')
		self.focusbrush = QtGui.QBrush()

		self.focuspen = QtGui.QPen(QtCore.Qt.DashLine) # SolidLine, DashLine
		self.focuspen.setColor(QtCore.Qt.red)
		self.focuspen.setWidthF(self.penSize)
		#
		painter.setBrush(self.focusbrush)
		painter.setPen(self.focuspen)

		# THIS IS NECCESSARY !!!! Otherwise the rectangle disapears !!!
		painter.setOpacity(1.0)

		if self.xPos is not None and self.yPos is not None:
			#print('  xxx drawCrosshairRect() self.boundingRect():', self.boundingRect())
			painter.drawRect(self.boundingRect())
		else:
			#print('  !!! myCrosshairRectItem.drawCrosshairRect() did not draw')
			pass
