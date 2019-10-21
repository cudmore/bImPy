# see for a cleaner example (no selection)
# https://stackoverflow.com/questions/44468775/how-to-draw-a-rectangle-and-adjust-its-shape-by-drag-and-drop-in-pyqt5

# good tutorial on drawing
# https://www.learnpyqt.com/courses/custom-widgets/bitmap-graphics/

import sys
import numpy as np
import random

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import Qt

from matplotlib.figure import Figure
from matplotlib.backends import backend_qt5agg

#class MouseTracker(QtWidgets.QGraphicsView):
class MouseTracker(QWidget):
	distance_from_center = 0
	def __init__(self):
		super().__init__()
		self.initUI()
		self.setMouseTracking(True)
		self.x = -1
		self.y = -1
		self.pos = None
		self.startPos = None
		self.isDrawing = False
		
		self.figure = Figure()
		self.canvas = backend_qt5agg.FigureCanvas(self.figure)
		self.axes = self.figure.add_axes([0, 0, 1, 1]) #remove white border
		self.axes.axis('off') #turn off axis labels

		#
		markerColor = 'red'
		markerSize = 5
		self.oneRoi = self.axes.scatter([], [], marker='o', color=markerColor, s=markerSize)
		
	def initUI(self):
		self.setGeometry(200, 200, 1000, 500)
		self.setWindowTitle('Mouse Tracker')
		self.label = QLabel(self)
		self.label.resize(500, 40)
		self.show()
		#self.pos = None

	def mouseMoveEvent(self, event):
		self.label.setText('Coordinates: ( %d : %d )' % (event.x(), event.y()))	   
		if self.isDrawing:
			self.pos = event.pos()
			self.update()

	def mousePressEvent(self, event):
		print('mousePressEvent', event.x(), event.y())
		self.isDrawing = True
		self.startPos = event.pos()
		
	def mouseReleaseEvent(self, event):
		print('mouseReleaseEvent', event.x(), event.y())
		self.isDrawing = False
		self.drawRoi()
		
	def paintEvent(self, event):
		if self.pos:
			print('paintEvent', self.pos.x(), self.pos.y())
			q = QPainter(self)
			#q = QPainter(self.myPixmap)
			q.setPen(QPen(Qt.cyan, 5))
			#q.drawLine(self.pos.x(), self.pos.y(), 250, 500)
			q.drawLine(self.pos.x(), self.pos.y(), self.startPos.x(), self.startPos.y())


	def drawRoi(self):
		print('drawRoi()')
		x = [100, 200]
		y = [100, 300]
		self.oneRoi.set_offsets(np.c_[x, y])
		
		self.canvas.draw()
	
app = QApplication(sys.argv)
ex = MouseTracker()
sys.exit(app.exec_())