# Author: Robert Cudmore
# Date: 20190630

import os
from functools import partial
from collections import OrderedDict

import skimage
import tifffile
import numpy as np # added for contrast enhance

from PyQt5 import QtCore, QtWidgets, QtGui

import bimpy
from bimpy.interface import bStackWidget

class bCanvasApp(QtWidgets.QMainWindow):
	def __init__(self, parent=None):
		super(bCanvasApp, self).__init__(parent)

		tmpCanvasFolderPath = '/Users/cudmore/Dropbox/data/20190429/20190429_tst2'
		tmpCanvasFolderPath = '/Users/cudmore/box/data/nathan/canvas/20190429_tst2'
		self.canvas = bimpy.bCanvas(folderPath=tmpCanvasFolderPath)

		# this is only for import from igor
		self.canvas.importIgorCanvas()

		self.canvas.buildFromScratch()

		self.centralwidget = QtWidgets.QWidget(parent)
		self.centralwidget.setObjectName("centralwidget")

		self.myQHBoxLayout = QtWidgets.QHBoxLayout(self.centralwidget)

		self.title = 'Canvas'
		self.left = 10
		self.top = 10
		self.width = 1024 #640
		self.height = 768 #480

		self.setMinimumSize(320, 240)
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)

		# main view to hold images
		self.myGraphicsView = myQGraphicsView(self.canvas, self) #myQGraphicsView(self.centralwidget)
		self.myQHBoxLayout.addWidget(self.myGraphicsView)

		# here I am linking the toolbar to the graphics view
		# i can't figure out how to use QAction !!!!!!
		self.motorToolbarWidget = myScopeToolbarWidget(self.canvas)
		self.addToolBar(QtCore.Qt.LeftToolBarArea, self.motorToolbarWidget)

		self.toolbarWidget = myToolbarWidget(self.myGraphicsView, self.canvas)
		self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbarWidget)

		self.setCentralWidget(self.centralwidget)

		self.myStackList = [] # a list of open bStack

	def mousePressEvent(self, event):
		print('=== bCanvasApp.mousePressEvent()')
		super().mousePressEvent(event)
		#event.setAccepted(False)

	def keyPressEvent(self, event):
		print('myApp.keyPressEvent() event:', event)
		self.myGraphicsView.keyPressEvent(event)

	def selectInFileList(self, filename):
		"""
		User click on canvas image will select in file list
		"""
		print('bCanvasApp.selectInFileList() filename:', filename)
		self.toolbarWidget.setSelectedItem(filename)

	# This is from bStackBrowser
	#def showStackWindow(self, path):
	def openStack(self, filename, layer, channel=1):
		"""
		open a stack from the canvas
		"""
		print('=== bCanvasApp.openStack() filename:', filename)

		canvasPath = self.canvas._folderPath

		if layer == 'Video Layer':
			#canvasPath = os.path.join(canvasPath, 'video')
			canvasPath = self.canvas.videoFolderPath

		print('   canvasPath:', canvasPath)

		stackPath = os.path.join(canvasPath, filename)
		print('   bCanvasApp.openStack() is opening stackPath:', stackPath)

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
			tmp = bStackWidget(path=stackPath)
			tmp.show()
			self.myStackList.append(tmp)


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
	def __init__(self, fileName, index, myLayer, parent=None):
		super(QtWidgets.QGraphicsPixmapItem, self).__init__(parent)
		#self.myQGraphicsView = myQGraphicsView
		self._fileName = fileName
		self._index = index # index into canvas list (list of either video or scope)
		self.myLayer = myLayer
		self._isVisible = True

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
		#print('   myQGraphicsPixmapItem.mouseReleaseEvent()')
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
	def __init__(self, theCanvas, parent=None):
		super(QtWidgets.QGraphicsView, self).__init__(parent)

		self.myParentApp = parent
		self.myCanvas = theCanvas

		self.setBackgroundBrush(QtCore.Qt.darkGray)

		self.myScene = QtWidgets.QGraphicsScene()

		# visually turn off scroll bars
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

		# these work
		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

		# I want to set the initial videw of the scene to include all items ??????
		#self.myScene.setSceneRect(QtCore.QRectF())

		# add an object at really small x/y
		'''
		rect_item = myQGraphicsRectItem('video', QtCore.QRectF(-20000, -20000, 100, 100))
		self.myScene.addItem(rect_item)
		'''

		numItems = 0 # used to stack items with item.setZValue()

		for idx, videoFile in enumerate(theCanvas.videoFileList):
			path = videoFile.path # todo: remove use of ._ ## fakeImages[image]['path']
			fileName = videoFile._fileName
			#videoFileHeader = videoFile.getHeader()
			xMotor = videoFile.header.header['xMotor']
			yMotor = videoFile.header.header['yMotor']
			umWidth = videoFile.header.header['umWidth']
			umHeight = videoFile.header.header['umHeight']

			#videoImage = videoFile.getVideoImage() # ndarray
			videoImage = videoFile.getImage() # ndarray
			imageStackHeight, imageStackWidth = videoImage.shape

			myQImage = QtGui.QImage(videoImage, imageStackWidth, imageStackHeight, QtGui.QImage.Format_Indexed8)
			#myQImage = QtGui.QImage(videoImage, imageStackWidth, imageStackHeight, QtGui.QImage.Format_RGB32)

			pixmap = QtGui.QPixmap(myQImage)
			pixmap = pixmap.scaled(umWidth, umHeight, QtCore.Qt.KeepAspectRatio)

			# insert
			#pixMapItem = myQGraphicsPixmapItem(fileName, idx, 'Video Layer', self, parent=pixmap)
			pixMapItem = myQGraphicsPixmapItem(fileName, idx, 'Video Layer', parent=pixmap)
			pixMapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
			pixMapItem.setToolTip(str(idx))
			pixMapItem.setPos(xMotor,yMotor)
			pixMapItem.setZValue(numItems)

			# add to scene
			self.myScene.addItem(pixMapItem)

			numItems += 1

		# this is to load 2p file ... put back in
		#for idx, image in enumerate(fakeTwoPImages.keys()):
		for idx, scopeFile in enumerate(theCanvas.scopeFileList):
			'''
			print('scopeFile.header.prettyPrint():', scopeFile.header.prettyPrint())
			print('   xMotor:', scopeFile.header.header['xMotor'])
			print('   yMotor:', scopeFile.header.header['yMotor'])
			print('   umWidth:', scopeFile.header.header['umWidth'])
			print('   umHeight:', scopeFile.header.header['umHeight'])
			'''

			# THESE ARE FUCKING STRINGS !!!!!!!!!!!!!!!!!!!!
			fileName = scopeFile._fileName
			xMotor = scopeFile.header.header['xMotor']
			yMotor = scopeFile.header.header['yMotor']
			umWidth = scopeFile.header.header['umWidth']
			umHeight = scopeFile.header.header['umHeight']
			print('umWidth:', umWidth, 'umHeight:', umHeight)

			if xMotor == 'None':
				xMotor = None
			if yMotor == 'None':
				yMotor = None

			if xMotor is None or yMotor is None:
				print('bCanvasApp.myQGraphicsView() not inserting scopeFile -->> xMotor or yMotor is None ???')
				continue

			# todo: specify channel (1,2,3,4,...)
			stackMax = scopeFile.loadMax(channel=1, convertTo8Bit=True) # stackMax can be None
			#imageStackHeight, imageStackWidth = stackMax.shape
			imageStackWidth = scopeFile.pixelsPerLine
			imageStackHeight = scopeFile.linesPerFrame
			print('imageStackWidth:', imageStackWidth, 'imageStackHeight:', imageStackHeight)

			if stackMax is None:
				print('myQGraphicsView.__init__() is making zero max image for scopeFile:', scopeFile)
				stackMax = np.zeros((imageStackWidth, imageStackHeight), dtype=np.uint8)

			myQImage = QtGui.QImage(stackMax, imageStackWidth, imageStackHeight, QtGui.QImage.Format_Indexed8)

			pixmap = QtGui.QPixmap(myQImage)
			pixmap = pixmap.scaled(umWidth, umHeight, QtCore.Qt.KeepAspectRatio)

			# insert
			#pixMapItem = myQGraphicsPixmapItem(fileName, idx, '2P Max Layer', self, parent=pixmap)
			pixMapItem = myQGraphicsPixmapItem(fileName, idx, '2P Max Layer', parent=pixmap)
			pixMapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
			pixMapItem.setToolTip(str(idx))
			pixMapItem.setPos(xMotor,yMotor)
			pixMapItem.setZValue(numItems)
			# this also effects bounding rect
			#pixMapItem.setOpacity(0.0) # 0.0 transparent 1.0 opaque

			pixMapItem.setShapeMode(QtWidgets.QGraphicsPixmapItem.BoundingRectShape)
			print('pixMapItem.shapeMode():', pixMapItem.shapeMode())

			# add to scene
			self.myScene.addItem(pixMapItem)
			numItems += 1

			'''
			# a rectangle
			myPen = QtGui.QPen(QtCore.Qt.cyan)
			myPen.setWidth(10)
			rect_item = myQGraphicsRectItem('2P Squares Layer', QtCore.QRectF(xMotor, yMotor, width, height))
			rect_item.setPen(myPen) #QBrush
			rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
			self.myScene.addItem(rect_item)
			'''

			'''
			path = fakeTwoPImages[image]['path']
			xMotor = fakeTwoPImages[image]['xMotor']
			yMotor = fakeTwoPImages[image]['yMotor']
			width = fakeTwoPImages[image]['width']
			height = fakeTwoPImages[image]['height']
			# load the image (need to somehow load max of stack ???
			pixmap = QtGui.QPixmap(path)
			pixmap.fill()
			#pixmapWidth = pixmap.width()
			#pixmapHeight = pixmap.height()
			# scale image
			#newWidth = 200 #pixmapWidth
			#newHeight = 200 #pixmapHeight
			pixmap = pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio)
			# insert
			#pixMapItem = QtWidgets.QGraphicsPixmapItem(pixmap)
			pixMapItem = myQGraphicsPixmapItem('2P Max Layer', pixmap)
			pixMapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
			pixMapItem.setToolTip('2p_' + str(idx))
			pixMapItem.setPos(xMotor,yMotor)
			#pixMapItem.setOpacity(0) # this works but we loose mouse click selection and bounding selection rect
			pixMapItem.setVisible(True) # this works
			self.myScene.addItem(pixMapItem)
			'''

			# 20191104 removed scope rectangles, try and just hide image but still show selection rectangle?
			'''
			if xMotor is not None and yMotor is not None:
				myPen = QtGui.QPen(QtCore.Qt.cyan)
				myPen.setWidth(10)
				rect_item = myQGraphicsRectItem(fileName,'2P Squares Layer', QtCore.QRectF(xMotor, yMotor, umWidth, umHeight))
				rect_item.setPen(myPen) #QBrush
				rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True) # we don't want to select rects?
				rect_item.setZValue(numItems)
				self.myScene.addItem(rect_item)
				numItems += 1
			'''

			#numItems += 1


		# add an object at really big x/y
		'''
		rect_item = myQGraphicsRectItem('video', QtCore.QRectF(20000, 20000, 100, 100))
		self.myScene.addItem(rect_item)
		'''

		self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
		self.setScene(self.myScene)

	def setSelectedItem(self, fileName):
		"""
		Select the item at itemIndex.
		This is usually coming from toolbar file list selection
		"""
		print('   myQGraphicsView.setSelectedItem() fileName:', fileName)
		selectThisItem = None
		for item in self.myScene.items():
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
			print('   myQGraphicsView.setSelectedItem:', selectThisItem, selectThisItem._fileName)
		self.myScene.setFocusItem(selectThisItem)
		selectThisItem.setSelected(True)

	def hideShowItem(self, fileName, doShow):
		"""
		Hide/Show individual items

		todo: if a layer is off then do not hide/show, better yet,
		when layer is off, disable checkboxes in myToolbarWidget
		"""
		for item in self.myScene.items():
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
		print('myQGraphicsView.hideShowLayer()', thisLayer, isVisible)
		for item in self.myScene.items():
			if item.myLayer == thisLayer:
				# don't show items in this layer that are not visible
				# not visible are files that are checked off in myToolbarWidget
				if isVisible and not item._isVisible:
					continue
				if thisLayer=='Video Layer':
					# turn off both image and outline
					item.setOpacity(1.0 if isVisible else 0)
				else:
					item.setOpacity(1.0 if isVisible else 0.01)
				# not with 0
				#item.setOpacity(1.0 if isVisible else 0.1)

	def mouseDoubleClickEvent(self, event):
		"""
		open a stack on a double-click
		"""
		print('=== myQGraphicsView.mouseDoubleClickEvent')
		selectedItems = self.myScene.selectedItems()
		if len(selectedItems) > 0:
			selectedItem = selectedItems[0]
			fileName = selectedItem._fileName
			layer = selectedItem.myLayer
			self.myParentApp.openStack(fileName, layer)

	def mousePressEvent(self, event):
		print('=== myQGraphicsView.mousePressEvent()')
		super().mousePressEvent(event)
		#event.setAccepted(False)

	def mouseMoveEvent(self, event):
		#print('=== myQGraphicsView.mouseMoveEvent()')
		# this is critical, allows dragging view/scene around
		super().mouseMoveEvent(event)
		event.setAccepted(True)

	def mouseReleaseEvent(self, event):
		print('=== myQGraphicsView.mouseReleaseEvent() event:', event)
		super().mouseReleaseEvent(event)

		print('   tell the parent self.myParentApp (bCanvasApp) to select this file in its file list')
		selectedItems = self.myScene.selectedItems()
		print('   selectedItems:', selectedItems)#event.setAccepted(False)
		if len(selectedItems) > 0:
			selectedItem = selectedItems[0]
			'''
			print('selectedItem._fileName:', selectedItem._fileName)
			print('selectedItem._index:', selectedItem._index)
			print('selectedItem.myLayer:', selectedItem.myLayer)
			'''
			fileName = selectedItem._fileName
			self.myParentApp.selectInFileList(fileName)
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

	def keyPressEvent(self, event):
		print('=== myQGraphicsView.keyPressEvent() event.key():', event.key())
		# QtCore.Qt.Key_Tab

		# pan
		'''
		if event.key() == QtCore.Qt.Key_Left:
			self.pan('left')
		if event.key() == QtCore.Qt.Key_Right:
			self.pan('right')
		if event.key() == QtCore.Qt.Key_Up:
			self.pan('up')
		if event.key() == QtCore.Qt.Key_Down:
			self.pan('down')
		'''
		super().keyPressEvent(event)

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


	def changeOrder(self, this):
		"""
		this can be:
			'bring to front': Will bring the selected item BEFORE its previous item
			'send to back': Will put the selected item AFTER its next item

			This does not bring entirely to front or entirely to back???
		"""
		print('myQGraphicsView.changeOrder()', this)
		if this == 'bring to front':
			selectedItems = self.myScene.selectedItems()
			if len(selectedItems) > 0:
				print('   bring item to front:', selectedItems)
				selectedItem = selectedItems[0]
				selectedItem.bringForward()
			else:
				print('myQGraphicsView.changeOrder() did not find a selected item???')
		elif this == 'send to back':
			selectedItems = self.myScene.selectedItems()
			if len(selectedItems) > 0:
				print('   send item to back:', selectedItems)
				selectedItem = selectedItems[0]
				selectedItem.sendBackward()
			else:
				print('myQGraphicsView.changeOrder() did not find a selected item???')

	def wheelEvent(self, event):
		#if self.hasPhoto():
		if 1:
			if event.angleDelta().y() > 0:
				self.zoom('in')
				#factor = 1.25
				#self._zoom += 1
			else:
				self.zoom('out')
				#factor = 0.8
				#self._zoom -= 1
			'''
			if self._zoom > 0:
				self.scale(factor, factor)
			elif self._zoom == 0:
				self.fitInView()
			else:
				self._zoom = 0
			'''
	'''
	def pan(self, direction):
		stepSize = 100
		xOffset = 0
		yOffset = 0
		if direction == 'left':
			xOffset = stepSize
		if direction == 'right':
			xOffset = -stepSize
		if direction == 'up':
			yOffset = stepSize
		if direction == 'down':
			yOffset = -stepSize

		print('pan() x:', xOffset, 'y:', yOffset)
		#self.translate(xOffset,yOffset)
	'''

	def zoom(self, zoom):
		#print('=== myGraphicsView.zoom()', zoom)
		if zoom == 'in':
			scale = 1.2
		else:
			scale = 0.8
		self.scale(scale,scale)

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

class myTreeWidget(QtWidgets.QTreeWidget):
	def __init__(self, parent=None):
		super(myTreeWidget, self).__init__(parent)
		self.myQGraphicsView = parent

	def keyPressEvent(self, event):
		print('myTreeWidget.keyPressEvent() event.text():', event.text())
		#self.myGraphicsView.keyPressEvent(event)

		# todo: fix this, this assumes selected file in list is same as selected file in graphics view !
		if event.key() == QtCore.Qt.Key_F:
			#print('f for bring to front')
			self.myQGraphicsView.changeOrder('bring to front')
		elif event.key() == QtCore.Qt.Key_B:
			#print('b for send to back')
			self.myQGraphicsView.changeOrder('send to back')
		elif event.key() == QtCore.Qt.Key_Left:
			print('todo: left arrow reselect')
		elif event.key() == QtCore.Qt.Key_Right:
			print('todo: right arrow reselect')
		elif event.key() == QtCore.Qt.Key_Up:
			print('todo: up arrow, previous annotations')
		elif event.key() == QtCore.Qt.Key_Down:
			print('todo: down arrow, next selection')
		else:
			print('  key not handled:text:', event.text(), 'modifyers:', event.modifiers())

class myScopeToolbarWidget(QtWidgets.QToolBar):
	def __init__(self, theCanvas, parent=None):
		print('myScopeToolbarWidget.__init__')
		super(QtWidgets.QToolBar, self).__init__(parent)
		self.theCanvas = theCanvas

		myGroupBox = QtWidgets.QGroupBox()
		myGroupBox.setTitle('Scope Controller')
		myGroupBox.setFlat(True)

		# main v box
		vBoxLayout = QtWidgets.QVBoxLayout()

		#
		# arrows for left/right, front/back
		grid = QtWidgets.QGridLayout()

		buttonName = 'move stage left'
		icon  = QtGui.QIcon('icons/left-arrow.png')
		leftButton = QtWidgets.QPushButton()
		leftButton.setIcon(icon)
		leftButton.setToolTip('Move stage left')
		leftButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'move stage right'
		icon  = QtGui.QIcon('icons/right-arrow.png')
		rightButton = QtWidgets.QPushButton()
		rightButton.setIcon(icon)
		rightButton.setToolTip('Move stage right')
		rightButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'move stage back'
		icon  = QtGui.QIcon('icons/up-arrow.png')
		backButton = QtWidgets.QPushButton()
		backButton.setIcon(icon)
		backButton.setToolTip('Move stage back')
		backButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'move stage front'
		icon  = QtGui.QIcon('icons/down-arrow.png')
		frontButton = QtWidgets.QPushButton()
		frontButton.setIcon(icon)
		frontButton.setToolTip('Move stage back')
		frontButton.clicked.connect(partial(self.on_button_click,buttonName))

		grid.addWidget(leftButton, 1, 0) # row, col
		grid.addWidget(rightButton, 1, 2) # row, col
		grid.addWidget(backButton, 0, 1) # row, col
		grid.addWidget(frontButton, 2, 1) # row, col

		vBoxLayout.addLayout(grid)

		# x/y step size
		grid2 = QtWidgets.QGridLayout()

		xStepLabel = QtWidgets.QLabel("X Step")
		self.xStepSpinBox = QtWidgets.QSpinBox()
		self.xStepSpinBox.setMinimum(0) # si user can specify whatever they want
		self.xStepSpinBox.setMaximum(10000)
		self.xStepSpinBox.setValue(1000)
		self.xStepSpinBox.valueChanged.connect(self.stepValueChanged)

		yStepLabel = QtWidgets.QLabel("Y Step")
		self.yStepSpinBox = QtWidgets.QSpinBox()
		self.yStepSpinBox.setMinimum(0) # si user can specify whatever they want
		self.yStepSpinBox.setMaximum(10000)
		self.yStepSpinBox.setValue(500)
		self.yStepSpinBox.valueChanged.connect(self.stepValueChanged)

		grid2.addWidget(xStepLabel, 0, 0) # row, col
		grid2.addWidget(self.xStepSpinBox, 0, 1) # row, col
		grid2.addWidget(yStepLabel, 1, 0) # row, col
		grid2.addWidget(self.yStepSpinBox, 1, 1) # row, col

		vBoxLayout.addLayout(grid2)

		#
		# show video window and grab video
		video_hBoxLayout = QtWidgets.QHBoxLayout()

		buttonName = 'Live Video'
		icon  = QtGui.QIcon('icons/video.png')
		liveVideoButton = QtWidgets.QPushButton()
		liveVideoButton.setToolTip('Show Live Video Window')
		liveVideoButton.setIcon(icon)
		liveVideoButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'Grab'
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
		icon  = QtGui.QIcon('icons/folder.png')
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

	def stepValueChanged(self):
		xStep = self.xStepSpinBox.value()
		yStep = self.yStepSpinBox.value()
		print('myScopeToolbarWidget.stepValueChanged() xStep:', xStep, 'yStep:', yStep)

	@QtCore.pyqtSlot()
	def on_button_click(self, name):
		print('=== myScopeToolbarWidget.on_button_click() name:', name)

class myToolbarWidget(QtWidgets.QToolBar):
	def __init__(self, myQGraphicsView, theCanvas, parent=None):
		"""
		todo: remove theCanvas, not used
		"""
		print('myToolbarWidget.__init__')
		super(QtWidgets.QToolBar, self).__init__(parent)

		self.myQGraphicsView = myQGraphicsView

		# a button
		'''
		buttonName = 'Load Canvas'
		button = QtWidgets.QPushButton(buttonName)
		button.setToolTip('Load a canvas from disk')
		#button.move(100,70)
		button.clicked.connect(partial(self.on_button_click,buttonName))
		self.addWidget(button)
		'''

		buttonName = 'Save Canvas'
		button = QtWidgets.QPushButton(buttonName)
		button.setToolTip('Load a canvas from disk')
		button.clicked.connect(partial(self.on_button_click,buttonName))
		self.addWidget(button)

		checkBoxName = 'Video Layer'
		self.showVideoCheckBox = QtWidgets.QCheckBox(checkBoxName)
		self.showVideoCheckBox.setToolTip('Load a canvas from disk')
		self.showVideoCheckBox.setCheckState(2) # Really annoying it is not 0/1 False/True but 0:False/1:Intermediate/2:True
		self.showVideoCheckBox.clicked.connect(partial(self.on_checkbox_click, checkBoxName, self.showVideoCheckBox))
		self.addWidget(self.showVideoCheckBox)

		checkBoxName = '2P Max Layer'
		self.show2pMaxCheckBox = QtWidgets.QCheckBox(checkBoxName)
		self.show2pMaxCheckBox.setToolTip('Load a canvas from disk')
		self.show2pMaxCheckBox.setCheckState(2) # Really annoying it is not 0/1 False/True but 0:False/1:Intermediate/2:True
		self.show2pMaxCheckBox.clicked.connect(partial(self.on_checkbox_click, checkBoxName, self.show2pMaxCheckBox))
		self.addWidget(self.show2pMaxCheckBox)

		checkBoxName = '2P Squares Layer'
		self.show2pSquaresCheckBox = QtWidgets.QCheckBox(checkBoxName)
		self.show2pSquaresCheckBox.setToolTip('Load a canvas from disk')
		self.show2pSquaresCheckBox.setCheckState(2) # Really annoying it is not 0/1 False/True but 0:False/1:Intermediate/2:True
		self.show2pSquaresCheckBox.clicked.connect(partial(self.on_checkbox_click, checkBoxName, self.show2pSquaresCheckBox))
		self.addWidget(self.show2pSquaresCheckBox)

		#
		# radio buttons to select type of contrast (selected, video layer, scope layer)
		self.contrastGroupBox = QtWidgets.QGroupBox('Image Contrast')

		self.selectedContrast = QtWidgets.QRadioButton('Selected')
		self.videoLayerContrast = QtWidgets.QRadioButton('Video Layer')
		self.scopeLayerContrast = QtWidgets.QRadioButton('Scope Layer')

		'''
		self.selectedContrast.toggled.connect(self.on_toggle_image_contrast)
		self.videoLayerContrast.toggled.connect(self.on_toggle_image_contrast)
		self.scopeLayerContrast.toggled.connect(self.on_toggle_image_contrast)
		'''

		self.selectedContrast.setChecked(True)

		contrastVBox = QtWidgets.QVBoxLayout()
		contrastVBox.addWidget(self.selectedContrast)
		contrastVBox.addWidget(self.videoLayerContrast)
		contrastVBox.addWidget(self.scopeLayerContrast)

		#
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
		# file list
		#self.fileList = QtWidgets.QListWidget()

		#self.fileList = QtWidgets.QTreeWidget()
		self.fileList = myTreeWidget(self.myQGraphicsView)
		self.fileList.itemSelectionChanged.connect(self.fileSelected_callback)
		self.fileList.itemChanged.connect(self.fileSelected_changed)

		self.addWidget(self.fileList)

		self.fileList.setHeaderLabels(['File',]) # 'Show'])

		itemList = []
		for videoFile in theCanvas.videoFileList:
			print('videoFile:', videoFile._fileName)
			#self.fileList.addItem(videoFile._fileName)
			item = QtWidgets.QTreeWidgetItem(self.fileList)
			item.setText(0, videoFile._fileName)
			item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
			item.setCheckState(0, QtCore.Qt.Checked)

			itemList.append(item)
		for scopeFile in theCanvas.scopeFileList:
			print('scopeFile:', scopeFile._fileName)
			#self.fileList.addItem(scopeFile._fileName)
			item = QtWidgets.QTreeWidgetItem(self.fileList)
			item.setText(0, scopeFile._fileName)
			item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
			item.setCheckState(0, QtCore.Qt.Checked)
			itemList.append(item)

		# add all file list items to tree
		self.fileList.insertTopLevelItems(0, itemList)

		# itemChanged

		# try and make checkboxes
		# 20191105, get this working!!!
		'''
		for item in itemList:
			checkBoxName = 'File Check Box'
			tmpCheckbox = QtWidgets.QCheckBox(checkBoxName)
			tmpCheckbox.setToolTip('show/Hide Image')
			tmpCheckbox.setCheckState(2) # Really annoying it is not 0/1 False/True but 0:False/1:Intermediate/2:True
			tmpCheckbox.clicked.connect(partial(self.on_checkbox_click, checkBoxName, 'tmptmptmp'))
			#
			column = 2
			self.fileList.setItemWidget(item, column, tmpCheckbox)
		'''

		print('myToolbarWidget.__init__() done')

	'''
	def on_toggle_image_contrast(self):
		print('=== on_toggle_image_contrast()')
	'''

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
		selectedItems = self.myQGraphicsView.myScene.selectedItems() # can be none
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
		#	selectedItems = self.myQGraphicsView.myScene.selectedItems()
		#	print('NOT IMPLEMENTED')

		print('=== on_contrast_slider', 'adjustThisLayer:', adjustThisLayer, 'useMaxProject:', useMaxProject)

		for item in  self.myQGraphicsView.myScene.items():

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
				adjustThisItem = item.myLayer ==adjustThisLayer

			#if item.myLayer == adjustThisLayer:
			if adjustThisItem:
				# CHANGE TO GENERALIZE
				# todo: canvas should have one list of stacks (not separate video and scope lists)
				#if adjustThisLayer == 'Video Layer':
				if item.myLayer == 'Video Layer':
					videoFile = self.myQGraphicsView.myCanvas.videoFileList[item._index]
				#elif adjustThisLayer == '2P Max Layer':
				elif item.myLayer == '2P Max Layer':
					videoFile = self.myQGraphicsView.myCanvas.scopeFileList[item._index]
				else:
					print('bCanvasApp.on_contrast_slider() ERRRRRRRORRORORORRORORRORORORORORRORORO')
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

				imageStackHeight, imageStackWidth = videoImage.shape

				#print('mean:', np.mean(videoImage))

				myQImage = QtGui.QImage(videoImage, imageStackWidth, imageStackHeight, QtGui.QImage.Format_Indexed8)
				pixmap = QtGui.QPixmap(myQImage)
				pixmap = pixmap.scaled(umWidth, umHeight, QtCore.Qt.KeepAspectRatio)

				item.setPixmap(pixmap)
		#firstItem.setPixmap(pixmap)

	def fileSelected_changed(self, item, col):
		"""
		called when user clicks on check box
		"""
		print('=== fileSelected_changed() item:', item, 'col:', col, 'is now checked:', item.checkState(0))
		column = 0
		filename = item.text(column)
		isNowChecked = item.checkState(column) # 0:not checked, 2:is checked
		doShow = True if isNowChecked==2 else False
		print('   telling self.myQGraphicsView.hideShowItem() filename:', filename, 'doShow:', doShow)
		self.myQGraphicsView.hideShowItem(filename, doShow)

	def fileSelected_callback(self):
		"""
		Respond to user click in the file list (selects a file)
		"""
		print('=== myToolbarWidget.fileSelected_callback()')
		theItems = self.fileList.selectedItems()
		if len(theItems) > 0:
			theItem = theItems[0]
			#selectedRow = self.fileList.currentRow() # self.fileList is a QTreeWidget
			column = 0
			filename = theItem.text(column)
			#print('   fileSelected_callback()', filename)
			# visually select image in canvas with yellow square
			self.myQGraphicsView.setSelectedItem(filename)

	def setSelectedItem(self, filename):
		"""
		Respond to user clicking on the image and select the file in the list.
		"""
		print('myToolbarWidget.setSelectedItem() filename:', filename)
		items = self.fileList.findItems(filename, QtCore.Qt.MatchFixedString, column=0)
		if len(items)>0:
			item = items[0]
			print('   item:', item)
			self.fileList.setCurrentItem(item)

	def mousePressEvent(self, event):
		print('myToolbarWidget.mousePressEvent()')

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
			self.myQGraphicsView.hideShowLayer('Video Layer', checkState==2)
		if name == '2P Max Layer':
			self.myQGraphicsView.hideShowLayer('2P Max Layer', checkState==2)
		if name == '2P Squares Layer':
			self.myQGraphicsView.hideShowLayer('2P Squares Layer', checkState==2)

if __name__ == '__main__':
	import sys
	#import bJavaBridge

	import logging
	import traceback

	try:
		#from bJavaBridge import bJavaBridge
		myJavaBridge = bimpy.bJavaBridge()
		myJavaBridge.start()

		app = QtWidgets.QApplication(sys.argv)
		w = bCanvasApp()
		w.resize(640, 480)
		w.show()
		sys.exit(app.exec_())
	except Exception as e:
		print('bCanvasApp __main__ exception')
		print(traceback.format_exc())
		#logging.error(traceback.format_exc())
		myJavaBridge.stop()
		#sys.exit(app.exec_())
		#raise
	finally:
		myJavaBridge.stop()
		#sys.exit(app.exec_())
