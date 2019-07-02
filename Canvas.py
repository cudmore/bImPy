# Author: Robert Cudmore
# Date: 20190630

from functools import partial
from collections import OrderedDict

from PyQt5 import QtCore, QtWidgets, QtGui

globalSelectionSquare = {
	'pen': QtCore.Qt.SolidLine, # could be QtCore.Qt.DotLine
	'penColor': QtCore.Qt.yellow,
	'penWidth': 5,
}

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

		self.setMinimumSize(1024, 768)
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)

		self.myGraphicsView = myQGraphicsView() #myQGraphicsView(self.centralwidget)
		self.myQHBoxLayout.addWidget(self.myGraphicsView)
	
		self.toolbarWidget = myToolbarWidget()

		self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbarWidget)

		self.setCentralWidget(self.centralwidget)

	def keyPressEvent(self, event):
		print('myApp.keyPressEvent() event:', event)
		self.myGraphicsView.keyPressEvent(event)

# I am assuming file names are unique
fakeImages = OrderedDict()
rowStep = 500
colStep = 700
numRows = 20
numCols = 20
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
		
# define a xxx class just to draw selection as yellow square
# see: https://stackoverflow.com/questions/27752706/how-to-make-the-bounding-rect-of-a-selected-qgraphicsitem-show-automatically
class myQGraphicsPixmapItem(QtWidgets.QGraphicsPixmapItem):
	def __init__(self, parent=None):
		super(QtWidgets.QGraphicsPixmapItem, self).__init__(parent)

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
		
class myQGraphicsView(QtWidgets.QGraphicsView):
	def __init__(self, parent=None):
		super(QtWidgets.QGraphicsView, self).__init__(parent)

		scene = QtWidgets.QGraphicsScene()

		# add an object at really small x/y
		rect_item = QtWidgets.QGraphicsRectItem(QtCore.QRectF(0, 0, 100, 100))
		scene.addItem(rect_item)

		#
		# to select and draw as yellow square
		# see: https://gist.github.com/eyllanesc/168aced67ffc2df0afb85e1e58b0eaff
		#
		
		for idx, image in enumerate(fakeImages.keys()):
			path = fakeImages[image]['path']
			xMotor = fakeImages[image]['xMotor']
			yMotor = fakeImages[image]['yMotor']
			# load the image (need to somehow load max of stack ???
			pixmap = QtGui.QPixmap(path)
			pixmapWidth = pixmap.width()
			pixmapHeight = pixmap.height()
			# scale image
			newWidth = pixmapWidth / 2
			newHeight = pixmapHeight / 2
			pixmap = pixmap.scaled(newWidth, newHeight, QtCore.Qt.KeepAspectRatio)
			# insert
			#pixMapItem = QtWidgets.QGraphicsPixmapItem(pixmap)
			pixMapItem = myQGraphicsPixmapItem(pixmap)
			pixMapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
			pixMapItem.setToolTip(str(idx))
			pixMapItem.setPos(xMotor,yMotor)
			scene.addItem(pixMapItem)
		
		# add an object at really big x/y
		rect_item = QtWidgets.QGraphicsRectItem(QtCore.QRectF(2500, 2500, 100, 100))
		scene.addItem(rect_item)

		self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
		self.setScene(scene)

		#print(self.items()) # a list of items in this view

	def mousePressEvent(self, event):
		print('=== myQGraphicsView.mousePressEvent()')
		print('   ', event.pos())
		xyPos = event.pos()
		item = self.itemAt(xyPos)
		print('   mouse selected item:', item)

		if item is not None:
			print('i want to draw a bounding yellow rectangle')
			print(item.boundingRect())
			theRect = item.boundingRect()
			#item.drawRect(QRect(rtheRect.x(), theRect.y(), theRect.width()-p.width(), theRect.height()-theRect.width()));

		#super(QtWidgets.QGraphicsView, self).mousePressEvent(event)
		super().mousePressEvent(event)

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
	def __init__(self, parent=None):
		super(QtWidgets.QToolBar, self).__init__(parent)

		#myQVBoxLayout = QtWidgets.QVBoxLayout(self)

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

	@QtCore.pyqtSlot()
	def on_button_click(self, name):
		print('=== myToolbarWidget.on_button_click() name:', name)

if __name__ == '__main__':
	import sys

	app = QtWidgets.QApplication(sys.argv)
	w = MainWindow()
	w.resize(640, 480)
	w.show()
	sys.exit(app.exec_())
