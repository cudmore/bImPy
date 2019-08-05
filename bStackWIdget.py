# 20190802

# goal: make a stack window and overlay tracing from deepvess

"""
make left tool bar
make top contrast bar

make segment selection
on selecting segment, select in list
on selecting segment in list, select in image

take stats on vessel segments
"""

import os

import tifffile

import pandas as pd
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends import backend_qt5agg

class bPointList:
	def __init__(self, tifPath):
		
		self.x = None
		self.y = None
		self.z = None
		
		self.edgeList = []
		
		pointFilePath, ext = os.path.splitext(tifPath)
		pointFilePath += '.txt'
		
		if not os.path.isfile(pointFilePath):
			print('bPointList error, did not find', pointFilePath)
			return
		else:
			df = pd.read_csv(pointFilePath)
			
			self.x = df.iloc[:,0].values
			self.y = df.iloc[:,1].values
			self.z = df.iloc[:,2].values
			
			print('tracing z max:', np.nanmax(self.z))
			
		self.analyze()
		
	def numPoints(self):
		return len(self.x)
	
	def analyze(self):
		edgeIdx = 0
		edgeDict = {'Idx':edgeIdx, 'n':'', 'Length':''}
		n = self.numPoints()
		for pointIdx in range(n):
			x = self.x[pointIdx]
			y = self.y[pointIdx]
			z = self.z[pointIdx]
			if np.isnan(z):
				edgeIdx += 1
				self.edgeList.append(edgeDict)
				continue
			edgeDict['Idx'] = edgeIdx
		
		#print(self.edgeList)
		
class bAnnotationTable(QtWidgets.QWidget):
	def __init__(self, mainWindow=None, parent=None, pointList=None):
		super(bAnnotationTable, self).__init__(parent)
		self.pointList = pointList

		self.myQVBoxLayout = QtWidgets.QVBoxLayout(self)

		self.myTableWidget = QtWidgets.QTableWidget()
		self.myTableWidget.setRowCount(self.pointList.numPoints())
		self.myTableWidget.setColumnCount(3)
		self.myTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.myTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.myTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		self.myTableWidget.cellClicked.connect(self.on_clicked)
	
		headerLabels = ['x', 'y', 'z']
		self.myTableWidget.setHorizontalHeaderLabels(headerLabels)

		header = self.myTableWidget.horizontalHeader()	   
		header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		# QHeaderView will automatically resize the section to fill the available space.
		# The size cannot be changed by the user or programmatically.
		#header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

		for idx, stat in enumerate(self.pointList.x):
			stat = str(stat)
			item = QtWidgets.QTableWidgetItem(stat)
			self.myTableWidget.setItem(idx, 0, item)
		
			item = QtWidgets.QTableWidgetItem(stat)
			self.myTableWidget.setItem(idx, 1, item)
			
			item = QtWidgets.QTableWidgetItem(stat)
			self.myTableWidget.setItem(idx, 2, item)
			
		self.myQVBoxLayout.addWidget(self.myTableWidget)

	@QtCore.pyqtSlot()
	def on_clicked(self):
		print('bAnnotationTable.on_clicked')
		row = self.myTableWidget.currentRow()
		if row == -1 or row is None:
			return
		print('   row:', row)
		yStat = self.myTableWidget.item(row,0).text() #
		print('   ', row, yStat)
		#self.myParent.metaPlotStat(yStat)
	
#class bStackWindow(FigureCanvas):
#	def __init__(self, parent=None, path=''):
class bStackWidget(QtWidgets.QWidget):
	def __init__(self, mainWindow=None, parent=None, path=''):
		super(bStackWidget, self).__init__(parent)
		self.path = path

		basename = os.path.basename(self.path)
		self.setWindowTitle(basename)
		
		self.setAcceptDrops(True)
		
		self.loadStack()
				
		self.currentSlice = 0
		self.voxelx = 1
		self.voxely = 1
		self.imgplot = None
		
		dpi = 100
		width = 12
		height = 12
		
		self.myHBoxLayout = QtWidgets.QHBoxLayout(self)

		# image
		self.figure = Figure(figsize=(width, height), dpi=dpi)
		self.canvas = backend_qt5agg.FigureCanvas(self.figure)
		self.axes = self.figure.add_axes([0, 0, 1, 1]) #remove white border
		self.axes.axis('off') #turn off axis labels

		# point list
		self.pointList = bPointList(self.path)
		markersize = 5
		self.myScatterPlot = self.axes.scatter([], [], marker='o', color='y', s=markersize, picker=True)
		self.annotationTable = bAnnotationTable(mainWindow=None, parent=None, pointList=self.pointList)
		self.myHBoxLayout.addWidget(self.annotationTable, stretch=2) # stretch=10, not sure on the units???
		

		#FigureCanvas.__init__(self, self.figure)
		#self.setParent(parent)

		self.canvas.mpl_connect('key_press_event', self.onkey)
		self.canvas.mpl_connect('button_press_event', self.onclick)
		self.canvas.mpl_connect('scroll_event', self.onscroll)
		self.canvas.mpl_connect('pick_event', self.onpick)


		# finalize
		self.myHBoxLayout.addWidget(self.canvas, stretch=9) # stretch=10, not sure on the units???

		#self.connect(self.myHBoxLayout, QtCore.SIGNAL("dropped"), self.dropEvent)
		'''
		self.setFocusPolicy(QtCore.Qt.ClickFocus)
		self.setFocus()
		'''
		
	def dragEnterEvent(self, event):
		#print('dragEnterEvent:', event)
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		#print('dragMoveEvent:', event)
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		print('dropEvent:', event)
		if event.mimeData().hasUrls:
			for url in event.mimeData().urls():
				print('   ', url.toLocalFile())
		else:
			event.ignore()
		

	def setSlice(self, index):
		print('setSlice:', index)
		
		if index < 0:
			index = 0
		if index > self.numSlices-1:
			index = self.numSlices -1
		
		iLeft = 0
		iTop = 0
		iRight = self.voxelx * self._images.shape[2] # reversed
		iBottom = self.voxely * self._images.shape[1]

		if self.imgplot is None:
			self.imgplot = self.axes.imshow(self._images[index,:,:], cmap='Greens_r', extent=[iLeft, iRight, iBottom, iTop])  # l, r, b, t		
		else:
			self.imgplot.set_data(self._images[index,:,:])
			
		#
		# update point annotations
		showTracing = True
		if showTracing:
			upperz = index - 5
			lowerz = index + 5
			#try:
			if 1:
				self.zMask = np.ma.masked_outside(self.pointList.z, upperz, lowerz)
				self.xMasked = self.pointList.y[~self.zMask.mask] # swapping
				self.yMasked = self.pointList.x[~self.zMask.mask]
			#except:
			#	print('ERROR: bStackWindow.setSlice')
			
			self.myScatterPlot.set_offsets(np.c_[self.xMasked, self.yMasked])
		
		self.currentSlice = index # update slice
		
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!
		
	@property
	def numSlices(self):
		if self._images is not None:
			return self._images.shape[0]
		else:
			return None

	def loadStack(self):
		with tifffile.TiffFile(path) as tif:
			self._images = tif.asarray()
		print('self.path', self.path)
		print('self.images.shape:', self._images.shape)
		print('self.images.dtype:', self._images.dtype)

	def onkey(self, event):
		print('bStackWindow.onkey()', event.key)
		key = event.key

	def onclick(self, event):
		print('bStackWindow.onclick()', event.button, event.x, event.y, event.xdata, event.ydata)

	def onscroll(self, event):
		if event.button == 'up':
			self.currentSlice -= 1
		elif event.button == 'down':
			self.currentSlice += 1
		self.setSlice(self.currentSlice)
		
	def onpick(self, event):
		print('bStackWindow.onpick()', event.ind)
	
if __name__ == '__main__':
	import sys
	
	#path = '/Users/cudmore/box/DeepVess/data/invivo/20190613__0028.tif'
	path = '/Users/cudmore/box/DeepVess/data/mytest.tif'
	
	app = QtWidgets.QApplication(sys.argv)

	sw = bStackWidget(mainWindow=app, parent=None, path=path)
	sw.show()
	sw.setSlice(0)
	
	'''
	sw2 = bStackWidget(mainWindow=app, parent=None, path=path)
	sw2.show()
	sw2.setSlice(0)
	'''
	
	print('app.topLevelWidgets():', app.topLevelWidgets())
	
	sys.exit(app.exec_())