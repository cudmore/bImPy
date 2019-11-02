# Author: Robert Cudmore
# Date: 20190630

from functools import partial
from collections import OrderedDict

import skimage
import tifffile
import numpy as np # added for contrast enhance

from PyQt5 import QtCore, QtWidgets, QtGui

from bCanvas import bCanvas

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)

		tmpCanvasFolderPath = '/Users/cudmore/Dropbox/data/20190429/20190429_tst2'
		tmpCanvasFolderPath = '/Users/cudmore/box/data/nathan/canvas/20190429_tst2'
		self.canvas = bCanvas(folderPath=tmpCanvasFolderPath)

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
		self.myGraphicsView = myQGraphicsView(self.canvas) #myQGraphicsView(self.centralwidget)
		self.myQHBoxLayout.addWidget(self.myGraphicsView)

		# here I am linking the toolbar to the graphics view
		# i can't figure out how to use QAction !!!!!!
		self.toolbarWidget = myToolbarWidget(self.myGraphicsView, self.canvas)

		self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbarWidget)

		self.setCentralWidget(self.centralwidget)

	def keyPressEvent(self, event):
		print('myApp.keyPressEvent() event:', event)
		self.myGraphicsView.keyPressEvent(event)

globalSelectionSquare = {
	'pen': QtCore.Qt.SolidLine, # could be QtCore.Qt.DotLine
	'penColor': QtCore.Qt.yellow,
	'penWidth': 10,
}

class myQGraphicsPixmapItem(QtWidgets.QGraphicsPixmapItem):
	"""
	To display images in canvas
	"""
	def __init__(self, fileName, index, myLayer, parent=None):
		super(QtWidgets.QGraphicsPixmapItem, self).__init__(parent)
		self._fileName = fileName
		self._index = index # index into canvas list (list of either video or scope)
		self.myLayer = myLayer

	def paint(self, painter, option, widget=None):
		super().paint(painter, option, widget)
		"""
		painter.setBrush(self.brush)
		painter.setPen(self.pen)
		painter.drawEllipse(self.rect)
		"""

		#print('myQGraphicsPixmapItem.paint() isSelected', self.isSelected())
		if self.isSelected():
			self.drawFocusRect(painter)

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
		#painter.drawRect(self.focusrect)
		# ???
		painter.drawRect(self.boundingRect())

	def mousePressEvent(self, event):
		#print('   myQGraphicsPixmapItem.mousePressEvent()')
		super().mousePressEvent(event)
		#self.setSelected(True)
		event.setAccepted(False)
	def mouseMoveEvent(self, event):
		#print('   myQGraphicsPixmapItem.mouseMoveEvent()')
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
		print('myQGraphicsPixmapItem.myQGraphicsPixmapItem.bringForward()')
		myScene = self.scene()
		previousItem = None
		for item in self.scene().items():
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
		#print('   myQGraphicsPixmapItem.mousePressEvent()')
		super().mousePressEvent(event)
		#self.setSelected(True)
		event.setAccepted(False)
	def mouseMoveEvent(self, event):
		#print('   myQGraphicsPixmapItem.mouseMoveEvent()')
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
			pixMapItem = myQGraphicsPixmapItem(fileName, idx, 'Video Layer', pixmap)
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
			pixMapItem = myQGraphicsPixmapItem(fileName, idx, '2P Max Layer', pixmap)
			pixMapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
			pixMapItem.setToolTip(str(idx))
			pixMapItem.setPos(xMotor,yMotor)
			pixMapItem.setZValue(numItems)

			# add to scene
			self.myScene.addItem(pixMapItem)

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

			# 20190705 removed scope rectangles
			if xMotor is not None and yMotor is not None:
				myPen = QtGui.QPen(QtCore.Qt.cyan)
				myPen.setWidth(10)
				rect_item = myQGraphicsRectItem(fileName,'2P Squares Layer', QtCore.QRectF(xMotor, yMotor, umWidth, umHeight))
				rect_item.setPen(myPen) #QBrush
				rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
				self.myScene.addItem(rect_item)

			numItems += 1


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
		selectThisItem = None
		for item in self.myScene.items():
			if item._fileName == fileName:
				selectThisItem = item
		if selectThisItem is not None:
			print('myQGraphicsView.setSelectedItem:', selectThisItem, selectThisItem._fileName)
		self.myScene.setFocusItem(selectThisItem)

	def hideShowLayer(self, thisLayer, isVisible):
		print('myQGraphicsView.hideShowLayer()', thisLayer, isVisible)
		for item in self.myScene.items():
			if item.myLayer == thisLayer:
				item.setVisible(isVisible)

	def mousePressEvent(self, event):
		print('=== myQGraphicsView.mousePressEvent()')
		super().mousePressEvent(event)
		#event.setAccepted(False)
	def mouseMoveEvent(self, event):
		#print('=== myQGraphicsView.mouseMoveEvent()')
		super().mouseMoveEvent(event)
		#event.setAccepted(False)
	def mouseReleaseEvent(self, event):
		print('=== myQGraphicsView.mouseReleaseEvent()')
		super().mouseReleaseEvent(event)
		#event.setAccepted(False)

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
		print('=== myCanvasWidget.keyPressEvent() event.key():', event.key())
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
		"""
		print('changeOrder()', this)
		if this == 'bring to front':
			selectedItems = self.myScene.selectedItems()
			if len(selectedItems) > 0:
				selectedItem = selectedItems[0]
				selectedItem.bringForward()
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
		#print('=== myCanvasWidget.zoom()', zoom)
		if zoom == 'in':
			scale = 1.2
		else:
			scale = 0.8
		self.scale(scale,scale)

class myToolbarWidget(QtWidgets.QToolBar):
	def __init__(self, myQGraphicsView, theCanvas, parent=None):
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
		self.fileList = QtWidgets.QTreeWidget()
		self.fileList.itemSelectionChanged.connect(self.fileSelected)
		self.addWidget(self.fileList)

		self.fileList.setHeaderLabels(['File'])

		itemList = []
		for videoFile in theCanvas.videoFileList:
			print(videoFile._fileName)
			#self.fileList.addItem(videoFile._fileName)
			item = QtWidgets.QTreeWidgetItem(self.fileList)
			item.setText(0, videoFile._fileName)
			item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
			item.setCheckState(0, QtCore.Qt.Checked)
			itemList.append(item)
		for scopeFile in theCanvas.scopeFileList:
			print(scopeFile._fileName)
			#self.fileList.addItem(scopeFile._fileName)
			item = QtWidgets.QTreeWidgetItem(self.fileList)
			item.setText(0, scopeFile._fileName)
			item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
			item.setCheckState(0, QtCore.Qt.Checked)
			itemList.append(item)
		self.fileList.insertTopLevelItems(0, itemList)

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

	def fileSelected(self):
		print('fileSelected() FIX')
		'''
		theItems = self.fileList.selectedItems()
		if len(theItems) > 0:
			theItem = theItems[0]
			selectedRow = self.fileList.currentRow()
			print('fileSelected()', theItem.text(), 'row:', selectedRow)
			self.myQGraphicsView.setSelectedItem(theItem.text())
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
	import bJavaBridge

	import logging
	import traceback

	try:
		from bJavaBridge import bJavaBridge
		myJavaBridge = bJavaBridge()
		myJavaBridge.start()

		app = QtWidgets.QApplication(sys.argv)
		w = MainWindow()
		w.resize(640, 480)
		w.show()
		sys.exit(app.exec_())
	except Exception as e:
		print('bCanvasApp __main__ exception')
		print(traceback.format_exc())
		#logging.error(traceback.format_exc())
		print('   2')
		myJavaBridge.stop()
		print('   3')
		#sys.exit(app.exec_())
		print('   4')
		#raise
		print('   5')
	finally:
		print('   6')
		myJavaBridge.stop()
		print('   7')
		#sys.exit(app.exec_())
		print('   8')
