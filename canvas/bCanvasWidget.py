# Robert H Cudmore
# 20191224

import os, sys, subprocess
from functools import partial

import numpy as np

from PyQt5 import QtCore, QtWidgets, QtGui

import bimpy
#from bimpy.interface import bStackWidget
import canvas

# I want this to inherit from QWidget, but that does not have addToolbar ???
#class bCanvasWidget(QtWidgets.QWidget):
class bCanvasWidget(QtWidgets.QMainWindow):
	def __init__(self, filePath, parent=None):
		"""
		parent: bCanvasApp
		"""
		super(bCanvasWidget, self).__init__(parent)
		self.filePath = filePath
		self.myCanvasApp = parent
		self.myCanvas = canvas.bCanvas(filePath=filePath, parent=self)
		self.myStackList = [] # a list of open bStack

		folderPath = os.path.dirname(self.filePath)
		self.myLogFilePosiiton = canvas.bLogFilePosition(folderPath, self.myCanvasApp.xyzMotor)
		#self.myLogFilePosiiton.run()

		self.buildUI()

		self.show()

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
		codeFolder = self._getCodeFolder()
		iconPath = os.path.join(codeFolder, 'icons', name)
		return iconPath

	def selectInFileList(self, filename):
		"""
		User click on canvas image will select in file list
		"""
		print('bCanvasApp.selectInFileList() filename:', filename)
		self.toolbarWidget.setSelectedItem(filename)

	def toggleVisibleCheck(self, filename, doShow):
		"""
		toggle checkbox in list on/off
		"""
		self.toolbarWidget.setCheckedState(filename, doShow)

	# This is from bStackBrowser
	#def showStackWindow(self, path):
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
		print('   bCanvasWidget.openStack() is opening stackPath:', stackPath)

		alreadyOpen = False
		for stack in self.myStackList:
			if stack.path == stackPath:
				# bring to front
				alreadyOpen = True
				break
		if alreadyOpen:
			stack.show()
			stack.activateWindow()
			stack.raise_()
		else:
			# if I pass parent=self, all hell break loos (todo: fix this)
			# when i don't pass parent=self then closing the last stack window quits the application?
			#tmp = bimpy.interface.bStackWidget(path=stackPath, parent=self)
			tmp = bimpy.interface.bStackWidget(path=stackPath)
			#print('done creating bStackWidget')
			tmp.show()
			self.myStackList.append(tmp)

	def userEvent(self, event):
		print('=== myCanvasWidget.userEvent() event:', event)
		xStep, yStep = self.motorToolbarWidget.getStepSize()
		if event == 'move stage right':
			# todo: read current x/y move distance
			thePos = self.myCanvasApp.xyzMotor.move('right', xStep) # the pos is (x,y)
			self.userEvent('read motor position')
		elif event == 'move stage left':
			# todo: read current x/y move distance
			thePos = self.myCanvasApp.xyzMotor.move('left', xStep) # the pos is (x,y)
			self.userEvent('read motor position')
		elif event == 'move stage front':
			# todo: read current x/y move distance
			thePos = self.myCanvasApp.xyzMotor.move('front', yStep) # the pos is (x,y)
			self.userEvent('read motor position')
		elif event == 'move stage back':
			# todo: read current x/y move distance
			thePos = self.myCanvasApp.xyzMotor.move('back', yStep) # the pos is (x,y)
			self.userEvent('read motor position')
		elif event == 'read motor position':
			# update the interface
			x,y = self.myCanvasApp.xyzMotor.readPosition()
			self.motorToolbarWidget.xStagePositionLabel.setText(str(round(x,1)))
			self.motorToolbarWidget.xStagePositionLabel.repaint()
			self.motorToolbarWidget.yStagePositionLabel.setText(str(round(y,1)))
			self.motorToolbarWidget.yStagePositionLabel.repaint()

			#self.motorToolbarWidget.setStepSize(x,y)

			# x/y coords are not updating???
			#self.motorToolbarWidget.xStagePositionLabel.update()

			# set red crosshair
			self.myGraphicsView.myCrosshair.setMotorPosition(x, y)

		elif event == 'Canvas Folder':
			#print('sys.platform:', sys.platform)
			print('open folder on hdd', self.myCanvas._folderPath)
			path = self.myCanvas._folderPath
			if sys.platform.startswith('darwin'):
				subprocess.Popen(["open", path])
			elif sys.platform.startswith('win'):
				windowsPath = os.path.abspath(path)
				#print('windowsPath:', windowsPath)
				os.startfile(windowsPath)
			else:
				subprocess.Popen(["xdg-open", path])

		elif event == 'Grab Image':
			print('=== bCanvasWidget.userEvent() event:', event)
			# load .tif file that is being repeatdely saved by bCamera
			# grab (videoWidth, videoHeight) fropm options
			codeFolder = self._getCodeFolder()
			oneImage = self.myCanvasApp.options['video']['oneimage']
			oneImagePath = os.path.join(codeFolder, oneImage)
			if os.path.isfile(oneImagePath):
				print('   found it', oneImagePath)
			else:
				print('   error: did not find file:', oneImagePath)
				return
			#
			umWidth = self.myCanvasApp.options['video']['umWidth']
			umHeight = self.myCanvasApp.options['video']['umHeight']

			# when loading from images that are saved at an interval, this will occassionally file with
			#   IndexError: list index out of range
			# presumably because file can not be read at same time as write
			# maybe add try/except to actual bStack code ?
			# todo: add try/except clause to catch it

			# load image as a new stack
			try:
				newVideoStack = bimpy.bStack(oneImagePath, loadImages=True)
			except (IndexError) as e:
				print('warning: exception while loading stack. this happends when background video stream is saving saving at the same time')
				print('just try loading again !!!')
				print(e)
				return

			# tweek header
			# todo: this is not complete
			xMotor,yMotor = self.myCanvasApp.xyzMotor.readPosition()
			#newVideoStack.header.header['bitDepth'] = 8
			#newVideoStack.header.header['bitDepth'] = 8
			newVideoStack.header.header['umWidth'] = umWidth
			newVideoStack.header.header['umHeight'] = umHeight
			newVideoStack.header.header['xMotor'] = xMotor # flipped
			newVideoStack.header.header['yMotor'] = yMotor

			print('   newVideoStack:', newVideoStack.print())

			# save as (in canvas video folder)
			try:
				numVideoFiles = len(self.myCanvas.videoFileList)
				saveVideoFile = 'v' + self.myCanvas.enclosingFolder + '_' + str(numVideoFiles) + '.tif'
				saveVideoPath = os.path.join(self.myCanvas.videoFolderPath, saveVideoFile)
				newVideoStack.saveVideoAs(saveVideoPath)
			except (TypeError) as e:
				print('error: exception while trying to save new video stack, canvas has no folder ... FIX THIS')

			# append to canvas
			#self.canvas.videoFileList.append(newVideoStack)
			self.myCanvas.appendVideo(newVideoStack)

			# append to graphics view
			self.myGraphicsView.appendVideo(newVideoStack)

			# append to toolbar widget (list of files)
			self.toolbarWidget.appendVideo(newVideoStack)

			# save canvas
			self.myCanvas.save()

		elif event =='Import From Scope':
			print('=== bCanvasWidget.userEvent() event:', event)
			newScopeFileList = self.myCanvas.importNewScopeFiles()
			for newScopeFile in newScopeFileList:
				# append to view
				self.myGraphicsView.appendScopeFile(newScopeFile)

				# append to list
				self.toolbarWidget.appendScopeFile(newScopeFile)
			if len(newScopeFileList) > 0:
				self.myCanvas.save()

		elif event == 'print stack info':
			selectedItem = self.myGraphicsView.getSelectedItem()
			if selectedItem is not None:
				selectedItem.myStack.print()
				'''
				fileName = selectedItem._fileName
				selectedStack = self.myCanvas.findScopeFileByName(fileName)
				if selectedStack is not None:
					selectedStack.print()
				else:
					print('no stack selection')
				'''

		elif event == 'center canvas on motor position':
			self.getGraphicsView().centerOnCrosshair()

		else:
			print('bCanvasWidget.userEvent() not understood:', event)

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
		self.width = 1000
		self.height = 1000

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
		self.myGraphicsView = myQGraphicsView(self)
		self.myQVBoxLayout.addWidget(self.myGraphicsView)

		# todo: 20191217, add a status bar !!!
		self.statusToolbarWidget = myStatusToolbarWidget(parent=self)
		self.addToolBar(QtCore.Qt.BottomToolBarArea, self.statusToolbarWidget)

		# here I am linking the toolbar to the graphics view
		# i can't figure out how to use QAction !!!!!!
		self.motorToolbarWidget = myScopeToolbarWidget(parent=self)
		self.addToolBar(QtCore.Qt.LeftToolBarArea, self.motorToolbarWidget)

		self.toolbarWidget = myToolbarWidget(self)
		self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbarWidget)

		self.setCentralWidget(self.centralwidget)

		#self.myStackList = [] # a list of open bStack

globalSquare = {
	'pen': QtCore.Qt.SolidLine, # could be QtCore.Qt.DotLine
	'penColor': QtCore.Qt.blue,
	'penWidth': 4,
}
globalSelectionSquare = {
	'pen': QtCore.Qt.SolidLine, # could be QtCore.Qt.DotLine
	'penColor': QtCore.Qt.yellow,
	'penWidth': 10,
}

class myQGraphicsPixmapItem(QtWidgets.QGraphicsPixmapItem):
	"""
	To display images in canvas

	Each item is added to a scene (QGraphicsScene)
	"""
	#def __init__(self, fileName, index, myLayer, myQGraphicsView, parent=None):
	def __init__(self, fileName, index, myLayer, theStack, parent=None):
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
		self._index = index # index into canvas list (list of either video or scope)
		self.myLayer = myLayer
		self._isVisible = True
		# new 20191229
		self.myStack = theStack # underlying bStack

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
		#print('myQGraphicsPixmapItem.drawFocusRect() self.boundingRect():', self.boundingRect())
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

		#painter.drawRect(self.focusrect)
		# ???
		painter.drawRect(self.boundingRect())

	def mousePressEvent(self, event):
		print('   myQGraphicsPixmapItem.mousePressEvent()')
		super().mousePressEvent(event)
		# this is necc. to create yellow selection around image but DOES NOT ALLOW DRAGGING ON MOUSE MOVE?
		#self.setSelected(True)

	def mouseMoveEvent(self, event):
		#print('   myQGraphicsPixmapItem.mouseMoveEvent()')
		super().mouseMoveEvent(event)
		#event.setAccepted(False)
		# i want to somehow tell the view (or maybe the scene) to move?
		#if self.isSelected():
		#	print(self.parent)

	def mouseReleaseEvent(self, event):
		print('   myQGraphicsPixmapItem.mouseReleaseEvent()', 'motor position:', self.pos())
		super().mouseReleaseEvent(event)
		#self.setSelected(False)
		#event.setAccepted(False)

	def bringForward(self):
		"""
		move this item before its previous sibling

		todo: don't ever move video in front of 2p!
		"""
		print('myQGraphicsPixmapItem.myQGraphicsPixmapItem.bringForward()')
		myScene = self.scene()
		previousItem = None
		for item in self.scene().items(QtCore.Qt.DescendingOrder):
			if item == self:
				break
			previousItem = item
		if previousItem is not None:
			print('   myQGraphicsPixmapItem.bringForward() is moving', self._fileName, 'before', previousItem._fileName)
			# this does not work !!!!
			#self.stackBefore(previousItem)
			previous_zvalue = previousItem.zValue()
			this_zvalue = self.zValue()
			previousItem.setZValue(this_zvalue)
			self.setZValue(previous_zvalue)
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
		else:
			print('   myQGraphicsPixmapItem.bringToFront() item is already front most')

#
# amazing post
#
# LOOK AT THIS 20190703
#
# https://stackoverflow.com/questions/35508711/how-to-enable-pan-and-zoom-in-a-qgraphicsview

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

		# I want to set the initial videw of the scene to include all items ??????
		#myScene.setSceneRect(QtCore.QRectF())

		# add an object at really small x/y
		'''
		rect_item = myQGraphicsRectItem('video', QtCore.QRectF(-20000, -20000, 100, 100))
		myScene.addItem(rect_item)
		'''

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
		# todo: add popup to select 2p zoom (Video, 1, 2, 3, 4)
		#20191217
		#self.myCrosshair = myQGraphicsRectItem(self)
		self.myCrosshair = myQGraphicsRectItem()
		self.myCrosshair.setZValue(300)
		self.scene().addItem(self.myCrosshair)

		# add an object at really big x/y
		'''
		rect_item = myQGraphicsRectItem('video', QtCore.QRectF(20000, 20000, 100, 100))
		myScene.addItem(rect_item)
		'''

		self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
		#self.setScene(self.myScene)

		# trying to snap to the visible objects -- does not work???
		'''tmpSceneRect = self.scene().sceneRect()
		print('  myQGraphicsView() is done initializing. self.scene().sceneRect()',
			tmpSceneRect.left(),
			tmpSceneRect.top(),
			tmpSceneRect.right(),
			tmpSceneRect.bottom(),
			)

		self.ensureVisible(tmpSceneRect)
		'''

	def centerOnCrosshair(self):
		print('myQGraphicsView.centerOnCrosshair()')

		# works on windows
		# works when paired with self.scene().update(sceneRect)
		self.centerOn(self.myCrosshair)

		# kinda works
		print('self.myCrosshair.rect():', self.myCrosshair.rect())
		self.ensureVisible(self.myCrosshair.rect(), xMargin=500, yMargin=500)
		# end works on windows

		'''
		sceneRect = self.scene().sceneRect() #this is qrectf
		self.ensureVisible(sceneRect, xMargin=0, yMargin=0)
		'''

		#sceneRect = self.mapToScene(self.rect()).boundingRect()
		#self.fitInView(sceneRect)
		#self.ensureVisible(sceneRect)

		#viewRect = self.mapFromScene(sceneRect)
		#self.update(sceneRect.toRect()) # update requires QRect, not QRectF

		#self.ensureVisible(sceneRect)
		#self.fitInView(sceneRect)

		#self.setSceneRect(sceneRect)
		#self.updateSceneRect(sceneRect)
		#self.update()

		# needed for update on macos
		sceneRect = self.scene().sceneRect() #this is qrectf
		self.scene().update(sceneRect)

	def appendScopeFile(self, newScopeFile):
		"""
		"""

		# what about
		# pixMapItem.setZValue(numItems)

		# THESE ARE FUCKING STRINGS !!!!!!!!!!!!!!!!!!!!
		fileName = newScopeFile._fileName
		xMotor = newScopeFile.header.header['xMotor']
		yMotor = newScopeFile.header.header['yMotor']
		umWidth = newScopeFile.header.header['umWidth']
		umHeight = newScopeFile.header.header['umHeight']
		#print('umWidth:', umWidth, 'umHeight:', umHeight)

		if xMotor == 'None':
			xMotor = None
		if yMotor == 'None':
			yMotor = None

		#if xMotor is None or yMotor is None:
		#	print('bCanvasWidget.myQGraphicsView() not inserting scopeFile -->> xMotor or yMotor is None ???')
		#	#continue

		# todo: specify channel (1,2,3,4,...)
		stackMax = newScopeFile.loadMax(channel=1, convertTo8Bit=True) # stackMax can be None
		#imageStackHeight, imageStackWidth = stackMax.shape
		imageStackWidth = newScopeFile.pixelsPerLine
		imageStackHeight = newScopeFile.linesPerFrame
		#print('imageStackWidth:', imageStackWidth, 'imageStackHeight:', imageStackHeight)

		if stackMax is None:
			print('myQGraphicsView.appendScopeFile() is making zero max image for newScopeFile:', newScopeFile)
			stackMax = np.zeros((imageStackWidth, imageStackHeight), dtype=np.uint8)

		myQImage = QtGui.QImage(stackMax, imageStackWidth, imageStackHeight, QtGui.QImage.Format_Indexed8)

		#
		# try and set color
		colors=[]
		for i in range(256): colors.append(QtGui.qRgb(i/4,i,i/2))
		myQImage.setColorTable(colors)

		pixmap = QtGui.QPixmap(myQImage)
		pixmap = pixmap.scaled(umWidth, umHeight, QtCore.Qt.KeepAspectRatio)

		# insert
		#pixMapItem = myQGraphicsPixmapItem(fileName, idx, '2P Max Layer', self, parent=pixmap)
		newIdx = 999 # do i use this???
		pixMapItem = myQGraphicsPixmapItem(fileName, newIdx, '2P Max Layer', newScopeFile, parent=pixmap)
		pixMapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
		pixMapItem.setToolTip(fileName)
		pixMapItem.setPos(xMotor,yMotor)
		#todo: this is important, self.myScene needs to keep all video BELOW 2p images!!!
		pixMapItem.setZValue(200)
		# this also effects bounding rect
		#pixMapItem.setOpacity(0.0) # 0.0 transparent 1.0 opaque

		pixMapItem.setShapeMode(QtWidgets.QGraphicsPixmapItem.BoundingRectShape)
		print('appendScopeFile() setting pixMapItem.shapeMode():', pixMapItem.shapeMode())

		# add to scene
		self.scene().addItem(pixMapItem)

		#numItems += 1

	# todo: put this in __init__() as a function
	def appendVideo(self, newVideoStack):
		# what about
		# pixMapItem.setZValue(numItems)

		path = newVideoStack.path
		fileName = newVideoStack._fileName
		#videoFileHeader = videoFile.getHeader()
		xMotor = newVideoStack.header.header['xMotor']
		yMotor = newVideoStack.header.header['yMotor']
		umWidth = newVideoStack.header.header['umWidth']
		umHeight = newVideoStack.header.header['umHeight']

		xMotor = float(xMotor)
		yMotor = float(yMotor)

		#print('myQGraphicsView.appendVideo() xMotor:', xMotor, 'yMotor:', yMotor)

		#videoImage = videoFile.getVideoImage() # ndarray
		videoImage = newVideoStack.getImage() # ndarray
		imageStackHeight, imageStackWidth = videoImage.shape

		myQImage = QtGui.QImage(videoImage, imageStackWidth, imageStackHeight, QtGui.QImage.Format_Indexed8)
		#myQImage = QtGui.QImage(videoImage, imageStackWidth, imageStackHeight, QtGui.QImage.Format_RGB32)

		pixmap = QtGui.QPixmap(myQImage)
		pixmap = pixmap.scaled(umWidth, umHeight, QtCore.Qt.KeepAspectRatio)

		# insert
		#pixMapItem = myQGraphicsPixmapItem(fileName, idx, 'Video Layer', self, parent=pixmap)
		newIdx = 999 # do i use this???
		pixMapItem = myQGraphicsPixmapItem(fileName, newIdx, 'Video Layer', newVideoStack, parent=pixmap)
		pixMapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
		pixMapItem.setToolTip(fileName)
		pixMapItem.setPos(xMotor,yMotor)
		#todo: this is important, self.myScene needs to keep all video BELOW 2p images!!!
		#tmpNumItems = 100
		pixMapItem.setZValue(100) # do i use this???

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
		"""
		print('myQGraphicsView.hideShowLayer() thisLayer:', thisLayer, 'isVisible:', isVisible)
		for item in self.scene().items():
			#print(item._fileName, item.myLayer)
			if item.myLayer == thisLayer:
				# don't show items in this layer that are not visible
				# not visible are files that are checked off in myToolbarWidget
				if isVisible and not item._isVisible:
					continue
				if thisLayer=='Video Layer':
					# turn off both image and outline
					item.setOpacity(1.0 if isVisible else 0)
				else:
					#print('not hiding 2p squares???')
					item.setOpacity(1.0 if isVisible else 0.01)
				# not with 0
				#item.setOpacity(1.0 if isVisible else 0.1)
			else:
				#debug
				#print('rejected:', item.myLayer)
				pass

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

	def mousePressEvent(self, event):
		scenePoint = self.mapToScene(event.x(), event.y())
		#print('=== myQGraphicsView.mousePressEvent() scene_x:', scenePoint.x(), 'scene_y:', scenePoint.y())
		super().mousePressEvent(event)
		#event.setAccepted(False)

	def mouseMoveEvent(self, event):
		#print('=== myQGraphicsView.mouseMoveEvent() x:', event.x(), 'y:', event.y())
		# this is critical, allows dragging view/scene around
		#scenePoint = self.mapToScene(event.x(), event.y())
		#print(scenePoint)

		scenePoint = self.mapToScene(event.x(), event.y())
		self.myCanvasWidget.getStatusToolbar().setMousePosition(scenePoint)

		self.myMouse_x = event.x() #scenePoint.x()
		self.myMouse_y = event.y() #scenePoint.y()

		super().mouseMoveEvent(event)
		event.setAccepted(True)

	def mouseReleaseEvent(self, event):
		#print('=== myQGraphicsView.mouseReleaseEvent() event:', event)
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

		oldPos = self.mapToScene(event.pos())
		if event.angleDelta().y() > 0:
			#self.zoom('in')
			scale = 1.25
		else:
			#self.zoom('out')
			scale = 1/1.25
		self.scale(scale,scale)
		newPos = self.mapToScene(event.pos())
		delta = newPos - oldPos
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
		print('\n=== myQGraphicsView.keyPressEvent()', event.text())
		# QtCore.Qt.Key_Tab

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
		if event.key() == QtCore.Qt.Key_Minus:
			self.zoom('out')
		if event.key() == QtCore.Qt.Key_F:
			#print('f for bring to front')
			self.changeOrder('bring to front')
		if event.key() == QtCore.Qt.Key_B:
			#print('b for send to back')
			self.changeOrder('send to back')
		if event.key() == QtCore.Qt.Key_H:
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
		if event.key() == QtCore.Qt.Key_I:
			# 'i' is for info
			self.myCanvasWidget.userEvent('print stack info')

		if event.key() == QtCore.Qt.Key_C:
			print('todo: set scene centered on crosshair, if no crosshair, center on all images')

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

class myCrosshair(QtWidgets.QGraphicsTextItem):
	def __init__(self, parent=None):
		super(myCrosshair, self).__init__(parent)
		self.fontSize = 50
		self._fileName = ''
		self.myLayer = 'crosshair'
		theFont = QtGui.QFont("Times", self.fontSize, QtGui.QFont.Bold)
		self.setFont(theFont)
		self.setPlainText('+')
		self.setDefaultTextColor(QtCore.Qt.red)
		self.document().setDocumentMargin(0)
		# hide until self.setMotorPosition
		self.hide()

	def setMotorPosition(self, x, y):
		if x is None or y is None:
			self.hide()
			print('setMotorPosition() hid crosshair')
			return

		self.show()

		# offset so it is centered
		x = x
		y = y - self.fontSize/2

		print('myCrosshair.setMotorPosition() x:', x, 'y:', y)

		newPnt = self.mapToScene(x, y)

		#print('   after mapToScene x:', newPnt.x(), 'y:', newPnt.y())

		#self.setPos(x,y)
		self.setPos(newPnt)

class myQGraphicsRectItem(QtWidgets.QGraphicsRectItem):
	"""
	To display rectangles in canvas.
	Used for 2p images so we can show/hide max project and still see square
	"""
	def __init__(self, parent=None):
		super(myQGraphicsRectItem, self).__init__(parent)

		#-9815.6, -20083.0
		#self.fake_x = -4811.0 #-9811.7 #185
		#self.fake_y = -10079.0 #-20079.0 #-83
		self.penSize = 15

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

		#self.myCrosshair = QtWidgets.QGraphicsTextItem(self)
		#self.myCrosshair.setPlainText('x')
		self.myCrosshair = myCrosshair(self)
		#self.myCrosshair.setMotorPosition(self.xPos, self.yPos)
		#self.myCrosshair.setPos(self.xPos, self.yPos)

		#print('self.boundingRect():', self.boundingRect())

	def setWidthHeight(self, width, height):
		"""Use this to set different 2p zooms and video"""
		self.width = width
		self.height = height
		self.setMotorPosition(xMotor=None, yMotor=None) # don't adjust position, just size

	def setMotorPosition(self, xMotor=None, yMotor=None):
		"""
		update the crosshair to a new position

		also used when changing the size of the square (Video, 1x, 1.5x, etc)
		"""
		#print('myQGraphicsRectItem.setMotorPosition() xMotor:', xMotor, 'yMotor:', yMotor)
		if xMotor is not None and yMotor is not None:
			self.xPos = xMotor #- self.width/2
			self.yPos = yMotor #- self.height/2

		# BINGO, DO NOT USE setPos !!! Only use setRect !!!
		#self.setPos(self.xPos, self.yPos)

		if self.xPos is not None and self.yPos is not None:
			self.setRect(self.xPos, self.yPos, self.width, self.height)

			xCrosshair = self.xPos + (self.width/2)
			yCrosshair = self.yPos + (self.height/2)
			self.myCrosshair.setMotorPosition(xCrosshair, yCrosshair)
		else:
			print('setMotorPosition() did not set')

	def paint(self, painter, option, widget=None):
		super().paint(painter, option, widget)
		self.drawCrosshairRect(painter)

	def drawCrosshairRect(self, painter):
		#print('myQGraphicsRectItem.drawCrosshairRect()')
		self.focusbrush = QtGui.QBrush()

		self.focuspen = QtGui.QPen(QtCore.Qt.DashLine) # SolidLine, DashLine
		self.focuspen.setColor(QtCore.Qt.red)
		self.focuspen.setWidthF(self.penSize)
		#
		painter.setBrush(self.focusbrush)
		painter.setPen(self.focuspen)

		# THIS IS NECCESSARY !!!! OTherwise the rectangle disapears !!!
		painter.setOpacity(1.0)

		if self.xPos is not None and self.yPos is not None:
			print('drawCrosshairRect() self.boundingRect():', self.boundingRect())
			painter.drawRect(self.boundingRect())
		else:
			print('!!! myQGraphicsRectItem.drawCrosshairRect() did not draw')
'''
class myQGraphicsRectItem(QtWidgets.QGraphicsRectItem):
	"""
	To display rectangles in canvas.
	Used for 2p images so we can show/hide max project and still see square
	"""
	def __init__(self, fileName, myLayer, parent=None):
		super(QtWidgets.QGraphicsRectItem, self).__init__(parent)
		self._fileName = fileName
		self.myLayer = myLayer

	def paint(self, painter, option, widget=None):
		super().paint(painter, option, widget)
		if self.isSelected():
			self.drawFocusRect(painter)

	def drawFocusRect(self, painter):
		self.focusbrush = QtGui.QBrush()
		self.focuspen = QtGui.QPen(globalSelectionSquare['pen'])
		self.focuspen.setColor(globalSelectionSquare['penColor'])
		self.focuspen.setWidthF(globalSelectionSquare['penWidth'])
		#
		painter.setBrush(self.focusbrush)
		painter.setPen(self.focuspen)
		painter.drawRect(self.boundingRect())

	def mousePressEvent(self, event):
		print('   myQGraphicsPixmapItem.mousePressEvent()')
		super().mousePressEvent(event)
		#self.setSelected(True)
		event.setAccepted(False)
	def mouseMoveEvent(self, event):
		print('   myQGraphicsPixmapItem.mouseMoveEvent()')
		super().mouseMoveEvent(event)
		event.setAccepted(False)
	def mouseReleaseEvent(self, event):
		#print('   myQGraphicsPixmapItem.mouseReleaseEvent()')
		super().mouseReleaseEvent(event)
		#self.setSelected(False)
		event.setAccepted(False)

	def bringForward(self):
		"""
		move this item before its previous sibling
		"""
		print('myQGraphicsRectItem.bringForward()')
		myScene = self.scene()
		previousItem = None
		for item in self.scene().items():
			if item == self:
				break
			previousItem = item
		if previousItem is not None:
			print('   myQGraphicsRectItem.bringForward() is moving', self._fileName, 'before', previousItem._fileName)
			# this does not work !!!!
			#self.stackBefore(previousItem)
			previous_zvalue = previousItem.zValue()
			this_zvalue = self.zValue()
			previousItem.setZValue(this_zvalue)
			self.setZValue(previous_zvalue)
		else:
			print('   myQGraphicsRectItem.bringToFront() item is already front most')
'''

class myStatusToolbarWidget(QtWidgets.QToolBar):
	def __init__(self, parent):
		print('myStatusToolbarWidget.__init__')
		super(QtWidgets.QToolBar, self).__init__(parent)
		self.myCanvasWidget = parent

		self.setMovable(False)

		myGroupBox = QtWidgets.QGroupBox()
		myGroupBox.setTitle('')

		hBoxLayout = QtWidgets.QHBoxLayout()

		self.lastActionLabel = QtWidgets.QLabel("Last Action: None")
		hBoxLayout.addWidget(self.lastActionLabel)

		xMousePosition_ = QtWidgets.QLabel("X (um)")
		self.xMousePosition = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(xMousePosition_)
		hBoxLayout.addWidget(self.xMousePosition)

		yMousePosition_ = QtWidgets.QLabel("X (um)")
		self.yMousePosition = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(yMousePosition_)
		hBoxLayout.addWidget(self.yMousePosition)

		# finish
		myGroupBox.setLayout(hBoxLayout)
		self.addWidget(myGroupBox)

	def setMousePosition(self, point):
		self.xMousePosition.setText(str(round(point.x(),1)))
		self.xMousePosition.repaint()
		self.yMousePosition.setText(str(round(point.y(),1)))
		self.yMousePosition.repaint()

class myScopeToolbarWidget(QtWidgets.QToolBar):
	def __init__(self, parent):
		"""
		A Toolbar for controlling the scope. This includes:
			- reading and moving stage/objective position
			- setting the size of a crosshair/box to show current motor position
			- setting x/y step size
			- showing a video window
			- capturing single images from video camera
			- importing scanning files from scope
		"""
		print('myScopeToolbarWidget.__init__')
		super(QtWidgets.QToolBar, self).__init__(parent)
		self.myCanvasWidget = parent

		myGroupBox = QtWidgets.QGroupBox()
		myGroupBox.setTitle('Scope Controller')
		#myGroupBox.setFlat(True)

		# main v box
		vBoxLayout = QtWidgets.QVBoxLayout()
		vBoxLayout.setSpacing(4)

		#
		# arrows for left/right, front/back
		grid = QtWidgets.QGridLayout()

		buttonName = 'move stage left'
		iconPath = self.myCanvasWidget._getIcon('left-arrow.png')
		icon  = QtGui.QIcon(iconPath)
		leftButton = QtWidgets.QPushButton()
		leftButton.setIcon(icon)
		leftButton.setToolTip('Move stage left')
		leftButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'move stage right'
		iconPath = self.myCanvasWidget._getIcon('right-arrow.png')
		icon  = QtGui.QIcon(iconPath)
		rightButton = QtWidgets.QPushButton()
		rightButton.setIcon(icon)
		rightButton.setToolTip('Move stage right')
		rightButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'move stage back'
		iconPath = self.myCanvasWidget._getIcon('up-arrow.png')
		icon  = QtGui.QIcon(iconPath)
		backButton = QtWidgets.QPushButton()
		backButton.setIcon(icon)
		backButton.setToolTip('Move stage back')
		backButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'move stage front'
		iconPath = self.myCanvasWidget._getIcon('down-arrow.png')
		icon  = QtGui.QIcon(iconPath)
		frontButton = QtWidgets.QPushButton()
		frontButton.setIcon(icon)
		frontButton.setToolTip('Move stage front')
		frontButton.clicked.connect(partial(self.on_button_click,buttonName))

		grid.addWidget(leftButton, 1, 0) # row, col
		grid.addWidget(rightButton, 1, 2) # row, col
		grid.addWidget(backButton, 0, 1) # row, col
		grid.addWidget(frontButton, 2, 1) # row, col

		vBoxLayout.addLayout(grid)

		#
		# read position and report x/y position
		gridReadPosition = QtWidgets.QGridLayout()

		buttonName = 'read motor position'
		#icon  = QtGui.QIcon('icons/down-arrow.png')
		readPositionButton = QtWidgets.QPushButton('Read Position')
		#readPositionButton.setIcon(icon)
		readPositionButton.setToolTip('Read Motor Position')
		readPositionButton.clicked.connect(partial(self.on_button_click,buttonName))

		# we will need to set these from code
		xStagePositionLabel_ = QtWidgets.QLabel("X (um)")
		self.xStagePositionLabel = QtWidgets.QLabel("None")
		yStagePositionLabel_ = QtWidgets.QLabel("Y (um)")
		self.yStagePositionLabel = QtWidgets.QLabel("Y (um)")

		gridReadPosition.addWidget(readPositionButton, 0, 0) # row, col
		gridReadPosition.addWidget(xStagePositionLabel_, 0, 1) # row, col
		gridReadPosition.addWidget(self.xStagePositionLabel, 0, 2) # row, col
		gridReadPosition.addWidget(yStagePositionLabel_, 0, 3) # row, col
		gridReadPosition.addWidget(self.yStagePositionLabel, 0, 4) # row, col

		vBoxLayout.addLayout(gridReadPosition)

		#
		# center crosshair
		crosshair_hBoxLayout = QtWidgets.QHBoxLayout()
		buttonName = 'center canvas on motor position'
		centerCrosshairButton = QtWidgets.QPushButton('+')
		centerCrosshairButton.setToolTip('Center canvas on motor position crosshair')
		centerCrosshairButton.clicked.connect(partial(self.on_button_click,buttonName))
		crosshair_hBoxLayout.addWidget(centerCrosshairButton)

		squareSizeLabel_ = QtWidgets.QLabel("Square Size")
		comboBox = QtGui.QComboBox()
		comboBox.addItem("Video")
		comboBox.addItem("1x")
		comboBox.addItem("1.5x")
		comboBox.addItem("2x")
		comboBox.addItem("2.5x")
		comboBox.addItem("3x")
		comboBox.addItem("3.5x")
		comboBox.addItem("4x")
		comboBox.addItem("4.5x")
		comboBox.addItem("5x")
		comboBox.addItem("5.5x")
		comboBox.addItem("6x")
		comboBox.activated[str].connect(self.crosshairSizeChoice)
		crosshair_hBoxLayout.addWidget(squareSizeLabel_)
		crosshair_hBoxLayout.addWidget(comboBox)

		vBoxLayout.addLayout(crosshair_hBoxLayout)

		#
		# x/y step size
		grid2 = QtWidgets.QGridLayout()

		xStepLabel = QtWidgets.QLabel("X Step (um)")
		self.xStepSpinBox = QtWidgets.QDoubleSpinBox()
		self.xStepSpinBox.setMinimum(0.0)
		self.xStepSpinBox.setMaximum(10000.0) # need something here, otherwise max is 100
		#self.xStepSpinBox.setValue(1000)
		self.xStepSpinBox.valueChanged.connect(self.stepValueChanged)

		yStepLabel = QtWidgets.QLabel("Y Step (um)")
		self.yStepSpinBox = QtWidgets.QDoubleSpinBox()
		self.yStepSpinBox.setMinimum(0)
		self.yStepSpinBox.setMaximum(10000) # need something here, otherwise max is 100
		#self.yStepSpinBox.setValue(500)
		self.yStepSpinBox.valueChanged.connect(self.stepValueChanged)

		# set values of x/y step to Video
		self.crosshairSizeChoice('Video')

		grid2.addWidget(xStepLabel, 0, 0) # row, col
		grid2.addWidget(self.xStepSpinBox, 0, 1) # row, col
		grid2.addWidget(yStepLabel, 1, 0) # row, col
		grid2.addWidget(self.yStepSpinBox, 1, 1) # row, col

		vBoxLayout.addLayout(grid2)

		#
		# show video window and grab video
		video_hBoxLayout = QtWidgets.QHBoxLayout()

		buttonName = 'Live Video'
		#iconPath = os.path.join(os.path.join(self.myParentApp.getCodeFolder(), 'icons/video.png'))
		iconPath = self.myCanvasWidget._getIcon('video.png')
		icon  = QtGui.QIcon(iconPath)
		liveVideoButton = QtWidgets.QPushButton()
		liveVideoButton.setToolTip('Show Live Video Window')
		liveVideoButton.setIcon(icon)
		liveVideoButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'Grab Image'
		grabVideoButton = QtWidgets.QPushButton(buttonName)
		grabVideoButton.setToolTip('Grab an image from video')
		grabVideoButton.clicked.connect(partial(self.on_button_click,buttonName))

		video_hBoxLayout.addWidget(liveVideoButton)
		video_hBoxLayout.addWidget(grabVideoButton)

		vBoxLayout.addLayout(video_hBoxLayout)

		#
		# import new files from scope
		scope_hBoxLayout = QtWidgets.QHBoxLayout()

		buttonName = 'Import From Scope'
		importScopeFilesButton = QtWidgets.QPushButton(buttonName)
		importScopeFilesButton.setToolTip('Import new files from scope')
		importScopeFilesButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'Canvas Folder'
		#iconPath = os.path.join(os.path.join(self.myParentApp.getCodeFolder(), 'icons/folder.png'))
		iconPath = self.myCanvasWidget._getIcon('folder.png')
		icon  = QtGui.QIcon(iconPath)
		showCanvasFolderButton = QtWidgets.QPushButton()
		showCanvasFolderButton.setToolTip('Show canvas folder')
		showCanvasFolderButton.setIcon(icon)
		showCanvasFolderButton.clicked.connect(partial(self.on_button_click,buttonName))

		scope_hBoxLayout.addWidget(importScopeFilesButton)
		scope_hBoxLayout.addWidget(showCanvasFolderButton)

		vBoxLayout.addLayout(scope_hBoxLayout)

		#
		# finalize

		#
		# add
		myGroupBox.setLayout(vBoxLayout)

		# finish
		self.addWidget(myGroupBox)

	def crosshairSizeChoice(self, text):
		print('crosshairSizeChoice() text:', text)
		options = self.myCanvasWidget.getOptions()
		if text=='Video':
			umWidth = options['video']['umWidth']
			umHeight = options['video']['umHeight']
			stepFraction = options['video']['stepFraction']
			# set step size
			xStep = umWidth - (umWidth*stepFraction)
			yStep = umHeight - (umHeight*stepFraction)
			self.setStepSize(xStep, yStep)
			# set visible red rectangle
			self.myCanvasWidget.getGraphicsView().myCrosshair.setWidthHeight(umWidth, umHeight)
		else:
			# assuming each option is of form(1x, 1.5x, etc)
			text = text.strip('x')
			zoom = float(text)
			zoomOneWidthHeight = options['scanning']['zoomOneWidthHeight']
			stepFraction = options['scanning']['stepFraction']
			# set step size
			zoomWidthHeight = zoomOneWidthHeight / zoom
			xStep = zoomWidthHeight - (zoomWidthHeight*stepFraction) # always square
			yStep = zoomWidthHeight - (zoomWidthHeight*stepFraction)
			self.setStepSize(xStep, yStep)
			# set visible red rectangle
			self.myCanvasWidget.getGraphicsView().myCrosshair.setWidthHeight(zoomWidthHeight, zoomWidthHeight)

	def getStepSize(self):
		xStep = self.xStepSpinBox.value()
		yStep = self.yStepSpinBox.value()
		return xStep, yStep

	def setStepSize(self, xStep, yStep):
		self.xStepSpinBox.setValue(xStep)
		self.yStepSpinBox.setValue(yStep)

	def stepValueChanged(self):
		xStep = self.xStepSpinBox.value()
		yStep = self.yStepSpinBox.value()
		print('myScopeToolbarWidget.stepValueChanged() xStep:', xStep, 'yStep:', yStep)

	@QtCore.pyqtSlot()
	def on_button_click(self, name):
		print('=== myScopeToolbarWidget.on_button_click() name:', name)
		self.myCanvasWidget.userEvent(name)

#todo: put all this in a grid
class myToolbarWidget(QtWidgets.QToolBar):
	def __init__(self, parent=None):
		"""
		"""
		print('myToolbarWidget.__init__')
		super(myToolbarWidget, self).__init__(parent)

		self.myCanvasWidget = parent

		#
		# layers
		layersGroupBox = QtWidgets.QGroupBox('Layers')
		layersHBoxLayout = QtWidgets.QHBoxLayout()

		checkBoxName = 'Video Layer'
		self.showVideoCheckBox = QtWidgets.QCheckBox('Video')
		self.showVideoCheckBox.setToolTip('Toggle video layer on and off')
		self.showVideoCheckBox.setCheckState(2) # Really annoying it is not 0/1 False/True but 0:False/1:Intermediate/2:True
		self.showVideoCheckBox.clicked.connect(partial(self.on_checkbox_click, checkBoxName, self.showVideoCheckBox))
		#self.addWidget(self.showVideoCheckBox)
		layersHBoxLayout.addWidget(self.showVideoCheckBox)

		checkBoxName = '2P Max Layer'
		self.show2pMaxCheckBox = QtWidgets.QCheckBox('Scanning Max Project')
		self.show2pMaxCheckBox.setToolTip('Toggle scanning layer on and off')
		self.show2pMaxCheckBox.setCheckState(2) # Really annoying it is not 0/1 False/True but 0:False/1:Intermediate/2:True
		self.show2pMaxCheckBox.clicked.connect(partial(self.on_checkbox_click, checkBoxName, self.show2pMaxCheckBox))
		#self.addWidget(self.show2pMaxCheckBox)
		layersHBoxLayout.addWidget(self.show2pMaxCheckBox)

		checkBoxName = '2P Squares Layer'
		self.show2pSquaresCheckBox = QtWidgets.QCheckBox('Scanning Squares')
		self.show2pSquaresCheckBox.setToolTip('Toggle scanning squares on and off')
		self.show2pSquaresCheckBox.setCheckState(2) # Really annoying it is not 0/1 False/True but 0:False/1:Intermediate/2:True
		self.show2pSquaresCheckBox.clicked.connect(partial(self.on_checkbox_click, checkBoxName, self.show2pSquaresCheckBox))
		#self.addWidget(self.show2pSquaresCheckBox)
		layersHBoxLayout.addWidget(self.show2pSquaresCheckBox)

		layersGroupBox.setLayout(layersHBoxLayout)
		self.addWidget(layersGroupBox)

		#
		# radio buttons to select type of contrast (selected, video layer, scope layer)
		self.contrastGroupBox = QtWidgets.QGroupBox('Image Contrast')

		contrastVBox = QtWidgets.QVBoxLayout()

		contrastRadioHBoxLayout = QtWidgets.QHBoxLayout()
		self.selectedContrast = QtWidgets.QRadioButton('Selected')
		self.videoLayerContrast = QtWidgets.QRadioButton('Video Layer')
		self.scopeLayerContrast = QtWidgets.QRadioButton('Scope Layer')

		# default to selecting 'Selected' image (for contrast adjustment)
		self.selectedContrast.setChecked(True)

		contrastRadioHBoxLayout.addWidget(self.selectedContrast)
		contrastRadioHBoxLayout.addWidget(self.videoLayerContrast)
		contrastRadioHBoxLayout.addWidget(self.scopeLayerContrast)

		contrastVBox.addLayout(contrastRadioHBoxLayout)

		# contrast sliders
		# min
		self.minSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.minSlider.setMinimum(0)
		self.minSlider.setMaximum(255)
		self.minSlider.setValue(0)
		self.minSlider.valueChanged.connect(partial(self.on_contrast_slider, 'minSlider', self.minSlider))
		#self.addWidget(self.minSlider)
		contrastVBox.addWidget(self.minSlider)
		# max
		self.maxSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.maxSlider.setMinimum(0)
		self.maxSlider.setMaximum(255)
		self.maxSlider.setValue(255)
		self.maxSlider.valueChanged.connect(partial(self.on_contrast_slider, 'maxSlider', self.maxSlider))
		#self.addWidget(self.maxSlider)
		contrastVBox.addWidget(self.maxSlider)

		self.contrastGroupBox.setLayout(contrastVBox)
		self.addWidget(self.contrastGroupBox)

		#
		# file list (tree view)
		self.fileList = myTreeWidget(self.myCanvasWidget)

		self.addWidget(self.fileList)

		itemList = []
		for videoFile in self.myCanvasWidget.getCanvas().videoFileList:
			#print('   myToolbarWidget appending videoFile to fileList (tree):', videoFile._fileName)
			self.fileList.appendStack(videoFile, 'Video Layer')

		for scopeFile in self.myCanvasWidget.getCanvas().scopeFileList:
			#print('   myToolbarWidget appending scopeFile to fileList (tree):', scopeFile._fileName)
			self.fileList.appendStack(scopeFile, '2P Max Layer')

	def appendScopeFile(self, newStack):
		self.fileList.appendStack(newStack, '2P Max Layer') #type: ('Video Layer', '2P Max Layer')

	def appendVideo(self, newStack):
		self.fileList.appendStack(newStack, 'Video Layer') #type: ('Video Layer', '2P Max Layer')

	def getSelectedContrast(self):
		if self.selectedContrast.isChecked():
			return 'selected'
		elif self.videoLayerContrast.isChecked():
			return 'Video Layer'
		elif self.scopeLayerContrast.isChecked():
			return '2P Max Layer'

	def on_contrast_slider(self, name, object):

		theMin = self.minSlider.value()
		theMax = self.maxSlider.value()

		adjustThisLayer = self.getSelectedContrast() # todo: work out the strings I am using !!!!!!!!!!!!!

		selectedItem = None
		selectedItems = self.myCanvasWidget.getGraphicsView().scene().selectedItems() # can be none
		if len(selectedItems) > 0:
			# the first selected item
			selectedItem = selectedItems[0]

		useMaxProject = False
		#todo: work out these string s!!!!!!!! (VIdeo LAyer, 2P Max Layer)
		if adjustThisLayer == 'Video Layer':
			useMaxProject = False
		elif adjustThisLayer == '2P Max Layer':
			# todo: change this in future
			useMaxProject = True
		#elif adjustThisLayer == 'selected':
		#	selectedItems = self.myCanvasWidget.getGraphicsView().scene().selectedItems()
		#	print('NOT IMPLEMENTED')

		print('=== myToolbarWidget.on_contrast_slider() adjustThisLayer:', adjustThisLayer, 'useMaxProject:', useMaxProject, 'theMin:', theMin, 'theMax:', theMax)

		for item in  self.myCanvasWidget.getGraphicsView().scene().items():

			# CHANGE TO GENERALIZE
			#if item.myLayer == 'Video Layer':
			#if item.myLayer == '2P Max Layer':
			#print('item.myLayer:', item.myLayer)

			# decide if we adjust this item
			# noramlly we are using layers
			# there is a special case where we are adjusting the selected it !!!!!!!!!!!!!!!!!!!!
			#adjustThisItem =
			if adjustThisLayer == 'selected':
				adjustThisItem = item == selectedItem
				if item.myLayer == 'Video Layer':
					useMaxProject = False
				elif item.myLayer == '2P Max Layer':
					# todo: change this in future
					useMaxProject = True
			else:
				adjustThisItem = item.myLayer == adjustThisLayer

			#if item.myLayer == adjustThisLayer:
			if adjustThisItem:
				# CHANGE TO GENERALIZE
				# todo: canvas should have one list of stacks (not separate video and scope lists)
				#if adjustThisLayer == 'Video Layer':
				if item.myLayer == 'Video Layer':
					# new 20191229
					#videoFile = self.myCanvasWidget.getCanvas().findByName(item._fileName)
					videoFile = item.myStack
				elif item.myLayer == '2P Max Layer':
					try:
						#videoFile = self.myCanvasWidget.getCanvas().findScopeFileByName(item._fileName)
						videoFile = item.myStack
					except:
						print('exception !!!@@@!!!', len(self.myCanvasWidget.getCanvas().scopeFileList), item._index)
						videoFile = None
				else:
					print('bCanvasWidget.on_contrast_slider() ERRRRRRRORRORORORRORORRORORORORORRORORO')
					continue

				if videoFile is None:
					continue

				umWidth = videoFile.getHeaderVal('umWidth')
				umHeight = videoFile.getHeaderVal('umHeight')
				#print('umWidth:', umWidth)


				# get an contrast enhanced ndarray
				# CHANGE TO GENERALIZE
				#videoImage = videoFile.getImage_ContrastEnhanced(theMin, theMax) # return the original as an nd_array

				# each scope stack needs to know if it is diplaying a real stack OR just a max project
				# where do I put this ???????
				videoImage = videoFile.getImage_ContrastEnhanced(theMin, theMax, useMaxProject=useMaxProject) # return the original as an nd_array

				if videoImage is None:
					# error
					pass
				else:
					imageStackHeight, imageStackWidth = videoImage.shape

					#print('mean:', np.mean(videoImage))

					myQImage = QtGui.QImage(videoImage, imageStackWidth, imageStackHeight, QtGui.QImage.Format_Indexed8)

					#
					# try and set color
					if adjustThisLayer == '2P Max Layer':
						colors=[]
						for i in range(256): colors.append(QtGui.qRgb(i/4,i,i/2))
						myQImage.setColorTable(colors)

					pixmap = QtGui.QPixmap(myQImage)
					pixmap = pixmap.scaled(umWidth, umHeight, QtCore.Qt.KeepAspectRatio)

					item.setPixmap(pixmap)
		#firstItem.setPixmap(pixmap)

	def setSelectedItem(self, filename):
		"""
		Respond to user clicking on the image and select the file in the list.
		"""
		#print('myToolbarWidget.setSelectedItem() filename:', filename)
		self.fileList.setSelectedItem(filename)

		'''
		# todo: use self._findItemByFilename()
		items = self.fileList.findItems(filename, QtCore.Qt.MatchFixedString, column=0)
		if len(items)>0:
			item = items[0]
			#print('   item:', item)
			self.fileList.setCurrentItem(item)
		'''

	def setCheckedState(self, filename, doShow):
		"""
		set the visible checkbox
		"""
		#print('myToolbarWidget.setCheckedState() filename:', filename, 'doShow:', doShow)
		self.fileList.setCheckedState(filename, doShow)

		'''
		item = self._findItemByFilename(filename)
		if item is not None:
			column = 0
			item.setCheckState(column, doShow)
		'''

	'''
	def _findItemByFilename(self, filename):
		"""
		Given a filename, return the item. Return None if not found.
		"""
		items = self.fileList.findItems(filename, QtCore.Qt.MatchFixedString, column=0)
		if len(items)>0:
			return items[0]
		else:
			return None
	'''

	'''
	def mousePressEvent(self, event):
		print('myToolbarWidget.mousePressEvent()')
	'''

	'''
	def keyPressEvent(self, event):
		print('myToolbarWidget.keyPressEvent() event:', event)
		print('   enable bring to front and send to back')
	'''

	@QtCore.pyqtSlot()
	def on_button_click(self, name):
		print('=== myToolbarWidget.on_button_click() name:', name)

	@QtCore.pyqtSlot()
	def on_checkbox_click(self, name, checkBoxObject):
		print('=== myToolbarWidget.on_checkbox_click() name:', name, 'checkBoxObject:', checkBoxObject)
		checkState = checkBoxObject.checkState()

		if name == 'Video Layer':
			self.myCanvasWidget.getGraphicsView().hideShowLayer('Video Layer', checkState==2)
			#self.myQGraphicsView.hideShowLayer('Video Layer', checkState==2)
		if name == '2P Max Layer':
			self.myCanvasWidget.getGraphicsView().hideShowLayer('2P Max Layer', checkState==2)
			#self.myQGraphicsView.hideShowLayer('2P Max Layer', checkState==2)
		if name == '2P Squares Layer':
			self.myCanvasWidget.getGraphicsView().hideShowLayer('2P Squares Layer', checkState==2)
			#self.myQGraphicsView.hideShowLayer('2P Squares Layer', checkState==2)

class myTreeWidget(QtWidgets.QTreeWidget):
	def __init__(self, parent=None):
		super(myTreeWidget, self).__init__(parent)
		self.myCanvasWidget = parent

		myColumns = ['Index', 'File', 'Type', 'xPixels', 'yPixels', 'numSlices'] # have to be unique
		self.myColumns = {}
		for idx, column in enumerate(myColumns):
			self.myColumns[column] = idx

		self.setHeaderLabels(myColumns) # 'Show'])
		self.setColumnWidth(self.myColumns['Index'], 40)
		self.setColumnWidth(self.myColumns['File'], 200)
		self.setColumnWidth(self.myColumns['Type'], 20)
		self.setColumnWidth(self.myColumns['xPixels'], 40)
		self.setColumnWidth(self.myColumns['yPixels'], 40)
		self.setColumnWidth(self.myColumns['numSlices'], 40)

		self.itemSelectionChanged.connect(self.fileSelected_callback)
		self.itemChanged.connect(self.fileSelected_changed)

	def appendStack(self, theStack, type):
		"""
		type: ('Video Layer', '2P Max Layer')
		"""

		myIndex = self.topLevelItemCount()
		#print('!!! appendStack() myIndex:', myIndex)

		item = QtWidgets.QTreeWidgetItem(self)
		item.setText(self.myColumns['Index'], str(myIndex+1))
		item.setText(self.myColumns['File'], theStack._fileName)
		if type == 'Video Layer':
			item.setText(self.myColumns['Type'], 'v')
		elif type == '2P Max Layer':
			item.setText(self.myColumns['Type'], '2p')
		else:
			print('ERROR: myTreeWidget.appendStack() got unknown type???')
			item.setText(self.myColumns['Type'], 'Unknown')
		item.setText(self.myColumns['xPixels'], str(theStack.pixelsPerLine))
		item.setText(self.myColumns['yPixels'], str(theStack.linesPerFrame))
		item.setText(self.myColumns['numSlices'], str(theStack.numImages))
		item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
		item.setCheckState(0, QtCore.Qt.Checked)

		#self.insertTopLevelItems(0, item)
		self.addTopLevelItem(item)


	def setSelectedItem(self, filename):
		"""
		Respond to user clicking on the image and select the file in the list.
		"""
		items = self.findItems(filename, QtCore.Qt.MatchFixedString, column=self.myColumns['File'])
		if len(items)>0:
			item = items[0]
			self.setCurrentItem(item)
		else:
			print('warning: myTreeWidget.setSelectedItem() did not find filename:', filename)

	def setCheckedState(self, filename, doShow):
		"""
		set the visible checkbox
		"""
		items = self.findItems(filename, QtCore.Qt.MatchFixedString, column=self.myColumns['File'])
		if len(items)>0:
			item = items[0]
			column = 0
			item.setCheckState(column, doShow)

	def keyPressEvent(self, event):
		#print('myTreeWidget.keyPressEvent() event.text():', event.text())

		# todo: fix this, this assumes selected file in list is same as selected file in graphics view !
		if event.key() == QtCore.Qt.Key_F:
			#print('f for bring to front')
			self.myCanvasWidget.getGraphicsView().changeOrder('bring to front')
		elif event.key() == QtCore.Qt.Key_B:
			#print('b for send to back')
			self.myCanvasWidget.getGraphicsView().changeOrder('send to back')

		elif event.key() == QtCore.Qt.Key_Left:
			super(myTreeWidget, self).keyPressEvent(event)
		elif event.key() == QtCore.Qt.Key_Right:
			super(myTreeWidget, self).keyPressEvent(event)
		elif event.key() == QtCore.Qt.Key_Up:
			super(myTreeWidget, self).keyPressEvent(event)
		elif event.key() == QtCore.Qt.Key_Down:
			super(myTreeWidget, self).keyPressEvent(event)
		else:
			print('  key not handled:text:', event.text(), 'modifyers:', event.modifiers())
			super(myTreeWidget, self).keyPressEvent(event)

	def mouseDoubleClickEvent(self, event):
		"""
		open a stack on a double-click
		"""
		print('=== myTreeWidget.mouseDoubleClickEvent')
		selectedItems = self.selectedItems()
		if len(selectedItems) > 0:
			selectedItem = selectedItems[0]
			fileName = selectedItem.text(self.myColumns['File'])
			type = selectedItem.text(self.myColumns['Type']) # in ['v', '2p']
			if type == 'v':
				layer = 'Video Layer'
			elif type == '2p':
				layer = '2P Max Layer'
			else:
				# error
				layer = None
			if layer is not None:
				self.myCanvasWidget.openStack(fileName, layer)

	def fileSelected_changed(self, item, col):
		"""
		called when user clicks on check box
		"""
		#print('=== fileSelected_changed() item:', item, 'col:', col, 'is now checked:', item.checkState(0))
		filename = item.text(self.myColumns['File'])
		#isNowChecked = item.checkState(self.myColumns['Index']) # 0:not checked, 2:is checked
		isNowChecked = item.checkState(0) # 0:not checked, 2:is checked
		doShow = True if isNowChecked==2 else False
		#print('   telling self.myQGraphicsView.hideShowItem() filename:', filename, 'doShow:', doShow)
		self.myCanvasWidget.getGraphicsView().hideShowItem(filename, doShow)

	def fileSelected_callback(self):
		"""
		Respond to user click in the file list (selects a file)
		"""
		print('=== myTreeWidget.fileSelected_callback()')
		theItems = self.selectedItems()
		if len(theItems) > 0:
			theItem = theItems[0]
			#selectedRow = self.fileList.currentRow() # self.fileList is a QTreeWidget
			filename = theItem.text(self.myColumns['File'])
			#print('   fileSelected_callback()', filename)
			# visually select image in canvas with yellow square
			self.myCanvasWidget.getGraphicsView().setSelectedItem(filename)
