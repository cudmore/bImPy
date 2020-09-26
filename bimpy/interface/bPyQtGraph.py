"""

NEEDS PyQt 5.13.0 !!!!!

see here for class diagram:
    https://stackoverflow.com/questions/45879148/pyqtgraph-help-understanding-source-code#:~:text=PyQtGraph%20will%20create%20a%20QGraphicsScene,of%20that%20view%20for%20you.

see
    https://stackoverflow.com/questions/58526980/how-to-connect-mouse-clicked-signal-to-pyqtgraph-plot-widget

"""

import sys, os, math
from collections import OrderedDict

import numpy as np

import pickle # to load/save _pre computed masks

from qtpy import QtCore, QtGui, QtWidgets
#from PyQt5 import QtCore, QtGui, QtWidgets

#from PyQt5.QtCore import QT_VERSION_STR
#print('bPyQtGraph QT_VERSION_STR=', QT_VERSION_STR)

from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

import tifffile

import bimpy

################################################################
class myPyQtGraphWindow2(QtWidgets.QMainWindow):

	def __init__(self, *args, **kwargs):
		super(myPyQtGraphWindow2, self).__init__(*args, **kwargs)

		self.setWindowTitle('pyqtgraph example: PlotWidget')
		self.resize(600,800)

		centralWidget = QtGui.QWidget()
		self.setCentralWidget(centralWidget)

		myVBoxLayout = QtGui.QVBoxLayout()
		centralWidget.setLayout(myVBoxLayout)

		'''
		self.graphicsView = pg.PlotWidget(cw)
		self.graphicsView.plot([1,2], [1,2])
		'''

		# load stack
		path = '/Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch2.tif'
		self.mySimpleStack = bimpy.bStack(path) # backend stack

		# makes new window
		self.myPyQtGraphPlotWidget = myPyQtGraphPlotWidget(self, mySimpleStack=self.mySimpleStack)

		button1 = QtGui.QPushButton('xxx')
		button2 = QtGui.QPushButton('xxx')

		myVBoxLayout.addWidget(button1)

		myVBoxLayout.addWidget(self.myPyQtGraphPlotWidget)

		myVBoxLayout.addWidget(button2)

		# does not work, embeds in window but no zooming
		# without *self makes new window
		#self.myPyQtGraphPlotWidget = myPyQtGraphPlotWidget(self)

###########################################################################
class myPyQtGraphPlotWidget(pg.PlotWidget):
	setSliceSignal = QtCore.Signal(str, object)
	selectNodeSignal = QtCore.Signal(object)
	selectEdgeSignal = QtCore.Signal(object)
	selectAnnotationSignal = QtCore.Signal(object)
	#
	tracingEditSignal = QtCore.Signal(object) # on new/delete/edit of node, edge, slab
	#
	# not implemented, what did this do? see class bStackView
	displayStateChangeSignal = QtCore.Signal(str, object)

	#def __init__(self, *args, **kwargs):
	#	super(myPyQtGraphPlotWidget, self).__init__(*args, **kwargs)
	def __init__(self, parent=None, mySimpleStack=None):
		super(myPyQtGraphPlotWidget, self).__init__(parent=parent)

		self.mainWindow = parent # usually bStackWidget
		self.myZoom = 1 # to control point size of tracing plot() and setdata()

		##
		##
		# (1) set imageAxisOrder to row-major
		# (2) flip y with self.getViewBox().invertY(True)
		# (3) flip ALL (x,y) we get from *this view (e.g. needs x/y swapped in all plots)
		##
		##

		#
		pg.setConfigOption('imageAxisOrder','row-major')

		# do this, also flips image, DOES NOT needs setSLice() with sliceImage = np.fliplr(sliceImage)
		#no self.getViewBox().invertX(True)
		self.getViewBox().invertY(True)

		self.setAspectLocked()

		# turn off both mouse pan and mouse wheel zoom
		#self.setMouseEnabled(x=False, y=False)

		self.hideButtons() # Causes auto-scale button (‘A’ in lower-left corner) to be hidden for this PlotItem

		# turns off default right-click menu, works
		#self.setMenuEnabled(False)

		# this is required for mouse callbacks to have proper x/y position !!!
		# hide bottom/left axis, works
		self.hideAxis('left')
		self.hideAxis('bottom')

		# Instances of ImageItem can be used inside a ViewBox or GraphicsView.
		fakeData = np.zeros((1,1,1))
		self.myImage = pg.ImageItem(fakeData)
		self.addItem(self.myImage)

		# self.plot() creates: <class 'pyqtgraph.graphicsItems.PlotDataItem.PlotDataItem'>

		#
		# slabs
		# see: https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/scatterplotitem.html#pyqtgraph.ScatterPlotItem.setData
		# pxMode: If True (default), spots are always the same size regardless of scaling, and size is given in px.
		#		Otherwise, size is in scene coordinates and the spots scale with the view. Default is True
		pen = pg.mkPen(color='c', width=3)
		symbolSize = 3
		pxMode = True #(default is True) # TOO SLOW IF False !!!!
		self.mySlabPlot = self.plot([], [], pen=pen, symbol='o', symbolSize=7, symbolBrush=('c'),
							connect='finite',
							pxMode = pxMode,
							clickable=True)
		#self.mySlabPlot = self.plot([], [], self.slabPlotParams, connect='finite')

		self.mySlabPlot.sigPointsClicked.connect(self.onMouseClicked_slabs)
		# should be faster but does not seem to work?
		#self.mySlabPlot.setClipToView(True)

		pen = pg.mkPen(color='y', width=3)
		self.mySlabPlotSelection = self.plot([], [], pen=pen, symbol='o', symbolSize=10, symbolBrush=('y'),
							connect='finite', clickable=False)

		# for a single slab (not the edge)
		self.mySlabPlotSelection2 = self.plot([], [], pen=None, symbol='x', symbolSize=20, symbolBrush=('g'),
							connect='finite', clickable=False)

		self.myEdgeSelectionFlash = self.plot([], [],
							pen=pen, symbol='o', symbolSize=20, symbolBrush=('y'),
							connect='finite', clickable=False)

		#
		# one slab (line orthogonal to edges)
		oneSlabPen = pg.mkPen(color='g', width=5)
		self.mySlabPlotOne = self.plot([], [],
							pen=oneSlabPen, symbol='x', symbolSize=20, symbolBrush=('g'),
							connect='finite', clickable=False)

		#
		# nodes
		self.myNodePlot = self.plot([], [], pen=None, symbol='o', symbolSize=8, symbolBrush=('r'))
		self.myNodePlot.sigPointsClicked.connect(self.onMouseClicked_nodes)

		self.myNodePlotSelection = self.plot([], [], pen=None, symbol='o', symbolSize=10, symbolBrush=('y'),
							connect='finite')

		self.myNodeSelectionFlash = self.plot([], [],
											pen=None, symbol='o', symbolSize=20, symbolBrush=('y'))


		#
		# annotations
		self.myAnnotationPlot = self.plot([], [], pen=None, symbol='t', symbolSize=10, symbolBrush=('b'))
		self.myAnnotationPlot.sigPointsClicked.connect(self.onMouseClicked_annotations)

		self.myAnnotationPlotSelection = self.plot([], [], pen=None, symbol='x', symbolSize=15, symbolBrush=('y'),
							connect='finite')

		self.myAnnotationSelectionFlash = self.plot([], [],
											pen=None, symbol='o', symbolSize=20, symbolBrush=('y'))

		# click on scene
		#self.mySlabPlot.scene().sigMouseClicked.connect(self.onMouseClicked_scene)
		#self.mySlabPlot.scene().sigMouseMoved.connect(self.onMouseMoved_scene)

		#self.scene().sigMouseClicked.connect(self.sceneClicked)
		self.scene().sigMouseMoved.connect(self.onMouseMoved_scene)
		self.scene().sigMouseClicked.connect(self.onMouseClicked_scene) # works but confusing coordinates

		#
		# new
		self.mySimpleStack = mySimpleStack

		self.keyIsDown = None # to detect 'e' key to ('e' click) existing node to make new edge
		self.currentSlice = 0

		self.displayStateDict = OrderedDict()
		# from older code
		self.displayStateDict['displayThisStack'] = 2
		self.displayStateDict['displaySlidingZ'] = False
		self.displayStateDict['showImage'] = True
		#'showTracing' = True,
		# abb removed
		#self.displayStateDict['triState'] = 0 # 0: all, 1: just nodes, 2: just edges, 3: none
		#self.displayStateDict['showNodes'] = True
		#self.displayStateDict['showEdges'] = True
		# abb removed
		#self.displayStateDict['showDeadEnds'] = True # not used ???
		#
		self.displayStateDict['showNodes'] = True
		self.displayStateDict['showEdges'] = True
		self.displayStateDict['showAnnotations'] = True
		self.displayStateDict['selectedNode'] = None
		self.displayStateDict['selectedEdge'] = None
		self.displayStateDict['selectedSlab'] = None
		self.displayStateDict['selectedAnnotation'] = None
		#
		self.displayStateDict['selectedEdgeList'] = []

		# put this in __init__
		self.myColorLutDict = {}

		pos = np.array([0.0, 0.5, 1.0])
		#
		grayColor = np.array([[0,0,0,255], [128,128,128,255], [255,255,255,255]], dtype=np.ubyte)
		map = pg.ColorMap(pos, grayColor)
		lut = map.getLookupTable(0.0, 1.0, 256)
		self.myColorLutDict['gray'] = lut

		grayColor_r = np.array([[255,255,255,255], [128,128,128,255], [0,0,0,255]], dtype=np.ubyte)
		map = pg.ColorMap(pos, grayColor_r)
		lut = map.getLookupTable(0.0, 1.0, 256)
		self.myColorLutDict['gray_r'] = lut

		greenColor = np.array([[0,0,0,255], [0,128,0,255], [0,255,0,255]], dtype=np.ubyte)
		map = pg.ColorMap(pos, greenColor)
		lut = map.getLookupTable(0.0, 1.0, 256)
		self.myColorLutDict['green'] = lut

		redColor = np.array([[0,0,0,255], [128,0,0,255], [255,0,0,255]], dtype=np.ubyte)
		map = pg.ColorMap(pos, redColor)
		lut = map.getLookupTable(0.0, 1.0, 256)
		self.myColorLutDict['red'] = lut

		blueColor = np.array([[0,0,0,255], [0,0,128,255], [0,0,266,255]], dtype=np.ubyte)
		map = pg.ColorMap(pos, blueColor)
		lut = map.getLookupTable(0.0, 1.0, 256)
		self.myColorLutDict['blue'] = lut

		self.contrastDict = None # assigned in self.slot_contrastChange()

		#
		self._preComputeAllMasks()
		#self.setSlice()

	def mainOptions(self):
		return self.mainWindow.options

	@property
	def options(self):
		return self.mainWindow.options

	def _drawNodes(self):
		#print('myPyQtGraphPlotWidget.drawNodes()')
		if not self.displayStateDict['showNodes']:
			xNodeMasked = []
			yNodeMasked = []
		else:
			showTracingAboveSlices = 3
			showTracingAboveSlices = 3

			index = self.currentSlice
			firstSlice = index - showTracingAboveSlices
			lastSlice = index + showTracingAboveSlices

			aicsNodeList_x = self.maskedEdgesDict['aicsNodeList_x']
			aicsNodeList_y = self.maskedEdgesDict['aicsNodeList_y']
			aicsNodeList_z = self.maskedEdgesDict['aicsNodeList_z']
			aicsNodeList_nodeIdx = self.maskedEdgesDict['aicsNodeList_nodeIdx'] # use for user clicks _onpick

			zNodeMasked = np.ma.masked_inside(aicsNodeList_z, firstSlice, lastSlice) # this unintentionally removes np.nan
			zNodeMasked = zNodeMasked.mask

			xNodeMasked = np.where(zNodeMasked==True, aicsNodeList_x, np.nan)
			yNodeMasked = np.where(zNodeMasked==True, aicsNodeList_y, np.nan)

		#
		# was triggering warning
		#  /Users/cudmore/Sites/bImPy/bImPy_env/lib/python3.7/site-packages/pyqtgraph/graphicsItems/ScatterPlotItem.py:668:
		#  RuntimeWarning: All-NaN slice encountered self.bounds[ax] = (np.nanmin(d) - self._maxSpotWidth*0.7072, np.nanmax(d) + self._maxSpotWidth*0.7072)

		nodePenSize = self.options['Tracing']['nodePenSize']
		#tracingPenSize = self.options['Tracing']['tracingPenSize'] # slabs
		#tracingPenWidth = self.options['Tracing']['tracingPenWidth'] # lines between slabs
		#showTracingAboveSlices = self.options['Tracing']['showTracingAboveSlices']
		#showTracingBelowSlices = self.options['Tracing']['showTracingBelowSlices']

		if np.isnan(xNodeMasked).all() or np.isnan(yNodeMasked).all():
			xNodeMasked = []
			yNodeMasked = []

		#
		# update
		self.myNodePlot.setData(yNodeMasked, xNodeMasked, symbolSize=nodePenSize) # flipped

	def _drawEdges(self):
		#print('myPyQtGraphPlotWidget.drawEdges()')
		if not self.displayStateDict['showEdges']:
			xEdgeMasked = []
			yEdgeMasked = []
		else:
			showTracingAboveSlices = self.mainOptions()['Tracing']['showTracingAboveSlices']
			showTracingBelowSlices = self.mainOptions()['Tracing']['showTracingBelowSlices']

			index = self.currentSlice
			firstSlice = index - showTracingAboveSlices
			lastSlice = index + showTracingBelowSlices

			#
			aicsSlabList_x = self.maskedEdgesDict['aicsSlabList_x']
			aicsSlabList_y = self.maskedEdgesDict['aicsSlabList_y']
			aicsSlabList_z = self.maskedEdgesDict['aicsSlabList_z']

			zMasked = np.ma.masked_inside(aicsSlabList_z, firstSlice, lastSlice) # this unintentionally removes np.nan
			zMasked = zMasked.mask

			nanMasked = np.ma.masked_invalid(aicsSlabList_z) # True if [i] is np.nan
			nanMasked = nanMasked.mask

			finalEdgeMask = np.ma.mask_or(zMasked, nanMasked)

			# always one more step than I expect? Not sure why and really do not understand?
			xEdgeMasked = np.where(finalEdgeMask==True, aicsSlabList_x, np.nan)
			yEdgeMasked = np.where(finalEdgeMask==True, aicsSlabList_y, np.nan)

		#
		# was triggering warning
		#  /Users/cudmore/Sites/bImPy/bImPy_env/lib/python3.7/site-packages/pyqtgraph/graphicsItems/ScatterPlotItem.py:668:
		#  RuntimeWarning: All-NaN slice encountered self.bounds[ax] = (np.nanmin(d) - self._maxSpotWidth*0.7072, np.nanmax(d) + self._maxSpotWidth*0.7072)
		if np.isnan(xEdgeMasked).all() or np.isnan(yEdgeMasked).all():
			xEdgeMasked = []
			yEdgeMasked = []

		#
		# update
		pxMode = True #(default is True) # TOO SLOW IF False !!!!
		tracingPenSize = self.options['Tracing']['tracingPenSize'] # slabs symbolSize
		tracingPenWidth = self.options['Tracing']['tracingPenWidth'] # lines between slabs, pen width
		#if self.myZoom > 5:
		#	tracingPenSize *= 3
		#	tracingPenWidth *= 3
		pen = pg.mkPen(color='c', width=tracingPenWidth) # want to update this to change with user options
		# self.slabPlotParams
		try:
			self.mySlabPlot.setData(yEdgeMasked, xEdgeMasked,
						pen=pen, pxMode=pxMode,
						symbolSize=tracingPenSize, connected='finite') # flipped
			#self.mySlabPlot.setData(yEdgeMasked, xEdgeMasked,
			#			self.slabPlotParams, connected='finite')  # flipped
		except (ValueError) as e:
			print('my ValueError in _drawEdges()')
			print('  e:', e)
			print('  yEdgeMasked:', yEdgeMasked)
			print('  xEdgeMasked:', xEdgeMasked)

	def incrementDecrimentTracing(self, doThis='increase'):
		if doThis == 'increase':
			increment = +1
		elif doThis == 'decrease':
			increment = -1
		else:
			increment = 0
		# nodes
		self.options['Tracing']['nodePenSize'] += increment
		if self.options['Tracing']['nodePenSize'] < 0:
			self.options['Tracing']['nodePenSize'] = 0
		# edges
		self.options['Tracing']['tracingPenSize'] += increment
		if self.options['Tracing']['tracingPenSize'] < 0:
			self.options['Tracing']['tracingPenSize'] = 0
		self.options['Tracing']['tracingPenWidth'] += increment
		if self.options['Tracing']['tracingPenWidth'] < 0:
			self.options['Tracing']['tracingPenWidth'] = 0

		# update
		self.setSlice()

	def _drawAnnotation(self):
		#print('myPyQtGraphPlotWidget.drawNodes()')
		if not self.displayStateDict['showAnnotations']:
			xNodeMasked = []
			yNodeMasked = []
		else:
			showTracingAboveSlices = 3
			showTracingAboveSlices = 3

			index = self.currentSlice
			firstSlice = index - showTracingAboveSlices
			lastSlice = index + showTracingAboveSlices

			annotationMaskDict = self.mySimpleStack.annotationList.getMaskDict()
			if annotationMaskDict is None:
				return
			annotationIndex = annotationMaskDict['annotationIndex'] # use for user clicks _onpick
			xAnnotationArray = annotationMaskDict['x']
			yAnnotationArray = annotationMaskDict['y']
			zAnnotationArray = annotationMaskDict['z']

			zNodeMasked = np.ma.masked_inside(zAnnotationArray, firstSlice, lastSlice) # this unintentionally removes np.nan
			zNodeMasked = zNodeMasked.mask

			xNodeMasked = np.where(zNodeMasked==True, xAnnotationArray, np.nan)
			yNodeMasked = np.where(zNodeMasked==True, yAnnotationArray, np.nan)

		#
		# was triggering warning
		#  /Users/cudmore/Sites/bImPy/bImPy_env/lib/python3.7/site-packages/pyqtgraph/graphicsItems/ScatterPlotItem.py:668:
		#  RuntimeWarning: All-NaN slice encountered self.bounds[ax] = (np.nanmin(d) - self._maxSpotWidth*0.7072, np.nanmax(d) + self._maxSpotWidth*0.7072)

		#nodePenSize = self.options['Tracing']['nodePenSize']

		if np.isnan(xNodeMasked).all() or np.isnan(yNodeMasked).all():
			xNodeMasked = []
			yNodeMasked = []

		#
		# update
		#self.myAnnotationPlot.setData(xNodeMasked, yNodeMasked, symbolSize=nodePenSize)
		self.myAnnotationPlot.setData(yNodeMasked, xNodeMasked) # flipped

	def drawSlabLine(self, slabIdx=None, radius=None):
		"""
		draw one slab as a line orthogonal to edge
		"""
		print('bPyQtGraph.drawSlabLine() slabIdx:', slabIdx)
		if radius is None:
			radius = 12 # pixels
		print('  radius:', radius)

		if slabIdx is None:
			slabIdx = self.selectedSlab()
		if slabIdx is None:
			return

		# todo: could pas edgeIdx as a parameter
		edgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(slabIdx)
		if edgeIdx is None:
			print('warning: myPyQtGraphPlotWidget.drawSlabLine() got bad edgeIdx:', edgeIdx)
			return
		edgeSlabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
		thisSlabIdx = edgeSlabList.index(slabIdx) # index within edgeSlabList
		#print('   edgeIdx:', edgeIdx, 'thisSlabIdx:', thisSlabIdx, 'len(edgeSlabList):', len(edgeSlabList))
		# todo: not sure but pretty sure this will not fail?
		if thisSlabIdx==0 or thisSlabIdx==len(edgeSlabList)-1:
			# we were at a slab that was also a node
			return
		prevSlab = edgeSlabList[thisSlabIdx - 1]
		nextSlab = edgeSlabList[thisSlabIdx + 1]
		this_x, this_y, this_z = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)
		prev_x, prev_y, prev_z = self.mySimpleStack.slabList.getSlab_xyz(prevSlab)
		next_x, next_y, next_z = self.mySimpleStack.slabList.getSlab_xyz(nextSlab)
		dy = next_y - prev_y
		dx = next_x - prev_x
		slope = dy/dx
		slope = dx/dy # flipped
		inverseSlope = -1/slope
		x_ = radius / math.sqrt(slope**2 + 1) #
		y_ = x_ * slope
		#y_ = radius / math.sqrt(slope**2 + 1) # flipped
		#x_ = y_ * slope

		xLine1 = this_x - x_ #
		xLine2 = this_x + x_

		yLine1 = this_y + y_
		yLine2 = this_y - y_
		#yLine1 = this_y - y_ # PyQtGraph
		#yLine2 = this_y + y_

		xSlabPlot = [xLine1, xLine2]
		ySlabPlot = [yLine1, yLine2]
		'''
		print('selectSlab() slabIdx:', slabIdx, 'slope:', slope, 'inverseSlope:', inverseSlope)
		print('   slope:', slope, 'inverseSlope:', inverseSlope)
		print('   xSlabPlot:', xSlabPlot)
		print('   ySlabPlot:', ySlabPlot)
		'''
		# was this
		#self.mySlabLinePlot.set_xdata(ySlabPlot) # flipped
		#self.mySlabLinePlot.set_ydata(xSlabPlot)
		#print('  bPyQtGraph.drawSlabLine() xSlabPlot:', xSlabPlot, 'ySlabPlot:', ySlabPlot)
		self.mySlabPlotOne.setData(ySlabPlot, xSlabPlot) # flipped

		displayThisStack = self.displayStateDict['displayThisStack']
		profileDict = {
			'xSlabPlot': xSlabPlot,
			'ySlabPlot': ySlabPlot,
			'displayThisStack': displayThisStack,
			'slice': self.currentSlice,
		}

		self.mainWindow.signal('update line profile', profileDict)
		# todo: implement this

		#
		# emit
		selectededge = self.selectedEdge()
		myEvent = bimpy.interface.bEvent('select edge', edgeIdx=selectededge, slabIdx=slabIdx)
		self.selectEdgeSignal.emit(myEvent)

	def cancelSelection(self):
		#print('myPyQtGraphPlotWidget.cancelSelection()')
		self.selectNode(None, doEmit=True)
		self.selectEdge(None, doEmit=True)
		self.selectSlab(None, doEmit=True)
		self.selectAnnotation(None, doEmit=True)

		self.displayStateDict['selectedNode'] = None
		self.displayStateDict['selectedEdge'] = None
		self.displayStateDict['selectedSlab'] = None
		self.displayStateDict['selectedAnnotation'] = None
		#
		self.displayStateDict['selectedEdgeList'] = []

	def selectedNode(self):
		return self.displayStateDict['selectedNode']
	def selectedEdge(self):
		return self.displayStateDict['selectedEdge']
	def selectedSlab(self):
		return self.displayStateDict['selectedSlab']
	def selectedAnnotation(self):
		return self.displayStateDict['selectedAnnotation']

	def selectNode(self, nodeIdx, snapz=False, isShift=False, doEmit=False):

		if nodeIdx is not None:
			nodeIdx = int(nodeIdx)

		self.displayStateDict['selectedNode'] = nodeIdx

		if nodeIdx is None:
			x = []
			y = []
			self.myNodePlotSelection.setData(y, x) # flipped
		else:

			x,y,z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)

			if snapz:
				z = int(z)
				self.setSlice(z)

				#self._zoomToPoint(x, y)
				self._zoomToPoint(y, x) # flipped

			# update
			x = [x]
			y = [y]
			self.myNodePlotSelection.setData(y, x) # flipped

			QtCore.QTimer.singleShot(20, lambda:self.flashNode(nodeIdx, 2))

		#
		if doEmit:
			myEvent = bimpy.interface.bEvent('select node', nodeIdx=nodeIdx)
			self.selectNodeSignal.emit(myEvent)

	def selectEdge(self, edgeIdx, snapz=False, isShift=False, doEmit=False):

		if edgeIdx is not None:
			edgeIdx = int(edgeIdx)

		self.displayStateDict['selectedEdge'] = edgeIdx

		if edgeIdx is None:
			xMasked = []
			yMasked = []
			self.mySlabPlotSelection.setData(yMasked, xMasked, symbolBrush=None) # flipped
		else:

			theseIndices = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)

			xMasked = self.mySimpleStack.slabList.x[theseIndices]
			yMasked = self.mySimpleStack.slabList.y[theseIndices]

			#print('xMasked:', xMasked)
			#print('yMasked:', yMasked)

			if snapz:
				#tmpEdgeDict = self.mySimpleStack.slabList.getEdge(edgeIdx)
				#z = tmpEdgeDict['z']
				z = self.mySimpleStack.slabList.edgeDictList[edgeIdx]['z']
				z = int(z)
				self.setSlice(z)

				# snap to point
				# get the (x,y) of the middle slab
				tmpEdgeDict = self.mySimpleStack.slabList.getEdge(edgeIdx)
				tmp_nSlab = tmpEdgeDict['nSlab']
				middleSlab = int(tmp_nSlab/2)
				middleSlabIdx = tmpEdgeDict['slabList'][middleSlab]
				tmpx, tmpy, tmpz = self.mySimpleStack.slabList.getSlab_xyz(middleSlabIdx)
				self._zoomToPoint(tmpy, tmpx) # flipped

			# update
			pen = pg.mkPen(color='y', width=3)
			self.mySlabPlotSelection.setData(yMasked, xMasked, pen=pen, symbolBrush=('y'), connected='finite') # flipped

			QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, 2))

		#
		if doEmit:
			myEvent = bimpy.interface.bEvent('select edge', edgeIdx=edgeIdx)
			self.selectEdgeSignal.emit(myEvent)

	def selectEdgeList(self, edgeList):
		colorList = ['r', 'g', 'b', 'm']

		self.displayStateDict['selectedEdgeList'] = []

		xList = []
		yList = []
		#slabList = []
		symbolBrushList = []
		colorIdx = 0
		for idx, edgeIdx in enumerate(edgeList):
			theseIndices = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
			numIndices = len(theseIndices)

			#slabList += theseIndices

			xList += self.mySimpleStack.slabList.x[theseIndices].tolist()
			yList += self.mySimpleStack.slabList.y[theseIndices].tolist()

			# make a list of pg.mkColor using colorList[idx]
			symbolBrushList += [pg.mkColor(colorList[colorIdx]) for tmp in range(numIndices)]

			xList.append(np.nan)
			yList.append(np.nan)
			symbolBrushList.append(pg.mkColor('w'))

			self.displayStateDict['selectedEdgeList'] += [edgeIdx]

			colorIdx += 1
			if colorIdx > len(colorList)-1:
				colorIdx = 0

		#x = self.mySimpleStack.slabList.x[slabList]
		#y = self.mySimpleStack.slabList.y[slabList]

		self.mySlabPlotSelection.setData(yList, xList, symbolBrush=symbolBrushList) # flipped

		#QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, 2))

	def selectSlab(self, slabIdx, snapz=False, doEmit=False):

		if slabIdx is not None:
			slabIdx = int(slabIdx)

		self.displayStateDict['selectedSlab'] = slabIdx

		if slabIdx is None or np.isnan(slabIdx):
			self.displayStateDict['selectedSlab'] = None
			#self.mySlabSelectionPlot.set_offsets(np.c_[[], []])
			#self.mySlabLinePlot.set_xdata([])
			#self.mySlabLinePlot.set_ydata([])
			self.mySlabPlotSelection2.setData([], [])
			self.mySlabPlotOne.setData([], [])

		else:
			# only if we are showing the line profile panel
			if not self.options['Panels']['showLineProfile']:
				return

			x,y,z = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)

			if snapz:
				z = int(z)
				self.setSlice(z)

			x = [x]
			y = [y]

			print('  selectSlab() slabIdx:', slabIdx, 'x:', x, 'y:', y)

			# update
			self.mySlabPlotSelection2.setData(y, x) # flipped

			# todo: put this back in
			# update display
			'''
			linewidth = self.options['Tracing']['lineProfileLineSize']
			markersize = self.options['Tracing']['lineProfileMarkerSize']
			c = self.options['Tracing']['lineProfileColor']
			self.mySlabLinePlot.set_linewidth(linewidth)
			self.mySlabLinePlot.set_markersize(markersize)
			self.mySlabLinePlot.set_color(c)
			'''

			#
			# draw the orthogonal line
			self.drawSlabLine(slabIdx)

		#
		if doEmit:
			edgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(slabIdx)
			myEvent = bimpy.interface.bEvent('select edge', edgeIdx=edgeIdx, slabIdx=slabIdx)
			self.selectEdgeSignal.emit(myEvent)

	def selectAnnotation(self, annotationIdx, snapz=False, isShift=False, doEmit=False):

		if annotationIdx is not None:
			annotationIdx = int(annotationIdx)

		self.displayStateDict['selectedAnnotation'] = annotationIdx

		if annotationIdx is None:
			x = []
			y = []
			self.myAnnotationPlotSelection.setData(y, x) # flipped
		else:
			#x,y,z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)
			x, y, z = self.mySimpleStack.annotationList.getAnnotation_xyz(annotationIdx)

			if snapz:
				z = int(z)
				self.setSlice(z)

				self._zoomToPoint(x, y)

			# update
			x = [x]
			y = [y]
			self.myAnnotationPlotSelection.setData(y, x) # flipped

			QtCore.QTimer.singleShot(20, lambda:self.flashAnnotation(annotationIdx, 2))

		if doEmit:
			myEvent = bimpy.interface.bEvent('select annotation', nodeIdx=annotationIdx)
			self.selectAnnotationSignal.emit(myEvent)

	def flashNode(self, nodeIdx, numberOfFlashes):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashNode() nodeIdx:', nodeIdx, 'numberOfFlashes:', numberOfFlashes)
		if nodeIdx is None:
			return
		if numberOfFlashes>0:
			if self.mySimpleStack.slabList is not None:
				x, y, z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)
				x = [x]
				y = [y]
				self.myNodeSelectionFlash.setData(y, x) # flipped
				#self.myNodeSelectionFlash.set_offsets(np.c_[y, x])
				#
				QtCore.QTimer.singleShot(20, lambda:self.flashNode(nodeIdx, numberOfFlashes-1))
		else:
			self.myNodeSelectionFlash.setData([], [])
			#self.myNodeSelectionFlash.set_offsets(np.c_[[], []])
		#
		#self.repaint() # this is updating the widget !!!!!!!!

	def flashEdge(self, edgeIdx, on):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashEdge() edgeIdx:', edgeIdx, on)
		if edgeIdx is None:
			return
		if on:
			if self.mySimpleStack.slabList is not None:
				theseIndices = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
				xMasked = self.mySimpleStack.slabList.x[theseIndices]
				yMasked = self.mySimpleStack.slabList.y[theseIndices]
				self.myEdgeSelectionFlash.setData(yMasked, xMasked) # flipped
				#self.myEdgeSelectionFlash.set_offsets(np.c_[xMasked, yMasked])
				#
				QtCore.QTimer.singleShot(20, lambda:self.flashEdge(edgeIdx, False))
		else:
			self.myEdgeSelectionFlash.setData([], [])
			#self.myEdgeSelectionFlash.set_offsets(np.c_[[], []])

	def flashAnnotation(self, annotationIdx, numberOfFlashes):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashNode() nodeIdx:', nodeIdx, 'numberOfFlashes:', numberOfFlashes)
		if annotationIdx is None:
			return
		if numberOfFlashes>0:
			if self.mySimpleStack.slabList is not None:
				#x, y, z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)
				x, y, z = self.mySimpleStack.annotationList.getAnnotation_xyz(annotationIdx)
				x = [x]
				y = [y]
				self.myAnnotationSelectionFlash.setData(y, x) # flipped
				#self.myNodeSelectionFlash.set_offsets(np.c_[y, x])
				#
				QtCore.QTimer.singleShot(20, lambda:self.flashAnnotation(annotationIdx, numberOfFlashes-1))
		else:
			self.myAnnotationSelectionFlash.setData([], [])
			#self.myNodeSelectionFlash.set_offsets(np.c_[[], []])
		#
		#self.repaint() # this is updating the widget !!!!!!!!

	def _preComputeAllMasks(self):
		self.maskedEdgesDict = self.mySimpleStack.slabList._preComputeAllMasks()

		#self.maskedAnnotationDict = self.mySimpleStack.annotationList._preComputeMasks()

		self.setSlice() #refresh

	def setSlice(self, thisSlice=None):

		#timeIt = bimpy.util.bTimer(' setSlice()')

		if thisSlice is None:
			thisSlice = self.currentSlice
		else:
			self.currentSlice = thisSlice

		maxNumChannels = self.mySimpleStack.maxNumChannels

		#
		# image
		if self.displayStateDict['showImage']:
			displayThisStack = self.displayStateDict['displayThisStack'] # (1,2,3, ... 5,6,7)

			#print('=== myPyQtGraphPlotWidget.setSlice() displayThisStack:', displayThisStack)

			sliceImage = None
			autoLevels = True
			levels = None

			if displayThisStack == 'rgb':
				sliceImage1 = self.mySimpleStack.getImage2(channel=1, sliceNum=thisSlice)
				if sliceImage1 is None:
					print('errror setSlice() showing rgb, sliceImage1 is None')
					return False
				sliceImage2 = self.mySimpleStack.getImage2(channel=2, sliceNum=thisSlice)
				if sliceImage2 is None:
					print('errror setSlice() showing rgb, sliceImage2 is None')
					return False
				m = sliceImage1.shape[0]
				n = sliceImage1.shape[1]
				dtype = sliceImage1.dtype # assuming both have same dtype
				sliceImage = np.ndarray((m,n,3), dtype=dtype)
				# assuming we want channel 1 as green and channel 2 as magenta
				sliceImage[:,:,0] = sliceImage2 # red
				sliceImage[:,:,1] = sliceImage1 # green
				sliceImage[:,:,2] = sliceImage2 # blue
			elif self.displayStateDict['displaySlidingZ']:
				upSlices = self.options['Stack']['upSlidingZSlices']
				downSlices = self.options['Stack']['downSlidingZSlices']
				#print('upSlices:', upSlices, 'downSlices:', downSlices)
				sliceImage = self.mySimpleStack.getSlidingZ2(displayThisStack, thisSlice, upSlices, downSlices)
			elif displayThisStack > maxNumChannels: #in [5,6,7,8]:
				# mask + image ... need to set contrast of [0,1] mask !!!
				sliceMaskImage = self.mySimpleStack.getImage2(channel=displayThisStack, sliceNum=thisSlice)
				if sliceMaskImage is None:
					print('warning: got None sliceMaskImage for displayThisStack:', displayThisStack)
				else:
					#imageChannel = displayThisStack-maxNumChannels
					imageChannel = displayThisStack % maxNumChannels # remainder after division
					#print('bPyQtGraph.setSlice() imageChannel:', imageChannel)
					sliceChannelImage = self.mySimpleStack.getImage2(channel=imageChannel, sliceNum=thisSlice)
					skelChannel = displayThisStack + maxNumChannels
					sliceSkelImage = self.mySimpleStack.getImage2(channel=skelChannel, sliceNum=thisSlice)
					m = sliceMaskImage.shape[0]
					n = sliceMaskImage.shape[1]
					sliceImage = np.zeros((m,n,3), dtype=np.uint8)
					# assuming we want channel 1 as green and channel 2 as magenta
					sliceImage[:,:,0] = sliceChannelImage # red
					if sliceSkelImage is not None:
						sliceImage[:,:,1] = sliceSkelImage # green
					sliceImage[:,:,2] = sliceMaskImage # blue
					# contrast for [0,1] mask
					autoLevels = False
					levels = [[0,255], [0,2], [0,2]]
					#self.myImage.setLevels(levels, update=True)
			else:
				sliceImage = self.mySimpleStack.getImage2(channel=displayThisStack, sliceNum=thisSlice)

			if sliceImage is None:
				#print('setSlice() got None image for displayThisStack:', displayThisStack, 'thisSlice:', thisSlice)
				sliceImage = np.ndarray((1,1,1), dtype=np.uint8)

			# use fliplr if using
			#   pg.setConfigOption('imageAxisOrder','row-major')
			#   self.getViewBox().invertX(True)
			#   self.getViewBox().invertY(True)
			#sliceImage = np.fliplr(sliceImage)
			#no sliceImage = np.flipud(sliceImage)

			self.myImage.setImage(sliceImage, levels=levels, autoLevels=autoLevels)

			# todo: fix this and put back in
			if displayThisStack in [1,2,3]:
				if self.contrastDict is not None:
					minContrast = self.contrastDict['minContrast']
					maxContrast = self.contrastDict['maxContrast']
					self.myImage.setLevels([minContrast,maxContrast], update=True)

					colorLutStr = self.contrastDict['colorLut']
					colorLut = self.myColorLutDict[colorLutStr] # like (green, red, blue, gray, gray_r, ...)
					self.myImage.setLookupTable(colorLut, update=True)

		else:
			#print('not showing image')
			fakeImage = np.ndarray((1,1,1), dtype=np.uint8)
			self.myImage.setImage(fakeImage)

		# plot slabs/nodes
		self._drawEdges()
		self._drawNodes()
		self._drawAnnotation()

		#print(timeIt.elapsed())

		#
		# force update?
		self.update()

	'''
	def setStackDisplay(self, stackNumber):
		"""
		stackNumber: (1,2,3, ... 5,6,7)
		"""
		self.displayStateDict['displayThisStack'] = stackNumber
		self.setSlice() # just refresh
	'''

	def editNote(self):
		'''
		windowTitle = 'xxx'
		dialogLabel = 'yyy'
		text = 'zzz'
		text, ok = QtWidgets.QInputDialog.getText(self, windowTitle, dialogLabel, text=text)
		if ok:
			print('text:', text)
		else:
			print('cancelled by user')
		'''

		selectedNodeIdx = self.selectedNode()
		selectedEdgeIdx = self.selectedEdge()
		selectedAnnotationIdx = self.selectedAnnotation()
		if selectedNodeIdx is not None:
			dialogTitle = f'Edit note for node {selectedNodeIdx}'
			dialogLabel = dialogTitle
			existingNote = self.mySimpleStack.slabList.getNode(selectedNodeIdx)['note']
			text, ok = QtWidgets.QInputDialog.getText(self, dialogTitle, dialogLabel, text=existingNote)
			if ok:
				self.mySimpleStack.slabList.getNode(selectedNodeIdx)['note'] = text
				#
				newNodeDict = self.mySimpleStack.slabList.getNode(selectedNodeIdx)
				myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=selectedNodeIdx, nodeDict=newNodeDict)
				self.tracingEditSignal.emit(myEvent)
			else:
				print('cancelled by user')
		elif selectedEdgeIdx is not None:
			dialogTitle = f'Edit note for edge {selectedEdgeIdx}'
			dialogLabel = dialogTitle
			existingNote = self.mySimpleStack.slabList.getEdge(selectedEdgeIdx)['note']
			text, ok = QtWidgets.QInputDialog.getText(self, dialogTitle, dialogLabel, text=existingNote)
			if ok:
				self.mySimpleStack.slabList.getEdge(selectedEdgeIdx)['note'] = text
				#
				newEdgeDict = self.mySimpleStack.slabList.getEdge(selectedEdgeIdx)
				myEvent = bimpy.interface.bEvent('updateEdge', edgeIdx=selectedEdgeIdx, edgeDict=newEdgeDict)
				self.tracingEditSignal.emit(myEvent)
			else:
				print('cancelled by user')
		elif selectedAnnotationIdx is not None:
			dialogTitle = f'Edit note for annotation {selectedAnnotationIdx}'
			dialogLabel = dialogTitle
			existingNote = self.mySimpleStack.annotationList.getItemDict(selectedAnnotationIdx)['note']
			text, ok = QtWidgets.QInputDialog.getText(self, dialogTitle, dialogLabel, text=existingNote)
			if ok:
				self.mySimpleStack.annotationList.getItemDict(selectedAnnotationIdx)['note'] = text
				#
				newAnnotationDict = self.mySimpleStack.annotationList.getItemDict(selectedAnnotationIdx)
				myEvent = bimpy.interface.bEvent('updateAnnotation', nodeIdx=selectedAnnotationIdx, nodeDict=newAnnotationDict)
				self.tracingEditSignal.emit(myEvent)
			else:
				print('cancelled by user')

	def _zoomToPoint(self, x, y):
		"""
		ALREADY FLIPPED !!!!

		see code at: https://pyqtgraph.readthedocs.io/en/latest/_modules/pyqtgraph/widgets/GraphicsView.html#GraphicsView
		"""
		#print('=== zoomToPoint()')

		# This works !!!!!!!!!!!!!!
		zoomPoint = QtCore.QPoint(x, y)
		viewRect = self.viewRect()
		viewRect.moveCenter(zoomPoint)
		padding = 0.0
		self.setRange(viewRect, padding=padding)

		print('  zoomPoint:', type(zoomPoint), zoomPoint)
		print('  viewRect:', type(viewRect), viewRect)

	def _myTranslate(self, direction):
		"""
		pan image in response to arrow keys
		"""
		print('myTranslate() direction:', direction)
		print('  not implemented')
		return

		[xRange, yRange] = self.viewRange()
		xWidth = xRange[1] - xRange[0]
		yWidth = yRange[1] - yRange[0]
		xTenPercent = xWidth * 0.01
		yTenPercent = yWidth * 0.01

		if direction == 'left':
			t = (-xTenPercent,0)
			self.translateBy(t=t)
		elif direction == 'right':
			t = (xTenPercent,0)
			self.translateBy(t=t)
		elif direction == 'up':
			t = (0,-yTenPercent)
			self.translateBy(t=t)
		elif direction == 'down':
			t = (0,yTenPercent)
			self.translateBy(t=t)

	def _setFullView(self):
		imageBoundingRect = self.myImage.boundingRect()
		padding = 0.0
		self.setRange(imageBoundingRect, padding=padding)
		self.myZoom = 1

	'''
	def mousePressEvent(self, event):
		"""
		This is a PyQt callback (not PyQtGraph)
		Set event.setAccepted(False) to keep propogation so we get to PyQt callbacks like
			self.onMouseClicked_scene(), _slabs(), _nodes()
		"""
		#print('mousePressEvent() event:', event)
		if event.button() == QtCore.Qt.RightButton:
			#print('myPyQtGraphPlotWidget.mousePressEvent() right click !!!')
			pos = self.mapToScene(event.pos())
			pos = QtCore.QPoint(pos.x(), pos.y())
			#pos = event.pos()
			print('pos:', type(pos), pos)
			self.mainWindow.showRightClickMenu(pos)
			self.mouseReleaseEvent(event)
		else:
			event.setAccepted(False)
			super().mousePressEvent(event)
	'''

	def mouseReleaseEvent(self, event):
		event.setAccepted(False)
		super().mouseReleaseEvent(event)

	def keyPressEvent(self, event):
		"""
		event: <PyQt5.QtGui.QKeyEvent object at 0x13e1f7410>
		"""

		# event.key() is a number
		if event.text() != 'e':
			print(f'=== myPyQtGraphPlotWidget.keyPressEvent() event.text() "{event.text()}"')

		# this works to print 'left', 'right' etc etc
		# but raises 'UnicodeEncodeError' for others
		#print('  ', QtGui.QKeySequence(event.key()).toString())

		# to catch 'e' for new edge and 'a' for new annotation
		self.keyIsDown = event.text()

		# command/option/control
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		isControl = modifiers == QtCore.Qt.ControlModifier # on macOS, this is 'command' (e.g. open-apple)

		if event.key() in [QtCore.Qt.Key_Escape]:
			self.cancelSelection()

		elif event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
			self._setFullView()

		elif event.key() in [QtCore.Qt.Key_D, QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
			event = {'type':'deleteSelection'}
			self.myEvent(event)

		elif event.key() in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			selectedSlabIdx = self.selectedSlab()
			if selectedSlabIdx is not None:
				tmpEdgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(selectedSlabIdx)
				if tmpEdgeIdx is None:
					print('warning: move to next/prev slab got bad edge idx:', tmpEdgeIdx)
					return
				tmpSlabList = self.mySimpleStack.slabList.getEdgeSlabList(tmpEdgeIdx) # abb aics, get all including nodes
				try:
					slabIdxInList = tmpSlabList.index(selectedSlabIdx)
				except (ValueError) as e:
					print('warning: bStackWidget.keyPressEvent() did not find slabIdx:', selectedSlabIdx, 'in edge', tmpEdgeIdx, 'list:', tmpSlabList)
					return
				if event.key() == QtCore.Qt.Key_Left:
					slabIdxInList -= 1
				elif event.key() == QtCore.Qt.Key_Right:
					slabIdxInList += 1
				#print('  moving to slabIdxInList:', slabIdxInList)
				if slabIdxInList==0 or slabIdxInList==len(tmpSlabList)-1:
					print('  --> at end of edge', tmpEdgeIdx)
					return
				try:
					newSlabIdx = tmpSlabList[slabIdxInList]
				except (IndexError) as e:
					print('  at end of edge', tmpEdgeIdx)
					return
				print('  --> selecting slab:', newSlabIdx, 'slab number', slabIdxInList+1, 'of', len(tmpSlabList), 'in edge', tmpEdgeIdx)
				self.selectSlab(newSlabIdx, snapz=True)
			else:
				# arrow key should either pan image or scroll slices
				if event.key() in [QtCore.Qt.Key_Left]:
					if self.selectedSlab() is None:
						self._myTranslate('left')
				elif event.key() in [QtCore.Qt.Key_Right]:
					if self.selectedSlab() is None:
						self._myTranslate('right')

				# abb aics
				'''
				if key == QtCore.Qt.Key_Left:
					self.currentSlice -= 1
				else:
					self.currentSlice += 1
				self.setSlice(self.currentSlice)
				#self.displayStateChangeSignal.emit('set slice', self.currentSlice)
				self.setSliceSignal.emit('set slice', self.currentSlice)
				'''
		# choose which stack to display
		elif event.key() == QtCore.Qt.Key_1:
			self.displayStateChange('displayThisStack', value=1)
			#self.setStackDisplay(1)
		elif event.key() == QtCore.Qt.Key_2:
			self.displayStateChange('displayThisStack', value=2)
			#self.setStackDisplay(2)
		elif event.key() == QtCore.Qt.Key_3:
			self.displayStateChange('displayThisStack', value=2)
			#self.setStackDisplay(3)

		# masks
		elif event.key() == QtCore.Qt.Key_5:
			self.displayStateChange('displayThisStack', value=5)
			#self.setStackDisplay(5)
		elif event.key() == QtCore.Qt.Key_6:
			self.displayStateChange('displayThisStack', value=6)
			#self.setStackDisplay(6)
		# todo: put this back in
		#elif event.key() == QtCore.Qt.Key_7:
		#	self.setStackDisplay(7)

		# old
		#elif 0 and event.key() == QtCore.Qt.Key_9:
		#	# not implemented (was for deepvess)
		#	if self.mySimpleStack._imagesSkel is not None:
		#		#self.displayThisStack = 'skel'
		#		self.displayStateDict['displayThisStack'] = 'skel'
		#		self.setSlice() # just refresh

		# old
		#elif 0 and event.key() == QtCore.Qt.Key_0:
		#	if 1: #self.mySimpleStack._imagesMask is not None:
		#		#self.displayThisStack = 'mask'
		#		self.displayStateDict['displayThisStack'] = 'mask'
		#		self.setSlice() # just refresh

		elif event.key() in [QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal]:
			# increase tracing
			self.incrementDecrimentTracing('increase')
		elif event.key() == QtCore.Qt.Key_Minus:
			# increase tracing
			self.incrementDecrimentTracing('decrease')

		elif event.key() == QtCore.Qt.Key_J:
			event = {'type':'joinTwoEdges'}
			self.myEvent(event)

		elif event.key() in [QtCore.Qt.Key_N]:
			# set note of selected item
			self.editNote()

		elif event.key() in [QtCore.Qt.Key_R]:
			self._preComputeAllMasks()

		elif isControl and event.key() == QtCore.Qt.Key_S:
			self.mainWindow.signal('save')

		elif event.key() in [QtCore.Qt.Key_T]:
			# todo: use this after adding deferUpdate=True
			#  self.displayStateChange('showNodes', toggle=True)
			self.displayStateDict['showNodes'] = not self.displayStateDict['showNodes']
			self.displayStateDict['showEdges'] = not self.displayStateDict['showEdges']
			self.displayStateDict['showAnnotations'] = not self.displayStateDict['showAnnotations']
			self.setSlice() # refresh

		elif event.key() in [QtCore.Qt.Key_Z]:
			self.displayStateChange('displaySlidingZ', toggle=True)

		else:
			# if not handled by *this, this will continue propogation
			event.setAccepted(False)

	def keyReleaseEvent(self, event):
		#print(f'=== keyReleaseEvent() event.text() {event.text()}')
		self.keyIsDown = None

	# this is over-riding existing member function
	def wheelEvent(self, event):
		"""
		event: <PyQt5.QtGui.QWheelEvent object at 0x11d486910>
		"""

		'''
		print('=== wheelEvent()')
		print('  event:', event)
		'''

		#print('  angleDelta:', event.angleDelta().y())
		#print('  pixelDelta:', event.pixelDelta().y())

		yAngleDelta = event.angleDelta().y()
		mouseUp = False
		mouseDown = False
		if yAngleDelta > 0:
			# zoom in
			mouseUp = True
		elif yAngleDelta < 0:
			# zoom out
			mouseDown = True

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		if modifiers == QtCore.Qt.ControlModifier:
			# zoom in/out with mouse
			super(myPyQtGraphPlotWidget, self).wheelEvent(event)

			'''
			viewRect = self.viewRect()
			print('  - viewRect:', viewRect)
			print('  viewRect.width():', viewRect.width())
			print('  viewRect.height():', viewRect.height())
			'''

			'''
			sceneViewRect = self.scene().sceneRect() # does not change
			print('  - sceneViewRect:', sceneViewRect)
			print('  sceneViewRect.width():', sceneViewRect.width())
			print('  sceneViewRect.height():', sceneViewRect.height())
			'''
			if mouseUp:
				self.myZoom += 1
			elif mouseDown:
				self.myZoom -= 1
			#print('  self.myZoom:', self.myZoom)

		else:
			# set slice
			yAngleDelta = event.angleDelta().y()
			#print('yAngleDelta:', yAngleDelta)
			# getting yAngleDelta==0 on macbook laptop trackpad?
			if yAngleDelta > 0:
				# mouse up
				self.currentSlice -= 1
				if self.currentSlice < 0:
					self.currentSlice = 0
			if yAngleDelta < 0:
				# mouse down
				self.currentSlice += 1
				if self.currentSlice > self.mySimpleStack.numSlices-1:
					self.currentSlice -= 1

			#print(event.angleDelta().y()) # always +/- the same value
			#print(event.pixelDelta().y()) # +/- and larger magnitude, if >100 then got by 5 !!!

			self.setSlice()

			self.setSliceSignal.emit('set slice', self.currentSlice)

	def onMouseClicked_scene(self, event):
		eKeyIsDown = self.keyIsDown == 'e'

		print('=== onMouseClicked_scene()', event.pos().x(), event.pos().y(), 'eKeyIsDown:', eKeyIsDown)

		#imagePos = self.myImage.mapFromScene(event.pos())
		imagePos = self.myImage.mapFromScene(event.pos())
		slabPos = self.mySlabPlot.mapFromScene(event.pos())

		#print('  self.getViewBox():', self.getViewBox())

		x = imagePos.x()
		y = imagePos.y()
		z = self.currentSlice

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		isControl = modifiers == QtCore.Qt.ControlModifier # on macOS, this is 'command' (e.g. open-apple)

		oldSelectedNode = self.selectedNode()
		oldSelectedEdge = self.selectedEdge()
		if eKeyIsDown and oldSelectedNode is not None:
			print('  onMouseClicked_scene() new edge from oldSelectedNode:', oldSelectedNode)

			#newNodeIdx = self.mySimpleStack.slabList.newNode(x, y, self.currentSlice)
			newNodeEvent = {'type':'newNode','x':y,'y':x,'z':z} # flipped
			newNodeIdx = self.myEvent(newNodeEvent)

			#newEdgeIdx = self.mySimpleStack.slabList.newEdge(oldSelectedNode, newNodeIdx)
			newEdgeEvent = {'type':'newEdge','srcNode':oldSelectedNode, 'dstNode':newNodeIdx}
			newEdgeIdx = self.myEvent(newEdgeEvent)

			self.selectNode(None) # cancel self.selectedNode()
			self.selectEdge(newEdgeIdx) # select the new edge

			self._preComputeAllMasks()

		elif isShift:
			if self.selectedEdge() is not None:
				if self.options['Panels']['showLineProfile']:
					# new slab
					print('\n=== bStackWidget.onclick_mpl() new slab ...')
					newSlabEvent = {'type':'newSlab','edgeIdx':self.selectedEdge(), 'x':y, 'y':x, 'z':z} # flipped
					# abb removed???
					self.myEvent(newSlabEvent)
				else:
					print('To add slabs, open the line profile panel with keyboard "l"')
			else:
				# new node
				print('  onMouseClicked_scene() new node')
				#newNodeIdx = self.mySimpleStack.slabList.newNode(x, y, self.currentSlice)
				newNodeEvent = {'type':'newNode','x':y,'y':x,'z':z} # flipped
				newNodeIdx = self.myEvent(newNodeEvent)

				self._preComputeAllMasks()

		elif isControl:
			# abb aics
			# extend to multiple selections
			pass

		elif self.keyIsDown == 'a':
			# new annotation
			self.newAnnotation(y, x, z) # flipped

	def onMouseMoved_scene(self, pos):

		doDebug = False

		if doDebug: print('=== onMouseMoved_scene()')
		if doDebug: print('       pos:', pos)

		imagePos = self.myImage.mapFromScene(pos)

		if doDebug: print('  imagePos:', imagePos)

		xPos = imagePos.x()
		yPos = imagePos.y()
		#thePoint = QtCore.QPoint(xPos, yPos)

		displayThisStack = self.displayStateDict['displayThisStack'] # (ch1, ch2, ch2, rgb)
		if doDebug: print('       displayThisStack:', displayThisStack, type(displayThisStack))

		if displayThisStack == 'RGB':
			# don't do this
			return

		self.mainWindow.getStatusToolbar().setMousePosition(displayThisStack, self.currentSlice, yPos, xPos) # flipped

	'''
	def sceneClicked(self, event):
		print('=== sceneClicked() event:', event)


		# see: https://stackoverflow.com/questions/27222016/pyqt-mousepressevent-get-object-that-was-clicked-on
		#items = w.scene().items(event.scenePos())
		#print "Plots:", [x for x in items if isinstance(x, pg.PlotItem)]
		items = self.mySlabPlotWidget.scene().items(event.scenePos())
		#print("Plots:", [x for x in items if isinstance(x, pg.PlotItem)])
		for x in items:
			if isinstance(x, pg.PlotItem):
				print('  ', x)
	'''

	def onMouseClicked_slabs(self, item, points):
		"""
		get edge index from displayed masked edges

		item: self.mySlabPlot
		points: [<pyqtgraph.graphicsItems.ScatterPlotItem.SpotItem object at 0x13cdb6f10>]
		"""

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		isControl = modifiers == QtCore.Qt.ControlModifier # on macOS, this is 'command' (e.g. open-apple)

		# this works gives me the point number!!!!
		thePoint = points[0].index()

		aicsSlabList_edgeIdx = self.maskedEdgesDict['aicsSlabList_edgeIdx']
		selectedEdgeIdx = aicsSlabList_edgeIdx[thePoint]
		selectedEdgeIdx = int(selectedEdgeIdx) # todo: fix this constant problem

		aicsSlabList_slabIdx = self.maskedEdgesDict['aicsSlabList_slabIdx']
		selectedSlabIdx = aicsSlabList_slabIdx[thePoint]
		selectedSlabIdx = int(selectedSlabIdx) # todo: fix this constant problem

		print('=== onMouseClicked_slabs() thePoint:', thePoint, 'selectedEdgeIdx:', selectedEdgeIdx, 'selectedSlabIdx:', selectedSlabIdx)

		if isControl:
			# append to selectedEdgeList list,
			# remember, selectEdgeList() resets self.displayStateDict['selectedEdgeList']
			selectedEdgeList = self.displayStateDict['selectedEdgeList']
			selectedEdgeList += [selectedEdgeIdx]
			self.selectEdgeList(selectedEdgeList)
		else:
			self.selectEdge(selectedEdgeIdx)
			self.selectSlab(selectedSlabIdx)

		# emit
		myEvent = bimpy.interface.bEvent('select edge', edgeIdx=selectedEdgeIdx, slabIdx=selectedSlabIdx)
		self.selectEdgeSignal.emit(myEvent)

	def onMouseClicked_annotations(self, item, points):
		thePoint = points[0].index()
		print('=== onMouseClicked_annotations() thePoint:', thePoint)

		# get
		annotationMaskDict = self.mySimpleStack.annotationList.getMaskDict()

		#print(self.maskedAnnotationDict['annotationIndex'])

		annotationIndex = annotationMaskDict['annotationIndex'][thePoint]
		x = annotationMaskDict['x'][thePoint]
		y = annotationMaskDict['y'][thePoint]
		z = annotationMaskDict['z'][thePoint]
		print(f'  annotationIndex:{annotationIndex}, x:{x}, y:{y}, z:{z}')

		self.selectAnnotation(annotationIndex)

		# emit
		myEvent = bimpy.interface.bEvent('select annotation', nodeIdx=annotationIndex)
		self.selectAnnotationSignal.emit(myEvent)

	def onMouseClicked_nodes(self, item, points):
		"""
		get node index from displayed masked node

		item: self.myNodePlot
		points: [<pyqtgraph.graphicsItems.ScatterPlotItem.SpotItem object at 0x13cdb6f10>]
		"""

		# check if 'e' key is down
		#modifiers = QtWidgets.QApplication.keyboardModifiers()
		#isShift = modifiers == QtCore.Qt.ShiftModifier
		eKeyIsDown = self.keyIsDown == 'e'

		oldSelectedNodeIdx = self.selectedNode()

		print('=== onMouseClicked_nodes() eKeyIsDown:', eKeyIsDown)

		# this works gives me the point number!!!!
		thePoint = points[0].index()

		aicsNodeList_nodeIdx = self.maskedEdgesDict['aicsNodeList_nodeIdx']
		newSelectedNodeIdx = aicsNodeList_nodeIdx[thePoint]

		print('  newSelectedNodeIdx:', newSelectedNodeIdx)

		if eKeyIsDown and oldSelectedNodeIdx is not None and newSelectedNodeIdx>0:
			# make a new edge from current selection to new selection
			print('MAKE A NEW EDGE from:', oldSelectedNodeIdx, 'to', newSelectedNodeIdx)
		else:
			# just select the node
			self.selectNode(newSelectedNodeIdx)

			# emit
			myEvent = bimpy.interface.bEvent('select node', nodeIdx=newSelectedNodeIdx)
			self.selectNodeSignal.emit(myEvent)

	def slot_StateChange(self, signalName, signalValue):
		#print(' myPyQtGraphPlotWidget.slot_StateChange() signalName:', signalName, 'signalValue:', signalValue)

		# not sure?
		if signalName == 'set slice':
			self.setSlice(signalValue)

		else:
			print('myPyQtGraphPlotWidget.slot_StateChange() did not understand signalName:', signalName)

		'''
		elif signalName == 'bSignal Image':
			self.displayStateDict['showImage'] = signalValue
			self.setSlice() # just refresh

		elif signalName == 'bSignal Sliding Z':
			self.displayStateDict['displaySlidingZ'] = signalValue
			self.setSlice() # just refresh

		elif signalName == 'bSignal Nodes':
			self.displayStateDict['showNodes'] = signalValue
			self.setSlice() # just refresh

		elif signalName == 'bSignal Edges':
			self.displayStateDict['showEdges'] = signalValue
			self.setSlice() # just refresh
		else:
			print('myPyQtGraphPlotWidget.slot_StateChange() did not understand signalName:', signalName)
		'''

	def slot_contrastChange(self, myEvent):
		myEvent.printSlot('myPyQtGraphPlotWidget.slot_contrastChange()')
		self.contrastDict = myEvent.contrastDict
		# refresh
		self.setSlice() # refresh

	def slot_selectNode(self, myEvent):
		myEvent.printSlot('myPyQtGraphPlotWidget.slot_selectNode()')
		if len(myEvent.nodeList) > 0:
			self.selectNodeList(myEvent.nodeList)
		else:
			nodeIdx = myEvent.nodeIdx
			snapz = myEvent.snapz
			isShift = myEvent.isShift
			self.selectNode(nodeIdx, snapz=snapz, isShift=isShift)

	def slot_selectEdge(self, myEvent):
		myEvent.printSlot('myPyQtGraphPlotWidget.slot_selectEdge()')
		if myEvent.eventType == 'select node':
			return
		edgeList = myEvent.edgeList
		colorList = myEvent.colorList
		if len(edgeList)>0:
			# select a list of edges
			self.selectEdgeList(edgeList, thisColorList=colorList, snapz=True)
		else:
			# select a single edge
			edgeIdx = myEvent.edgeIdx
			slabIdx = myEvent.slabIdx
			snapz = myEvent.snapz
			isShift = myEvent.isShift
			self.selectEdge(edgeIdx, snapz=snapz, isShift=isShift)
		self.selectNode(myEvent.nodeIdx)
		self.selectSlab(myEvent.slabIdx)

	def slot_selectAnnotation(self, myEvent):
		myEvent.printSlot('myPyQtGraphPlotWidget.slot_selectAnnotation()')
		if len(myEvent.nodeList) > 0:
			self.selectNodeList(myEvent.nodeList)
		else:
			annotationIdx = myEvent.nodeIdx
			snapz = myEvent.snapz
			isShift = myEvent.isShift
			self.selectAnnotation(annotationIdx, snapz=snapz, isShift=isShift)

	def displayStateChange(self, key1, value=None, toggle=False):
		#print('displayStateChange() key1:', key1, 'value:', value, 'toggle:', toggle)
		if toggle:
			value = not self.displayStateDict[key1]
		self.displayStateDict[key1] = value
		self.setSlice()
		self.displayStateChangeSignal.emit(key1, self.displayStateDict)

	def myEvent(self, event):
		theRet = None
		doUpdate = False

		# abb aics
		if event['type']=='joinTwoEdges':
			selectedEdgeList = self.displayStateDict['selectedEdgeList']
			print('=== myEvent() joinTwoEdges:', selectedEdgeList)
			if len(selectedEdgeList) != 2:
				print('  please select just two edges')
			else:
				edge1 = selectedEdgeList[0]
				edge2 = selectedEdgeList[1]
				#print('=== myPyQtGraphPlotWidget.myEvent() ... join edges', edge1, edge2)

				# this will join two edges (via common node) and make a new longer edge
				# use this mostly when (1) nodes have just two edges
				#		(2) when nodes have 4 edges
				newEdgeIdx, srcNode, dstNode = bimpy.bVascularTracingAics.joinEdges(self.mySimpleStack.slabList, edge1, edge2)

				if newEdgeIdx is  None:
					# did not join (usually when edges are not connected)
					pass
				else:
					print('  newEdgeIdx:', newEdgeIdx, 'srcNode:', srcNode, 'dstNode:', dstNode)

					# fill in new diameter
					self.mySimpleStack.slabList._analyze(thisEdgeIdx=newEdgeIdx)

					# clear multi selection
					self.cancelSelection()

					# select the new edge
					self.selectEdge(newEdgeIdx) # select the new edge

					myEvent = bimpy.interface.bEvent('select edge', edgeIdx=newEdgeIdx)
					self.selectEdgeSignal.emit(myEvent)


					#
					# emit change
					#
					#doUpdate = True

					#
					# update tracing
					# can't just do zMin/zMax because all 'later' edges have changed index
					'''
					zMin, zMax = self.mySimpleStack.slabList.getEdgeMinMax_Z(newEdgeIdx)
					print('  only refresh z:', zMin, zMax)
					self._preComputeAllMasks(firstSlice=zMin, lastSlice=zMax)
					self.setSlice() #refresh
					'''
					self._preComputeAllMasks()

					#
					# todo: fix this, need to grab edgeDict1 BEFORE join?
					#myEvent = bimpy.interface.bEvent('deleteEdge', edgeIdx=edge1, edgeDict=deleteEdgeDict)
					#self.tracingEditSignal.emit(myEvent)

					#
					# before I emit to tables, I need to refresh the tables
					#self.refreshView()
					self.mainWindow.repopulateAllTables()

					#
					# select the one new edge
					myEvent = bimpy.interface.bEvent('select edge', edgeIdx=newEdgeIdx, slabIdx=None)
					self.selectEdgeSignal.emit(myEvent)

					'''
					newEdgeDict = self.mySimpleStack.slabList.getEdge(newEdgeIdx)
					myEvent = bimpy.interface.bEvent('newEdge', edgeIdx=newEdgeIdx, edgeDict=newEdgeDict)
					myEvent._srcNodeDict = self.mySimpleStack.slabList.getNode(srcNode)
					myEvent._dstNodeDict = self.mySimpleStack.slabList.getNode(dstNode)
					#self.tracingEditSignal.emit(myEvent)
					self.selectEdgeSignal.emit(myEvent)
					'''
					#
					# update the pre/post nodes, they have new edges
					'''
					srcNodeDict = self.mySimpleStack.slabList.getNode(srcNode)
					myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=srcNode, nodeDict=srcNodeDict)
					self.tracingEditSignal.emit(myEvent)
					dstNodeDict = self.mySimpleStack.slabList.getNode(dstNode)
					myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=dstNode, nodeDict=dstNodeDict)
					self.tracingEditSignal.emit(myEvent)
					'''

		elif event['type']=='newNode':
			# this works fine, i need to make it more general to limit amount of code here !!!
			if bimpy.interface.myWarningsDialog('new node', self.options).canceled():
				print('new node cancelled by user')
				return theRet

			x = event['x']
			y = event['y']
			z = event['z']
			print('=== myPyQtGraphPlotWidget.myEvent() ... new node x:', x, 'y:', y, 'z:', z)
			newNodeIdx = self.mySimpleStack.slabList.newNode(x,y,z)

			# todo: select new node

			self._preComputeAllMasks()

			theRet = newNodeIdx

			# emit changes
			nodeDict = self.mySimpleStack.slabList.getNode(newNodeIdx)
			myEvent = bimpy.interface.bEvent('newNode', nodeIdx=newNodeIdx, nodeDict=nodeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='newEdge':
			srcNode = event['srcNode']
			dstNode = event['dstNode']
			print('=== myPyQtGraphPlotWidget.myEvent() ... new edge srcNode:', srcNode, 'dstNode:', dstNode)

			newEdgeIdx = self.mySimpleStack.slabList.newEdge(srcNode,dstNode)
			self._preComputeAllMasks()

			theRet = newEdgeIdx

			# todo: cancel node selection

			#
			# emit changes

			# update new edge
			edgeDict = self.mySimpleStack.slabList.getEdge(newEdgeIdx)
			myEvent = bimpy.interface.bEvent('newEdge', edgeIdx=newEdgeIdx, edgeDict=edgeDict)
			myEvent._srcNodeDict = self.mySimpleStack.slabList.getNode(srcNode)
			myEvent._dstNodeDict = self.mySimpleStack.slabList.getNode(dstNode)
			self.tracingEditSignal.emit(myEvent)

			# update the pre/post nodes, they have new edges
			srcNodeDict = self.mySimpleStack.slabList.getNode(srcNode)
			myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=srcNode, nodeDict=srcNodeDict)
			self.tracingEditSignal.emit(myEvent)

			dstNodeDict = self.mySimpleStack.slabList.getNode(dstNode)
			myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=dstNode, nodeDict=dstNodeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='newSlab':
			edgeIdx = event['edgeIdx']
			x = event['x']
			y = event['y']
			z = event['z']
			print('=== myPyQtGraphPlotWidget.myEvent() ... new slab edgeIdx:', edgeIdx)
			newSlabIdx = self.mySimpleStack.slabList.newSlab(edgeIdx, x, y, z)
			self._preComputeAllMasks()
			self.selectSlab(newSlabIdx) # self.setSlice() will draw new slab
			theRet = newSlabIdx

			# analyze
			self.mySimpleStack.slabList._analyze(thisEdgeIdx=edgeIdx)

			edgeDict = self.mySimpleStack.slabList.getEdge(edgeIdx)

			# new slab for edge idx mean: listeners should
			myEvent = bimpy.interface.bEvent('newSlab', edgeIdx=edgeIdx, edgeDict=edgeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='deleteNode':
			#objectType = event['objectType']
			deleteNodeIdx = event['objectIdx']
			deleteNodeDict = self.mySimpleStack.slabList.getNode(deleteNodeIdx)
			print('\n=== myPyQtGraphPlotWidget.myEvent() ... deleteNode:', deleteNodeIdx, deleteNodeDict)
			wasDeleted = self.mySimpleStack.slabList.deleteNode(deleteNodeIdx)
			if wasDeleted:
				# only here if node is not connected to edges
				self.selectNode(None)
				doUpdate = True
				#
				myEvent = bimpy.interface.bEvent('deleteNode', nodeIdx=deleteNodeIdx, nodeDict=deleteNodeDict)
				self.tracingEditSignal.emit(myEvent)
				#
				myEvent = bimpy.interface.bEvent('select node', nodeIdx=None)
				self.selectNodeSignal.emit(myEvent)

		elif event['type']=='deleteEdge':
			print('\n=== myPyQtGraphPlotWidget.myEvent() deleteEdge', event['objectIdx'])
			#objectType = event['objectType']
			deleteEdgeIdx = event['objectIdx']
			deleteEdgeDict = self.mySimpleStack.slabList.getEdge(deleteEdgeIdx)
			print('\n=== myPyQtGraphPlotWidget.myEvent() ... deleteEdge:', deleteEdgeIdx, deleteEdgeDict)
			self.mySimpleStack.slabList.deleteEdge(deleteEdgeIdx)
			self.selectEdge(None)
			self.selectSlab(None)
			doUpdate = True
			#
			myEvent = bimpy.interface.bEvent('deleteEdge', edgeIdx=deleteEdgeIdx, edgeDict=deleteEdgeDict)
			self.tracingEditSignal.emit(myEvent)
			#
			myEvent = bimpy.interface.bEvent('selectEdge', edgeIdx=None, slabIdx=None)
			self.selectEdgeSignal.emit(myEvent)

		elif event['type']=='deleteSelection':
			# there is order of execution here, if slab selected then delete slab
			# if no slab selected but edge is selected then delete edge
			# if neither slab or edge is selected but there is a node selection then delete node

			selectedSlabIdx = self.selectedSlab()
			selectedEdgeIdx = self.selectedEdge()
			selectedNodeIdx = self.selectedNode()
			selectedAnnotationIdx = self.selectedAnnotation()

			if selectedSlabIdx is not None and self.options['Panels']['showLineProfile']:
				# slab is selected and we are showing line profile
				if bimpy.interface.myWarningsDialog('delete slab', self.options).canceled():
					return theRet
				deleteSlabIdx = selectedSlabIdx
				print('\n=== myPyQtGraphPlotWidget.myEvent() ... deleteSelection delete slab:', deleteSlabIdx, 'from edge idx:', selectedEdgeIdx)
				self.mySimpleStack.slabList.deleteSlab(deleteSlabIdx)

				# interface
				self.selectEdge(None)
				self.selectSlab(None)
				doUpdate = True
				#
				selectedEdgeDict = self.mySimpleStack.slabList.getEdge(selectedEdgeIdx)
				myEvent = bimpy.interface.bEvent('deleteSlab', edgeIdx=selectedEdgeIdx, edgeDict=selectedEdgeDict, slabIdx=None)
				self.tracingEditSignal.emit(myEvent)

			elif selectedEdgeIdx is not None:
				deleteEdgeIdx = selectedEdgeIdx
				print('\n=== myPyQtGraphPlotWidget.myEvent() ... deleteSelection delete edge idx:', deleteEdgeIdx)
				self.mySimpleStack.slabList.deleteEdge(self.selectedEdge())

				# interface
				self.selectEdge(None)
				self.selectSlab(None)
				doUpdate = True
				#
				#deleteEdgeDict = self.mySimpleStack.slabList.getEdge(deleteEdgeIdx)
				myEvent = bimpy.interface.bEvent('deleteEdge', edgeIdx=deleteEdgeIdx) #, edgeDict=deleteEdgeDict)
				self.tracingEditSignal.emit(myEvent)
				#
				myEvent = bimpy.interface.bEvent('selectEdge', edgeIdx=None, slabIdx=None)
				self.selectEdgeSignal.emit(myEvent)

			elif selectedNodeIdx is not None:
				#delete node, only if it does not have edges !!!
				deleteNodeIdx = selectedNodeIdx
				print('\n=== myPyQtGraphPlotWidget.myEvent() ... deleteSelection delete node:', deleteNodeIdx)
				wasDeleted = self.mySimpleStack.slabList.deleteNode(deleteNodeIdx)
				if wasDeleted:
					# only here if node is not connected to edges
					self.selectNode(None)
					doUpdate = True
					#
					#deleteNodeDict = self.mySimpleStack.slabList.getNode(self.selectedNode())
					myEvent = bimpy.interface.bEvent('deleteNode', nodeIdx=deleteNodeIdx) #, nodeDict=deleteNodeDict)
					self.tracingEditSignal.emit(myEvent)
					#
					myEvent = bimpy.interface.bEvent('select node', nodeIdx=None)
					self.selectNodeSignal.emit(myEvent)

			elif selectedAnnotationIdx is not None:
				deleteAnnotationIdx = selectedAnnotationIdx
				wasDeleted = self.mySimpleStack.annotationList.deleteAnnotation(deleteAnnotationIdx)
				if wasDeleted:
					# only here if node is not connected to edges
					self.selectAnnotation(None)

					# all we need is set slice
					#doUpdate = True
					self.setSlice()

					#
					#deleteNodeDict = self.mySimpleStack.slabList.getNode(self.selectedNode())
					#deleteAnnotationDict = self.mySimpleStack.annotationList.getItemDict(xxx)
					myEvent = bimpy.interface.bEvent('deleteAnnotation', nodeIdx=deleteAnnotationIdx) #, nodeDict=deleteAnnotationDict)
					self.tracingEditSignal.emit(myEvent)
					#
					myEvent = bimpy.interface.bEvent('select annotation', nodeIdx=None)
					self.selectAnnotationSignal.emit(myEvent)

		elif event['type']=='analyzeEdge':
			objectIdx = event['objectIdx']

			print('\n=== myPyQtGraphPlotWidget.myEvent() ... analyzeEdge:', objectIdx)

			# analyze
			self.mySimpleStack.slabList._analyze(thisEdgeIdx=objectIdx)

			#
			newEdgeDict = self.mySimpleStack.slabList.getEdge(objectIdx)
			myEvent = bimpy.interface.bEvent('updateEdge', edgeIdx=objectIdx, edgeDict=newEdgeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='setType':
			# myEvent = {'event': 'setNodeType', 'newType': title, 'nodeIdx':int(nodeIdx)}
			bobID0 = event['bobID0'] # tells us nodes/edges
			newObjectType = event['newType']
			objectIdx = event['objectIdx']
			print(event)
			if bobID0 == 'nodes':
				self.mySimpleStack.slabList.setNodeType(objectIdx, newObjectType)
			elif bobID0 == 'edges':
				self.mySimpleStack.slabList.setEdgeType(objectIdx, newObjectType)
			#
			if bobID0 == 'nodes':
				newNodeDict = self.mySimpleStack.slabList.getNode(objectIdx)
				myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=objectIdx, nodeDict=newNodeDict)
			elif bobID0 == 'edges':
				newEdgeDict = self.mySimpleStack.slabList.getEdge(objectIdx)
				myEvent = bimpy.interface.bEvent('updateEdge', edgeIdx=objectIdx, edgeDict=newEdgeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='setIsBad':
			bobID0 = event['bobID0'] # tells us nodes/edges
			objectIdx = event['objectIdx']
			isChecked = event['isChecked']
			print(event)
			if bobID0 == 'nodes':
				self.mySimpleStack.slabList.setNodeIsBad(objectIdx, isChecked)
			elif bobID0 == 'edges':
				self.mySimpleStack.slabList.setEdgeIsBad(objectIdx, isChecked)
			#
			if bobID0 == 'nodes':
				newNodeDict = self.mySimpleStack.slabList.getNode(objectIdx)
				myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=objectIdx, nodeDict=newNodeDict)
			elif bobID0 == 'edges':
				newEdgeDict = self.mySimpleStack.slabList.getEdge(objectIdx)
				myEvent = bimpy.interface.bEvent('updateEdge', edgeIdx=objectIdx, edgeDict=newEdgeDict)
			'''
			newNodeDict = self.mySimpleStack.slabList.getNode(nodeIdx)
			myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=nodeIdx, nodeDict=newNodeDict)
			'''
			self.tracingEditSignal.emit(myEvent)

		elif event['type'] == 'cancelSelection':
			self.cancelSelection()

		else:
			print('myPyQtGraphPlotWidget.myEvent() not understood event:', event)

		# finalize
		if doUpdate:
			#print('myPyQtGraphPlotWidget.myEvent() is updating masks with _preComputeAllMasks()')
			self._preComputeAllMasks()

		return theRet

	def newAnnotation(self, x, y, z):
		"""
		add a generic annotation
		"""
		print(f'myPyQtGraphPlotWidget.newAnnotation() x:{x}, y:{y}, z:{z}')
		newAnnotationIdx = self.mySimpleStack.annotationList.addAnnotation(x, y, z)

		#print('newAnnotationIdx:', newAnnotationIdx)

		self.setSlice()

		'''
		print('list is now')
		self.mySimpleStack.annotationList.printList()
		'''

		# emit changes
		annotationDict = self.mySimpleStack.annotationList.getItemDict(newAnnotationIdx)
		myEvent = bimpy.interface.bEvent('newAnnotation', nodeIdx=newAnnotationIdx, nodeDict=annotationDict)
		self.tracingEditSignal.emit(myEvent)

	def loadMasks(self):
		"""
		load pickle file into self.maskedEdgesDict
		"""
		pickleFile = self.mySimpleStack._getSavePath() # tiff file without extension
		pickleFile += '.pickle'
		if os.path.isfile(pickleFile):
			print('  loadMasks() loading maskedNodes from pickleFile:', pickleFile)
			#timer = bimpy.util.bTimer()
			timer = bimpy.util.bTimer(name='loadMasks')
			with open(pickleFile, 'rb') as filename:
				#self.maskedNodes = pickle.load(filename)
				self.maskedEdgesDict = pickle.load(filename)
			print('    loaded mask file from', pickleFile)
			timer.elapsed()
			#
			return True
			#
		else:
			#print('error: _preComputeAllMasks did not find pickle file:', pickleFile)
			return False

	def saveMasks(self):
		"""
		save self.maskedEdgesDict to pickle file
		"""
		pickleFile = self.mySimpleStack._getSavePath() # tiff file without extension
		pickleFile += '.pickle'
		print('    myPyQtGraphPlotWidget.saveMasks() saving maskedNodes as pickleFile:', pickleFile)
		with open(pickleFile, 'wb') as fout:
			#pickle.dump(self.maskedNodes, fout)
			pickle.dump(self.maskedEdgesDict, fout)

def main():
	app = QtWidgets.QApplication(sys.argv)
	main = myPyQtGraphWindow2()
	main.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
