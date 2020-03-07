# Robert Cudmore
# 20191108

import os, sys, math, time
import numpy as np

#import pyqtgraph as pg
#from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

import bimpy
#from bimpy.interface import bShapeAnalysisWidget
import napari

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

		# todo: this is loading again? just pass data to __init__ if already loaded
		if theStack is not None:
			self.mySimpleStack = theStack
		else:
			self.mySimpleStack = bimpy.bStack(path)

		#print('   self.mySimpleStack.stack.shape:', self.mySimpleStack.stack.shape)

		self.sliceNum = 0

		#
		# napari
		colormap = 'green'
		scale = (1,1,1) #(1,0.2,0.2)
		#scale = (0.49718, 0.49718, 0.6)
		title = filename

		stack = self.mySimpleStack.getStackData(channel=1)
		stack_nDim = len(stack.shape)

		self.viewer = napari.Viewer(title=title, ndisplay=stack_nDim)
		#self.viewer = napari.Viewer(title=title)

		#
		#
		# replace all the above with this !!!
		# abb 20191216 removed
		self.bShapeAnalysisWidget = None
		#self.bShapeAnalysisWidget = bShapeAnalysisWidget(self.viewer, self.mySimpleStack)
		#
		#

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

		#self.myNapari = napari.view_image(
		#print('napari stack_nDim:', stack_nDim)
		if stack_nDim == 2:
			scale = (1,1)
		elif stack_nDim == 3:
			scale = (1,1,1)
		else:
			print('error: napari got stack dim it does not understand')

		self.myNapari = self.viewer.add_image(
			stack,
			colormap=colormap,
			scale=scale)

		dvMask = self.mySimpleStack.getDeepVessMask()
		if dvMask is not None:
			self.viewer.add_image(data=dvMask, contrast_limits=[0,1], opacity=0.8, colormap='gray', name='dvMask')

		# this works
		# make a callback for all mouse moves
		'''
		@self.myNapari.mouse_move_callbacks.append
		def myNapari_mouse_move_callback(viewer, event):
			self.myMouseMove_Action(viewer, event)
		'''

		# callback for user changing slices
		self.myNapari.dims.events.axis.connect(self.my_update_slider)

		if self.mySimpleStack.slabList is not None:
			x = self.mySimpleStack.slabList.x
			y = self.mySimpleStack.slabList.y
			z = self.mySimpleStack.slabList.z
			d = self.mySimpleStack.slabList.d
			nodeIdx = self.mySimpleStack.slabList.nodeIdx

			'''
			xUmPerPixel = 0.49718
			yUmPerPixel = 0.49718
			zUmPerPixel = 0.6
			'''

			#d /= 300

			# this has nans which I assume will lead to some crashes ...
			points = np.column_stack((z,x,y,))

			print('warning: bNapari is scaling diameters ... d = d * 0.8')
			dCopy = d * 0.8

			size = []
			face_color = []
			#foundNan = False
			for idx in range(len(x)):
				#if foundNan:
				if nodeIdx[idx]>=0:
					nodeSize = dCopy[idx] # might not be good idea
					size.append(nodeSize)
					face_color.append('red')
					foundNan = False
				else:
					slabSize = dCopy[idx] # might not be good idea
					size.append(slabSize)
					face_color.append('cyan')
				'''
				if math.isnan(x[dxi]):
					foundNan = True
					#print('point', idx, 'is nan')
				'''
			# remember, (size, face_color), etc. Can be a scalar to set one value
			# debug
			if 0:
				print('   points:', points.shape)
				print('   len(size)', len(size))
				print('   len(face_color)', len(face_color))

			self.pointLayer = self.viewer.add_points(points, size=size, face_color=face_color) #, n_dimensional=False)
			#pointLayer = self.viewer.add_points(points, n_dimensional=True)
			self.pointLayer.name = 'Vascular Tracing'

			@self.pointLayer.mouse_drag_callbacks.append
			def shape_mouse_move_callback(layer, event):
				"""respond to mouse_down """
				self.myMouseDown_Shape(layer, event)


		self.connectNapari() # connect signals and slots

		#
		# nodes
		# abb upgrade bSlabList
		'''
		if self.mySimpleStack.slabList is not None:
			# nodes are the correct connection points between vessels
			# e.g. the ones correctly identified in vesselucida xml
			x = self.mySimpleStack.slabList.nodex
			y = self.mySimpleStack.slabList.nodey
			z = self.mySimpleStack.slabList.nodez
			#size = 10
			size = self.mySimpleStack.slabList.noded
			#
			#size /= 300
			#
			face_color = 'red'
			nodePoints = np.column_stack((z,x,y,))
			#nodeLayer = self.myNapari.add_points(nodePoints, size=size, face_color=face_color, n_dimensional=False)
			nodeLayer = self.viewer.add_points(nodePoints, size=size, face_color=face_color, n_dimensional=False)
			nodeLayer.name = 'Nodes'
		'''

		#
		# dead ends
		# abb upgrade bSlabList
		'''
		if self.mySimpleStack.slabList is not None:
			x = self.mySimpleStack.slabList.deadEndx
			y = self.mySimpleStack.slabList.deadEndy
			z = self.mySimpleStack.slabList.deadEndz
			size = 10
			face_color = 'blue'
			nodePoints = np.column_stack((z,x,y,))
			#nodeLayer = self.myNapari.add_points(nodePoints, size=size, face_color=face_color, n_dimensional=False)
			nodeLayer = self.viewer.add_points(nodePoints, size=size, face_color=face_color, n_dimensional=False)
			nodeLayer.name = 'Dead Ends'
		'''

		#
		# make selection layers
		if self.mySimpleStack.slabList is not None:
			# edge selection
			size = np.column_stack((3,3,3,))
			face_color = 'yellow'
			tmpData = np.column_stack((np.nan,np.nan,np.nan,)) #todo: fix this
			self.selectionLayer = self.viewer.add_points(tmpData, size=size, face_color=face_color, n_dimensional=False)
			self.selectionLayer.name = 'Edge Selection'
			#print('nodeLayer.data:', nodeLayer.data)

			# node selection
			size = np.column_stack((6,6,6,))
			face_color = 'yellow'
			tmpData = np.column_stack((0,0,0,)) #todo: fix this
			self.nodeSelectionLayer = self.viewer.add_points(tmpData, size=size, face_color=face_color, n_dimensional=False)
			self.nodeSelectionLayer.name = 'Node Selection'

	def myMouseDown_Shape(self, layer, event):
		print('bNapari.myMouseDown_Shape()')
		selectedDataList = self.pointLayer.selected_data
		print('   selectedDataList:', selectedDataList)

	def connectNapari(self):
		"""
		connect to signal/slots
		"""
		self.myStackWidget.myStackView.selectNodeSignal.connect(self.slot_selectNode)
		self.myStackWidget.myStackView.selectEdgeSignal.connect(self.slot_selectEdge)
		# listen to self.annotationTable
		self.myStackWidget.nodeTable2.selectRowSignal.connect(self.slot_selectNode) # change to slot_selectNode ???
		self.myStackWidget.edgeTable2.selectRowSignal.connect(self.slot_selectEdge) # change to slot_selectNode ???
		# listen to edit table, self.
		self.myStackWidget.editTable2.selectRowSignal.connect(self.slot_selectEdge)

	def slot_selectNode(self, myEvent):
		print('bNapari.slot_selectNode() myEvent:', myEvent)
		nodeIdx = myEvent.nodeIdx
		if nodeIdx is None:
			nodeSelection = np.column_stack((np.nan,np.nan,np.nan,))
		else:
			'''
			slabIdx = self.mySimpleStack.slabList._getSlabFromNodeIdx(nodeIdx)
			x = self.mySimpleStack.slabList.x[nodeIdx]
			y = self.mySimpleStack.slabList.y[nodeIdx]
			z = self.mySimpleStack.slabList.z[nodeIdx]
			'''
			x, y, z, = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)

			#d = self.mySimpleStack.slabList.d[slabIdx]
			nodeSelection = np.column_stack((z,x,y,)) # (z, x, y)
			print('   nodeSelection:', nodeSelection)

		self.nodeSelectionLayer.data = nodeSelection

	def slot_selectEdge(self, myEvent):
		"""
		20200130, this is super messy ...
		todo: fix it
		"""
		#print('bNapari.slot_selectEdge() myEvent:', myEvent)

		isShift = myEvent.isShift
		edgeIdx = myEvent.edgeIdx
		edgeList = myEvent.edgeList

		print('bNapari.slot_selectEdge() edgeIdx:', edgeIdx)

		face_color = 'yellow'

		if len(edgeList)>0:
			#print('   selecting edge list:', edgeList)
			# select a list of edges
			slabList = []
			for edgeIdx in edgeList:
				slabs = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
				slabList += slabs
			x = self.mySimpleStack.slabList.x[slabList] # flipped
			y = self.mySimpleStack.slabList.y[slabList]
			z = self.mySimpleStack.slabList.z[slabList]
			d = self.mySimpleStack.slabList.d[slabList]
			edgeSelection = np.column_stack((z,x,y,)) # (z, x, y)
			size = d #/ 300

		elif edgeIdx is None:
			edgeSelection = np.column_stack((np.nan,np.nan,np.nan,))
		else:
			#print('   selecting single edge:', myEvent.edgeIdx)
			slabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
			x = self.mySimpleStack.slabList.x[slabList]
			y = self.mySimpleStack.slabList.y[slabList]
			z = self.mySimpleStack.slabList.z[slabList]
			d = self.mySimpleStack.slabList.d[slabList]
			edgeSelection = np.column_stack((z,x,y,)) # (z, x, y)
			size = d #/ 300

		self.selectionLayer.data = edgeSelection

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
				for tmpEdgeIdx in selectedEdgeList:
					slabs = self.mySimpleStack.slabList.getEdgeSlabList(tmpEdgeIdx)
					slabList += slabs

				x = self.mySimpleStack.slabList.x[slabList] # flipped
				y = self.mySimpleStack.slabList.y[slabList]
				z = self.mySimpleStack.slabList.z[slabList]
				d = self.mySimpleStack.slabList.d[slabList]

				edgeSelection = np.column_stack((z,x,y,)) # (z, x, y)
				size = d #/ 300
				face_color = 'yellow'
				#nodeLayer = self.viewer.add_points(self.edgeSelection, size=size, face_color=face_color, n_dimensional=False)
				#nodeLayer.name = 'Edge Selection'
				#print('2) edgeSelection:', edgeSelection)
				self.selectionLayer.data = edgeSelection

	# this works
	def myMouseMove_Shape(self, layer, event):
		"""
		Detect mouse move in shape layer (not called when mouse is down).

		event is type vispy.app.canvas.MouseEvent
		see: http://api.vispy.org/en/v0.1.0-0/event.html
		"""
		pass

	def my_update_slider(self, event):
		"""
		Respond to user changing slice/image slider
		"""
		#print('my_update_slider() event:', event)
		if (event.axis == 0):
			self.sliceNum = self.viewer.dims.indices[0]
			'''
			self.plot_pg_slice(self.sliceNum)
			# using new slice, update the intensity of a line
			self.updateLines()
			'''
			#
			# plugin
			'''
			self.bShapeAnalysisWidget.updateVerticalSliceLine(self.sliceNum)
			'''
			#self.bShapeAnalysisWidget.updateVerticalSliceLine(self.sliceNum)

			# todo: this does not feal right ... fix this !!!
			'''
			shapeType, data = self._getSelectedLine()
			if shapeType == 'line':
				src = data[0]
				dst = data[1]
				self.bShapeAnalysisWidget.updateLines(self.sliceNum, src, dst)
			if shapeType in ['rectangle', 'polygon']:
				self.bShapeAnalysisWidget.updatePolygon(self.sliceNum, data)
			'''

	def _getSelectedLine(self):
		"""
		return (src, dst), the coordinates of the selected line
		"""
		# selected_data is a list of int tell us index into self.shapeLayer.data of all selected shapes
		selectedDataList = self.shapeLayer.selected_data
		print('bNapari._getSelectedLine() selectedDataList:', selectedDataList)
		if len(selectedDataList) > 0:
			index = selectedDataList[0] # just the first selected shape
			shapeType = self.shapeLayer.shape_types[index]
			print('   shapeType:', shapeType) #('line', 'rectangle', 'polygon')
			print('      self.shapeLayer.data[index]:', self.shapeLayer.data[index])
			# was this
			#src = self.shapeLayer.data[index][0]
			#dst = self.shapeLayer.data[index][1]
			#return (src, dst)
			return shapeType, self.shapeLayer.data[index]
		else:
			return (None, None)

	def updateLines(self):
		"""
		update pg plots with line intensity profile

		get one selected line from list(self.shapeLayer.selected_data)
		"""
		# loop through all lines?
		#for data in self.shapeLayer.data:
		'''
		shapeType, data = self._getSelectedLine()
		if shapeType == 'line':
			src = data[0]
			dst = data[1]
			self.bShapeAnalysisWidget.updateLines(self.sliceNum, src, dst)
		if shapeType in ['rectangle', 'polygon']:
			self.bShapeAnalysisWidget.updatePolygon(self.sliceNum, data)
		'''

	def lineShapeChange_callback(self, layer, event):
		"""
		Callback for when user clicks+drags to resize a line shape.

		Responding to @self.shapeLayer.mouse_drag_callbacks
		"""
		self.updateLines()

	'''
	# this works
	def myMouseMove_Action(self, viewer, event):
		print('myMouseMove_Action() viewer:', viewer, 'event:', event)
		ind_z, ind_x, ind_y = np.round(viewer.coordinates).astype('int')
		print('   myMouseMove_Action()', ind_z, ind_x, ind_y)
	'''

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
