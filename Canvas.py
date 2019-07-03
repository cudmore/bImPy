# Author: Robert Cudmore
# Date: 20190630

from functools import partial
from collections import OrderedDict

from PyQt5 import QtCore, QtWidgets, QtGui

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)

		self.centralwidget = QtWidgets.QWidget(parent)
		self.centralwidget.setObjectName("centralwidget")

		self.myQHBoxLayout = QtWidgets.QHBoxLayout(self.centralwidget)
		
		self.title = 'PyQt5 image - pythonspot.com'
		self.left = 10
		self.top = 10
		self.width = 1024 #640
		self.height = 768 #480

		self.setMinimumSize(320, 240)
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)

		self.myGraphicsView = myQGraphicsView() #myQGraphicsView(self.centralwidget)
		self.myQHBoxLayout.addWidget(self.myGraphicsView)
	
		# here I am linking the toolbar to the graphics view
		# i can't figure out how to use QAction !!!!!!
		self.toolbarWidget = myToolbarWidget(self.myGraphicsView)

		self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbarWidget)

		self.setCentralWidget(self.centralwidget)

	def keyPressEvent(self, event):
		print('myApp.keyPressEvent() event:', event)
		self.myGraphicsView.keyPressEvent(event)

# I am assuming file names are unique
fakeImages = OrderedDict()
rowStep = 550
colStep = 550
numRows = 10
numCols = 10
xPos = 150
yPos = 50
imageNumber = 1
for row in range(numRows):
	xPos = 50
	for col in range(numCols):
		fakeImages[str(imageNumber)] = OrderedDict({
		'path': 'onfile.tif',
		'xMotor': xPos,
		'yMotor': yPos,
		})
		xPos += colStep
		imageNumber += 1
	yPos += rowStep

fakeTwoPImages = OrderedDict()
rowStep = 400
colStep = 400
numRows = 5
numCols = 5
xPos = 1500
yPos = 1500
imageNumber = 1
for row in range(numRows):
	xPos = 50
	for col in range(numCols):
		fakeTwoPImages[str(imageNumber)] = OrderedDict({
		'path': 'onfile.tif',
		'xMotor': xPos,
		'yMotor': yPos,
		'width': 200,
		'height': 200,
		})
		xPos += colStep
		imageNumber += 1
	yPos += rowStep

globalSelectionSquare = {
	'pen': QtCore.Qt.SolidLine, # could be QtCore.Qt.DotLine
	'penColor': QtCore.Qt.yellow,
	'penWidth': 10,
}

class myQGraphicsPixmapItem(QtWidgets.QGraphicsPixmapItem):
	"""
	To display images in canvas
	"""
	def __init__(self, myLayer, parent=None):
		super(QtWidgets.QGraphicsPixmapItem, self).__init__(parent)
		self.myLayer = myLayer
		
	def paint(self, painter, option, widget=None):
		super().paint(painter, option, widget)
		"""
		painter.setBrush(self.brush)
		painter.setPen(self.pen)
		painter.drawEllipse(self.rect)
		"""
		if self.isSelected():
			self.drawFocusRect(painter)

	def drawFocusRect(self, painter):
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
					
class myQGraphicsRectItem(QtWidgets.QGraphicsRectItem):
	"""
	To display rectangles in canvas.
	Used for 2p images so we can show/hide max project and still see square
	"""
	def __init__(self, myLayer, parent=None):
		super(QtWidgets.QGraphicsRectItem, self).__init__(parent)
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
	def __init__(self, parent=None):
		super(QtWidgets.QGraphicsView, self).__init__(parent)

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
		#rect_item = QtWidgets.QGraphicsRectItem(QtCore.QRectF(0, 0, 100, 100))
		rect_item = myQGraphicsRectItem('video', QtCore.QRectF(-10000, -10000, 100, 100))
		self.myScene.addItem(rect_item)

		for idx, image in enumerate(fakeImages.keys()):
			path = fakeImages[image]['path']
			xMotor = fakeImages[image]['xMotor']
			yMotor = fakeImages[image]['yMotor']
			# load the image (need to somehow load max of stack ???
			
			#
			# todo: 
			# 1) load as qimage (keep copy), 
			# 2) adjust brightness, second copy, 
			# 3) insert brightness adjusted into QPixmap/myGraphicsPixMapItem
			#
			
			pixmap = QtGui.QPixmap(path)
			pixmapWidth = pixmap.width()
			pixmapHeight = pixmap.height()
			# scale image
			newWidth = pixmapWidth #/ 2
			newHeight = pixmapHeight #/ 2
			pixmap = pixmap.scaled(newWidth, newHeight, QtCore.Qt.KeepAspectRatio)
			# insert
			#pixMapItem = QtWidgets.QGraphicsPixmapItem(pixmap)
			pixMapItem = myQGraphicsPixmapItem('Video Layer', pixmap)
			pixMapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
			pixMapItem.setToolTip(str(idx))
			pixMapItem.setPos(xMotor,yMotor)
			self.myScene.addItem(pixMapItem)
		
		for idx, image in enumerate(fakeTwoPImages.keys()):
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

			myPen = QtGui.QPen(QtCore.Qt.cyan)
			myPen.setWidth(10)
			#rect_item = QtWidgets.QGraphicsRectItem(QtCore.QRectF(xMotor, yMotor, width, height))
			rect_item = myQGraphicsRectItem('2P Squares Layer', QtCore.QRectF(xMotor, yMotor, width, height))
			rect_item.setPen(myPen) #QBrush
			rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
			self.myScene.addItem(rect_item)

		# add an object at really big x/y
		#rect_item = QtWidgets.QGraphicsRectItem(QtCore.QRectF(2500, 2500, 100, 100))
		rect_item = myQGraphicsRectItem('video', QtCore.QRectF(10000, 10000, 100, 100))
		self.myScene.addItem(rect_item)

		self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
		self.setScene(self.myScene)

	def hideShowLayer(self, thisLayer, isVisible):
		print('myQGraphicsView.hideShowLayer()', thisLayer, isVisible)
		for item in self.myScene.items():
			if item.myLayer == thisLayer:
				item.setVisible(isVisible)
				
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
		print('=== myCanvasWidget.zoom()', zoom)
		if zoom == 'in':
			scale = 1.2
		else:
			scale = 0.8
		self.scale(scale,scale)

class myToolbarWidget(QtWidgets.QToolBar):
	def __init__(self, myQGraphicsView, parent=None):
		super(QtWidgets.QToolBar, self).__init__(parent)

		self.myQGraphicsView = myQGraphicsView

		# a button
		buttonName = 'Load Canvas'
		button = QtWidgets.QPushButton(buttonName)
		button.setToolTip('Load a canvas from disk')
		#button.move(100,70)
		button.clicked.connect(partial(self.on_button_click,buttonName))
		self.addWidget(button)

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

	app = QtWidgets.QApplication(sys.argv)
	w = MainWindow()
	w.resize(640, 480)
	w.show()
	sys.exit(app.exec_())
