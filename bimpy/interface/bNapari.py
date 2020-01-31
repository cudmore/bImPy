# Robert Cudmore
# 20191108

import os, sys, math, time
import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

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

		#self.viewer = napari.Viewer(title=title, ndisplay=3)
		self.viewer = napari.Viewer(title=title)

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
		self.myNapari = self.viewer.add_image(
			self.mySimpleStack.stack[0,:,:,:],
			colormap=colormap,
			scale=scale)#,
			#title=title)

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

			'''
			xUmPerPixel = 0.49718
			yUmPerPixel = 0.49718
			zUmPerPixel = 0.6
			'''

			#d /= 300

			# this has nans which I assume will lead to some crashes ...
			points = np.column_stack((z,x,y,))
			print('   points.shape:', points.shape)

			# all points will be one size
			#size = 10
			size = d

			# this allows us to color different points with different colors
			#use this to label: ('nodes')
			# we can also change the size of different points
			#slabSize = 5
			#nodeSize = 9

			size = []
			face_color = []
			foundNan = False
			for i, idx in enumerate(range(len(x))):
				if foundNan:
					nodeSize = d[idx] # might not be good idea
					size.append(nodeSize)
					face_color.append('red')
					foundNan = False
				else:
					slabSize = d[idx] # might not be good idea
					size.append(slabSize)
					face_color.append('cyan')
				if math.isnan(x[i]):
					foundNan = True
					#print('point', i, 'is nan')

			# remember, (size, face_color), etc. Can be a scalar to set one value
			print('   points:', points.shape)
			print('   len(size)', len(size))
			print('   len(face_color)', len(face_color))
			#pointLayer = self.viewer.add_points(points, size=size, face_color=face_color, n_dimensional=False)
			pointLayer = self.viewer.add_points(points, n_dimensional=True)
			pointLayer.name = 'All Points'

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
		# make a selection layer
		self.nodeSelection = []
		self.edgeSelection = np.column_stack((np.nan,np.nan,np.nan,))
		if self.mySimpleStack.slabList is not None:
			'''
			slabList = self.mySimpleStack.slabList.getEdgeSlabList(10)
			x = self.mySimpleStack.slabList.x[slabList]
			y = self.mySimpleStack.slabList.y[slabList]
			z = self.mySimpleStack.slabList.z[slabList]
			d = self.mySimpleStack.slabList.d[slabList]
			self.edgeSelection = np.column_stack((x,y,z,))
			size = d / 300
			'''
			size = np.column_stack((10,10,10,))
			face_color = 'yellow'
			face_color = [1,1,1]
			#self.edgeSelection = np.column_stack((myNaN,myNaN,myNaN,))
			self.edgeSelection = np.column_stack((0,0,0,)) #todo: fix this
			self.selectionLayer = self.viewer.add_points(self.edgeSelection, size=size, face_color=face_color, n_dimensional=False)
			self.selectionLayer.name = 'Edge Selection'
			#print('nodeLayer.data:', nodeLayer.data)

	def connectNapari(self):
		"""
		connect to signal/slots
		"""
		self.myStackWidget.myStackView.selectNodeSignal.connect(self.slot_selectNode)
		self.myStackWidget.myStackView.selectEdgeSignal.connect(self.slot_selectEdge)
		# listen to self.annotationTable
		self.myStackWidget.annotationTable.selectNodeSignal.connect(self.slot_selectNode) # change to slot_selectNode ???
		self.myStackWidget.annotationTable.selectEdgeSignal.connect(self.slot_selectEdge) # change to slot_selectNode ???
		# listen to edit table, self.
		self.myStackWidget.annotationTable.myEditTableWidget.selectEdgeSignal.connect(self.slot_selectEdge)

	def slot_selectNode(Self, myEvent):
		print('bNapari.slot_selectNode()')

	def slot_selectEdge(self, myEvent):
		"""
		20200130, this is super messy ...
		todo: fix it
		"""
		#print('bNapari.slot_selectEdge() myEvent:', myEvent)

		isShift = myEvent.isShift
		edgeIdx = myEvent.edgeIdx
		edgeList = myEvent.edgeList

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

		else:
			#print('   selecting single edge:', myEvent.edgeIdx)
			slabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
			x = self.mySimpleStack.slabList.x[slabList]
			y = self.mySimpleStack.slabList.y[slabList]
			z = self.mySimpleStack.slabList.z[slabList]
			d = self.mySimpleStack.slabList.d[slabList]

		edgeSelection = np.column_stack((z,x,y,)) # (z, x, y)
		size = d #/ 300
		face_color = 'yellow'
		#nodeLayer = self.viewer.add_points(self.edgeSelection, size=size, face_color=face_color, n_dimensional=False)
		#nodeLayer.name = 'Edge Selection'
		#print('1) edgeSelection:', edgeSelection)
		self.selectionLayer.data = edgeSelection
		#self.selectionLayer.face_color = ['magenta']

		if edgeIdx is not None:
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
	# stack of vessel staining
	#path = '/Users/cudmore/box/data/nathan/vesselucida/20191017__0001.tif'
	# video of sa node artery, this file s too big, 1.2 GB, keep slices 4166, 9416
	path = '/Users/cudmore/box/data/bImpy-Data/high-k-video/HighK-aligned-8bit-short.tif'

	# octa
	#path = '/Users/cudmore/box/data/OCTa/vesselucida/PV_Crop_Reslice.tif'

	app = QtWidgets.QApplication(sys.argv)
	mn = bNapari(path)
	sys.exit(app.exec_())
