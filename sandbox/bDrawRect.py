import sys

from PyQt5 import QtGui, QtCore, QtWidgets

class myRectItem(QtWidgets.QGraphicsRectItem):
	def paint(self, painter, option, widget=None):
		super(myRectItem, self).paint(painter, option, widget)
		painter.save()
		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		painter.setBrush(QtCore.Qt.red)
		painter.drawEllipse(option.rect)
		painter.restore()

class MyWidget(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()
		self.setGeometry(30,30,600,400)
		self.begin = QtCore.QPoint()
		self.end = QtCore.QPoint()
		self.show()

	def paintEvent(self, event):
		qp = QtGui.QPainter(self)
		br = QtGui.QBrush(QtGui.QColor(100, 10, 10, 40))
		qp.setBrush(br)
		qp.drawRect(QtCore.QRect(self.begin, self.end))

	def mousePressEvent(self, event):
		self.begin = event.pos()
		self.end = event.pos()
		self.update()

	def mouseMoveEvent(self, event):
		self.end = event.pos()
		self.update()

	def mouseReleaseEvent(self, event):
		'''
		self.begin = event.pos()
		self.end = event.pos()
		'''
		print('mouseReleaseEvent()', self.begin, self.end)
		self.update()


app = QtWidgets.QApplication(sys.argv)
ex = MyWidget()
sys.exit(app.exec_())
