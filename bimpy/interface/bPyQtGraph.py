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

		#self.test1()


###########################################################################
class myPyQtGraphPlotWidget(pg.PlotWidget):
	setSliceSignal = QtCore.Signal(str, object)
	selectNodeSignal = QtCore.Signal(object)
	selectEdgeSignal = QtCore.Signal(object)
	#
	tracingEditSignal = QtCore.Signal(object) # on new/delete/edit of node, edge, slab
	#
	# not implemented, what did this do? see class bStackView
	displayStateChangeSignal = QtCore.Signal(str, object)

	#def __init__(self, *args, **kwargs):
	#	super(myPyQtGraphPlotWidget, self).__init__(*args, **kwargs)
	def __init__(self, parent=None, mySimpleStack=None):
		super(myPyQtGraphPlotWidget, self).__init__(parent=parent)

		# abb laptop, 2 channel composite
		'''
		import tifffile
		path = '/Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch1.tif'
		self.stackData_ch2 = tifffile.imread(path)
		'''

		#self.viewBox = self.addViewBox()
		#self.viewBox.setAspectLocked(True)

		#p1 = self.addPlot()

		#pg.setConfigOption('imageAxisOrder','row-major')

		self.mainWindow = parent
		self.myPlotWidget = self #pg.PlotWidget(name='Plot2')

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
		data = np.zeros((1,1,1))
		 #np.random.randint(0, high=256, size=(200,200), dtype=np.uint8)
		self.myImage = pg.ImageItem(data)
		self.myPlotWidget.addItem(self.myImage)

		#self.minContrast = 0
		#self.maxContrast = 255

		# self.myPlotWidget.plot
		# creates: <class 'pyqtgraph.graphicsItems.PlotDataItem.PlotDataItem'>

		#
		# slabs
		pen = pg.mkPen(color='c', width=5)
		self.mySlabPlot = self.myPlotWidget.plot([], [], pen=pen, symbol='o', symbolSize=7, symbolBrush=('c'),
							connect='finite', clickable=True)
		self.mySlabPlot.sigPointsClicked.connect(self.onMouseClicked_slabs)

		self.mySlabPlotSelection = self.myPlotWidget.plot([], [], pen=pen, symbol='o', symbolSize=10, symbolBrush=('y'),
							connect='finite', clickable=False)

		# for a single slab (not the edge)
		self.mySlabPlotSelection2 = self.myPlotWidget.plot([], [], pen=None, symbol='x', symbolSize=20, symbolBrush=('g'),
							connect='finite', clickable=False)

		self.myEdgeSelectionFlash = self.myPlotWidget.plot([], [],
							pen=pen, symbol='o', symbolSize=20, symbolBrush=('y'),
							connect='finite', clickable=False)

		#
		# one slab (line orthogonal to edges)
		oneSlabPen = pg.mkPen(color='g', width=5)
		self.mySlabPlotOne = self.myPlotWidget.plot([], [],
							pen=oneSlabPen, symbol='x', symbolSize=20, symbolBrush=('g'),
							connect='finite', clickable=False)

		#
		# nodes
		self.myNodePlot = self.myPlotWidget.plot([], [], pen=None, symbol='o', symbolSize=8, symbolBrush=('r'))
		self.myNodePlot.sigPointsClicked.connect(self.onMouseClicked_nodes)

		self.myNodePlotSelection = self.myPlotWidget.plot([], [], pen=None, symbol='o', symbolSize=10, symbolBrush=('y'),
							connect='finite')

		self.myNodeSelectionFlash = self.myPlotWidget.plot([], [],
											pen=None, symbol='o', symbolSize=20, symbolBrush=('y'))


		# click on scene
		#self.mySlabPlot.scene().sigMouseClicked.connect(self.onMouseClicked_scene)
		#self.mySlabPlot.scene().sigMouseMoved.connect(self.onMouseMoved_scene)

		#self.scene().sigMouseClicked.connect(self.sceneClicked)
		self.scene().sigMouseMoved.connect(self.onMouseMoved_scene)
		self.scene().sigMouseClicked.connect(self.onMouseClicked_scene) # works but confusing coordinates

		#self.myAddPlot()
		#self.myAddImage()

		#
		# new
		self.mySimpleStack = mySimpleStack

		self.keyIsDown = None # to detect 'n' key to ('n' click) existing node to make new edge
		self.currentSlice = 0

		self.displayStateDict = OrderedDict()
		# from older code
		self.displayStateDict['displayThisStack'] = 'ch1'
		self.displayStateDict['displaySlidingZ'] = False
		self.displayStateDict['showImage'] = True
		#'showTracing' = True,
		# abb removed
		#self.displayStateDict['triState'] = 0 # 0: all, 1: just nodes, 2: just edges, 3: none
		self.displayStateDict['showNodes'] = True
		self.displayStateDict['showEdges'] = True
		# abb removed
		#self.displayStateDict['showDeadEnds'] = True # not used ???
		#
		self.displayStateDict['showNodes'] = True
		self.displayStateDict['showEdges'] = True
		self.displayStateDict['selectedNode'] = None
		self.displayStateDict['selectedEdge'] = None
		self.displayStateDict['selectedSlab'] = None

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

	def drawNodes(self):
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
		if np.isnan(xNodeMasked).all() or np.isnan(yNodeMasked).all():
			xNodeMasked = []
			yNodeMasked = []

		#
		# update
		self.myNodePlot.setData(xNodeMasked, yNodeMasked)

	def drawEdges(self):
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
		self.mySlabPlot.setData(xEdgeMasked, yEdgeMasked, connected='finite')

	def drawSlab(self, slabIdx=None, radius=None):
		"""
		draw one slab as a line orthogonal to edge
		"""
		print('drawSlab() slabIdx:', slabIdx)
		if radius is None:
			radius = 30 # pixels

		if slabIdx is None:
			slabIdx = self.selectedSlab()
		if slabIdx is None:
			return

		# todo: could pas edgeIdx as a parameter
		edgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(slabIdx)
		if edgeIdx is None:
			print('warning: bStackView.drawSlab() got bad edgeIdx:', edgeIdx)
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

		#yLine1 = this_y + y_
		#yLine2 = this_y - y_
		yLine1 = this_y - y_ # PyQtGraph
		yLine2 = this_y + y_

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
		print('  xSlabPlot:', xSlabPlot, 'ySlabPlot:', ySlabPlot)
		self.mySlabPlotOne.setData(xSlabPlot, ySlabPlot)

		profileDict = {
			'xSlabPlot': xSlabPlot,
			'ySlabPlot': ySlabPlot,
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
		self.selectNode(None)
		self.selectEdge(None)
		self.selectSlab(None)

		self.displayStateDict['selectedNode'] = None
		self.displayStateDict['selectedEdge'] = None
		self.displayStateDict['selectedSlab'] = None

	def selectedNode(self):
		return self.displayStateDict['selectedNode']
	def selectedEdge(self):
		return self.displayStateDict['selectedEdge']
	def selectedSlab(self):
		return self.displayStateDict['selectedSlab']

	def selectNode(self, nodeIdx, snapz=False, isShift=False):

		if nodeIdx is not None:
			nodeIdx = int(nodeIdx)

		self.displayStateDict['selectedNode'] = nodeIdx

		if nodeIdx is None:
			x = []
			y = []
			self.myNodePlotSelection.setData(x, y)
		else:
			# todo: standardize this
			nodeIdx = int(nodeIdx)

			x,y,z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)

			if snapz:
				z = int(z)
				self.setSlice(z)

				self._zoomToPoint(x, y)

			# update
			x = [x]
			y = [y]
			self.myNodePlotSelection.setData(x, y)

			QtCore.QTimer.singleShot(20, lambda:self.flashNode(nodeIdx, 2))

	def selectEdge(self, edgeIdx, snapz=False, isShift=False):

		if edgeIdx is not None:
			edgeIdx = int(edgeIdx)

		self.displayStateDict['selectedEdge'] = edgeIdx

		if edgeIdx is None:
			xMasked = []
			yMasked = []
			self.mySlabPlotSelection.setData(xMasked, yMasked)
		else:
			# todo: standardize this
			edgeIdx = int(edgeIdx)

			theseIndices = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)

			xMasked = self.mySimpleStack.slabList.x[theseIndices] # flipped
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
				self._zoomToPoint(tmpx, tmpy)

			# update
			self.mySlabPlotSelection.setData(xMasked, yMasked)

			QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, 2))

	def selectSlab(self, slabIdx, snapz=False):

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

			slabIdx = int(slabIdx)

			self.displayStateDict['selectedSlab'] = slabIdx

			x,y,z = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)

			if snapz:
				z = int(z)
				self.setSlice(z)

			x = [x]
			y = [y]

			print('  selectSlab() slabIdx:', slabIdx, 'x:', x, 'y:', y)

			# update
			self.mySlabPlotSelection2.setData(x, y)

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
			self.drawSlab(slabIdx)

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
				self.myNodeSelectionFlash.setData(x, y)
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
				self.myEdgeSelectionFlash.setData(xMasked, yMasked)
				#self.myEdgeSelectionFlash.set_offsets(np.c_[xMasked, yMasked])
				#
				QtCore.QTimer.singleShot(20, lambda:self.flashEdge(edgeIdx, False))
		else:
			self.myEdgeSelectionFlash.setData([], [])
			#self.myEdgeSelectionFlash.set_offsets(np.c_[[], []])

	def _preComputeAllMasks(self):
		self.maskedEdgesDict = self.mySimpleStack.slabList._preComputeAllMasks()
		self.setSlice() #refresh

	def setSlice(self, thisSlice=None):

		if thisSlice is None:
			thisSlice = self.currentSlice
		else:
			self.currentSlice = thisSlice

		#
		# image
		if self.displayStateDict['showImage']:
			displayThisStack = self.displayStateDict['displayThisStack'] # (ch1, ch2, ch2, rgb)
			if displayThisStack == 'ch1':
				channel = 1
			if displayThisStack == 'ch2':
				channel = 2
			if displayThisStack == 'ch3':
				channel = 3
			#print('  displayThisStack:', displayThisStack)
			#sliceImage = self.mySimpleStack.setSliceContrast(thisSlice, thisStack=displayThisStack, minContrast=self.minContrast, maxContrast=self.maxContrast)
			#sliceImage = self.mySimpleStack.getImage(channel=1, sliceNum=thisSlice)

			if self.displayStateDict['displaySlidingZ']:
				upSlices = self.options['Stack']['upSlidingZSlices']
				downSlices = self.options['Stack']['downSlidingZSlices']
				#print('upSlices:', upSlices, 'downSlices:', downSlices)
				sliceImage = self.mySimpleStack.getSlidingZ2(thisSlice, displayThisStack, upSlices, downSlices)
			elif displayThisStack == 'rgb':
				sliceImage1 = self.mySimpleStack.getImage2(channel=1, sliceNum=thisSlice)
				sliceImage2 = self.mySimpleStack.getImage2(channel=2, sliceNum=thisSlice)
				m = sliceImage1.shape[0]
				n = sliceImage1.shape[1]
				sliceImage = np.ndarray((m,n,3), dtype=np.uint8)
				sliceImage[:,:,0] = sliceImage1
				sliceImage[:,:,1] = sliceImage2
				sliceImage[:,:,2] = 0
			else:
				sliceImage = self.mySimpleStack.getImage2(channel=channel, sliceNum=thisSlice)

			#sliceImage = sliceImage[:, ::-1].T

			self.myImage.setImage(sliceImage)

			if self.contrastDict is not None:
				minContrast = self.contrastDict['minContrast']
				maxContrast = self.contrastDict['maxContrast']
				self.myImage.setLevels([minContrast,maxContrast], update=True)

				colorLutStr = self.contrastDict['colorLut']
				colorLut = self.myColorLutDict[colorLutStr] # like (green, red, blue, gray, gray_r, ...)
				self.myImage.setLookupTable(colorLut, update=True)

		# plot slabs/nodes
		self.drawEdges()
		self.drawNodes()

	# this is over-riding existing member function

	def myAddPlot(self):
		xData = [20, 50, 100, 150, 180]
		yData = [20, 50, 100, 150, 180]

		pen = pg.mkPen(color=(255, 0, 0))
		self.tmp = self.plotWidget.plot(xData, yData, pen,
				symbol='+', symbolSize=30, symbolBrush=('b'),
				clickable=True)

	def myAddImage(self):
		# for callbacks, see
		#  https://stackoverflow.com/questions/38021869/getting-imageitem-values-from-pyqtgraph
		data = np.random.randint(0, high=256, size=(200,200), dtype=np.uint8)
		self.img = pg.ImageItem(data)


	def _zoomToPoint(self, x, y):
		print('zoomToPoint()')
		print('  x:', x, 'y:', y)
		pos = self.mapToScene(x, y)
		x = pos.x()
		y = pos.y()
		print('  x:', x, 'y:', y)
		[xRange, yRange] = self.viewRange()
		#yRange = self.viewRange()[1]
		xWidth = xRange[1] - xRange[0]
		yWidth = yRange[1] - yRange[0]
		xHalfWidth = int(xWidth/2)
		yHalfWidth = int(yWidth/2)
		xNewRange = [x-xHalfWidth, x+xHalfWidth]
		yNewRange = [y-yHalfWidth, y+yHalfWidth]
		print('  xRange:', xRange, 'yRange:', yRange)

		# update
		#self.setRange(xRange=xRange, yRange=yRange)

	def myTranslate(self, direction):
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

	def mousePressEvent(self, event):
		"""
		This is a PyQt callback (not PyQtGraph)
		Set event.setAccepted(False) to keep propogation so we get to PyQt callbacks like
			self.onMouseClicked_scene(), _slabs(), _nodes()
		"""
		#print('mousePressEvent() event:', event)
		if event.button() == QtCore.Qt.RightButton:
			#print('bStackView.mousePressEvent() right click !!!')
			self.mainWindow.showRightClickMenu(event.pos())
			self.mouseReleaseEvent(event)
		else:
			event.setAccepted(False)
			super().mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		event.setAccepted(False)
		super().mouseReleaseEvent(event)

	def keyPressEvent(self, event):
		"""
		event: <PyQt5.QtGui.QKeyEvent object at 0x13e1f7410>
		"""

		# event.key() is a number
		if event.text() != 'n':
			print(f'=== keyPressEvent() event.text() "{event.text()}"')

		# this works to print 'left', 'right' etc etc
		# but raises 'UnicodeEncodeError' for others
		#print('  ', QtGui.QKeySequence(event.key()).toString())

		self.keyIsDown = event.text()

		if event.key() in [QtCore.Qt.Key_Escape]:
			self.cancelSelection()

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
						self.myTranslate('left')
				elif event.key() in [QtCore.Qt.Key_Right]:
					if self.selectedSlab() is None:
						self.myTranslate('right')

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
			#self.displayThisStack = 'ch1'
			self.displayStateDict['displaySlidingZ'] = False
			self.displayStateDict['displayThisStack'] = 'ch1'
			self.setSlice() # just refresh
		elif event.key() == QtCore.Qt.Key_2:
			numChannels = self.mySimpleStack.numChannels
			if numChannels > 1:
				#self.displayThisStack = 'ch2'
				self.displayStateDict['displayThisStack'] = 'ch2'
				self.setSlice() # just refresh
			else:
				print('warning: stack only has', numChannels, 'channel(s)')
		elif event.key() == QtCore.Qt.Key_3:
			numChannels = self.mySimpleStack.numChannels
			if numChannels > 2:
				#self.displayThisStack = 'ch3'
				self.displayStateDict['displayThisStack'] = 'ch3'
				self.setSlice() # just refresh
			else:
				print('warning: stack only has', numChannels, 'channel(s)')


		elif event.key() == QtCore.Qt.Key_9:
			# not implemented (was for deepvess)
			if self.mySimpleStack._imagesSkel is not None:
				#self.displayThisStack = 'skel'
				self.displayStateDict['displayThisStack'] = 'skel'
				self.setSlice() # just refresh
		# should work, creates a mask from vesselucida tracing
		elif event.key() == QtCore.Qt.Key_0:
			if 1: #self.mySimpleStack._imagesMask is not None:
				#self.displayThisStack = 'mask'
				self.displayStateDict['displayThisStack'] = 'mask'
				self.setSlice() # just refresh

		elif event.key() in [QtCore.Qt.Key_R]:
			self._preComputeAllMasks()

		elif event.key() in [QtCore.Qt.Key_T]:
			self.displayStateDict['showNodes'] = not self.displayStateDict['showNodes']
			self.displayStateDict['showEdges'] = not self.displayStateDict['showEdges']
			self.setSlice() # refresh

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

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		if modifiers == QtCore.Qt.ControlModifier:
			super(myPyQtGraphPlotWidget, self).wheelEvent(event)
		else:
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
		nKeyIsDown = self.keyIsDown == 'n'

		print('=== onMouseClicked_scene()', event.pos().x(), event.pos().y(), 'nKeyIsDown:', nKeyIsDown)

		#imagePos = self.myImage.mapFromScene(event.pos())
		imagePos = self.myImage.mapFromScene(event.pos())
		slabPos = self.mySlabPlot.mapFromScene(event.pos())
		'''
		print('  event.pos():', event.pos())
		print('  imagePos:', imagePos) # slighlty off???
		print('  slabPos:', slabPos)
		'''

		'''
		print('  self.viewRange():', self.viewRange()) # [[xmin,xmax], [ymin,ymax]]

		xRange = self.viewRange()[0]
		yRange = self.viewRange()[1]
		xWidth = xRange[1] - xRange[0]

		xRange[0] += 100
		xRange[1] += 200

		self.setRange(xRange=xRange, yRange=yRange)
		'''

		print('  self.getViewBox():', self.getViewBox())

		x = imagePos.x()
		y = imagePos.y()
		z = self.currentSlice

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		isControl = modifiers == QtCore.Qt.ControlModifier # on macOS, this is 'command' (e.g. open-apple)

		oldSelectedNode = self.selectedNode()
		oldSelectedEdge = self.selectedEdge()
		if nKeyIsDown and oldSelectedNode is not None:
			print('  onMouseClicked_scene() new edge from oldSelectedNode:', oldSelectedNode)

			#newNodeIdx = self.mySimpleStack.slabList.newNode(x, y, self.currentSlice)
			newNodeEvent = {'type':'newNode','x':x,'y':y,'z':z}
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
					# make a new slab
					print('\n=== bStackWidget.onclick_mpl() new slab ...')
					newSlabEvent = {'type':'newSlab','edgeIdx':self.selectedEdge(), 'x':x, 'y':y, 'z':z}
					# abb removed???
					self.myEvent(newSlabEvent)
				else:
					print('To add slabs, open the line profile panel with keyboard "l"')
			else:
				# new node
				print('  onMouseClicked_scene() new node')
				#newNodeIdx = self.mySimpleStack.slabList.newNode(x, y, self.currentSlice)
				newNodeEvent = {'type':'newNode','x':x,'y':y,'z':z}
				newNodeIdx = self.myEvent(newNodeEvent)

				self._preComputeAllMasks()

		elif isControl:
			# abb aics
			# extend to multiple selections
			pass

	def onMouseMoved_scene(self, pos):
		if 1:
			#print('=== onMouseMoved_scene()', pos.x(), pos.y())
			imagePos = self.myImage.mapFromScene(pos)
			#print('  imagePos:', imagePos)

			xPos = imagePos.x()
			yPos = imagePos.y()
			thePoint = QtCore.QPoint(xPos, yPos)
			self.mainWindow.getStatusToolbar().setMousePosition(thePoint, sliceNumber=self.currentSlice)

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

		# this works gives me the point number!!!!
		thePoint = points[0].index()

		aicsSlabList_edgeIdx = self.maskedEdgesDict['aicsSlabList_edgeIdx']
		selectedEdgeIdx = aicsSlabList_edgeIdx[thePoint]

		aicsSlabList_slabIdx = self.maskedEdgesDict['aicsSlabList_slabIdx']
		selectedSlabIdx = aicsSlabList_slabIdx[thePoint]

		print('=== onMouseClicked_slabs() thePoint:', thePoint, 'selectedEdgeIdx:', selectedEdgeIdx, 'selectedSlabIdx:', selectedSlabIdx)

		self.selectEdge(selectedEdgeIdx)
		self.selectSlab(selectedSlabIdx)

		# emit
		myEvent = bimpy.interface.bEvent('select edge', edgeIdx=selectedEdgeIdx, slabIdx=selectedSlabIdx)
		self.selectEdgeSignal.emit(myEvent)

	def onMouseClicked_nodes(self, item, points):
		"""
		get node index from displayed masked node

		item: self.myNodePlot
		points: [<pyqtgraph.graphicsItems.ScatterPlotItem.SpotItem object at 0x13cdb6f10>]
		"""

		# check if 'n' key is down
		#modifiers = QtWidgets.QApplication.keyboardModifiers()
		#isShift = modifiers == QtCore.Qt.ShiftModifier
		nKeyIsDown = self.keyIsDown == 'n'

		oldSelectedNodeIdx = self.selectedNode()

		print('=== onMouseClicked_nodes() nKeyIsDown:', nKeyIsDown)

		# this works gives me the point number!!!!
		thePoint = points[0].index()

		aicsNodeList_nodeIdx = self.maskedEdgesDict['aicsNodeList_nodeIdx']
		newSelectedNodeIdx = aicsNodeList_nodeIdx[thePoint]

		print('  newSelectedNodeIdx:', newSelectedNodeIdx)

		if nKeyIsDown and oldSelectedNodeIdx is not None and newSelectedNodeIdx>0:
			# make a new edge from current selection to new selection
			print('MAKE A NEW EDGE from:', oldSelectedNodeIdx, 'to', newSelectedNodeIdx)
		else:
			# just select the node
			self.selectNode(newSelectedNodeIdx)

			# emit
			myEvent = bimpy.interface.bEvent('select node', nodeIdx=newSelectedNodeIdx)
			self.selectNodeSignal.emit(myEvent)

	def slot_StateChange(self, signalName, signalValue):
		#print(' bStackView.slot_StateChange() signalName:', signalName, 'signalValue:', signalValue)

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

	def displayStateChange(self, key1, value=None, toggle=False):
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
			selectedEdgeList = self.selectedEdgeList_get()
			print('=== myEvent() joinTwoEdges:', selectedEdgeList)
			if len(selectedEdgeList) != 2:
				print('  please select just two edges')
			else:
				edge1 = selectedEdgeList[0]
				edge2 = selectedEdgeList[1]
				#print('=== bStackView.myEvent() ... join edges', edge1, edge2)

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
					self.selectedEdgeList_append([]) # this updates 'state'
					#self.cancelSelection(doEmit=False)

					# select the new edge
					self.selectEdge(newEdgeIdx) # select the new edge

					myEvent = bimpy.interface.bEvent('select edge', edgeIdx=newEdgeIdx)
					self.selectEdgeSignal.emit(myEvent)

					# handled by doUpdate = True
					#self._preComputeAllMasks(fromCurrentSlice=True)
					#self.setSlice() #refresh

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
			print('=== bStackView.myEvent() ... new node x:', x, 'y:', y, 'z:', z)
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
			print('=== bStackView.myEvent() ... new edge srcNode:', srcNode, 'dstNode:', dstNode)

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
			print('=== bStackView.myEvent() ... new slab edgeIdx:', edgeIdx)
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
			print('\n=== bStackView.myEvent() ... deleteNode:', deleteNodeIdx, deleteNodeDict)
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
			print('\n=== bStackView.myEvent() deleteEdge', event['objectIdx'])
			#objectType = event['objectType']
			deleteEdgeIdx = event['objectIdx']
			deleteEdgeDict = self.mySimpleStack.slabList.getEdge(deleteEdgeIdx)
			print('\n=== bStackView.myEvent() ... deleteEdge:', deleteEdgeIdx, deleteEdgeDict)
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

			if selectedSlabIdx is not None:
				if bimpy.interface.myWarningsDialog('delete slab', self.options).canceled():
					return theRet
				deleteSlabIdx = selectedSlabIdx
				print('\n=== bStackView.myEvent() ... deleteSelection delete slab:', deleteSlabIdx, 'from edge idx:', selectedEdgeIdx)
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
				print('\n=== bStackView.myEvent() ... deleteSelection delete edge idx:', deleteEdgeIdx)
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
				print('\n=== bStackView.myEvent() ... deleteSelection delete node:', deleteNodeIdx)
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

		elif event['type']=='analyzeEdge':
			objectIdx = event['objectIdx']

			print('\n=== bStackView.myEvent() ... analyzeEdge:', objectIdx)

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
			print('bStackView.myEvent() not understood event:', event)

		# finalize
		if doUpdate:
			#print('bStackView.myEvent() is updating masks with _preComputeAllMasks()')
			self._preComputeAllMasks()

		return theRet

def main():
	app = QtWidgets.QApplication(sys.argv)
	main = myPyQtGraphWindow2()
	main.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
