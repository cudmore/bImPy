# 20190802

# goal: make a stack window and overlay tracing from deepvess

"""
[done] make left tool bar
[done] make top contrast bar

[done] make segment selection
on selecting segment, select in list
[done] on selecting segment in list, select in image

take stats on vessel segments
"""

import os, math, time

import tifffile

import pandas as pd
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends import backend_qt5agg

from bContrastWidget import bContrastWidget
from bStackFeebackWidget import bStackFeebackWidget

################################################################################
class bSlabList:
	"""
	full list of all points in a vascular tracing
	"""
	def __init__(self, tifPath):

		self.id = None # to count edges
		self.x = None
		self.y = None
		self.z = None

		self.edgeList = []

		# todo: change this to _slabs.txt
		pointFilePath, ext = os.path.splitext(tifPath)
		pointFilePath += '.txt'

		if not os.path.isfile(pointFilePath):
			print('bSlabList error, did not find', pointFilePath)
			return
		else:
			df = pd.read_csv(pointFilePath)

			nSlabs = len(df.index)
			self.id = np.full(nSlabs, np.nan) #df.iloc[:,0].values # each point/slab will have an edge id
			
			self.x = df.iloc[:,0].values
			self.y = df.iloc[:,1].values
			self.z = df.iloc[:,2].values

			print('tracing z max:', np.nanmax(self.z))

		self.analyze()

	@property
	def numSlabs(self):
		return len(self.x)

	@property
	def numEdges(self):
		return len(self.edgeList)

	def getEdge(self, edgeIdx):
		"""
		return a list of slabs in an edge
		"""
		theseIndices = np.argwhere(self.id == edgeIdx)
		return theseIndices
		
	def analyze(self):
		def euclideanDistance(x1, y1, z1, x2, y2, z2):
			if z1 is None and z2 is None:
				return math.sqrt((x2-x1)**2 + (y2-y1)**2)
			else:
				return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
			
		self.edgeList = []
		
		edgeIdx = 0
		edgeDict = {'n':0, 'Length 3D':0, 'Length 2D':0, 'z':None}
		n = self.numSlabs
		for pointIdx in range(n):
			self.id[pointIdx] = edgeIdx
			
			x1 = self.x[pointIdx]
			y1 = self.y[pointIdx]
			z1 = self.z[pointIdx]

			if np.isnan(z1):
				# move on to a new edge/vessel
				edgeDict['Length 3D'] = round(edgeDict['Length 3D'],2)
				edgeDict['Length 2D'] = round(edgeDict['Length 2D'],2)
				self.edgeList.append(edgeDict)
				edgeDict = {'n':0, 'Length 3D':0, 'Length 2D':0, 'z':None} # reset
				edgeIdx += 1
				continue

			edgeDict['n'] = edgeDict['n'] + 1
			if pointIdx > 0:
				edgeDict['Length 3D'] = edgeDict['Length 3D'] + euclideanDistance(prev_x1, prev_y1, prev_z1, x1, y1, z1)
				edgeDict['Length 2D'] = edgeDict['Length 2D'] + euclideanDistance(prev_x1, prev_y1, None, x1, y1, None)
			edgeDict['z'] = int(z1)
			prev_x1 = x1
			prev_y1 = y1
			prev_z1 = z1
			
		#print(self.edgeList)

################################################################################
class bSimpleStack:
	def __init__(self, path):
		self.path = path
		
		self._voxelx = 1
		self._voxely = 1

		self._images = None
		self.loadStack()
		
		self.slabList = bSlabList(self.path)
		
	@property
	def voxelx(self):
		return self._voxelx

	@property
	def voxely(self):
		return self._voxely
	
	@property
	def pixelsPerLine(self):
		return self._images.shape[2]
		
	@property
	def linesPerFrame(self):
		return self._images.shape[1]
		
	@property
	def numSlices(self):
		if self._images is not None:
			return self._images.shape[0]
		else:
			return None

	@property
	def bitDepth(self):
		dtype = self._images.dtype
		if dtype == 'uint8':
			return 8
		else:
			return 16
		
	def loadStack(self):
		with tifffile.TiffFile(path) as tif:
			self._images = tif.asarray()
		print('self.path', self.path)
		print('self._images.shape:', self._images.shape)
		print('self._images.dtype:', self._images.dtype)

	#
	# I really have no idea what the next two functions are doing 
	'''
	def _display0(self, image, display_min, display_max): # copied from Bi Rico
		# Here I set copy=True in order to ensure the original image is not
		# modified. If you don't mind modifying the original image, you can
		# set copy=False or skip this step.
		image = np.array(image, copy=True)
		image.clip(display_min, display_max, out=image)
		image -= display_min
		np.floor_divide(image, (display_max - display_min + 1) / 256,
						out=image, casting='unsafe')
		return image.astype(np.uint8)

	def getImage_ContrastEnhanced(self, display_min, display_max, channel=1, sliceNum=None, useMaxProject=False) :
		"""
		sliceNum: pass NOne to use self.currentImage
		"""
		#lut = np.arange(2**16, dtype='uint16')
		lut = np.arange(2**8, dtype='uint8')
		lut = self._display0(lut, display_min, display_max)
		if useMaxProject:
			# need to specify channel !!!!!!
			return np.take(lut, self.maxProjectImage)
		else:
			#return np.take(lut, self.getImage(channel=channel, sliceNum=sliceNum))
			return np.take(lut, self._images[sliceNum,:,:])
	'''


################################################################################
class bAnnotationTable(QtWidgets.QWidget):
	def __init__(self, mainWindow=None, parent=None, slabList=None):
		super(bAnnotationTable, self).__init__(parent)
		self.mainWindow = mainWindow
		self.slabList = slabList

		self.myQVBoxLayout = QtWidgets.QVBoxLayout(self)

		self.myTableWidget = QtWidgets.QTableWidget()
		self.myTableWidget.setRowCount(self.slabList.numEdges)
		self.myTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.myTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.myTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		self.myTableWidget.cellClicked.connect(self.on_clicked)

		self.myTableWidget.setColumnCount(4)
		headerLabels = ['n', 'Length 3D', 'Length 2D', 'z']
		self.myTableWidget.setHorizontalHeaderLabels(headerLabels)

		header = self.myTableWidget.horizontalHeader()
		header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		# QHeaderView will automatically resize the section to fill the available space.
		# The size cannot be changed by the user or programmatically.
		#header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

		for idx, stat in enumerate(self.slabList.edgeList):
			myString = str(stat['n'])
			item = QtWidgets.QTableWidgetItem(myString)
			self.myTableWidget.setItem(idx, 0, item)

			myString = str(stat['Length 3D'])
			item = QtWidgets.QTableWidgetItem(myString)
			self.myTableWidget.setItem(idx, 1, item)

			myString = str(stat['Length 2D'])
			item = QtWidgets.QTableWidgetItem(myString)
			self.myTableWidget.setItem(idx, 2, item)

			myString = str(stat['z'])
			item = QtWidgets.QTableWidgetItem(myString)
			self.myTableWidget.setItem(idx, 3, item)

		self.myQVBoxLayout.addWidget(self.myTableWidget)

	def selectRow(self, row):
		print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! bAnnotationTable.selectRow()', row)
		#self.selectRow(row)
		
	@QtCore.pyqtSlot()
	def on_clicked(self):
		#print('bAnnotationTable.on_clicked')
		row = self.myTableWidget.currentRow()
		if row == -1 or row is None:
			return
		#print('   row:', row)
		yStat = self.myTableWidget.item(row,0).text() #
		#print('   ', row, yStat)
		self.mainWindow.signal('selectEdge', row, fromTable=True)

################################################################################
class bStackView(QtWidgets.QGraphicsView):
	def __init__(self, simpleStack, mainWindow=None):
		QtWidgets.QGraphicsView.__init__(self)

		#self.path = path
		
		self.mySimpleStack = simpleStack #bSimpleStack(path)
		self.mainWindow = mainWindow
		
		self.currentSlice = 0
		self.minContrast = 0
		self.maxContrast = 2 ** self.mySimpleStack.bitDepth # -1

		self.showTracing = True

		self.imgplot = None
		self._images = None
				
		self.iLeft = 0
		self.iTop = 0
		self.iRight = self.mySimpleStack.voxelx * self.mySimpleStack.pixelsPerLine # reversed
		self.iBottom = self.mySimpleStack.voxely * self.mySimpleStack.linesPerFrame

		dpi = 100
		width = 12
		height = 12

		# for click and drag
		self.clickPos = None
		
		#
		scene = QtWidgets.QGraphicsScene(self)
		#self.scene = scene

		# visually turn off scroll bars
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

		# image
		self.figure = Figure(figsize=(width, height), dpi=dpi)
		self.canvas = backend_qt5agg.FigureCanvas(self.figure)
		self.axes = self.figure.add_axes([0, 0, 1, 1]) #remove white border
		self.axes.axis('off') #turn off axis labels

		# point list
		markersize = 2**2
		self.mySlabPlot = self.axes.scatter([], [], marker='o', color='y', s=markersize, picker=True)

		# selection
		markersize = 5**2
		self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color='c', s=markersize)

		# flash selection
		markersize = 10**2
		self.myEdgeSelectionFlash = self.axes.scatter([], [], marker='o', color='m', s=markersize)

		#self.canvas.mpl_connect('key_press_event', self.onkey)
		#self.canvas.mpl_connect('button_press_event', self.onclick)
		#self.canvas.mpl_connect('scroll_event', self.onscroll)
		self.canvas.mpl_connect('pick_event', self.onpick)

		scene.addWidget(self.canvas)
		
		self.setScene(scene)

	def flashEdge(self, edgeIdx, on):
		#print('flashEdge() edgeIdx:', edgeIdx, on)
		if edgeIdx is None:
			return
		if on:
			theseIndices = self.mySimpleStack.slabList.getEdge(edgeIdx)
			xMasked = self.mySimpleStack.slabList.y[theseIndices]
			yMasked = self.mySimpleStack.slabList.x[theseIndices]
			self.myEdgeSelectionFlash.set_offsets(np.c_[xMasked, yMasked])
			#
			QtCore.QTimer.singleShot(30, lambda:self.flashEdge(edgeIdx, False))
		else:
			self.myEdgeSelectionFlash.set_offsets(np.c_[[], []])
		#
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!
	
	def selectEdge(self, edgeIdx):
		#print('=== bStackView.selectEdge():', edgeIdx)
		if edgeIdx is None:
			print('bStackView.selectEdge() -->> NONE')
			#markersize = 10
			#self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color='c', s=markersize, picker=True)
			self.myEdgeSelectionPlot.set_offsets(np.c_[[], []])
		else:
			theseIndices = self.mySimpleStack.slabList.getEdge(edgeIdx)
			
			#print('selectEdge() theseIndices:', theseIndices)
			
			z = self.mySimpleStack.slabList.z[theseIndices[0]][0] # not sure why i need trailing [0] ???
			z = int(z)
			#print('z:', z)
			self.setSlice(z)
			
			self.xMasked = self.mySimpleStack.slabList.y[theseIndices]
			self.yMasked = self.mySimpleStack.slabList.x[theseIndices]
			self.myEdgeSelectionPlot.set_offsets(np.c_[self.xMasked, self.yMasked])

			QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, True))
			
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!
		
	def setSliceContrast(self, sliceNumber):
		img = self.mySimpleStack._images[sliceNumber, :, :].copy()
		
		#print('setSliceContrast() BEFORE min:', img.min(), 'max:', img.max(), 'mean:', img.mean(), 'dtype:', img.dtype)

		maxInt = 2 ** self.mySimpleStack.bitDepth - 1

		lowContrast = self.minContrast
		highContrast = self.maxContrast

		#print('   setSliceContrast() sliceNumber:', sliceNumber, 'maxInt:', maxInt, 'lowContrast:', lowContrast, 'highContrast:', highContrast)

		#mult = maxInt / abs(highContrast - lowContrast)
		denominator = abs(highContrast - lowContrast)
		if denominator != 0:
			mult = maxInt / denominator
		else:
			mult = maxInt 
			
		#img.astype(numpy.uint16)
		img[img < lowContrast] = lowContrast
		img[img > highContrast] = highContrast
		img -= lowContrast
		
		img = img * mult
		img = img.astype(np.uint8)

		#print('setSliceContrast() AFTER min:', img.min(), 'max:', img.max(), 'mean:', img.mean(), 'dtype:', img.dtype, 'int(mult):', int(mult))
		
		return img
		
	def setSlice(self, index=None, recursion=True):
		#print('bStackView.setSlice()', index)
		
		if index is None:
			index = self.currentSlice
		
		if index < 0:
			index = 0
		if index > self.mySimpleStack.numSlices-1:
			index = self.mySimpleStack.numSlices -1

		showImage = True
		
		if showImage:
			image = self.setSliceContrast(index)
			if self.imgplot is None:
				self.imgplot = self.axes.imshow(image, cmap='Greens_r', extent=[self.iLeft, self.iRight, self.iBottom, self.iTop])  # l, r, b, t
			else:
				self.imgplot.set_data(image)
		else:
			pass
		
		#
		# update point annotations
		if self.showTracing:
			upperz = index - 5
			lowerz = index + 5
			#try:
			if 1:
				self.zMask = np.ma.masked_outside(self.mySimpleStack.slabList.z, upperz, lowerz)
				self.xMasked = self.mySimpleStack.slabList.y[~self.zMask.mask] # swapping
				self.yMasked = self.mySimpleStack.slabList.x[~self.zMask.mask]
			#except:
			#	print('ERROR: bStackWindow.setSlice')

			self.mySlabPlot.set_offsets(np.c_[self.xMasked, self.yMasked])
		else:
			self.mySlabPlot.set_offsets(np.c_[[], []])
		
		self.currentSlice = index # update slice

		if self.mainWindow is not None and recursion:
			self.mainWindow.signal('set slice', index)
		
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def zoom(self, zoom):
		#print('=== myCanvasWidget.zoom()', zoom)
		if zoom == 'in':
			scale = 1.2
		else:
			scale = 0.8
		self.scale(scale,scale)

	def keyPressEvent(self, event):
		#print('=== bStackView.keyPressEvent() event.key():', event.key())
		if event.key() in [QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal]:
			self.zoom('in')
		elif event.key() == QtCore.Qt.Key_Minus:
			self.zoom('out')
		elif event.key() == QtCore.Qt.Key_T:
			self.showTracing = not self.showTracing
			self.setSlice() #refresh
		else:
			event.setAccepted(False)
				
	def wheelEvent(self, event):
		#if self.hasPhoto():
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		if modifiers == QtCore.Qt.ControlModifier:
			if event.angleDelta().y() > 0:
				self.zoom('in')
			else:
				self.zoom('out')
		else:
			if event.angleDelta().y() > 0:
				self.currentSlice -= 1
			else:
				self.currentSlice += 1
			self.setSlice(self.currentSlice)

	def mousePressEvent(self, event):
		#print('=== bStackView.mousePressEvent()', event.pos())
		self.clickPos = event.pos()
		super().mousePressEvent(event)
		event.setAccepted(True)

	def mouseMoveEvent(self, event):
		#print('=== bStackView.mouseMoveEvent()')
		if self.clickPos is not None:
			newPos = event.pos() - self.clickPos
			dx = self.clickPos.x() - newPos.x()
			dy = self.clickPos.y() - newPos.y()
			self.translate(dx, dy)
		super().mouseMoveEvent(event)
		event.setAccepted(True)

	def mouseReleaseEvent(self, event):
		#print('=== bStackView.mouseReleaseEvent()')
		self.clickPos = None
		super().mouseReleaseEvent(event)
		event.setAccepted(True)

	def onpick(self, event):
		print('\n====== bStackView.onpick()')
		xdata = event.mouseevent.xdata
		ydata = event.mouseevent.ydata
		ind = event.ind
	
		# find the first ind in bSlabList.id
		firstInd = ind[0]
		edgeIdx = self.mySimpleStack.slabList.id[firstInd]
		edgeIdx = int(edgeIdx)
		
		edgeIdx += 1
		
		print('   firstInd:', firstInd, 'edgeIdx:', edgeIdx)
		
		#self.selectEdge(edgeIdx)
		print('   edge:', edgeIdx, self.mySimpleStack.slabList.edgeList[edgeIdx])
		
################################################################################
class bStackWidget(QtWidgets.QWidget):
	def __init__(self, mainWindow=None, parent=None, path=''):
		super(bStackWidget, self).__init__(parent)

		self.path = path

		basename = os.path.basename(self.path)
		self.setWindowTitle(basename)

		#self.setAcceptDrops(True)

		#
		self.mySimpleStack = bSimpleStack(path) # backend stack
		#
		
		self.showLeftControlBar = True
		self.showContrastBar = True
		self.showFeebackBar = True
		
		self.myHBoxLayout = QtWidgets.QHBoxLayout(self)

		self.myVBoxLayout = QtWidgets.QVBoxLayout(self)

		self.myContrastWidget = bContrastWidget(mainWindow=self)
		
		self.bStackFeebackWidget = bStackFeebackWidget(self)
		self.bStackFeebackWidget.set('num slices', self.mySimpleStack.numSlices)
		
		self.myHBoxLayout2 = QtWidgets.QHBoxLayout(self)

		self.myStackView = bStackView(self.mySimpleStack, mainWindow=self) # a visual stack

		# a slider to set slice number
		self.mySliceSlider = QtWidgets.QSlider(QtCore.Qt.Vertical)
		self.mySliceSlider.setMaximum(self.mySimpleStack.numSlices)
		self.mySliceSlider.setInvertedAppearance(True) # so it goes from top:0 to bottom:numSlices
		self.mySliceSlider.setMinimum(0)
		self.mySliceSlider.valueChanged.connect(self.sliceSliderValueChanged)
		
		self.myHBoxLayout2.addWidget(self.myStackView)
		self.myHBoxLayout2.addWidget(self.mySliceSlider)
		
		# add
		self.myVBoxLayout.addWidget(self.myContrastWidget) #, stretch=0.1)
		self.myVBoxLayout.addWidget(self.bStackFeebackWidget) #, stretch=0.1)
		#self.myVBoxLayout.addWidget(self.myStackView) #, stretch = 9)
		self.myVBoxLayout.addLayout(self.myHBoxLayout2) #, stretch = 9)
		
		self.annotationTable = bAnnotationTable(mainWindow=self, parent=None, slabList=self.mySimpleStack.slabList)
		#self.verticalSpacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding) 


		self.myHBoxLayout.addWidget(self.annotationTable, stretch=3) # stretch=10, not sure on the units???		
		#self.myHBoxLayout.addItem(self.verticalSpacer)
		self.myHBoxLayout.addLayout(self.myVBoxLayout, stretch=7) # stretch=10, not sure on the units???

		#self.connect(self.myHBoxLayout, QtCore.SIGNAL("dropped"), self.dropEvent)
		'''
		self.setFocusPolicy(QtCore.Qt.ClickFocus)
		self.setFocus()
		'''

		self.updateDisplayedWidgets()
		
	def sliceSliderValueChanged(self):
		theSlice = self.mySliceSlider.value()
		self.signal('set slice', theSlice)
		
	def updateDisplayedWidgets(self):
		# left control bar
		if self.showLeftControlBar:
			self.annotationTable.show()
		else:
			self.annotationTable.hide()
		# contrast bar
		if self.showContrastBar:
			self.myContrastWidget.show()
		else:
			self.myContrastWidget.hide()
		# feedback bar
		if self.showFeebackBar:
			self.bStackFeebackWidget.show()
		else:
			self.bStackFeebackWidget.hide()

			
	# get rid of this
	def getStack(self):
		return self.mySimpleStack
	
	def signal(self, signal, value, fromTable=False):
		#print('=== bStackWidget.signal()', 'signal:', signal, 'value:', value, 'fromTable:', fromTable)
		if signal == 'selectEdge':
			self.selectEdge(value)
			if not fromTable:
				self.annotationTable.selectRow(value)
		
		if signal == 'contrast change':
			minContrast = value['minContrast']
			maxContrast = value['maxContrast']
			self.myStackView.minContrast = minContrast
			self.myStackView.maxContrast = maxContrast
			self.myStackView.setSlice(index=None) # will just refresh current slice
			
		if signal == 'set slice':
			self.bStackFeebackWidget.set('set slice', value)
			self.myStackView.setSlice(value, recursion=False)
			self.mySliceSlider.setValue(value)
			
	def selectEdge(self, edgeIdx):
		self.myStackView.selectEdge(edgeIdx)
	
	def keyPressEvent(self, event):
		#print('=== bStackWidget.keyPressEvent() event.key():', event.key())
		if event.key() in [QtCore.Qt.Key_Escape]:
			self.myStackView.selectEdge(None)
		if event.key() in [QtCore.Qt.Key_L]:
			self.showLeftControlBar = not self.showLeftControlBar
			self.updateDisplayedWidgets()
		if event.key() in [QtCore.Qt.Key_C]:
			self.showContrastBar = not self.showContrastBar
			self.updateDisplayedWidgets()
		if event.key() in [QtCore.Qt.Key_F]:
			self.showFeebackBar = not self.showFeebackBar
			self.updateDisplayedWidgets()
		if event.key() in [QtCore.Qt.Key_H]:
			self.printHelp()

	def printHelp(self):
		print('=============================================================')
		print('bStackWidget help')
		print('==============================================================')
		print(' Show/Hide interface')
		print('   t: show/hide tracing')
		print('   l: show/hide list of annotations')
		print('   c: show/hide contrast bar')
		print('   f: show/hide feedback bar')
		print('   esc: remove edge selection (cyan)')
		print(' Navigation')
		print('   mouse wheel: scroll through images')
		print('   command + mouse wheel: zoom in/out (follows mouse position)')
		print('   +/-: zoom in/out (follows mouse position)')
		print('   click + drag: pan')
		print(' ' )
		
	'''
	def mousePressEvent(self, event):
		print('=== bStackWidget.mousePressEvent()')
		super().mousePressEvent(event)
		self.myStackView.mousePressEvent(event)
		event.setAccepted(False)
	def mouseMoveEvent(self, event):
		#print('=== bStackWidget.mouseMoveEvent()')
		super().mouseMoveEvent(event)
		self.myStackView.mouseMoveEvent(event)
		event.setAccepted(False)
	def mouseReleaseEvent(self, event):
		print('=== bStackWidget.mouseReleaseEvent()')
		super().mouseReleaseEvent(event)
		self.myStackView.mousePressEvent(event)
		event.setAccepted(False)
	'''
	
	"""
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
	"""
		
	'''
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
	'''
	
if __name__ == '__main__':
	import sys

	#path = '/Users/cudmore/box/DeepVess/data/invivo/20190613__0028.tif'
	if len(sys.argv) == 2:
		path = sys.argv[1]
	else:
		path = '/Users/cudmore/box/DeepVess/data/mytest.tif'
		path = '/Users/cudmore/box/DeepVess/data/invivo/20190613__0028.tif'
		
	app = QtWidgets.QApplication(sys.argv)

	sw = bStackWidget(mainWindow=app, parent=None, path=path)
	sw.show()
	sw.myStackView.setSlice(0)

	'''
	sw2 = bStackWidget(mainWindow=app, parent=None, path=path)
	sw2.show()
	sw2.setSlice(0)
	'''

	#print('app.topLevelWidgets():', app.topLevelWidgets())

	sys.exit(app.exec_())
