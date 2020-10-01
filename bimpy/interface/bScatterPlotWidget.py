"""
# 20200929

class to make scatter and histogram plots of nodes and edge prameters
"""

import sys

import numpy as np

from qtpy import QtCore, QtGui, QtWidgets

from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

import qdarkstyle

import bimpy

class bScatterPlotWidget(QtWidgets.QMainWindow):
	mainWindowSignal = QtCore.Signal(object)

	def __init__(self, stackObject, parent=None):
		super(bScatterPlotWidget, self).__init__()
		self.myStack = stackObject
		self.myParent = parent

		# all widgets should inherit this
		self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

		centralWidget = QtWidgets.QWidget(self)
		self.setCentralWidget(centralWidget)

		#
		# main toolbar
		myToolbar = bPlotToolBar()
		#myToolbar.selectTypeSignal.connect(self.slot_selectType)
		self.addToolBar(myToolbar)

		# hboxlayout for x/y/plot
		self.myHBoxLayout = QtWidgets.QHBoxLayout(self)
		centralWidget.setLayout(self.myHBoxLayout)

		defaultType = 'Nodes' # 'nodes'
		myStatListWidget_x = bStatListWidget(defaultType, 'x', self.myStack, parent=None)
		myStatListWidget_y = bStatListWidget(defaultType, 'y', self.myStack, parent=None)
		self.myHBoxLayout.addWidget(myStatListWidget_x)#, stretch=2)
		self.myHBoxLayout.addWidget(myStatListWidget_y)#, stretch=2)

		myPlot = bPyQtPlot(parent=None, stackObject=self.myStack)
		self.myHBoxLayout.addWidget(myPlot)#, stretch=2)

		# connect plot to stat selection
		myStatListWidget_x.selectStatSignal.connect(myPlot.slot_selectStat)
		myStatListWidget_y.selectStatSignal.connect(myPlot.slot_selectStat)

		# connect point selection to toolbar
		myPlot.selectPointSignal.connect(self.slot_selectPoint)
		myPlot.selectPointSignal.connect(myToolbar.slot_selectPoint)
		self.mainWindowSignal.connect(myPlot.slot_mainWindowSignal)

		# connect type selection to plot
		myToolbar.selectTypeSignal.connect(myPlot.slot_selectType)
		myToolbar.selectTypeSignal.connect(myStatListWidget_x.slot_selectType)
		myToolbar.selectTypeSignal.connect(myStatListWidget_y.slot_selectType)
		myToolbar.selectPlotTypeSignal.connect(myPlot.slot_selectPlotType)

		# to disable when toolbar selects 'Histogram'
		myToolbar.selectPlotTypeSignal.connect(myStatListWidget_y.slot_selectPlotType)

	'''
	def slot_selectType(self, type):
		self.myStatListWidget_x.switchToType(type)
		self.myStatListWidget_y.switchToType(type)
	'''
	def keyPressEvent(self, event):
		if event.text() == 'i':
			# print stack header info
			self.myStack.prettyPrint()

		if event.text() == 'r':
			# toggle rect roi on/off
			signalDict = {'name': 'toggle rect roi'}
			self.mainWindowSignal.emit(signalDict)

	# used internally
	def slot_selectPoint(self, selectionDict):
		"""
		selectionDict: like {'type':'Nodes', 'idx':1}
		"""
		# will go back to bPyQtPlot but be ignored
		# use this to propogate selection back to main bImPy bStack widget
		self.mainWindowSignal.emit(selectionDict)

	# coming from main bImPy interface
	def slot_selectNode(self, myEvent):
		myEvent.printSlot('bScatterPlotWidget.slot_selectNode()')
		# I don't understand how to deal with these 'circular' signal/slot situations???
		# for now, just select in each of our interface objects
		signalDict = {'name': 'external select node', 'idx':myEvent.nodeIdx}
		self.mainWindowSignal.emit(signalDict)

	# coming from main bImPy interface
	def slot_selectEdge(self, myEvent):
		myEvent.printSlot('bScatterPlotWidget.slot_selectEdge()')
		signalDict = {'name': 'external select edge', 'idx':myEvent.edgeIdx}
		self.mainWindowSignal.emit(signalDict)

class bStatListWidget(QtWidgets.QTableWidget):
	selectStatSignal = QtCore.Signal(object)

	def __init__(self, type, xy, stackObject, parent=None):
		"""
		type: (nodes, edges, annotations)
		xy: (x, y)
		stackObject: bStack
		"""
		super(bStatListWidget, self).__init__(parent)
		self.mainWindow = parent
		self.myType = type #(nodes , edges, annotation)
		self.xy = xy
		self.myStack = stackObject

		fnt = self.font()
		fnt.setPointSize(12)
		self.setFont(fnt)
		self._rowHeight = 12

		self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

		# signals/slots
		self.itemSelectionChanged.connect(self.on_clicked_row)
		#self.itemPressed.connect(self.on_clicked_row)

		self.populate()

	def switchToType(self, type):
		self.myType = type
		self.populate()

	def populate(self):
		if self.myType == 'Nodes':
			thisDict = self.myStack.slabList.getNode(0)
		elif self.myType == 'Edges':
			thisDict = self.myStack.slabList.getEdge(0)
		else:
			print('bStatListWidget.populate() unknown myType:', self.myType)
			return

		self.headerLabels = [self.xy + ' ' + self.myType] # just one column of either (nodes, edges, annotations)
		self.setColumnCount(len(self.headerLabels))
		self.setHorizontalHeaderLabels(self.headerLabels)

		statCol = 0

		#
		keys = thisDict.keys()
		nKeys = len(keys)
		self.setRowCount(nKeys)
		for rowIdx, statStr in enumerate(keys):
			self.setRowHeight(rowIdx, self._rowHeight)

			# make an item
			item = QtWidgets.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, statStr)

			#
			self.setItem(rowIdx, statCol, item)

		#
		self.setAlternatingRowColors(True)
		# width
		self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
		self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)

		# size policy
		self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum) # ---
		# not this, it expands
		#self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)# +++

		self.clearSelection()

	def on_clicked_row(self):
		row = self.currentRow() # row is 0 based, display is 1 based

		print('bStatListWidget.on_clicked_row() row:', row)

		myItem = self.item(row, 0) # 0 is idx column
		myItemText = myItem.text()
		if myItemText=='':
			print('  on_clicked_row() got empty item?')
			return
		print('  myItemText:', myItemText)

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier

		# emit
		selectionDict = {
			'name': 'bStatListWidget',
			'type': self.myType,
			'xy': self.xy,
			'stat': myItemText,
		}
		self.selectStatSignal.emit(selectionDict)

	def slot_selectType(self, type):
		"""
		type is in (Nodes, Edges, Annotations)
		"""
		self.switchToType(type)

	def slot_selectPlotType(self, plotType):
		"""
		when histogram is selective, disable y-list
		"""
		print('bPlotToolbar.slot_selectPlotType() plotType:', plotType)
		if self.xy == 'y' and plotType == 'Histogram':
			self.setEnabled(False)
		else:
			self.setEnabled(True)

class bPlotToolBar(QtWidgets.QToolBar):
	selectTypeSignal = QtCore.Signal(object) # object can be a dict
	selectPlotTypeSignal = QtCore.Signal(object) # object can be a dict

	def __init__(self, parent=None):
		super(bPlotToolBar, self).__init__(parent)

		typePopup = QtWidgets.QComboBox()
		typeList = ['Nodes', 'Edges', 'Annotations']
		typePopup.addItems(typeList)
		typePopup.activated[str].connect(self.typePopupSelection)
		self.addWidget(typePopup)

		# checkbox to toggle (scatter, histogram)
		aCheckbox = QtWidgets.QCheckBox('Histogram')
		aCheckbox.setChecked(False)
		aCheckbox.stateChanged.connect(self.histogramCallback)
		self.addWidget(aCheckbox)

		# show selected point
		self.pointLabel = QtWidgets.QLabel('Selection:None')
		self.addWidget(self.pointLabel)

	def histogramCallback(self, value):
		""""
		value==0 is unchecked
		value==2 is checked
		"""
		print('histogramCallback() value:', value)
		if value == 2:
			typeStr = 'Histogram'
		else:
			typeStr = 'Scatter'
		self.selectPlotTypeSignal.emit(typeStr)

	def typePopupSelection(self, str):
		print('typePopupSelection() str:', str)
		self.selectTypeSignal.emit(str)

	def slot_selectPoint(self, selectionDict):
		theIdx = None
		if selectionDict is not None:
			theIdx = selectionDict['idx']
		print('bPlotToolbar.slot_selectPoint() theIdx:', theIdx)
		self.pointLabel.setText('Selection:' + str(theIdx))

class bPyQtPlot(pg.PlotWidget):

	# signals
	selectPointSignal = QtCore.Signal(object) # object can be a dict

	def __init__(self, parent=None, stackObject=None):
		super(bPyQtPlot, self).__init__(parent=parent)

		self.mainWindow = parent # usually bStackWidget
		self.myStack = stackObject

		self.plotType = 'Scatter' # from (Histogram, Scatter)
		self.myType = None
		self.xStatDict = None
		self.yStatDict = None

		# todo: these should start off as np.ndarray
		#keep this up-to-date so we can select with rect-roi
		self.xData = np.zeros(1) * np.nan #[] #
		self.yData = np.zeros(1) * np.nan #[]

		xFake = []
		yFake = []
		self.myPointPlot = self.plot(xFake, yFake, pen=None,
							symbol='o', symbolSize=8, symbolBrush=('r'), symbolPen=None)
		self.myPointPlot.sigPointsClicked.connect(self.onMouseClicked_points)
		#self.myPointPlot.sigMouseMoved.connect(self.onMouseMoved_points)
		#self.getPlotItem().getViewBox().mouseDragEvent = self.myDrag

		self.myPointPlotSelection = self.plot([], [], pen=None,
							symbol='o', symbolSize=10, symbolBrush=('y'),
							symbolPen=None,
							connect='finite')

		# roi selection
		pos = [20, 20]
		size = [20, 20]
		self.myLinearRegion = pg.RectROI(pos, size, pen=(0,9),
										invertible=True,
										centered=False)
		#self.myLinearRegion = pg.LinearRegionItem()
		self.myLinearRegion.sigRegionChanged.connect(self.myRectROI_changed)
		self.myLinearRegion.show()
		self.getPlotItem().getViewBox().addItem(self.myLinearRegion)

		# initialize empty plot
		self.doPlot()

	def toggleRectROI(self):
		if self.myLinearRegion.isVisible():
			self.myLinearRegion.hide()
		else:
			self.myLinearRegion.show()

	def myRectROI_changed(self, e):
		"""
		e: pyqtgraph.graphicsItems.ROI.RectROI
		"""
		#print('bPyQtPlot.myRegionChanged() e:', e)
		state = self.myLinearRegion.getState()
		#print('  pos', state['pos']) # [0] is x-left, [1] is y-bottom
		#print('  size', state['size'])
		pos = state['pos']
		size = state['size']
		# when allowing invertible=True we need to hand pos/neg size
		# if basically flips left--right and top--bottom
		if size[0] > 0:
			left = pos[0]
			right = left + size[0]
		else:
			right = pos[0]
			left = right + size[0]
		if size[1] > 0:
			bottom = pos[1]
			top = bottom + size[1]
		else:
			top = pos[1]
			bottom = top + size[1]
		#print('  ', left, top, right, bottom)
		xSel = self.xData[(self.xData>left) & (self.xData<right) &
							(self.yData>bottom) & (self.yData<top)]
		ySel = self.yData[(self.xData>left) & (self.xData<right) &
							(self.yData>bottom) & (self.yData<top)]

		print(f'  myRectROI_changed() selected {len(xSel)} points')

		self.myPointPlotSelection.setData(xSel, ySel)

		# force update
		self.update()

	def myDrag(self, event):
		leftButton = event.button() == QtCore.Qt.LeftButton
		isControl = event.modifiers() & QtCore.Qt.ControlModifier
		vb = self.getPlotItem().getViewBox()
		if (leftButton) and (isControl):
			self.myLinearRegion.show()
			#self.myLinearRegion.setRegion([vb.mapToView(event.buttonDownPos()).x(),
			#								vb.mapToView(event.pos()).x()])
			#event.accept()
			#print('\nbuttonDownPos:', event.buttonDownPos())
			#print('pos:', event.pos())
		#elif leftButton and not isControl:
		#	self.myLinearRegion.hide()

		#else:
		#	#self.myPointPlot.ViewBox.mouseDragEvent(self.myPointPlot..plotItem.vb, event)
		#	self.getPlotItem().getViewBox().mouseDragEvent(event)

	def doPlotHist(self, xDict=None):
		if xDict is None:
			xDict = self.xStatDict
		if xDict is None:
			self.myPointPlot.setData([], [])
			self.getPlotItem().setLabel('left', 'Counts')
			self.getPlotItem().setLabel('bottom', 'None')
			return

		xType = xDict['type'] # from (nodes, edges, annotations)
		xStat = xDict['stat'] # the name of the stat, corresponds to 'key'

		if xType == 'Nodes':
			xData = [node[xStat] for node in self.myStack.slabList.nodeDictList]
		elif xType == 'Edges':
			xData = [edge[xStat] for edge in self.myStack.slabList.edgeDictList]

		# todo: do this check before we build
		ignoreInstances = (str, list, dict)
		if isinstance(xData[0], ignoreInstances):
			print('bPyQtPlot.doPlotHist() is ignoring x-data type:', xType, 'for key:', xStat)
			return

		# plot
		theMin = np.min(xData)
		theMax = np.max(xData)
		y,x = np.histogram(xData, bins=np.linspace(theMin, theMax, 40))
		self.myPointPlot.setData(x, y, stepMode=True, fillLevel=0, brush=(0,0,255,150))

		# set the axis
		self.getPlotItem().setLabel('left', 'Count')
		self.getPlotItem().setLabel('bottom', xStat)

		# clear selection
		self.selectPoint(None)
		self.selectPointSignal.emit(None)

		# force update
		self.update()


	def doPlot(self, xDict=None, yDict=None):
		if self.plotType == 'Histogram':
			self.doPlotHist(xDict=xDict)
			return

		if xDict is None:
			xDict = self.xStatDict
		if yDict is None:
			yDict = self.yStatDict

		if xDict is None or yDict is None:
			self.myPointPlot.setData([], [], stepMode=False, fillLevel=None)
			self.getPlotItem().setLabel('left', 'None')
			self.getPlotItem().setLabel('bottom', 'None')
			return

		xType = xDict['type'] # from (nodes, edges, annotations)
		yType = yDict['type']

		if xType != yType:
			# can't ever plot e.g. x-nodes versus y-edges
			return

		theType = xType

		xStat = xDict['stat'] # the name of the stat, corresponds to 'key'
		yStat = yDict['stat']

		# fake
		#xData = np.random.normal(loc=1, scale=10, size=1000)
		#yData = np.random.normal(loc=-20, scale=50, size=1000)

		if theType == 'Nodes':
			# super slow
			#xData = [node[xStat] for node in self.myStack.slabList.nodeIter()]
			#yData = [node[yStat] for node in self.myStack.slabList.nodeIter()]
			# super fast !!!
			self.xData = np.asarray([node[xStat] for node in self.myStack.slabList.nodeDictList])
			self.yData = np.asarray([node[yStat] for node in self.myStack.slabList.nodeDictList])
		elif theType == 'Edges':
			# super slow
			#xData = [edge[xStat] for edge in self.myStack.slabList.edgeIter()]
			#yData = [edge[yStat] for edge in self.myStack.slabList.edgeIter()]
			# super fast !!!
			self.xData = np.asarray([edge[xStat] for edge in self.myStack.slabList.edgeDictList])
			self.yData = np.asarray([edge[yStat] for edge in self.myStack.slabList.edgeDictList])

		# todo: do this check before we build
		ignoreInstances = (str, list, dict)
		if isinstance(self.xData[0], ignoreInstances):
			print('bPyQtPlot.doPlot() is ignoring x-data type:', xType, 'for key:', xStat)
			return
		if isinstance(self.yData[0], ignoreInstances):
			print('bPyQtPlot.doPlot() is ignoring y-data type:', yType, 'for key:', yStat)
			return

		# using stepMode=False to reset any previous histograms
		# using fillLevel=None to reset any previous histograms
		self.myPointPlot.setData(self.xData, self.yData,
									stepMode=False, fillLevel=None) #, symbolSize=nodePenSize)

		# set the axis
		self.getPlotItem().setLabel('left', yStat)
		self.getPlotItem().setLabel('bottom', xStat)

		# clear selection
		self.selectPoint(None)
		self.selectPointSignal.emit(None)

		# same as right-click 'auto range'
		self.getPlotItem().getViewBox().autoRange()

		# force update
		self.update()

	def selectPoint(self, theIdx):
		if theIdx is None:
			self.myPointPlotSelection.setData([], [])
		else:
			myType = self.xStatDict['type'] # assuming xy are the same
			if myType == 'Nodes':
				thisDict = self.myStack.slabList.getNode(theIdx)
			elif myType == 'Edges':
				thisDict = self.myStack.slabList.getEdge(theIdx)
			else:
				print('bPyQtPlot.onMouseClicked_points() unknown type:', myType)
				return

			xStat = self.xStatDict['stat']
			xData = thisDict[xStat]
			xData = [xData]

			yStat = self.yStatDict['stat']
			yData = thisDict[yStat]
			yData = [yData]

			self.myPointPlotSelection.setData(xData, yData)

		# force update
		self.update()

	def onMouseClicked_points(self, item, points):
		if self.plotType == 'Histogram':
			print('bPyQtPlot.onMouseClicked_points() point selection is not allowed for histograms')
			return

		theIdx = points[0].index()
		print('=== onMouseClicked_annotations() theIdx:', theIdx)
		self.selectPoint(theIdx)

		emitDict = {'name':'bPyQtPlot', 'type':self.myType, 'idx':theIdx}
		self.selectPointSignal.emit(emitDict)

		# print info
		if self.myType == 'Nodes':
			self.myStack.slabList.printNodeInfo(theIdx)
		elif self.myType == 'Edges':
			self.myStack.slabList.printEdgeInfo(theIdx)

	def slot_mainWindowSignal(self, signalDict):
		"""
		receive updates from main window
		"""
		print('bPyQtPlot.slot_mainWindowSignal() signalDict:', signalDict)
		name = signalDict['name']
		idx = signalDict['idx']
		if name == 'toggle rect roi':
			self.toggleRectROI()
		elif name == 'external select node':
			if self.myType == 'Nodes':
				self.selectPoint(idx)
		elif name == 'external select edge':
			if self.myType == 'Edges':
				self.selectPoint(idx)

	def slot_selectStat(self, selectionDict):
		"""
		when user selects stat in bStatListWidget
		can be either xy
		"""
		print('bPyQtPlot.slot_selectStat() selectionDict:', selectionDict)
		self.myType = selectionDict['type']
		if selectionDict['xy'] == 'x':
			self.xStatDict = selectionDict
		elif selectionDict['xy'] == 'y':
			self.yStatDict = selectionDict

		self.doPlot(self.xStatDict, self.yStatDict)

	def slot_selectType(self, type):
		"""
		when user selects type (Nodes, Edges, Annotations) in main toolbar
		This is extreme, we are just clearing the plot????
		"""
		print('bPyQtPlot.slot_selectType() type:', type)
		if self.type != type:
			self.type = type
			self.xStatDict = None
			self.yStatDict = None
			self.doPlot()
			self.selectPoint(None)

	def slot_selectPlotType(self, plotType):
		print('bPyQtPlot.slot_selectPlotType() plotType:', plotType)
		self.plotType = plotType
		self.doPlot()

def main(path):
	myStack = bimpy.bStack(path, loadImages=False, loadTracing=True)

	print(1)
	app = QtWidgets.QApplication(sys.argv)

	'''
	print(2)
	myPlot = bPyQtPlot(None, myStack)
	myPlot.show()
	'''

	myPlotWidget = bScatterPlotWidget(myStack, None)
	myPlotWidget.show()

	print(3)
	sys.exit(app.exec_()) # this will loop

if __name__ == '__main__':
	path = '/home/cudmore/data/nathan/SAN4/aicsAnalysis/SAN4_head_ch2.tif'
	path = '/home/cudmore/data/nathan/SAN4/aicsAnalysis/SAN4_tail_ch2.tif'
	main(path)
