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

import os, time
from collections import OrderedDict

import pandas as pd
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends import backend_qt5agg

import bimpy

'''
from bimpy import bStackContrastWidget
from bimpy import bStackContrastWidget
from bimpy import bStackFeebackWidget
from bimpy import bStack
#from bSimpleStack import bSimpleStack
'''

################################################################################
class bAnnotationTable(QtWidgets.QWidget):
	def __init__(self, mainWindow=None, parent=None, slabList=None):
		super(bAnnotationTable, self).__init__(parent)

		'''
		self.setObjectName('bAnnotationTable')
		self.setStyleSheet("""
			#bAnnotationTable {
				background-color: #222;
			}
			.QTableWidget {
				background-color: #222;
			}
		""")
		'''

		self.mainWindow = mainWindow
		self.slabList = slabList

		self.myQVBoxLayout = QtWidgets.QVBoxLayout(self)

		#
		# buttons
		mySaveButton = QtWidgets.QPushButton('Save')
		mySaveButton.clicked.connect(self.saveButton_Callback)
		self.myQVBoxLayout.addWidget(mySaveButton)

		self.myQHBoxLayout = QtWidgets.QHBoxLayout(self) # to hold nodes and edges
		self.myQVBoxLayout.addLayout(self.myQHBoxLayout)

		#
		# table of node annotation
		self.myNodeTableWidget = QtWidgets.QTableWidget()
		if self.slabList is None:
			numNodes = 0
		else:
			numNodes = self.slabList.numNodes
		self.myNodeTableWidget.setRowCount(numNodes)
		self.myNodeTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.myNodeTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.myNodeTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		self.myNodeTableWidget.cellClicked.connect(self.on_clicked_node)
		nodeHeaderLabels = ['zSlice', 'nEdges']
		self.myNodeTableWidget.setColumnCount(len(nodeHeaderLabels))
		self.myNodeTableWidget.setHorizontalHeaderLabels(nodeHeaderLabels)
		header = self.myNodeTableWidget.horizontalHeader()
		for idx, label in enumerate(nodeHeaderLabels):
			header.setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeToContents)
		if self.slabList is None:
			pass
		else:
			print('bAnnotationTable num nodes:', len(self.slabList.nodeDictList))
			'''
			for tmpNode in self.slabList.nodeDictList:
				print('tmpNode:', tmpNode)
			'''
			for idx, stat in enumerate(self.slabList.nodeDictList):
				for colIdx, header in enumerate(nodeHeaderLabels):
					myString = str(stat[header])
					'''
					# special cases
					if header == 'Bad':
						myString = 'X' if myString=='True' else ''
					'''
					#assign
					item = QtWidgets.QTableWidgetItem(myString)
					self.myNodeTableWidget.setItem(idx, colIdx, item)

		#
		# table of edge annotations
		self.myTableWidget = QtWidgets.QTableWidget()
		if self.slabList is None:
			numEdges = 0
		else:
			numEdges = self.slabList.numEdges
		self.myTableWidget.setRowCount(numEdges)
		self.myTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.myTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.myTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		# signals/slots
		self.myTableWidget.cellClicked.connect(self.on_clicked_edge)
		# todo: this work to select edge when arrow keys are used but casuses bug in interface
		# figure out how to get this to work
		#self.myTableWidget.currentCellChanged.connect(self.on_clicked)
		#headerLabels = ['type', 'n', 'Length 3D', 'Length 2D', 'z', 'preNode', 'postNode', 'Good']
		headerLabels = ['n', 'Len 3D', 'Len 2D', 'z', 'preNode', 'postNode', 'Bad']
		self.myTableWidget.setColumnCount(len(headerLabels))
		self.myTableWidget.setHorizontalHeaderLabels(headerLabels)
		header = self.myTableWidget.horizontalHeader()
		for idx, label in enumerate(headerLabels):
			header.setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeToContents)
		# QHeaderView will automatically resize the section to fill the available space.
		# The size cannot be changed by the user or programmatically.
		#header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
		if self.slabList is None:
			pass
		else:
			for idx, stat in enumerate(self.slabList.edgeDictList):
				for colIdx, header in enumerate(headerLabels):
					myString = str(stat[header])
					# special cases
					if header == 'Bad':
						myString = 'X' if myString=='True' else ''
					if header == 'preNode':
						myString = '' if myString=='-1' else myString
					if header == 'postNode':
						myString = '' if myString=='-1' else myString
					#assign
					item = QtWidgets.QTableWidgetItem(myString)
					self.myTableWidget.setItem(idx, colIdx, item)


		self.myQHBoxLayout.addWidget(self.myNodeTableWidget)
		self.myQHBoxLayout.addWidget(self.myTableWidget)

	# todo: this is broken
	def saveButton_Callback(self):
		"""
		Save the current annotation list
		"""
		print('bAnnotationTable.saveButton_Callback()')
		self.mainWindow.signal('save')

	def refreshRow(self, idx):
		stat = self.slabList.edgeDictList[idx]

		myString = str(stat['type'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myTableWidget.setItem(idx, 0, item)

		myString = str(stat['n'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myTableWidget.setItem(idx, 1, item)

		myString = str(stat['Length 3D'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myTableWidget.setItem(idx, 2, item)

		myString = str(stat['Length 2D'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myTableWidget.setItem(idx, 3, item)

		myString = str(stat['z'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myTableWidget.setItem(idx, 4, item)

		if stat['Good']:
			myString = ''
		else:
			myString = 'False'
		#myString = str(stat['Good'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myTableWidget.setItem(idx, 5, item)

	def selectRow(self, row):
		print('bAnnotationTable.selectRow()', row)
		self.myTableWidget.selectRow(row)
		self.repaint()

	@QtCore.pyqtSlot()
	def on_clicked_node(self):
		print('bAnnotationTable.on_clicked_node')
		row = self.myNodeTableWidget.currentRow()
		self.mainWindow.signal('selectNodeFromTable', row, fromTable=True)

	@QtCore.pyqtSlot()
	def on_clicked_edge(self):
		#print('bAnnotationTable.on_clicked_edge')
		row = self.myTableWidget.currentRow()
		if row == -1 or row is None:
			return
		#print('   row:', row)
		yStat = self.myTableWidget.item(row,0).text() #
		#print('   ', row, yStat)
		self.mainWindow.signal('selectEdgeFromTable', row, fromTable=True)

################################################################################
#class bStackView(QtWidgets.QWidget):
class bStackView(QtWidgets.QGraphicsView):
	def __init__(self, simpleStack, mainWindow=None, parent=None):
		super(bStackView, self).__init__(parent)

		self.setObjectName('bStackView')
		self.setStyleSheet("""
			#bStackView {
				background-color: #222;
			}
		""")

		#self.path = path
		self.options_defaults()

		self.mySimpleStack = simpleStack #bSimpleStack(path)
		self.mainWindow = mainWindow

		self.mySelectedNode = None # node index of selected node
		self.mySelectedEdge = None # edge index of selected edge

		self.displayThisStack = 'ch1'
		self.displaySlidingZ = False

		self.currentSlice = 0
		self.minContrast = 0
		#self.maxContrast = 2 ** self.mySimpleStack.getHeaderVal('bitDepth')
		print('   bStackView.__init__ got stack bot depth of:', self.mySimpleStack.bitDepth, 'type:', type(self.mySimpleStack.bitDepth))
		self.maxContrast = 2 ** self.mySimpleStack.bitDepth

		'''
		self.idMasked = None
		self.xMasked = None
		self.yMasked = None
		self.zMasked = None
		'''

		self.showTracing = True
		self.showNodes = True
		self.showEdges = True
		self.showDeadEnds = True

		self.imgplot = None

		# coordinates of the image
		'''
		self.iLeft = 0
		self.iTop = 0
		#self.iRight = self.mySimpleStack.xVoxel * self.mySimpleStack.pixelsPerLine # reversed
		#self.iBottom = self.mySimpleStack.yVoxel * self.mySimpleStack.linesPerFrame
		self.iRight = self.mySimpleStack.pixelsPerLine # reversed
		self.iBottom = self.mySimpleStack.linesPerFrame
		'''

		'''
		dpi = 100
		width = 24 #12
		height = 24 #12
		'''

		# for click and drag
		self.clickPos = None

		self._preComputeAllMasks()

		#
		scene = QtWidgets.QGraphicsScene(self)
		#self.scene = scene

		# was this
		# visually turn off scroll bars
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

		#self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
		self.setFrameShape(QtWidgets.QFrame.NoFrame)

		#todo: add interface to turn axes.axis ('on', 'off')
		# image
		#self.figure = Figure(figsize=(width, height), dpi=dpi)
		self.figure = Figure()
		self.canvas = backend_qt5agg.FigureCanvas(self.figure)
		self.axes = self.figure.add_axes([0, 0, 1, 1]) #remove white border
		self.axes.axis('off') #turn off axis labels

		# slab/point list
		markersize = self.options['Tracing']['tracingPenSize'] #2**2
		markerColor = self.options['Tracing']['tracingColor'] #2**2
		self.mySlabPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, picker=True)

		# nodes (put this after slab/point list to be on top, order matter)
		markersize = self.options['Tracing']['nodePenSize'] #2**2
		markerColor = self.options['Tracing']['nodeColor'] #2**2
		self.myNodePlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, picker=True)

		# tracing/slabs that are dead end
		markersize = self.options['Tracing']['deadEndPenSize'] #2**2
		markerColor = self.options['Tracing']['deadEndColor'] #2**2
		self.myDeadEndPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, picker=True)

		# node selection
		markersize = self.options['Tracing']['nodeSelectionPenSize'] #2**2
		markerColor = self.options['Tracing']['nodeSelectionColor'] #2**2
		self.myNodeSelectionPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize)

		# flash node selection
		markersize = self.options['Tracing']['nodeSelectionFlashPenSize'] #2**2
		markerColor = self.options['Tracing']['nodeSelectionFlashColor'] #2**2
		self.myNodeSelectionFlash = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize)

		# edge selection
		markersize = self.options['Tracing']['tracingSelectionPenSize'] #2**2
		markerColor = self.options['Tracing']['tracingSelectionColor'] #2**2
		self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize)

		# flash edge selection
		markersize = self.options['Tracing']['tracingSelectionFlashPenSize'] #2**2
		markerColor = self.options['Tracing']['tracingSelectionFlashColor'] #2**2
		self.myEdgeSelectionFlash = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize)

		#self.canvas.mpl_connect('key_press_event', self.onkey)
		#self.canvas.mpl_connect('button_press_event', self.onclick)
		#self.canvas.mpl_connect('scroll_event', self.onscroll)
		self.canvas.mpl_connect('pick_event', self.onpick)

		# trying this
		'''
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(self.canvas)
		self.setLayout(layout)
		'''

		# was this
		scene.addWidget(self.canvas)

		self.setScene(scene)

		print('sceneRect:', self.sceneRect())
		#self.setSceneRect(-100, -100, 640+100, 640+100)

	def flashNode(self, nodeIdx, numberOfFlashes):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashEdge() edgeIdx:', edgeIdx, on)
		if nodeIdx is None:
			return
		if numberOfFlashes>0:
			if self.mySimpleStack.slabList is not None:
				x, y, z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)
				self.myNodeSelectionFlash.set_offsets(np.c_[x, y])
				#
				QtCore.QTimer.singleShot(10, lambda:self.flashNode(nodeIdx, numberOfFlashes-1))
		else:
			self.myNodeSelectionFlash.set_offsets(np.c_[[], []])
		#
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def flashEdge(self, edgeIdx, on):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashEdge() edgeIdx:', edgeIdx, on)
		if edgeIdx is None:
			return
		if on:
			if self.mySimpleStack.slabList is not None:
				theseIndices = self.mySimpleStack.slabList.getEdge(edgeIdx)
				xMasked = self.mySimpleStack.slabList.y[theseIndices]
				yMasked = self.mySimpleStack.slabList.x[theseIndices]
				self.myEdgeSelectionFlash.set_offsets(np.c_[xMasked, yMasked])
				#
				QtCore.QTimer.singleShot(20, lambda:self.flashEdge(edgeIdx, False))
		else:
			self.myEdgeSelectionFlash.set_offsets(np.c_[[], []])
		#
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def selectNode(self, nodeIdx, snapz=False):
		print('selectNode() nodeIdx:', nodeIdx)
		if nodeIdx is None:
			self.mySelectionNode = None
			self.myNodeSelectionPlot.set_offsets(np.c_[[], []])
		else:
			if self.mySimpleStack.slabList is not None:
				self.mySelectedNode = nodeIdx
				x,y,z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)

				if snapz:
					z = self.mySimpleStack.slabList.getNode_zSlice(nodeIdx)
					self.setSlice(z)

					self.myEdgeSelectionPlot.set_offsets(np.c_[x, y])

					self.zoomToPoint(x, y)

					numberOfFlashes = 1
					QtCore.QTimer.singleShot(10, lambda:self.flashNode(nodeIdx, numberOfFlashes))

		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def selectEdge(self, edgeIdx, snapz=False):
		#print('=== bStackView.selectEdge():', edgeIdx)
		if edgeIdx is None:
			print('bStackView.selectEdge() -->> NONE')
			#markersize = 10
			#self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color='c', s=markersize, picker=True)
			self.mySelectedEdge = None
			self.myEdgeSelectionPlot.set_offsets(np.c_[[], []])
		else:
			self.mySelectedEdge = edgeIdx

			if self.mySimpleStack.slabList is not None:
				theseIndices = self.mySimpleStack.slabList.getEdge(edgeIdx)

				#print('selectEdge() theseIndices:', theseIndices)

				# todo: add option to snap to a z
				# removed this because it was confusing
				if snapz:
					'''
					z = self.mySimpleStack.slabList.z[theseIndices[0]][0] # not sure why i need trailing [0] ???
					z = int(z)
					'''
					z = self.mySimpleStack.slabList.edgeDictList[edgeIdx]['z']
					z = int(z)
					self.setSlice(z)

				xMasked = self.mySimpleStack.slabList.y[theseIndices] # flipped
				yMasked = self.mySimpleStack.slabList.x[theseIndices]
				self.myEdgeSelectionPlot.set_offsets(np.c_[xMasked, yMasked])

				QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, True))

		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	'''
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
	'''

	def _preComputeAllMasks(self):
		"""
		Precompute all masks once. When user scrolls through slices this is WAY faster
		"""
		self.maskedNodes = []
		self.maskedEdges = []
		self.maskedDeadEnds = []
		for i in range(self.mySimpleStack.numImages):
			upperz = i - self.options['Tracing']['showTracingAboveSlices']
			lowerz = i + self.options['Tracing']['showTracingBelowSlices']

			if self.mySimpleStack.slabList is not None:
				#
				# nodes
				zNodeMasked = np.ma.masked_outside(self.mySimpleStack.slabList.nodez, upperz, lowerz)
				if len(zNodeMasked) > 0:
					#idMasked = self.mySimpleStack.slabList.id[~self.zMasked.mask]
					xNodeMasked = self.mySimpleStack.slabList.nodey[~zNodeMasked.mask] # swapping
					yNodeMasked = self.mySimpleStack.slabList.nodex[~zNodeMasked.mask]
				else:
					xNodeMasked = []
					yNodeMasked = []

				maskedNodeDict = {
					'zNodeMasked': zNodeMasked,
					'xNodeMasked': xNodeMasked,
					'yNodeMasked': yNodeMasked,
				}
				self.maskedNodes.append(maskedNodeDict)

				#
				# edges
				zMasked = np.ma.masked_outside(self.mySimpleStack.slabList.z, upperz, lowerz)

				#todo: this need to be combined list of all slabs AND nodes,
				#when we click we can look up which was clicked
				idMasked = self.mySimpleStack.slabList.id[~zMasked.mask]
				xMasked = self.mySimpleStack.slabList.y[~zMasked.mask] # swapping
				yMasked = self.mySimpleStack.slabList.x[~zMasked.mask]
				maskedEdgeDict = {
					'idMasked': idMasked,
					'zMasked': zMasked,
					'xMasked': xMasked,
					'yMasked': yMasked,
				}
				self.maskedEdges.append(maskedEdgeDict)

				#
				# slabs/edges dead ends
				maskedDeadEndDict = {
					'zMasked': [],
					'xMasked': [],
					'yMasked': [],
				}
				for edgeDict in self.mySimpleStack.slabList.edgeDictList:
					if edgeDict['preNode'] == -1:
						# include dead end
						# get the z of the first slab
						firstSlabIdx = edgeDict['slabList'][0]
						tmpz = self.mySimpleStack.slabList.z[firstSlabIdx]
						if tmpz > upperz and tmpz < lowerz:
							tmpx = self.mySimpleStack.slabList.x[firstSlabIdx]
							tmpy = self.mySimpleStack.slabList.y[firstSlabIdx]
							maskedDeadEndDict['yMasked'].append(tmpx) # swapping
							maskedDeadEndDict['xMasked'].append(tmpy)
							maskedDeadEndDict['zMasked'].append(tmpz)
					if edgeDict['postNode'] == -1:
						# include dead end
						# get the z of the last slab
						lastSlabIdx = edgeDict['slabList'][-1]
						tmpz = self.mySimpleStack.slabList.z[lastSlabIdx]
						if tmpz > upperz and tmpz < lowerz:
							tmpx = self.mySimpleStack.slabList.x[lastSlabIdx]
							tmpy = self.mySimpleStack.slabList.y[lastSlabIdx]
							maskedDeadEndDict['yMasked'].append(tmpx) # swapping
							maskedDeadEndDict['xMasked'].append(tmpy)
							maskedDeadEndDict['zMasked'].append(tmpz)
				self.maskedDeadEnds.append(maskedDeadEndDict)

			#print('slice', i, '_preComputeAllMasks() len(x):', len(xMasked), 'len(y)', len(yMasked))

	def setSlice(self, index=None, recursion=True):
		#print('bStackView.setSlice()', index)

		if index is None:
			index = self.currentSlice

		if index < 0:
			index = 0
		if index > self.mySimpleStack.numImages-1:
			index = self.mySimpleStack.numImages -1

		showImage = True

		if showImage:
			if self.displaySlidingZ:
				upSlices = self.options['Stack']['upSlidingZSlices']
				downSlices = self.options['Stack']['downSlidingZSlices']
				image = self.mySimpleStack.getSlidingZ(index, self.displayThisStack, upSlices, downSlices, self.minContrast, self.maxContrast)
			else:
				print('setSlice() index:', index)
				#image = self.mySimpleStack.getImage_ContrastEnhanced(self.minContrast, self.maxContrast, channel=1, sliceNum=index, useMaxProject=False)
				# works
				image = self.mySimpleStack.setSliceContrast(index, thisStack=self.displayThisStack, minContrast=self.minContrast, maxContrast=self.maxContrast)

			if self.imgplot is None:
				print('bStackWIdget.setSlice() self.imgplot:', self.imgplot)
				cmap = self.options['Stack']['colorLut'] #2**2
				#self.imgplot = self.axes.imshow(image, cmap=cmap, extent=[self.iLeft, self.iRight, self.iBottom, self.iTop])  # l, r, b, t
				self.imgplot = self.axes.imshow(image, cmap=cmap)  # l, r, b, t
			else:
				self.imgplot.set_data(image)
		else:
			pass

		#
		# update point annotations
		if self.showTracing:
			if self.mySimpleStack.slabList is None:
				# no tracing
				pass
			else:
				#try:
				if 1:
					# nodes
					if self.showNodes:
						self.myNodePlot.set_offsets(np.c_[self.maskedNodes[index]['xNodeMasked'], self.maskedNodes[index]['yNodeMasked']])
					# slabs
					if self.showEdges:
						self.mySlabPlot.set_offsets(np.c_[self.maskedEdges[index]['xMasked'], self.maskedEdges[index]['yMasked']])
					if self.showDeadEnds:
						self.myDeadEndPlot.set_offsets(np.c_[self.maskedDeadEnds[index]['xMasked'], self.maskedDeadEnds[index]['yMasked']])
				#except:
				#	print('ERROR: bStackWindow.setSlice')

		else:
			self.myNodePlot.set_offsets(np.c_[[], []])
			self.mySlabPlot.set_offsets(np.c_[[], []])

		self.currentSlice = index # update slice

		if self.mainWindow is not None and recursion:
			self.mainWindow.signal('set slice', value=index, recursion=False)

		#self.canvas.draw()
		self.canvas.draw_idle()
		#self.repaint() # this is updating the widget !!!!!!!!
		#print(1)

	def zoomToPoint(self, x, y):
		# todo convert this to use a % of the total image ?
		print('zoomToPoint() x:', x, 'y:', y)
		'''
		zoomPixels = 20
		left = x - zoomPixels
		top = y - zoomPixels # flip ?
		right = x + zoomPixels
		bottom = y + zoomPixels # flip?
		width = right - left
		height = bottom - top
		print('   ', left, top, right, bottom, 'width:', width, 'height:', height)
		'''

		# this sort of works
		#self.scale(2, 2)
		scenePnt = self.mapToScene(x, y)
		scenePnt = self.mapFromScene(x, y)
		print('   scenePnt:', scenePnt)
		self.centerOn(scenePnt)

		#self.centerOn(x, y)

		'''
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!
		'''

	def zoom(self, zoom):
		#print('=== bStackView.zoom()', zoom)
		if zoom == 'in':
			scale = 1.2
		else:
			scale = 0.8
		self.scale(scale,scale)
		#self.zoomToPoint(100,100)

	def keyPressEvent(self, event):
		#print('=== bStackView.keyPressEvent() event.key():', event.key())
		if event.key() in [QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal]:
			self.zoom('in')
		elif event.key() == QtCore.Qt.Key_Minus:
			self.zoom('out')
		elif event.key() == QtCore.Qt.Key_T:
			self.showTracing = not self.showTracing
			self.setSlice() #refresh
		elif event.key() == QtCore.Qt.Key_N:
			self.showNodes = not self.showNodes
			self.setSlice() #refresh
		elif event.key() == QtCore.Qt.Key_E:
			self.showEdges = not self.showEdges
			self.setSlice() #refresh
		elif event.key() == QtCore.Qt.Key_D:
			self.showDeadEnds = not self.showDeadEnds
			self.setSlice() #refresh

		# choose which stack to display
		elif event.key() == QtCore.Qt.Key_1:
			self.displayThisStack = 'ch1'
			self.setSlice(recursion=False) # just refresh
		elif event.key() == QtCore.Qt.Key_2:
			self.displayThisStack = 'ch2'
			self.setSlice(recursion=False) # just refresh
		elif event.key() == QtCore.Qt.Key_3:
			self.displayThisStack = 'ch3'
			self.setSlice(recursion=False) # just refresh
		elif event.key() == QtCore.Qt.Key_9:
			if self.mySimpleStack._imagesMask is not None:
				self.displayThisStack = 'mask'
				self.setSlice(recursion=False) # just refresh
		elif event.key() == QtCore.Qt.Key_0:
			if self.mySimpleStack._imagesSkel is not None:
				self.displayThisStack = 'skel'
				self.setSlice(recursion=False) # just refresh

		elif event.key() == QtCore.Qt.Key_Z:
			self._toggleSlidingZ()

		else:
			event.setAccepted(False)

	def _toggleSlidingZ(self, recursion=True):
		self.displaySlidingZ = not self.displaySlidingZ
		# todo: don't call this deep
		if recursion:
			self.mainWindow.bStackFeebackWidget.setFeedback('sliding z', self.displaySlidingZ)
		self.setSlice(recursion=False) # just refresh

	def wheelEvent(self, event):
		#if self.hasPhoto():

		#print('event.angleDelta().y():', event.angleDelta().y())

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		if modifiers == QtCore.Qt.ControlModifier:
			if event.angleDelta().y() > 0:
				self.zoom('in')
			else:
				self.zoom('out')
			event.setAccepted(True)
		else:
			if event.angleDelta().y() > 0:
				self.currentSlice -= 1
			else:
				self.currentSlice += 1
			self.setSlice(self.currentSlice)
			event.setAccepted(True)

	def mousePressEvent(self, event):
		print('=== bStackView.mousePressEvent()', event.pos())
		self.clickPos = event.pos()
		super().mousePressEvent(event)
		# 20191104, was this
		#event.setAccepted(True)

	def mouseMoveEvent(self, event):
		#print('=== bStackView.mouseMoveEvent()')
		if self.clickPos is not None:
			newPos = event.pos() - self.clickPos
			dx = self.clickPos.x() - newPos.x()
			dy = self.clickPos.y() - newPos.y()
			self.translate(dx, dy)
		super().mouseMoveEvent(event)
		# 20191104, was this
		#event.setAccepted(True)

	def mouseReleaseEvent(self, event):
		#print('=== bStackView.mouseReleaseEvent()')
		self.clickPos = None
		super().mouseReleaseEvent(event)
		event.setAccepted(True)

	def onpick(self, event):
		print('\n=== bStackView.onpick()')
		xdata = event.mouseevent.xdata
		ydata = event.mouseevent.ydata
		ind = event.ind

		'''
		print('   event.mouseevent.xdata:', event.mouseevent.xdata)
		print('   event.mouseevent.ydata:', event.mouseevent.ydata)
		print('   event.artist:', event.artist)
		print('   event.ind:', event.ind)
		'''

		# find the first ind in bSlabList.id
		firstInd = ind[0]
		#edgeIdx = self.mySimpleStack.slabList.id[firstInd]
		#edgeIdx = self.idMasked[firstInd]

		edgeIdx = self.maskedEdges[self.currentSlice]['idMasked'][firstInd]
		edgeIdx = int(edgeIdx)


		#edgeIdx += 1

		#print('   firstInd:', firstInd, 'edgeIdx:', edgeIdx)

		#self.selectEdge(edgeIdx)
		print('   edge:', edgeIdx, self.mySimpleStack.slabList.edgeDictList[edgeIdx])

		if self.mainWindow is not None:
			self.mainWindow.signal('selectEdgeFromImage', edgeIdx)

	def options_defaults(self):
		self.options = OrderedDict()

		"""
		Possible values are: Accent, Accent_r, Blues, Blues_r, BrBG, BrBG_r, BuGn, BuGn_r, BuPu, BuPu_r, CMRmap, CMRmap_r, Dark2, Dark2_r, GnBu, GnBu_r, Greens, Greens_r, Greys, Greys_r, OrRd, OrRd_r, Oranges, Oranges_r, PRGn, PRGn_r, Paired, Paired_r, Pastel1, Pastel1_r, Pastel2, Pastel2_r, PiYG, PiYG_r, PuBu, PuBuGn, PuBuGn_r, PuBu_r, PuOr, PuOr_r, PuRd, PuRd_r, Purples, Purples_r, RdBu, RdBu_r, RdGy, RdGy_r, RdPu, RdPu_r, RdYlBu, RdYlBu_r, RdYlGn, RdYlGn_r, Reds, Reds_r, Set1, Set1_r, Set2, Set2_r, Set3, Set3_r, Spectral, Spectral_r, Wistia, Wistia_r, YlGn, YlGnBu, YlGnBu_r, YlGn_r, YlOrBr, YlOrBr_r, YlOrRd, YlOrRd_r, afmhot, afmhot_r, autumn, autumn_r, binary, binary_r, bone, bone_r, brg, brg_r, bwr, bwr_r, cividis, cividis_r, cool, cool_r, coolwarm, coolwarm_r, copper, copper_r, cubehelix, cubehelix_r, flag, flag_r, gist_earth, gist_earth_r, gist_gray, gist_gray_r, gist_heat, gist_heat_r, gist_ncar, gist_ncar_r, gist_rainbow, gist_rainbow_r, gist_stern, gist_stern_r, gist_yarg, gist_yarg_r, gnuplot, gnuplot2, gnuplot2_r, gnuplot_r, gray, gray_r, hot, hot_r, hsv, hsv_r, inferno, inferno_r, jet, jet_r, magma, magma_r, nipy_spectral, nipy_spectral_r, ocean, ocean_r, pink, pink_r, plasma, plasma_r, prism, prism_r, rainbow, rainbow_r, seismic, seismic_r, spring, spring_r, summer, summer_r, tab10, tab10_r, tab20, tab20_r, tab20b, tab20b_r, tab20c, tab20c_r, terrain, terrain_r, twilight, twilight_r, twilight_shifted, twilight_shifted_r, viridis, viridis_r, winter, winter_r
		"""

		self.options['Stack'] = OrderedDict()
		self.options['Stack'] = OrderedDict({
			'colorLut': 'gray',
			'upSlidingZSlices': 5,
			'downSlidingZSlices': 5,
			})

		self.options['Tracing'] = OrderedDict()
		self.options['Tracing'] = OrderedDict({
			'nodePenSize': 80,
			'nodeColor': 'r',
			'nodeSelectionPenSize': 120,
			'nodeSelectionColor': 'c',
			'nodeSelectionFlashPenSize': 200,
			'nodeSelectionFlashColor': 'm',
			'showTracingAboveSlices': 5,
			'showTracingBelowSlices': 5,
			'tracingPenSize': 10,
			'tracingColor': 'y',
			'tracingSelectionPenSize': 10,
			'tracingSelectionColor': 'c',
			'tracingSelectionFlashPenSize': 80,
			'tracingSelectionFlashColor': 'm',
			'deadEndPenSize': 40,
			'deadEndColor': 'b',
			})

################################################################################
class bStackWidget(QtWidgets.QWidget):
	"""
	A widget to display a stack. This includes a bStackView and a bAnnotationTable.
	"""
	def __init__(self, mainWindow=None, parent=None, path=''):
		super(bStackWidget, self).__init__(parent)

		#self.options_defaults()

		self.path = path

		basename = os.path.basename(self.path)
		self.setWindowTitle(basename)

		self.setObjectName('bStackWidget0')
		self.setStyleSheet("""
			#bStackWidget0 {
				background-color: #222;
			}
			.QLabel {
				color: #bbb;
			}
			.QCheckBox {
				color: #bbb;
			}
		""")

		#
		#self.mySimpleStack = bSimpleStack(path) # backend stack
		self.mySimpleStack = bimpy.bStack(path) # backend stack
		#

		self.showLeftControlBar = True
		self.showContrastBar = True
		self.showFeebackBar = True

		self.myHBoxLayout = QtWidgets.QHBoxLayout(self)

		self.myVBoxLayout = QtWidgets.QVBoxLayout(self)

		self.myContrastWidget = bimpy.interface.bStackContrastWidget(mainWindow=self)

		self.bStackFeebackWidget = bimpy.interface.bStackFeebackWidget(mainWindow=self)
		self.bStackFeebackWidget.setFeedback('num slices', self.mySimpleStack.numImages)

		self.myHBoxLayout2 = QtWidgets.QHBoxLayout(self)

		self.myStackView = bStackView(self.mySimpleStack, mainWindow=self) # a visual stack

		# a slider to set slice number
		self.mySliceSlider = QtWidgets.QSlider(QtCore.Qt.Vertical)
		self.mySliceSlider.setMaximum(self.mySimpleStack.numImages)
		self.mySliceSlider.setInvertedAppearance(True) # so it goes from top:0 to bottom:numImages
		self.mySliceSlider.setMinimum(0)
		if self.mySimpleStack.numImages < 2:
			self.mySliceSlider.setDisabled(True)
		self.mySliceSlider.valueChanged.connect(self.sliceSliderValueChanged)

		self.myHBoxLayout2.addWidget(self.myStackView)
		self.myHBoxLayout2.addWidget(self.mySliceSlider)

		# add
		self.myVBoxLayout.addWidget(self.myContrastWidget) #, stretch=0.1)
		self.myVBoxLayout.addWidget(self.bStackFeebackWidget) #, stretch=0.1)
		#self.myVBoxLayout.addWidget(self.myStackView) #, stretch = 9)
		self.myVBoxLayout.addLayout(self.myHBoxLayout2) #, stretch = 9)

		# todo: Need to show/hide annotation table
		self.annotationTable = bAnnotationTable(mainWindow=self, parent=None, slabList=self.mySimpleStack.slabList)
		self.myHBoxLayout.addWidget(self.annotationTable, stretch=3) # stretch=10, not sure on the units???
		print('self.mySimpleStack.slabList:', self.mySimpleStack.slabList)
		if self.mySimpleStack.slabList is None:
			self.annotationTable.hide()
			self.showLeftControlBar = False
		else:
			pass
			#self.annotationTable.hide()

		self.myHBoxLayout.addLayout(self.myVBoxLayout, stretch=7) # stretch=10, not sure on the units???

		'''
		self.setFocusPolicy(QtCore.Qt.ClickFocus)
		self.setFocus()
		'''

		self.updateDisplayedWidgets()

		self.move(100,100)

		self.myStackView.setSlice(0)

	def sliceSliderValueChanged(self):
		theSlice = self.mySliceSlider.value()
		self.signal('set slice', theSlice)

	def updateDisplayedWidgets(self):
		# left control bar
		if self.showLeftControlBar:
			# todo: fix this
			if self.annotationTable is not None:
				self.annotationTable.show()
		else:
			if self.annotationTable is not None:
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

	def signal(self, signal, value=None, fromTable=False, recursion=True):
		#print('=== bStackWidget.signal()', 'signal:', signal, 'value:', value, 'fromTable:', fromTable)
		if signal == 'selectNodeFromTable':
			nodeIdx = value
			print('=== bStackWidget.signal() selectNodeFromTable nodeIdx:', nodeIdx)
			self.selectNode(nodeIdx, snapz=True)
			'''
			if not fromTable:
				self.annotationTable.selectRow(nodeIdx)
			'''
			#self.myStackView.selectNode(nodeIdx, snapz=True)

		if signal == 'selectEdgeFromTable':
			print('=== bStackWidget.signal() selectEdgeFromTable')
			self.selectEdge(value, snapz=True)
			if not fromTable:
				self.annotationTable.selectRow(value)
		if signal == 'selectEdgeFromImage':
			print('=== bStackWidget.signal() selectEdgeFromImage')
			self.selectEdge(value, snapz=False)
			if not fromTable:
				self.annotationTable.selectRow(value)

		if signal == 'contrast change':
			minContrast = value['minContrast']
			maxContrast = value['maxContrast']
			self.myStackView.minContrast = minContrast
			self.myStackView.maxContrast = maxContrast
			self.myStackView.setSlice(index=None) # will just refresh current slice

		if signal == 'set slice':
			self.bStackFeebackWidget.setFeedback('set slice', value)
			if recursion:
				self.myStackView.setSlice(value, recursion=False)
			self.mySliceSlider.setValue(value)

		if signal == 'toggle sliding z':
			self.myStackView._toggleSlidingZ(recursion=recursion)

		if signal == 'save':
			self.mySimpleStack.saveAnnotations()

	def selectNode(self, nodeIdx, snapz=False):
		print('bStackWidget.selectNode() nodeIdx:', nodeIdx)
		self.myStackView.selectNode(nodeIdx, snapz=snapz)
		#self.repaint() # this is updating the widget !!!!!!!!

	def selectEdge(self, edgeIdx, snapz=False):
		print('bStackWidget.selectEdge() edgeIdx:', edgeIdx)
		self.myStackView.selectEdge(edgeIdx, snapz=snapz)
		#self.repaint() # this is updating the widget !!!!!!!!

	def keyPressEvent(self, event):
		#print('=== bStackWidget.keyPressEvent() event.key():', event.key())
		if event.key() in [QtCore.Qt.Key_Escape]:
			self.myStackView.selectEdge(None)
		elif event.key() in [QtCore.Qt.Key_L]:
			self.showLeftControlBar = not self.showLeftControlBar
			self.updateDisplayedWidgets()
		elif event.key() in [QtCore.Qt.Key_C]:
			self.showContrastBar = not self.showContrastBar
			self.updateDisplayedWidgets()
		elif event.key() in [QtCore.Qt.Key_F]:
			self.showFeebackBar = not self.showFeebackBar
			self.updateDisplayedWidgets()
		elif event.key() in [QtCore.Qt.Key_H]:
			self.printHelp()
		elif event.key() in [QtCore.Qt.Key_B]:
			print('set selected edge to bad')
			selectedEdge = self.myStackView.mySelectedEdge
			self.mySimpleStack.setAnnotation('toggle bad edge', selectedEdge)
			# force refresh of table, I need to use model/view/controller !!!!
			self.annotationTable.refreshRow(selectedEdge)

		#elif event.key() == QtCore.Qt.Key_BraceLeft: # '['
		elif event.text() == '[':
			isVisible = self.annotationTable.isVisible()
			if isVisible:
				self.annotationTable.hide()
				self.showLeftControlBar = False
			else:
				self.annotationTable.show()
				self.showLeftControlBar = True

		else:
			print('bStackWidget.keyPressEvent() not handled', event.text())

	def printHelp(self):
		print('=============================================================')
		print('bStackWidget help')
		print('==============================================================')
		print(' Navigation')
		print('   mouse wheel: scroll through images')
		print('   command + mouse wheel: zoom in/out (follows mouse position)')
		print('   +/-: zoom in/out (follows mouse position)')
		print('   click + drag: pan')
		print(' Show/Hide interface')
		print('   t: show/hide tracing')
		print('   l: show/hide list of annotations')
		print('   c: show/hide contrast bar')
		print('   f: show/hide feedback bar')
		print('   esc: remove edge selection (cyan)')
		print(' Stacks To Display')
		print('   1: Channel 1 - Raw Data')
		print('   2: Channel 2 - Raw Data')
		print('   3: Channel 3 - Raw Data')
		print('   9: Segmentation mask - DeepVess')
		print('   0: Skeleton mask - DeepVess')
		print(' Sliding Z-Projection')
		print('   z: toggle sliding z-projection on/off, will apply to all "Stacks To Display"')
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
	#from bimpy.interface import bStackWidget

	#path = '/Users/cudmore/box/DeepVess/data/invivo/20190613__0028.tif'
	if len(sys.argv) == 2:
		path = sys.argv[1]
	else:
		path = '/Users/cudmore/box/DeepVess/data/immuno-stack/mytest.tif'
		#path = '/Users/cudmore/box/DeepVess/data/invivo/20190613__0028.tif'

		# works well
		path = '/Users/cudmore/box/data/bImpy-Data/deepvess/mytest.tif'
		path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/20191017__0001.tif'

		# for this one, write code to revover tracing versus image scale
		# x/y=0.3107, z=0.5
		path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/high_mag_top_of_node/tracing_20191217.tif'

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
