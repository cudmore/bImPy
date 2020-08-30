# Robert Cudmore
# 20191108

import os, sys, math, time
import numpy as np

#import pyqtgraph as pg
#from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

import bimpy
#from bimpy.interface import bShapeAnalysisWidget
import napari

# not sure if we can use Qt inside of napari???
from qtpy import QtGui, QtCore, QtWidgets

class bNapari:
	"""
	discussion on callbacks
	https://github.com/napari/napari/issues/630

	good example code with mouse callbacks and plotting in pyqtGraph
	https://gist.github.com/aasensio/cb46290686a808c838bcabd01cf9bde2

	discussion about mouse move/dragging, i can't get it to work???
	https://github.com/napari/napari/pull/544
	"""
	def __init__(self, path='', theStack=None, myStackWidget=None):

		print('=== bNapari.__init__() path:', path)

		self.myStackWidget = myStackWidget

		filename = os.path.basename(path)

		# load stack if neccessary
		if theStack is not None:
			self.mySimpleStack = theStack
		else:
			self.mySimpleStack = bimpy.bStack(path)

		#
		title = filename

		stack = self.mySimpleStack.getStackData(channel=1)
		stack_nDim = len(stack.shape)

		self.viewer = napari.Viewer(title=title, ndisplay=stack_nDim)

		#
		# abb 20191216 removed
		self.bShapeAnalysisWidget = None
		#self.bShapeAnalysisWidget = bShapeAnalysisWidget(self.viewer, self.mySimpleStack)
		#

		xVoxel = self.mySimpleStack.xVoxel
		yVoxel = self.mySimpleStack.yVoxel
		zVoxel = self.mySimpleStack.zVoxel

		colormap = 'gray'
		if stack_nDim == 2:
			scale = (xVoxel, yVoxel)
		elif stack_nDim == 3:
			scale = (zVoxel, xVoxel, yVoxel) # (z, x, y)
		else:
			print('error: napari got stack dim it does not understand')

		self.myNapari = self.viewer.add_image(
			stack,
			colormap=colormap,
			scale=scale)

		dvMask = self.mySimpleStack.getDeepVessMask()
		if dvMask is not None:
			self.viewer.add_image(data=dvMask, contrast_limits=[0,1], opacity=0.8, colormap='gray', scale=scale, name='dvMask')

		'''
		@self.viewer.bind_key('u')
		def keyboard_u(viewer):
			shapeType, data = self._getSelectedLine()
			print('   keyboard_u()', shapeType, data)
			if shapeType == 'line':
				src = data[0]
				dst = data[1]
				self.bShapeAnalysisWidget.updateStackLineProfile(src, dst)
			if shapeType in ['rectangle', 'polygon']:
				self.bShapeAnalysisWidget.updateStackPolygon(data)
		'''

		if self.mySimpleStack.slabList is not None:
			x = self.mySimpleStack.slabList.x * xVoxel
			y = self.mySimpleStack.slabList.y * yVoxel
			z = self.mySimpleStack.slabList.z * zVoxel
			d = self.mySimpleStack.slabList.d * xVoxel # use x
			d2 = self.mySimpleStack.slabList.d2 * xVoxel # use x
			nodeIdx = self.mySimpleStack.slabList.nodeIdx

			# this has nans which I assume will lead to some crashes ...
			points = np.column_stack((z,x,y,))

			scaleFactor = 0.6
			print('warning: bNapari is scaling diameters by scaleFactor ... d = d *', scaleFactor)
			dCopy = d * scaleFactor
			d2Copy = d2 * scaleFactor

			fixedNodeSize = 4

			#
			size_myNodes = []
			face_color_myNodes = []
			slabs_nodes = []
			#
			size_myEdges = []
			face_color_myEdges = []
			slabs_edge = []
			for idx in range(len(x)):
				if np.isnan(dCopy[idx]):
					thisSize = 5
				else:
					thisSize = dCopy[idx]
				if nodeIdx[idx]>=0:
					intNodeIdx = int(float(nodeIdx[idx]))
					nEdges = self.mySimpleStack.slabList.nodeDictList[intNodeIdx]['nEdges']
					#nodeSize = thisSize # dynamic size
					nodeSize = fixedNodeSize # fixed size
					slabs_nodes.append(idx)
					size_myNodes.append(nodeSize)
					if nEdges == 1:
						# dead end
						face_color_myNodes.append('orange')
					else:
						face_color_myNodes.append('red')
				else:
					slabSize = thisSize
					#slabSize = 5 # fixed size
					slabs_edge.append(idx)
					size_myEdges.append(slabSize)
					face_color_myEdges.append('cyan')
			# remember, (size, face_color), etc. Can be a scalar to set one value

			# debug
			if 0:
				print('   points:', points.shape)
				print('   len(size)', len(size))
				print('   len(face_color)', len(face_color))

			# nodes
			points_nodes = np.column_stack((z[slabs_nodes],x[slabs_nodes],y[slabs_nodes],))
			self.pointLayer = self.viewer.add_points(points_nodes, size=size_myNodes, face_color=face_color_myNodes) #, n_dimensional=False)
			self.pointLayer.name = 'Nodes'

			# edges
			points_edges = np.column_stack((z[slabs_edge],x[slabs_edge],y[slabs_edge],))
			self.pointLayer = self.viewer.add_points(points_edges, size=size_myEdges, face_color=face_color_myEdges) #, n_dimensional=False)
			self.pointLayer.name = 'Edges'

			#
			# connect edges with shape layer of 'path'
			print('making edge vector layer ... WE WILL ONLY DO THIS FOR 800 edges !!!')
			defaultWidth = 2
			masterEdgeList = []
			myPathColors = []
			myPathEdgeWidths = []
			for idx, edge in enumerate(self.mySimpleStack.slabList.edgeIter()):
				if idx > 800:
					continue
				edgeColor = edge['color'] # when i make edges, i was not assigning color
				if edgeColor is None:
					edgeColor = 'cyan'
				slabList = edge['slabList']
				#print('edge idx:', idx, 'edgeColor:', edgeColor, 'len(slabList):', len(slabList))
				currentEdgeList = []
				for slab in slabList:
					slabWidth = d2Copy[slab] #* xVoxel # my slab width is still in pixels
					if np.isnan(slabWidth):
						#print('edge', idx, 'slab', slab, 'has nan width')
						slabWidth = defaultWidth
					currentEdgeList.append([z[slab], x[slab], y[slab]])
					myPathColors.append(edgeColor)
					myPathEdgeWidths.append(slabWidth)
				masterEdgeList.append(currentEdgeList) # this will be list of list

			myEdgesPaths  = [np.array(xx) for xx in masterEdgeList] # always give napari a list where each[i] is a np.array ???
			#
			self.myShapePathLayer = self.viewer.add_shapes(
				myEdgesPaths, shape_type='path', edge_width=myPathEdgeWidths, edge_color=myPathColors,
				name='Edges Paths'
			)
			self.myShapePathLayer.editable = True

		self.connectNapari() # connect signals and slots

		#
		# make selection layers
		if self.mySimpleStack.slabList is not None:
			# edge selection
			selectionSize = 7 * xVoxel #np.column_stack((6,6,6,))
			face_color = 'yellow'
			tmpData = np.column_stack((np.nan,np.nan,np.nan,)) #todo: fix this
			self.edgeSelectionLayer = self.viewer.add_points(tmpData, size=selectionSize, face_color=face_color, n_dimensional=False)
			self.edgeSelectionLayer.name = 'Edge Selection'
			#
			flashSize = 10 * xVoxel
			flashColor = 'magenta'
			self.edgeSelectionLayerFlash = self.viewer.add_points(tmpData, size=flashSize, face_color=flashColor, n_dimensional=False)
			self.edgeSelectionLayerFlash.name = 'Flash Selection'

			# node selection
			selectionSize = 7  * xVoxel #np.column_stack((6,6,6,))
			face_color = 'yellow'
			tmpData = np.column_stack((np.nan, np.nan, np.nan,)) #todo: fix this
			self.nodeSelectionLayer = self.viewer.add_points(tmpData, size=selectionSize, face_color=face_color, n_dimensional=False)
			self.nodeSelectionLayer.name = 'Node Selection'
			#
			flashSize = 15  * xVoxel
			flashColor = 'magenta'
			self.nodeSelectionLayerFlash = self.viewer.add_points(tmpData, size=flashSize, face_color=flashColor, n_dimensional=False)
			self.nodeSelectionLayerFlash.name = 'Node Selection'

	def myMouseDown_Shape(self, layer, event):
		print('bNapari.myMouseDown_Shape()')
		selectedDataList = self.pointLayer.selected_data
		print('   selectedDataList:', selectedDataList)

	def connectNapari(self):
		"""
		connect to signal/slots
		"""
		self.myStackWidget.getStackView().selectNodeSignal.connect(self.slot_selectNode)
		self.myStackWidget.getStackView().selectEdgeSignal.connect(self.slot_selectEdge)
		# listen to self.annotationTable
		self.myStackWidget.nodeTable2.selectRowSignal.connect(self.slot_selectNode) # change to slot_selectNode ???
		self.myStackWidget.edgeTable2.selectRowSignal.connect(self.slot_selectEdge) # change to slot_selectNode ???
		# listen to edit table, self.
		self.myStackWidget.editTable2.selectRowSignal.connect(self.slot_selectNode)
		self.myStackWidget.editTable2.selectRowSignal.connect(self.slot_selectEdge)

	def flashNode(self, nodeIdx, numberOfFlashes=2):
		if nodeIdx is None:
			return
		if self.mySimpleStack.slabList is None:
			return
		#
		if numberOfFlashes>0:
			x, y, z = self.mySimpleStack.slabList.getNode_xyz_scaled(nodeIdx)
			nodeSelection = np.column_stack((z,x,y,)) # (z, x, y)
			self.nodeSelectionLayerFlash.data = nodeSelection
			#
			QtCore.QTimer.singleShot(20, lambda:self.flashNode(nodeIdx, numberOfFlashes-1))
		else:
			nodeSelection = np.column_stack((np.nan,np.nan,np.nan,)) # (z, x, y)
			self.nodeSelectionLayerFlash.data = nodeSelection

	def flashEdgeSelection(self, numberOfFlashes=2):
		"""
		flash an existing edge selection
		slightly different, called after and uses data in self.edgeSelectionLayer.data
		Should be called flashEdgeSelection
		"""
		if self.mySimpleStack.slabList is None:
			return
		#
		# don't flash if we have lots of slabs
		if len (self.edgeSelectionLayer.data) > 1000:
			return
		#
		if numberOfFlashes>0:
			self.nodeSelectionLayerFlash.data = self.edgeSelectionLayer.data
			#
			QtCore.QTimer.singleShot(20, lambda:self.flashEdgeSelection(numberOfFlashes-1))
		else:
			emptyEdgeSelection = np.column_stack((np.nan,np.nan,np.nan,)) # (z, x, y)
			self.nodeSelectionLayerFlash.data = emptyEdgeSelection

	def slot_selectNode(self, myEvent):
		print('bNapari.slot_selectNode() myEvent:', myEvent)

		nodeIdx = myEvent.nodeIdx
		nodeList = myEvent.nodeList

		doSelection = False
		if len(nodeList)>0:
			doSelection = True
			xList = []
			yList = []
			zList = []
			for tmpNodeIdx in nodeList:
				x, y, z, = self.mySimpleStack.slabList.getNode_xyz_scaled(tmpNodeIdx)
				xList.append(x)
				yList.append(y)
				zList.append(z)
			#
			nodeSelection = np.column_stack((zList,xList,yList,))
		elif nodeIdx is None:
			#nodeSelection = np.column_stack((np.nan,np.nan,np.nan,))
			doSelection = False
		else:
			'''
			slabIdx = self.mySimpleStack.slabList._getSlabFromNodeIdx(nodeIdx)
			x = self.mySimpleStack.slabList.x[nodeIdx]
			y = self.mySimpleStack.slabList.y[nodeIdx]
			z = self.mySimpleStack.slabList.z[nodeIdx]
			'''
			doSelection = True
			x, y, z, = self.mySimpleStack.slabList.getNode_xyz_scaled(nodeIdx)

			#d = self.mySimpleStack.slabList.d[slabIdx]
			nodeSelection = np.column_stack((z,x,y,)) # (z, x, y)
			print('   nodeSelection:', nodeSelection)

			QtCore.QTimer.singleShot(10, lambda:self.flashNode(nodeIdx, 2))

		# select (can be nan)
		if doSelection:
			self.nodeSelectionLayer.data = nodeSelection
			'''
			xVoxel = self.mySimpleStack.xVoxel
			self.nodeSelectionLayer.size = 5 * xVoxel
			'''

	def slot_selectEdge(self, myEvent):
		"""
		todo: this is super messy ... fix it
		"""
		#print('bNapari.slot_selectEdge() myEvent:', myEvent)

		if myEvent.eventType == 'select node':
			return

		isShift = myEvent.isShift
		edgeIdx = myEvent.edgeIdx
		edgeList = myEvent.edgeList
		colorList = myEvent.colorList

		print('bNapari.slot_selectEdge() edgeIdx:', edgeIdx, 'edgeList:', edgeList, 'colorList:', colorList)

		face_color = 'yellow'
		plotColorList = []

		doSelection = False
		if len(edgeList)>0:
			# select a list of edges
			doSelection = True
			slabList = []
			for i, edgeIdx in enumerate(edgeList):
				slabs = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
				slabList += slabs
				tmpColor = self.mySimpleStack.slabList.getEdge(edgeIdx)['color'] # defined in bVascularTracing.colorize()
				for tmpSLab in slabs:
					if len(colorList) > 0:
						plotColorList.append(colorList[i])
					else:
						# use color of edge
						plotColorList.append(tmpColor)
		elif edgeIdx is None:
			doSelection = False
		elif edgeIdx >= 0:
			# select a single edge
			doSelection = True
			slabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)

		if doSelection:
			x = self.mySimpleStack.slabList.x[slabList] * self.mySimpleStack.xVoxel
			y = self.mySimpleStack.slabList.y[slabList] * self.mySimpleStack.yVoxel
			z = self.mySimpleStack.slabList.z[slabList] * self.mySimpleStack.zVoxel
			d = self.mySimpleStack.slabList.d[slabList] * self.mySimpleStack.xVoxel # using x
			edgeSelection = np.column_stack((z,x,y,)) # (z, x, y)
		else:
			edgeSelection = np.column_stack((np.nan,np.nan,np.nan,))

		#size = d #/ 300

		self.edgeSelectionLayer.data = edgeSelection
		#print('bNapari plotColorList:', plotColorList)
		if len(plotColorList)>0:
			self.edgeSelectionLayer.face_color = plotColorList
		else:
			self.edgeSelectionLayer.face_color = 'yellow'

		if edgeIdx is None:
			pass
		else:
			if isShift:
				colors = ['r', 'g', 'r', 'g']
				edge = self.mySimpleStack.slabList.edgeDictList[edgeIdx]
				selectedEdgeList = [edgeIdx] # could be [edgeIdx]
				colorList = ['y']
				if edge['preNode'] is not None:
					#print('   selectEdge() selecting edges on preNode:', edge['preNode'], 'of edgeIdx:', edgeIdx)
					edgeList = self.mySimpleStack.slabList.nodeDictList[edge['preNode']]['edgeList']
					edgeList = list(edgeList) # make a copy
					try:
						repeatIdx = edgeList.index(edgeIdx) # find the index of our original edgeIdx and remove it
						edgeList.pop(repeatIdx)
					except (ValueError) as e:
						print('WARNING: selectEdge() pre node:', edge['preNode'], 'edgeList:', edgeList, 'does not contain:', edgeIdx)
					selectedEdgeList += edgeList
					colorList += [colors[colorIdx] for colorIdx in range(len(edgeList))]
				if edge['postNode'] is not None:
					#print('   selectEdge() selecting edges on postNode:', edge['postNode'], 'of edgeIdx:', edgeIdx)
					edgeList = self.mySimpleStack.slabList.nodeDictList[edge['postNode']]['edgeList']
					edgeList = list(edgeList) # make a copy
					try:
						repeatIdx = edgeList.index(edgeIdx) # find the index of our original edgeIdx and remove it
						edgeList.pop(repeatIdx)
					except (ValueError) as e:
						print('WARNING: selectEdge() post node:', edge['postNode'], 'edgeList:', edgeList, 'does not contain:', edgeIdx)
					selectedEdgeList += edgeList
					colorList += [colors[colorIdx] for colorIdx in range(len(edgeList))]
				#print('edgeList:', edgeList)
				#self.selectEdgeList(selectedEdgeList, thisColorList=colorList)

				#print('   selecting edge list:', selectedEdgeList)
				# select a list of edges
				#self.selectEdgeList(edgeList, snapz=True)
				slabList = []
				plotColorList = []
				for tmpIdx, tmpEdgeIdx in enumerate(selectedEdgeList):
					slabs = self.mySimpleStack.slabList.getEdgeSlabList(tmpEdgeIdx)
					slabList += slabs
					for tmpSlab in slabs:
						plotColorList.append(colorList[tmpIdx])

				x = self.mySimpleStack.slabList.x[slabList] * self.mySimpleStack.xVoxel
				y = self.mySimpleStack.slabList.y[slabList] * self.mySimpleStack.yVoxel
				z = self.mySimpleStack.slabList.z[slabList] * self.mySimpleStack.zVoxel
				d = self.mySimpleStack.slabList.d[slabList] * self.mySimpleStack.xVoxel # using x

				edgeSelection = np.column_stack((z,x,y,)) # (z, x, y)
				size = d #/ 300
				face_color = 'yellow'
				#nodeLayer = self.viewer.add_points(self.edgeSelection, size=size, face_color=face_color, n_dimensional=False)
				#nodeLayer.name = 'Edge Selection'
				#print('2) edgeSelection:', edgeSelection)
				self.edgeSelectionLayer.data = edgeSelection
				#xVoxel = self.mySimpleStack.xVoxel
				if len(plotColorList) > 0:
					self.edgeSelectionLayer.face_color = plotColorList
				else:
					self.edgeSelectionLayer.face_color = 'yellow'

		# slighter different, flash once we have made the edge selection
		QtCore.QTimer.singleShot(10, lambda:self.flashEdgeSelection(2))

if __name__ == '__main__':
	#from PyQt5 import QtGui, QtCore, QtWidgets
	#from qtpy import QtGui, QtCore, QtWidgets
	# stack of vessel staining
	#path = '/Users/cudmore/box/data/nathan/vesselucida/20191017__0001.tif'
	# video of sa node artery, this file s too big, 1.2 GB, keep slices 4166, 9416
	path = '/Users/cudmore/box/data/bImpy-Data/high-k-video/HighK-aligned-8bit-short.tif'

	# octa
	#path = '/Users/cudmore/box/data/OCTa/vesselucida/PV_Crop_Reslice.tif'

	#app = QtWidgets.QApplication(sys.argv)
	with napari.gui_qt():
		mn = bNapari(path)
	#sys.exit(app.exec_())
