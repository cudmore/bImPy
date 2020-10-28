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

#import pickle # to load/save _pre computed masks
#import h5py

from qtpy import QtCore, QtGui, QtWidgets

#from PyQt5.QtCore import QT_VERSION_STR
#print('bPyQtGraph QT_VERSION_STR=', QT_VERSION_STR)

from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import pyqtgraph.exporters # see saveStackMovie()

from contextlib import ExitStack # for conditional with in saveStackMovie()
import cv2 # to export avi files in saveStackMovie()
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
# Only classes that inherit from QObject have the ability to create signals
class bPyQtGraphRoiList(QtCore.QObject):
	"""
	list of pyqtgraph rois, embedded in self.parentPlotWidget

	this is really just using
		self.parentPlotWidget.mySimpleStack.annotationList
	todo: don't make it a copy, make it use annotationList directly
	"""

	"""
	we need to signal/slot to self.parentPlotWidget (e.g. bPyQtGraph)
	about changes in rois

	roiNewRoiSignal = QtCore.Signal(object)
	roiChangeRoiSignal = QtCore.Signal(object)
	roiDeleteRoiSignal = QtCore.Signal(object)
	"""

	def __init__(self, parent):
		"""
		parent: bPyQtGraph
		"""
		super(bPyQtGraphRoiList, self).__init__(parent=parent)

		self.parentPlotWidget = parent

		self._myAnnotationList = self.parentPlotWidget.mySimpleStack.annotationList

		#self.myRoiList = []
		self.mySelectedRoi = None
		self.justGotClicked = False

	def getAnnotationList(self):
		return self._myAnnotationList

	'''
	def slot_hover(self, e):
		print('myROI_hover() e:', e)
	'''

	def _findItemByIndex(self, annotationIdx):
		"""
		return the pyqtgraph roi OBJECT POINTER corresponding to annotationIdx
		use item.property('bAnnotationIndex')
		return None if not found
		"""
		foundItem = None
		items = self.parentPlotWidget.getViewBox().allChildren()
		for item in items:
			if isinstance(item, QtWidgets.QGraphicsRectItem):
				continue
			bAnnotationIndex = item.property('bAnnotationIndex')
			#print('  _findItemByIndex() bAnnotationIndex:', bAnnotationIndex, type(bAnnotationIndex))
			if bAnnotationIndex == annotationIdx:
				foundItem = item
				break
		return foundItem

	def _decriment_bAnnotationIndex(self, deletedAnnotationIdx):
		"""
		after delete, decriment remaining roi items who have
		item.property('bAnnotationIndex') > deletedAnnotationIdx

		todo: this is nasty and bug filled
		todo: stop keeping 2 copies of these object lists
		todo: look into using data list widget rather than list widget
		"""
		print('_decriment_bAnnotationIndex() deletedAnnotationIdx:', deletedAnnotationIdx)

		# I am not sure what allChildren() is returning
		# I just want a list of pyqtgraph rio and not sure how to get it
		items = self.parentPlotWidget.getViewBox().allChildren()

		for item in items:
			print('  item is type:', type(item))

			# I am not sure the scope/extent of items
			if isinstance(item, QtWidgets.QGraphicsRectItem):
				continue

			bAnnotationIndex = item.property('bAnnotationIndex')
			# todo: lots of items here, not all are roi with property 'bAnnotationIndex'
			if bAnnotationIndex is None:
				continue
			print('_decriment_bAnnotationIndex bAnnotationIndex:', bAnnotationIndex, 'type:', type(bAnnotationIndex))
			if bAnnotationIndex > deletedAnnotationIdx:
				newAnnotationIdx = bAnnotationIndex - 1
				print('  decrementing bAnnotationIndex:', bAnnotationIndex, 'to newAnnotationIdx:', newAnnotationIdx)
				item.setProperty('bAnnotationIndex', newAnnotationIdx)

	def selectByIdx(self, annotationIdx):
		"""
		selections coming from main interface
		it does not know object, only index

		annotationIdx: can be None
		"""
		print('bPyQtGraphRoiList.selectByIdx() annotationIdx:', annotationIdx)
		if annotationIdx is None:
			self.selectRoi(None)
		else:
			# I want this to be items()
			item = self._findItemByIndex(annotationIdx)
			self.selectRoi(item)
			'''
			items = self.parentPlotWidget.getViewBox().allChildren()
			for item in items:
				bAnnotationIndex = item.property('bAnnotationIndex')
				print('  bAnnotationIndex:', bAnnotationIndex, type(bAnnotationIndex))
				if bAnnotationIndex == annotationIdx:
					self.selectRoi(item) # make it 'blue'
			'''

	def selectRoi(self, roiObject=None):
		"""
		roiObject: pg.roi
		"""
		if roiObject is None:
			# cancel
			if self.mySelectedRoi is not None:
				# we are using red as default color
				self.mySelectedRoi.setPen(pg.mkPen('r'))
				self.mySelectedRoi = None
		else:
			# select

			# cancel previous selection
			if self.mySelectedRoi is not None:
				self.mySelectedRoi.setPen(pg.mkPen('r'))

			# update selected roi
			self.mySelectedRoi = roiObject
			self.mySelectedRoi.setPen(pg.mkPen('b'))

			# somehow we need to select an roi, like if it was created with 'a'+click
			# like
			'''
			self.selectAnnotation(annotationIndex)
			# emit
			myEvent = bimpy.interface.bEvent('select annotation', nodeIdx=annotationIndex)
			self.selectAnnotationSignal.emit(myEvent)
			'''


	def slot_clicked(self, e):
		"""
		user clicked directly on the annotation roi (in this view)
		"""
		annotationIdx = e.property('bAnnotationIndex')
		print('bPyQtGraphRoiList.slot_clicked() annotationIdx:', annotationIdx, 'e:', e)

		self.justGotClicked = True

		# visually select the roi, usually 'blue'
		self.selectRoi(e)

		# tell the parent to emit an ROI was selected
		self.parentPlotWidget.selectAnnotation(annotationIdx, doEmit=True)

	'''
	def slot_removeRequested(self, e):
		"""
		(1) remove from view
		(2) remove from
		"""
		print('bPyQtGraphRoiList.slot_removeRequested()')
	'''

	def deleteByIndex(self, roiIdx):
		"""
		when user hits 'del' key in myPyQtGraphWidget
		we do not know the item object
		"""
		print('  bPyQtGraphRoiList.deleteByIndex() roiIdx:', roiIdx)
		item = self._findItemByIndex(roiIdx)
		if item is None:
			print('  error: did not find roi item with property "bAnnotationIndex" of roiIdx:', roiIdx)
		else:
			print('  deleteByIndex() is removing roi item with roiIdx:', roiIdx, 'item:', item)
			self.parentPlotWidget.getViewBox().removeItem(item)
			self._decriment_bAnnotationIndex(roiIdx)
			# refresh ???

	'''
	def slot_changed(self, e):
		"""
		e: pyqtgraph.graphicsItems.ROI.RectROI
		"""
		return
		"""
		state = e.getState() #self.myRectROI.getState()
		pos = state['pos'] # (horizontal, vertical)
		size = state['size']
		print('myROI_changed() pos:', pos, 'size:', size)
		"""
	'''

	def getState(self, e):
		print('getState()', type(e))

		roiType = None
		if isinstance(e, pyqtgraph.graphicsItems.ROI.RectROI):
			roiType = 'rectROI'
		elif isinstance(e, pyqtgraph.graphicsItems.ROI.LineROI):
			roiType = 'lineROI'
		elif isinstance(e, pyqtgraph.graphicsItems.ROI.CircleROI):
			roiType = 'circleROI'

		if roiType is None:
			print('  bPyQtGraphRoiList.getState() defaulting to roiTye:rectROI')
			roiType = 'rectROI'

		# roiState is in pyqtgraph coordinates (horz, vert)
		# for lineROI, size is (length, width)
		roiState = e.getState() # dict with 'pos(Point)', 'size(Point)', 'angle(FLoat)'
		sceneHandlePositions = e.getSceneHandlePositions()
		#localHandlePositions = e.getLocalHandlePositions()
		print('  roiState:', roiState)
		#print('  sceneHandlePositions:', sceneHandlePositions)
		#print('  sceneHandlePositions:')
		#print('    ', sceneHandlePositions[0][1]) # one end
		#print('    ', sceneHandlePositions[1][1]) # other end
		#print('    ', sceneHandlePositions[2][1]) # middle
		# sceneHandlePositions is list with (None, Point)
		handleList = []
		for handle in sceneHandlePositions:
			thePnt = handle[1]
			pnt1 = (thePnt.x(), thePnt.y())
			handleList.append(pnt1)

		retDict = OrderedDict()
		retDict['type'] = roiType
		retDict['pos'] = (roiState['pos'].x(), roiState['pos'].y())
		retDict['size'] = (roiState['size'].x(), roiState['size'].y())
		#retDict['angle'] = roiState['angle'] # seem to need to divide by 360 to get it correct?
		retDict['handleList'] = handleList
		retDict['lineWidth'] = 1
		return retDict


	def slot_changeFinished(self, e):
		print('myROI_changed_finished()')
		print('  need to emit that annotation has changed')

		# emit signal that roi has changed
		emitState = self.getState(e)
		print('  emitState:', emitState)
		#self.changeFinished.emit(emitState)
		self.parentPlotWidget.roiChangeFinished(emitState)

	def populate(self, theAnnotationList):
		"""
		theAnnotationList: bimpy.bAnnotationList

		called when loading stack with
			self.parentPlotWidget.mySimpleStack.annotationList

		"""
		m = theAnnotationList.numItems()
		for annotIdx in range(m):
			itemDict = self.getAnnotationList().getAnnotationDict(annotIdx)
			print('  populate()', annotIdx, itemDict)
			type = itemDict['type']
			x = itemDict['x']
			y = itemDict['y']
			size = itemDict['size']
			lineWidth = itemDict['lineWidth']
			self.new(type, pos, size, lineWidth, useThisIdxOnLoad=annotIdx, emitNew=False)

	def new(self, type, pos, size=(20,20), lineWidth=1, useThisIdxOnLoad=None, emitNew=True):
		"""
		type: (rectROI, lineROI, circleROI)
		pos: (x,y), position of roi (usually where user clicked)
		size: (w,h),
		lineWidth: int,
		useThisIdxOnLoad: used by self.populate
		emitNew:

		use this when loading from bAnnotationList
		todo: need param to ay emitNew=False
		"""
		print(f'  bPyQtGraphRoiList.new() type:{type}, pos:{pos}, size:{size}')

		# what the user is looking at
		viewRect = self.parentPlotWidget.getViewBox().viewRect() # (l, t, w, h)

		# pos is in numpy (vert, horz)
		flippedPos = (pos[1], pos[0]) # flipped

		if type == 'rectROI':
			# centered: If True, scale handles affect the ROI relative to its center, rather than its origin.
			newROI = pg.RectROI(flippedPos, size,
								pen=(0,9),invertible=True,centered=False)
		elif type == 'circleROI':
			newROI = pg.CircleROI(flippedPos, size,
								pen=(0,9),invertible=True)
		elif type == 'lineROI':
			lineWidth = 1
			# pos1: The position of the center of the ROI’s left edge.
			# pos2: The position of the center of the ROI’s right edge.
			pos1 = flippedPos
			pos2 = [sum(x) for x in zip(pos1, size)] #list(map(add, pos, size))
			newROI = pg.LineROI(pos1, pos2,
								pen=(0,9),invertible=True,
								width=lineWidth)

		# this works but not needed?
		#newROI.sigRegionChanged.connect(self.slot_changed)
		newROI.sigRegionChangeFinished.connect(self.slot_changeFinished)

		# this is handled by parent
		#newROI.sigRemoveRequested.connect(self.slot_removeRequested)

		# clicking is disabled by default to prevent stealing
		# clicks from objects behind the ROI
		newROI.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
		# this works but not needed?
		#newROI.sigHoverEvent.connect(self.slot_hover)
		newROI.sigClicked.connect(self.slot_clicked)

		#
		# add to parent
		self.parentPlotWidget.getViewBox().addItem(newROI)

		#
		# add to bAnnotationList
		newAnnotationIdx = useThisIdxOnLoad
		if emitNew:
			x = pos[0] # pos is already in numpy (vert,horz)
			y = pos[1]
			z = 0
			newAnnotationIdx = self.getAnnotationList().addAnnotation(type, x, y, z, size=size)

		newROI.setProperty('bAnnotationIndex', newAnnotationIdx)

		return newAnnotationIdx

	'''
	def keyReleaseEvent(self, event):
		print(f'=== bPyQtGraphRoiList.keyReleaseEvent() event.text() {event.text()}')
		if self.mySelectedRoi is not None:
			print('  on del key, delete roi self.mySelectedRoi:', self.mySelectedRoi)
	'''

###########################################################################
class myPyQtGraphPlotWidget(pg.PlotWidget):
	roiChangeFinishedSignal = QtCore.Signal(object)
	setSliceSignal = QtCore.Signal(str, object)
	selectNodeSignal = QtCore.Signal(object)
	selectEdgeSignal = QtCore.Signal(object)
	selectAnnotationSignal = QtCore.Signal(object)
	#
	tracingEditSignal = QtCore.Signal(object) # on new/delete/edit of node, edge, slab
	#
	# not implemented, what did this do? see class bStackView
	displayStateChangeSignal = QtCore.Signal(str, object)

	def roiChangeFinished(self, roiDict):
		print('todo: (i) add handle position to dict and (ii) map scene coordinates of handle tim image coordinateds')
		# roiDict has handles, we need to map from scene to image coordinates
		# imagePos = self.myImage.mapFromScene(event.pos())

		# only use this for lineROI, use (pos, size) for rectROI
		for handlePnt in roiDict['handleList']:
			# handlePnt is pyqtgraph coords (h,v)
			imagePos = self.myImage.mapFromScene(handlePnt[0], handlePnt[1])
			print('roiChangeFinished() imagePos:', imagePos)

		# convert scene to image coordinates

		self.roiChangeFinishedSignal.emit(roiDict)

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

		# a caiman selection
		# first I tried an image but this caused opacity of raw data to get dimmed
		# in the end I am using a pg.ScatterPlotItem()
		'''
		caimanData = np.zeros((1,1,1))
		self.myCaimanImage = pg.ImageItem(caimanData)
		self.myCaimanImage.setZValue(10) # make sure this image is on top
		#self.myCaimanImage.setOpacity(0.5)
		self.addItem(self.myCaimanImage)
		'''

		#self.myCaimanROI = pg.PlotCurveItem()
		self.myCaimanROI = pg.ScatterPlotItem()
		self.myCaimanROI.setSize(4)
		self.addItem(self.myCaimanROI)
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
		self.myAnnotationPlotAllZ = True # abb caiman
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

		# 20201024 playing with rois to extract GCaMP6 signals
		self.myRoiList = bPyQtGraphRoiList(self)
		self.myClickMode = 'drag' #(drag, lineROI, rectROI, circleROI)


	def setCaimanImage(self, caimanIdx):
		"""
		caimanIdx : pass None to remove selection
		"""
		caimanDict = self.mySimpleStack.annotationList.caimanDict # caimanDict is loaded from h5f file
																# see bimpy.analysis.caiman.readCaiman

		if caimanDict is None:
			# no caiman analysis loaded
			return

		#caimanData = bimpy.analysis.caiman.getImage(caimanDict, caimanIdx)
		if caimanIdx is None:
			#caimanData = np.zeros((1,1))
			#caimanData[:] = np.nan
			xCaiman = []
			yCaiman = []
		else:
			# get a list of rois
			xCaiman = []
			yCaiman = []
			numCaimanRegions = bimpy.analysis.caiman.getNumRegions(caimanDict)
			roiList = range(numCaimanRegions)
			print('setCaimanImage() from roiList:', roiList)
			for roiIdx in roiList:
				caimanData = bimpy.analysis.caiman.getRing(caimanDict, roiIdx)
				xyList = np.argwhere(caimanData).tolist()
				xCaiman += [x for (x,y) in xyList] # make a list of x points (in the mask)
				yCaiman += [y for (x,y) in xyList] # make a list of y points (in the mask)
		'''
		originalShape = caimanDict['originalShape']
		caimanData = np.reshape(caimanDict['A'][:,caimanIdx].toarray(), originalShape, order='F')
		'''

		#self.myCaimanImage = pg.ImageItem(caimanData)
		'''
		levels = None
		autoLevels = True
		self.myCaimanImage.setImage(caimanData, levels=levels, autoLevels=autoLevels)
		'''

		# was working for one roi
		'''
		# convert 2d image mask to list of (x,y) points
		xyList = np.argwhere(caimanData).tolist()
		#print('  xyList:', xyList)
		xCaiman = [x for (x,y) in xyList] # make a list of x points (in the mask)
		yCaiman = [y for (x,y) in xyList] # make a list of y points (in the mask)
		'''


		nodePenSize = self.options['Tracing']['nodePenSize']

		#self.myCaimanROI.setData(xCaiman, yCaiman, connect='pairs')
		#self.myCaimanROI.setData(xCaiman, yCaiman, pen=None, brush='r', connect='pairs')
		#self.myCaimanROI.setData(pos=xyList)
		self.myCaimanROI.setData(yCaiman, xCaiman,
								pen=None, brush='r', size=nodePenSize) # flipped

		'''
		colorLut = self.myColorLutDict['red'] # like (green, red, blue, gray, gray_r, ...)
		self.myCaimanImage.setLookupTable(colorLut, update=True)
		'''

		#
		# force update?
		self.update()

	def getCurrentSlice(self):
		return self.currentSlice

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

			if self.myAnnotationPlotAllZ:
				xNodeMasked = xAnnotationArray
				yNodeMasked = yAnnotationArray
			else:
				# traditional
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

		# annotations are sharing node pen size
		nodePenSize = self.options['Tracing']['nodePenSize']

		#
		# update
		#self.myAnnotationPlot.setData(xNodeMasked, yNodeMasked, symbolSize=nodePenSize)
		self.myAnnotationPlot.setData(yNodeMasked, xNodeMasked, symbolSize=nodePenSize) # flipped

	def drawSlabLine(self, slabIdx=None):
		"""
		draw one slab as a line orthogonal to edge
		"""
		print('bPyQtGraph.drawSlabLine() slabIdx:', slabIdx)

		if slabIdx is None:
			slabIdx = self.selectedSlab()
		if slabIdx is None:
			return

		xSlabPlot, ySlabPlot = \
			self.mySimpleStack.myLineProfile.getSlabLine2(slabIdx)

		if xSlabPlot is None or ySlabPlot is None:
			return None

		# draw in window
		self.mySlabPlotOne.setData(ySlabPlot, xSlabPlot) # flipped

		displayThisStack = self.displayStateDict['displayThisStack']
		profileDict = {
			'slabIdx': slabIdx,
			'slice': self.currentSlice,
			'displayThisStack': displayThisStack,
			'xSlabPlot': xSlabPlot,
			'ySlabPlot': ySlabPlot,
		}

		self.mainWindow.signal('update line profile', profileDict)

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

		self.setCaimanImage(None)
		self.myRoiList.selectRoi(None) # abb 20201024

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

	def selectEdgeList(self, edgeList, snapz=False, nodeIdx=None, colorList=None):
		"""
		Select a list of edges

		nodeIdx: If given (ans snapz) then snap to the z of the node
		colorList: can be []

		we are snapping to the middle of the first edge edgeList[0]
		"""

		# todo: fix this, what am i passing for colorList ????
		if colorList is None or len(colorList)==0:
			colorList = ['r', 'g', 'b', 'm']

		print('  selectEdgeList() edgeList:', edgeList, 'colorList:', colorList)

		self.displayStateDict['selectedEdgeList'] = []

		xList = []
		yList = []
		#slabList = []
		symbolBrushList = []
		colorIdx = 0
		for idx, edgeIdx in enumerate(edgeList):
			theseSlabs = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
			numSlabs = len(theseSlabs)

			xList += self.mySimpleStack.slabList.x[theseSlabs].tolist()
			yList += self.mySimpleStack.slabList.y[theseSlabs].tolist()

			# make a list of pg.mkColor using colorList[colorIdx]
			symbolBrushList += [pg.mkColor(colorList[colorIdx]) for tmp in range(numSlabs)]

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

		if snapz:
			# snap to the first edge
			edgeIdx = edgeList[0]

			#tmpEdgeDict = self.mySimpleStack.slabList.getEdge(edgeIdx)
			#z = tmpEdgeDict['z']
			if nodeIdx is not None:
				z = self.mySimpleStack.slabList.getNode_zSlice(nodeIdx)
			else:
				z = self.mySimpleStack.slabList.edgeDictList[edgeIdx]['z']
				z = int(z)
			self.setSlice(z)

			# snap to point
			# get the (x,y) of the middle slab
			if nodeIdx is not None:
				tmpx, tmpy, tmpz = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)
			else:
				tmpEdgeDict = self.mySimpleStack.slabList.getEdge(edgeIdx)
				tmp_nSlab = tmpEdgeDict['nSlab']
				middleSlab = int(tmp_nSlab/2)
				middleSlabIdx = tmpEdgeDict['slabList'][middleSlab]
				tmpx, tmpy, tmpz = self.mySimpleStack.slabList.getSlab_xyz(middleSlabIdx)
			# do the zoom
			self._zoomToPoint(tmpy, tmpx) # flipped

		# flash edge list
		QtCore.QTimer.singleShot(10, lambda:self._flashEdgeList(edgeList, 2))

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
		"""
		called when
			(1) annotation is selected from list AND
			(2) when user clicks on pyqtgraph roi
		"""
		if annotationIdx is not None:
			annotationIdx = int(annotationIdx)

		self.displayStateDict['selectedAnnotation'] = annotationIdx

		# select a pyqtgraph roi (can be none)
		# todo: this is redundant, *this is being called when user clicks
		# via self.myRoiList.slot_Clicked()
		self.myRoiList.selectByIdx(annotationIdx)

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

				#self._zoomToPoint(x, y)
				self._zoomToPoint(y, x) # flipped

			# update
			x = [x]
			y = [y]
			# abb 20201026
			self.myAnnotationPlotSelection.setData(y, x) # flipped
			#self.myAnnotationPlotSelection.setData(x, y) # flipped

			# select caiman, will fail if not loaded
			self.setCaimanImage(annotationIdx)

			QtCore.QTimer.singleShot(20, lambda:self.flashAnnotation(annotationIdx, 2))


		# self.myRoiList does NOT respond to this
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

	def _flashEdgeList(self, edgeList, on):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashEdge() edgeIdx:', edgeIdx, on)
		if edgeList is None or len(edgeList)==0:
			return
		if on:
			# todo: probably slow !!!
			theseIndicesList = []
			xMasked = []
			yMasked = []
			for edgeIdx in edgeList:
				# theseIndices is a list
				theseIndices = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
				theseIndicesList = theseIndicesList + theseIndices
				xMasked = xMasked + self.mySimpleStack.slabList.x[theseIndices].tolist()
				xMasked = xMasked + [np.nan]
				yMasked = yMasked + self.mySimpleStack.slabList.y[theseIndices].tolist()
				yMasked = yMasked + [np.nan]
			self.myEdgeSelectionFlash.setData(yMasked, xMasked) # flipped
			#
			QtCore.QTimer.singleShot(20, lambda:self._flashEdgeList(edgeList, False))
		else:
			self.myEdgeSelectionFlash.setData([], [])

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
					try:
						colorLut = self.myColorLutDict[colorLutStr] # like (green, red, blue, gray, gray_r, ...)
						self.myImage.setLookupTable(colorLut, update=True)
					except (KeyError) as e:
						print(f'warning: bPyQtSetSlice() color lut {colorLutStr} is not defined, possible colors are {self.myColorLutDict.keys()}')
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

		# this does not work because of recursion !!!
		'''
		print('\n\nbPyQtGraph debugging saveStackMovie() ... REMOVE\n\n')
		self.saveStackMovie()
		'''

	def saveStackMovie(self):
		"""
		save  stack as a movie

		for now this saves a number of files, need to process them in Fiji???

		todo:
		   when we are zoomed,
		   it seems to save the full FOV with the movie in the middle?????????
		"""
		fileType = 'avi' #'tiff'
		fps = 20.0
		startSlice = 0 #271
		stopSlice = self.mySimpleStack.numSlices #477
		stepSlice =  1

		#saveFolder = '/home/cudmore/Desktop/pyqtgraph-movie'

		# get the name of our stack to make a file name
		myStackPath = self.mySimpleStack.path
		mySaveFolder, stackFileName = os.path.split(myStackPath)
		saveMoviewBaseName, tmpExt = os.path.splitext(stackFileName)

		print('bPyQtGraph.saveStackMovie()')
		#print('  saving movie to multiple files in:', saveFolder)
		print('  mySaveFolder:', mySaveFolder)
		print('  saveMoviewBaseName:', saveMoviewBaseName)
		print('  startSlice:', startSlice, 'stopSlice:', stopSlice)

		# set to first slice
		#self.setSlice(startSlice)

		theSliceRange = range(startSlice, stopSlice, stepSlice)

		# get width/height for cv2
		exporter = pg.exporters.ImageExporter(self.scene())
		theBytes = exporter.export(toBytes=True)
		width = theBytes.width()
		height = theBytes.height()
		print('  width:', width)
		print('  height:', height)

		if fileType =='tif':
			saveFile = saveMoviewBaseName + '_bimpy_movie.tif' #'/home/cudmore/Desktop/onetiff.tif'
			savePath = os.path.join(mySaveFolder,saveFile )
		elif fileType == 'avi':
			saveFile = saveMoviewBaseName + '_bimpy_movie.avi' #'/home/cudmore/Desktop/onetiff.tif'
			savePath = os.path.join(mySaveFolder,saveFile)
			# REMEMBER, DO NOT USE cv2.VideoWriter_fourcc(*'MJPG')
			myFile = cv2.VideoWriter(savePath,
									#cv2.VideoWriter_fourcc(*'MJPG'),
									cv2.VideoWriter_fourcc('M','J','P','G'),
									fps, (width,height), isColor=True)

		print('  saving to savePath:', savePath)

		#with tifffile.TiffWriter(oneTiffFile, bigtiff=True) as myTiffFile:
		with ExitStack() as stack:

			if fileType == 'tiff':
				myFile = stack.enter_context(tifffile.TiffWriter(savePath))
			'''
			elif fileType == 'avi':
				myFile = stack.enter_context(cv2.VideoWriter(saveFile,
										cv2.VideoWriter_fourcc(*'MJPG'),
										fps, (width,height)))
			'''

			for i in theSliceRange:
				self.setSlice(i)

				# this works, to just save the image
				#exporter = pg.exporters.ImageExporter(self.myImage)

				# this works to save the scene
				exporter = pg.exporters.ImageExporter(self.scene())

				#exporter.export('/home/cudmore/Desktop/pyqtgraph-movie/fileName.png')
				'''
				iStr = str(i)
				thisFileNameNumber = iStr.zfill(4)
				thisFileName = saveMoviewBaseName + '_' + thisFileNameNumber + '.tif'
				thisFilePath = os.path.join(saveFolder, thisFileName)
				#print('  saving thisFilePath:', thisFilePath)
				'''

				# this works fine
				#exporter.export(thisFilePath)

				# toBytes returns <class 'PyQt5.QtGui.QImage'>
				theBytes = exporter.export(toBytes=True)

				theBytes = theBytes.convertToFormat(QtGui.QImage.Format.Format_RGB32)

				#width = theBytes.width()
				#height = theBytes.height()

				ptr = theBytes.bits()
				ptr.setsize(height * width * 4)
				arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
				#print(i, arr.shape, arr.dtype)

				# append to open tiff file !!!
				# newer version of tifffile us ethis
				#myTiffFile.write(arr)
				if fileType == 'tiff':
					myFile.save(arr) # newer version of tifffile use write()
				elif fileType == 'avi':
					#print('  writing arr', arr.shape, arr.dtype)
					myFile.write(arr[:,:,0:-1])
					#myFile.write(arr)
		#
		if fileType == 'avi':
			myFile.release()
		print('  done')

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

	def toggleTracing(self):
		self.displayStateDict['showNodes'] = not self.displayStateDict['showNodes']
		self.displayStateDict['showEdges'] = not self.displayStateDict['showEdges']
		self.displayStateDict['showAnnotations'] = not self.displayStateDict['showAnnotations']
		self.setSlice() # refresh

	# abb 20201024 put back in working on rois
	# this seems to early in the event call chain
	# try to get it working with onMouseClicked_scene()
	'''
	def mousePressEvent(self, event):
		"""
		This is a PyQt callback (not PyQtGraph)
		Set event.setAccepted(False) to keep propogation so we get to PyQt callbacks like
			self.onMouseClicked_scene(), _slabs(), _nodes()

		event: PyQt5.QtGui.QMouseEvent
		"""

		print('bPyQtGraph.mousePressEvent() self.myClickMode:', self.myClickMode)

		if self.myClickMode in ['lineROI', 'rectROI', 'circleROI']:
			# when we are in click mode for new roi, annotation selection is off
			x = event.pos().x()
			y = event.pos().y()
			pos = (x,y)
			print('  make a new roi!!! pos:', pos)
			self.myRoiList.new((x,y), self.myClickMode)
			event.setAccepted(False)
		else:
			# assuming self.myClickMode == 'drag'
			event.setAccepted(False)
			super().mousePressEvent(event)

		# was this
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
		"""
	'''

	def mouseReleaseEvent(self, event):
		event.setAccepted(False)
		super().mouseReleaseEvent(event)

	def keyPressEvent(self, event):
		"""
		event: <PyQt5.QtGui.QKeyEvent object at 0x13e1f7410>
		"""

		if event.text() == 'm':
			print('=== bPyQtGraph.keyPressEvent() m')
			self.slot_setClickMode('drag')
			return

		# event.key() is a number
		'''
		if event.text() != 'e':
			print(f'=== myPyQtGraphPlotWidget.keyPressEvent() event.text() "{event.text()}"')
		'''

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
		#elif event.key() == QtCore.Qt.Key_1:
		#	self.displayStateChange('displayThisStack', value=1)
		#elif event.key() == QtCore.Qt.Key_2:
		#	self.displayStateChange('displayThisStack', value=2)
		#elif event.key() == QtCore.Qt.Key_3:
		#	self.displayStateChange('displayThisStack', value=2)

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

		#elif event.key() in [QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal]:
		#	# increase tracing
		#	self.incrementDecrimentTracing('increase')
		#elif event.key() == QtCore.Qt.Key_Minus:
		#	# decrease tracing
		#	self.incrementDecrimentTracing('decrease')

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
			'''
			self.displayStateDict['showNodes'] = not self.displayStateDict['showNodes']
			self.displayStateDict['showEdges'] = not self.displayStateDict['showEdges']
			self.displayStateDict['showAnnotations'] = not self.displayStateDict['showAnnotations']
			self.setSlice() # refresh
			'''
			self.toggleTracing()
		#elif event.key() in [QtCore.Qt.Key_Z]:
		#	self.displayStateChange('displaySlidingZ', toggle=True)

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


		imagePos = self.myImage.mapFromScene(event.pos())
		slabPos = self.mySlabPlot.mapFromScene(event.pos())

		# pyqtgraph coords (horz,vert)
		x = imagePos.x()
		y = imagePos.y()
		z = self.currentSlice

		print('=== myPyQtGraphPlotWidget.onMouseClicked_scene() imagePos is x:', x, 'y:', y, 'eKeyIsDown:', eKeyIsDown)
		print('  remeber that in pyqtGraph that x is horz and y is vertical')
		print('  this is opposed to numpy with x as vertical or top/bottom and y as horizontal ;eft/right !!!!!!!!!!!!!!!!')
		# abb 20201024 working on rois
		# moved this to self.mousePressEvent()
		# nope, can't get mousePressEvent() to work
		# for now, a single click will create an roi,
		# user then need to click again to modify
		if self.myRoiList.justGotClicked:
			# this halts signal propogation
			print('  user just clicked on an existing roi .. do nothing')
			self.myRoiList.justGotClicked = False
		else:
			if self.myClickMode in ['lineROI', 'rectROI', 'circleROI']:
				print('  user clicked in empty area ... make a new roi with ... self.newAnnotation()')
				print('    THIS IS NO LONGER HANDLING CLICKS ON EXISTING V1 blue ANNOTATIONS !!!!!!!!!!!!!!!!!!!')
				#self.myRoiList.new(self.myClickMode, pos=(x,y))

				# flip it
				#self.newAnnotation(x, y, z, type=self.myClickMode)
				self.newAnnotation(y, x, z, type=self.myClickMode) # flipped
				return

		##
		##

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

	# abb oct2020 to handle +/- tracing sliding z
	def slot_OptionsStateChange(self, key1, key2, value):
		print('    myPyQtGraphPlotWidget.slot_OptionsStateChange()', key1, key2, value)
		if key1 == 'Tracing':
			if key2 in ['showTracingAboveSlices', 'showTracingBelowSlices']:
				self.mainWindow.getStackView()._preComputeAllMasks()
				self.mainWindow.getStackView().setSlice()

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
		snapz = myEvent.snapz
		nodeIdx = myEvent.nodeIdx # used to snapz when given 2x (joined) edges
		edgeList = myEvent.edgeList
		colorList = myEvent.colorList # can be []
		if len(edgeList)>0:
			# select a list of edges
			# abb oct2020 removed snapz
			#self.selectEdgeList(edgeList, colorList=colorList, snapz=True)
			self.selectEdgeList(edgeList, snapz=snapz, nodeIdx=nodeIdx, colorList=colorList)
		else:
			# select a single edge
			edgeIdx = myEvent.edgeIdx
			slabIdx = myEvent.slabIdx
			#snapz = myEvent.snapz
			isShift = myEvent.isShift
			self.selectEdge(edgeIdx, snapz=snapz, isShift=isShift)
		self.selectNode(myEvent.nodeIdx)
		self.selectSlab(myEvent.slabIdx)

	def slot_selectAnnotation(self, myEvent):
		myEvent.printSlot('myPyQtGraphPlotWidget.slot_selectAnnotation()')

		'''
		# todo: caimen is not a special event, look for loaded caimen in slots
		if myEvent.eventType == 'select caiman':
			print('pyqtgraph.slot_selectAnnotation() select caiman', myEvent.nodeIdx, '!!!')
			caimanIdx = myEvent.nodeIdx
			self.setCaimanImage(caimanIdx)
		'''

		# todo: logic here is bad, we already selected caiman and now alist?
		if len(myEvent.nodeList) > 0:
			self.selectNodeList(myEvent.nodeList)
		else:
			annotationIdx = myEvent.nodeIdx
			snapz = myEvent.snapz
			isShift = myEvent.isShift
			self.selectAnnotation(annotationIdx, snapz=snapz, isShift=isShift)

	def slot_setClickMode(self, newMode):
		"""
		click mode changes how clicks are interpreted, default is drag
			drag: drag image (default)
			lineROI:
			rectROI:
			circleROI:
		"""

		# for debugging, just cycle mode
		if self.myClickMode == 'drag':
			newMode = 'lineROI'
		elif self.myClickMode == 'lineROI':
			newMode = 'rectROI'
		elif self.myClickMode == 'rectROI':
			newMode = 'circleROI'
		elif self.myClickMode == 'circleROI':
			newMode = 'drag'

		# put this back in
		self.myClickMode = newMode

		print('slot_setClickMode() myClickMode:', self.myClickMode)

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
				print('\n=== myPyQtGraphPlotWidget.myEvent() ... deleteSelection delete annotation:', deleteAnnotationIdx)
				print('  todo: move this annotationList.deleteAnnotation into bPyQtGraphRoiList')
				wasDeleted = self.mySimpleStack.annotationList.deleteAnnotation(deleteAnnotationIdx)
				if wasDeleted:
					print('  todo: abb roi, need to delete visual roi in myRoiList')

					#
					self.selectAnnotation(None) # the old v1 blue selection (not pyqtgraph rois)
					self.myRoiList.deleteByIndex(deleteAnnotationIdx) # the new list of pyqtgraph roi

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
			# see bTableWidget2.menuActionHandler
			print('  bPyQtGraph.myEvent() type: setType')
			objectType = event['objectType'] # like ('nodes', 'edges')
			newValue = event['newValue'] # like (1,2,3,...)
			objectIdx = event['objectIdx']
			#
			# make backend change
			if objectType == 'nodes':
				self.mySimpleStack.slabList.setNodeType(objectIdx, newValue)
			elif objectType == 'edges':
				self.mySimpleStack.slabList.setEdgeType(objectIdx, newValue)
			#
			# emit events
			if objectType == 'nodes':
				newNodeDict = self.mySimpleStack.slabList.getNode(objectIdx)
				myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=objectIdx, nodeDict=newNodeDict)
			elif objectType == 'edges':
				newEdgeDict = self.mySimpleStack.slabList.getEdge(objectIdx)
				myEvent = bimpy.interface.bEvent('updateEdge', edgeIdx=objectIdx, edgeDict=newEdgeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='setIsBad':
			objectType = event['objectType'] # like ('nodes', 'edges')
			newValue = event['newValue'] # like (True, False)
			objectIdx = event['objectIdx']
			#
			# make backend changes
			if objectType == 'nodes':
				self.mySimpleStack.slabList.setNodeIsBad(objectIdx, newValue)
			elif objectType == 'edges':
				self.mySimpleStack.slabList.setEdgeIsBad(objectIdx, newValue)
			elif objectType == 'annotations':
				self.mySimpleStack.annotationList.setAnnotationIsBad(objectIdx, newValue)
			#
			# emit a signal
			if objectType == 'nodes':
				newNodeDict = self.mySimpleStack.slabList.getNode(objectIdx)
				myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=objectIdx, nodeDict=newNodeDict)
			elif objectType == 'edges':
				newEdgeDict = self.mySimpleStack.slabList.getEdge(objectIdx)
				myEvent = bimpy.interface.bEvent('updateEdge', edgeIdx=objectIdx, edgeDict=newEdgeDict)
			elif objectType == 'annotations':
				newAnnotationDict = self.mySimpleStack.annotationList.getAnnotationDict(objectIdx)
				myEvent = bimpy.interface.bEvent('updateAnnotation', nodeIdx=objectIdx, nodeDict=newAnnotationDict)
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

	def newAnnotation(self, x, y, z, type='annotation'):
		"""
		add a generic annotation
		x,y: already in numpy coord x is vertical, y is horizontal
		"""
		print(f'myPyQtGraphPlotWidget.newAnnotation() type:{type}, x:{x}, y:{y}, z:{z}')

		# do not do this here, self.xxx is in charge
		#newAnnotationIdx = self.mySimpleStack.annotationList.addAnnotation(type, x, y, z)

		if type == 'annotation':
			# generic point annotation
			print('  making a generic annotation')
			# I AM SO FUCKING CONFUSED WITH THIS X/Y CRAP
			#newAnnotationIdx = self.mySimpleStack.annotationList.addAnnotation(type, x, y, z)
			newAnnotationIdx = self.mySimpleStack.annotationList.addAnnotation(type, x, y, z) # flipped
		else:
			print('  making an roi annotation with type:', type, 'in self.myRoiList')
			print('    this will show up as a pyqtgraph roi (line,square, circle)')

			# I AM SO FUCKING CONFUSED WITH THIS X/Y CRAP
			#newAnnotationIdx = self.myRoiList.new(type, pos=(x,y))
			newAnnotationIdx = self.myRoiList.new(type, pos=(x,y))

		#
		self.setSlice()

		#
		# emit changes
		annotationDict = self.mySimpleStack.annotationList.getItemDict(newAnnotationIdx)
		print('  tracingEditSignal.emit() with annotationDict:', annotationDict)
		myEvent = bimpy.interface.bEvent('newAnnotation', nodeIdx=newAnnotationIdx, nodeDict=annotationDict)
		self.tracingEditSignal.emit(myEvent)

	def loadMasks(self):
		"""
		load pickle file into self.maskedEdgesDict
		"""
		print('bPyQtGraph.loadMasks() now handled by bVascularTracing.load()')
		return True

		'''
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
		'''

	def saveMasks(self):
		"""
		save self.maskedEdgesDict to pickle file
		"""
		print('bPyQtGraph.saveMasks() now handled by bVascularTracing.save()')
		return True

		'''
		pickleFile = self.mySimpleStack._getSavePath() # tiff file without extension
		pickleFile += '.pickle'
		print('    myPyQtGraphPlotWidget.saveMasks() saving maskedNodes as pickleFile:', pickleFile)
		with open(pickleFile, 'wb') as fout:
			#pickle.dump(self.maskedNodes, fout)
			pickle.dump(self.maskedEdgesDict, fout)
		'''

def main():
	app = QtWidgets.QApplication(sys.argv)
	main = myPyQtGraphWindow2()
	main.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
