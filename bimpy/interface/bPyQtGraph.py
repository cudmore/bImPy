"""

NEEDS PyQt 5.13.0 !!!!!

see here for class diagram:
    https://stackoverflow.com/questions/45879148/pyqtgraph-help-understanding-source-code#:~:text=PyQtGraph%20will%20create%20a%20QGraphicsScene,of%20that%20view%20for%20you.

see
    https://stackoverflow.com/questions/58526980/how-to-connect-mouse-clicked-signal-to-pyqtgraph-plot-widget
    
"""

import sys  # We need sys so that we can pass argv to QApplication
import os
from collections import OrderedDict

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets

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

	#def __init__(self, *args, **kwargs):
	#	super(myPyQtGraphPlotWidget, self).__init__(*args, **kwargs)
	def __init__(self, parent=None, mySimpleStack=None):
		super(myPyQtGraphPlotWidget, self).__init__(parent=parent)

		#self.viewBox = self.addViewBox()
		#self.viewBox.setAspectLocked(True)
		
		#p1 = self.addPlot()

		#pg.setConfigOption('imageAxisOrder','row-major')
		
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
		
		self.minContrast = 0
		self.maxContrast = 255
			
		# self.myPlotWidget.plot
		# creates: <class 'pyqtgraph.graphicsItems.PlotDataItem.PlotDataItem'>

		#
		# slabs
		pen = None #pg.mkPen(color=(255, 255, 0))
		self.mySlabPlot = self.myPlotWidget.plot([], [], pen=pen, symbol='o', symbolSize=5, symbolBrush=('c'),
							connect='finite', clickable=True)
		self.mySlabPlot.sigPointsClicked.connect(self.clickedSlabPlot)
		
		self.mySlabPlotSelection = self.myPlotWidget.plot([], [], pen=pen, symbol='o', symbolSize=7, symbolBrush=('y'),
							connect='finite', clickable=False)

		self.mySlabPlotSelection2 = self.myPlotWidget.plot([], [], pen=pen, symbol='x', symbolSize=8, symbolBrush=('g'),
							connect='finite', clickable=False)

		self.myEdgeSelectionFlash = self.myPlotWidget.plot([], [],
							pen=pen, symbol='o', symbolSize=20, symbolBrush=('y'),
							connect='finite', clickable=False)

		#
		# nodes
		pen = None
		self.myNodePlot = self.myPlotWidget.plot([], [], pen=pen, symbol='o', symbolSize=8, symbolBrush=('r'))
		self.myNodePlot.sigPointsClicked.connect(self.clickedNodePlot)
		
		self.myNodePlotSelection = self.myPlotWidget.plot([], [], pen=pen, symbol='o', symbolSize=10, symbolBrush=('y'),
							connect='finite')

		self.myNodeSelectionFlash = self.myPlotWidget.plot([], [],
											pen=pen, symbol='o', symbolSize=20, symbolBrush=('y'))


		# click on scene
		#self.mySlabPlot.scene().sigMouseClicked.connect(self.onMouseClicked_scene)
		#self.mySlabPlot.scene().sigMouseMoved.connect(self.onMouseMoved_scene)

		#self.scene().sigMouseClicked.connect(self.sceneClicked)
		self.scene().sigMouseMoved.connect(self.onMouseMoved_scene)
		self.scene().sigMouseClicked.connect(self.onMouseClicked_scene) # works but confusing coordinates

		#self.myAddPlot()
		#self.myAddImage()
		
		#
		#
		self.mySimpleStack = mySimpleStack
		self._preComputeAllMasks2()
		
		self.currentSlice = 40

		self.displayStat = OrderedDict()
		self.displayStat['showNodes'] = True
		self.displayStat['showEdges'] = True
		
		self.setSlice()
		
	def plotNodes(self):
		if not self.displayStat['showNodes']:
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
		self.myNodePlot.setData(xNodeMasked, yNodeMasked)

	def plotSlabs(self):
		if not self.displayStat['showEdges']:
			xEdgeMasked = []
			yEdgeMasked = []
		else:
			showTracingAboveSlices = 3
			showTracingAboveSlices = 3
		
			index = self.currentSlice
			firstSlice = index - showTracingAboveSlices
			lastSlice = index + showTracingAboveSlices

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

		# update
		self.mySlabPlot.setData(xEdgeMasked, yEdgeMasked) #
		
	def cancelSelection(self):
		self.selectNode(None)
		self.selectEdge(None)
		self.selectSlab(None)
		
	def selectNode(self, nodeIdx, snapz=False, isShift=False):
		if nodeIdx is None:
			x = []
			y = []
			self.myNodePlotSelection.setData(x, y)
		else:
			# todo: standardize this
			nodeIdx = int(nodeIdx)
			
			x,y,z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)
	
			x = [x]
			y = [y]
			
			if snapz:
				z = int(z)
				self.setSlice(z)
			
			# update
			self.myNodePlotSelection.setData(x, y)

			QtCore.QTimer.singleShot(20, lambda:self.flashNode(nodeIdx, 2))
	
	def selectEdge(self, edgeIdx, snapz=False, isShift=False):
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
		
			# update
			self.mySlabPlotSelection.setData(xMasked, yMasked)

			QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, 2))
	
	def selectSlab(self, slabIdx):
		if slabIdx is None:
			x = []
			y = []
		else:
			slabIdx = int(slabIdx)
			x,y,z = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)

			x = [x]
			y = [y]

		# update
		self.mySlabPlotSelection2.setData(x, y)
				
	def flashNode(self, nodeIdx, numberOfFlashes):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		print('flashNode() nodeIdx:', nodeIdx, 'numberOfFlashes:', numberOfFlashes)
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

	def setSlice(self, thisSlice=None):
		
		if thisSlice is None:
			thisSlice = self.currentSlice
		else:
			self.currentSlice = thisSlice
		
		displayThisStack = 'ch1'
		#sliceImage = self.mySimpleStack.setSliceContrast(thisSlice, thisStack=displayThisStack, minContrast=self.minContrast, maxContrast=self.maxContrast)
		sliceImage = self.mySimpleStack.getImage(channel=1, sliceNum=thisSlice)
		
		#sliceImage = sliceImage[:, ::-1].T
		
		self.myImage.setImage(sliceImage)
				
		self.myImage.setLevels([self.minContrast,self.maxContrast], update=True)
		
		pos = np.array([0.0, 0.5, 1.0])
		color = np.array([[0,0,0,255], [255,128,0,255], [255,255,0,255]], dtype=np.ubyte)
		greenColor = np.array([[0,0,0,255], [0,128,0,255], [0,255,0,255]], dtype=np.ubyte)
		redColor = np.array([[0,0,0,255], [128,0,0,255], [255,0,0,255]], dtype=np.ubyte)
		grayColor = np.array([[0,0,0,255], [128,128,128,255], [255,255,255,255]], dtype=np.ubyte)
		grayInvertColor = np.array([[255,255,255,255], [128,128,128,255], [0,0,0,255]], dtype=np.ubyte)
		map = pg.ColorMap(pos, grayInvertColor)
		lut = map.getLookupTable(0.0, 1.0, 256)
		self.myImage.setLookupTable(lut, update=True)
		
		# plot slabs/nodes
		self.plotSlabs()
		self.plotNodes()
		
	# this is over-riding existing member function
	def keyPressEvent(self, event):
		"""
		event: <PyQt5.QtGui.QKeyEvent object at 0x13e1f7410>
		"""
		print('=== keyPressEvent() event:', event)

		if event.key() in [QtCore.Qt.Key_Escape]:
			self.cancelSelection()
		
		elif event.key() in [QtCore.Qt.Key_D, QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
			print('do delete')
			
		elif event.key() in [QtCore.Qt.Key_Left]:
			t = (100,100)
			#self.translateBy(t=t)
		
		elif event.key() in [QtCore.Qt.Key_T]:
			self.displayStat['showNodes'] = not self.displayStat['showNodes']
			self.displayStat['showEdges'] = not self.displayStat['showEdges']
			self.setSlice() # refresh
			
	# this is over-riding existing member function
	def wheelEvent(self, event):
		"""
		event: <PyQt5.QtGui.QWheelEvent object at 0x11d486910>
		"""
		
		'''
		print('=== wheelEvent()')
		print('  event:', event)
		'''
		
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		if modifiers == QtCore.Qt.ControlModifier:
			super(myPyQtGraphPlotWidget, self).wheelEvent(event)
		else:
			yAngleDelta = event.angleDelta().y()
			if yAngleDelta > 0:
				# mouse up
				self.currentSlice -= 1
				if self.currentSlice < 0:
					self.currentSlice = 0
			else:
				# mouse down
				self.currentSlice += 1
				if self.currentSlice > self.mySimpleStack.numSlices:
					self.currentSlice -= 1
					
			#print(event.angleDelta().y()) # always +/- the same value
			#print(event.pixelDelta().y()) # +/- and larger magnitude, if >100 then got by 5 !!!
		
			self.setSlice()

			self.setSliceSignal.emit('set slice', self.currentSlice)
			
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

	
	def zoomToPoint(self, x, y):
		xRange = self.viewRange()[0]
		#yRange = self.viewRange()[1]
		xWidth = xRange[1] - xRange[0]
		xHalfWidth = int(xWidth/2)
		xNewRange = [x-xHalfWidth, x+xHalfWidth]
		self.setRange(xRange=xRange)
		
	def onMouseClicked_scene(self, event):
		print('=== onMouseClicked_scene()', event.pos().x(), event.pos().y())
		imagePos = self.myImage.mapFromScene(event.pos())
		imagePos = self.myImage.mapFromScene(event.pos())
		slabPos = self.mySlabPlot.mapFromScene(event.pos())
		print('  event.pos():', event.pos())
		print('  imagePos:', imagePos) # slighlty off???
		print('  slabPos:', slabPos)
		
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

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		
		if isShift:
			# new node
			print('  onMouseClicked_scene() new node')
			newNodeIdx = self.mySimpleStack.slabList.newNode(x, y, self.currentSlice)

			self._preComputeAllMasks2()
			self.setSlice() #refresh
			
	def onMouseMoved_scene(self, pos):
		if 0:
			print('=== onMouseMoved_scene()', pos.x(), pos.y())
			imagePos = self.myImage.mapFromScene(pos)
			print('  imagePos:', imagePos)
			
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
	
	def clickedSlabPlot(self, item, points):
		"""
		get edge index from displayed masked edges

		item: self.mySlabPlot
		points: [<pyqtgraph.graphicsItems.ScatterPlotItem.SpotItem object at 0x13cdb6f10>]
		"""
		# this works gives me the point number!!!!
		thePoint = points[0].index()
		
		aicsSlabList_edgeIdx = self.maskedEdgesDict['aicsSlabList_edgeIdx']
		selectedEdgeIdx = aicsSlabList_edgeIdx[thePoint]
		
		aicsSlabList_slabIdx = self.maskedEdgesDict['aicsSlabList_edgeIdx']
		selectedSlabIdx = aicsSlabList_slabIdx[thePoint]

		print('=== clickedSlabPlot() thePoint:', thePoint, 'selectedEdgeIdx:', selectedEdgeIdx)
		
		self.selectEdge(selectedEdgeIdx)
		self.selectSlab(selectedSlabIdx)

		# emit
		myEvent = bimpy.interface.bEvent('select edge', edgeIdx=selectedEdgeIdx, slabIdx=selectedSlabIdx)
		self.selectEdgeSignal.emit(myEvent)
		
	def clickedNodePlot(self, item, points):
		"""
		get node index from displayed masked node
		
		item: self.myNodePlot
		points: [<pyqtgraph.graphicsItems.ScatterPlotItem.SpotItem object at 0x13cdb6f10>]
		"""
		# this works gives me the point number!!!!
		thePoint = points[0].index()

		aicsNodeList_nodeIdx = self.maskedEdgesDict['aicsNodeList_nodeIdx']
		selectedNodeIdx = aicsNodeList_nodeIdx[thePoint]
		
		print('=== clickedNodePlot()', selectedNodeIdx)
		self.selectNode(selectedNodeIdx)
		
		myEvent = bimpy.interface.bEvent('select node', nodeIdx=selectedNodeIdx)
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
		
		minContrast = myEvent.minContrast
		maxContrast = myEvent.maxContrast
		
		if minContrast is not None and maxContrast is not None:
			self.minContrast = minContrast
			self.maxContrast = maxContrast
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

	def _preComputeAllMasks2(self):
		print('_preComputeAllMasks2()')
		
		timeIt = bimpy.util.bTimer('_preComputeAllMasks2')
		
		aicsSlabList = []
		aicsSlabList_x = np.empty((0), np.float16) #[]
		aicsSlabList_y = np.empty((0), np.float16) #[]
		aicsSlabList_z = np.empty((0), np.float16) #[]
		aicsSlabList_edgeIdx = np.empty((0), np.uint16) #[]
		aicsSlabList_slabIdx = np.empty((0), np.uint16) #[]
		
		for edgeIdx, edge in enumerate(self.mySimpleStack.slabList.edgeDictList):
			tmpSlabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx) # includes nodes
			aicsSlabList += tmpSlabList + [np.nan] # abb aics
			
			# x
			aicsSlabList_x = np.append(aicsSlabList_x, self.mySimpleStack.slabList.x[tmpSlabList])
			aicsSlabList_x = np.append(aicsSlabList_x, np.nan) # abb aics
						
			# y
			aicsSlabList_y = np.append(aicsSlabList_y, self.mySimpleStack.slabList.y[tmpSlabList])
			aicsSlabList_y = np.append(aicsSlabList_y, np.nan) # abb aics
			# x
			aicsSlabList_z = np.append(aicsSlabList_z, self.mySimpleStack.slabList.z[tmpSlabList])
			aicsSlabList_z = np.append(aicsSlabList_z, np.nan) # abb aics

			# edgeIdx (needs to be float)
			aicsSlabList_edgeIdx = np.append(aicsSlabList_edgeIdx, self.mySimpleStack.slabList.edgeIdx[tmpSlabList])
			aicsSlabList_edgeIdx = np.append(aicsSlabList_edgeIdx, np.nan) # abb aics
				
			# slabIdx (needs to be float)
			aicsSlabList_slabIdx = np.append(aicsSlabList_slabIdx, tmpSlabList)
			aicsSlabList_slabIdx = np.append(aicsSlabList_slabIdx, np.nan) # abb aics
				
		#
		# nodes
		nodeIdxMask = np.ma.masked_greater_equal(self.mySimpleStack.slabList.nodeIdx, 0)
		nodeIdxMask = nodeIdxMask.mask
		
		aicsNodeList_x = self.mySimpleStack.slabList.x[nodeIdxMask]
		aicsNodeList_y = self.mySimpleStack.slabList.y[nodeIdxMask]
		aicsNodeList_z = self.mySimpleStack.slabList.z[nodeIdxMask]
		aicsNodeList_nodeIdx = self.mySimpleStack.slabList.nodeIdx[nodeIdxMask].astype(np.uint16)
		
		self.maskedEdgesDict = {
			# edges
			'aicsSlabList': aicsSlabList,
			'aicsSlabList_x': aicsSlabList_x,
			'aicsSlabList_y': aicsSlabList_y,
			'aicsSlabList_z': aicsSlabList_z,
			'aicsSlabList_slabIdx': aicsSlabList_slabIdx,
			'aicsSlabList_edgeIdx': aicsSlabList_edgeIdx,
			# nodes
			'aicsNodeList_x': aicsNodeList_x,
			'aicsNodeList_y': aicsNodeList_y,
			'aicsNodeList_z': aicsNodeList_z,
			'aicsNodeList_nodeIdx': aicsNodeList_nodeIdx,
			
		}
		
		print(timeIt.elapsed())
		
		#import sys
		#sys.exit()
		
def main():
	app = QtWidgets.QApplication(sys.argv)
	main = myPyQtGraphWindow2()
	main.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()