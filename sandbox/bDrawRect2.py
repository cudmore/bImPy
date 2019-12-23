from PyQt5 import QtCore, QtGui, QtWidgets

class GraphicsScene(QtWidgets.QGraphicsScene):
	def __init__(self, parent=None):
		super(GraphicsScene, self).__init__(QtCore.QRectF(-500, -500, 1000, 1000), parent)
		self._start = QtCore.QPointF()
		self._current_rect_item = None

	def mousePressEvent(self, event):
		if self.itemAt(event.scenePos(), QtGui.QTransform()) is None:
			self._current_rect_item = QtWidgets.QGraphicsRectItem()
			self._current_rect_item.setBrush(QtCore.Qt.red)
			self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
			self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
			self.addItem(self._current_rect_item)
			self._start = event.scenePos()
			r = QtCore.QRectF(self._start, self._start)
			self._current_rect_item.setRect(r)
		super(GraphicsScene, self).mousePressEvent(event)

	def mouseMoveEvent(self, event):
		if self._current_rect_item is not None:
			r = QtCore.QRectF(self._start, event.scenePos()).normalized()
			self._current_rect_item.setRect(r)
		super(GraphicsScene, self).mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		self._current_rect_item = None
		super(GraphicsScene, self).mouseReleaseEvent(event)


class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		scene =GraphicsScene(self)
		view = QtWidgets.QGraphicsView(scene)
		self.setCentralWidget(view)


if __name__ == '__main__':
	import sys

	app = QtWidgets.QApplication(sys.argv)
	w = MainWindow()
	w.resize(640, 480)
	w.show()
	sys.exit(app.exec_())
