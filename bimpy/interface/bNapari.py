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
	def __init__(self, path='', theStack=None):

		print('=== bNapari.__init__() path:', path)

		filename = os.path.basename(path)

		# todo: this is loading again? just pass data to __init__ if already loaded
		if theStack is not None:
			self.myStack = theStack
		else:
			self.myStack = bimpy.bStack(path)

		#print('   self.myStack.stack.shape:', self.myStack.stack.shape)

		self.sliceNum = 0

		#
		# napari
		colormap = 'green'
		scale = (1,1,1) #(1,0.2,0.2)
		#scale = (0.49718, 0.49718, 0.6)
		title = filename

		self.viewer = napari.Viewer(title=title, ndisplay=3)

		#
		#
		# replace all the above with this !!!
		# abb 20191216 removed
		self.bShapeAnalysisWidget = None
		#self.bShapeAnalysisWidget = bShapeAnalysisWidget(self.viewer, self.myStack)
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
			self.myStack.stack[0,:,:,:],
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

		if self.myStack.slabList is not None:
			x = self.myStack.slabList.x
			y = self.myStack.slabList.y
			z = self.myStack.slabList.z
			d = self.myStack.slabList.d

			'''
			xUmPerPixel = 0.49718
			yUmPerPixel = 0.49718
			zUmPerPixel = 0.6
			'''
			d /= 300

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
			pointLayer = self.viewer.add_points(points, size=size, face_color=face_color, n_dimensional=False)
			pointLayer.name = 'All Points'

		#
		# nodes
		if self.myStack.slabList is not None:
			# nodes are the correct connection points between vessels
			# e.g. the ones correctly identified in vesselucida xml
			x = self.myStack.slabList.nodex
			y = self.myStack.slabList.nodey
			z = self.myStack.slabList.nodez
			#size = 10
			size = self.myStack.slabList.noded
			#
			#size /= 300
			#
			face_color = 'red'
			nodePoints = np.column_stack((z,x,y,))
			#nodeLayer = self.myNapari.add_points(nodePoints, size=size, face_color=face_color, n_dimensional=False)
			nodeLayer = self.viewer.add_points(nodePoints, size=size, face_color=face_color, n_dimensional=False)
			nodeLayer.name = 'Nodes'

		#
		# dead ends
		if self.myStack.slabList is not None:
			x = self.myStack.slabList.deadEndx
			y = self.myStack.slabList.deadEndy
			z = self.myStack.slabList.deadEndz
			size = 10
			face_color = 'blue'
			nodePoints = np.column_stack((z,x,y,))
			#nodeLayer = self.myNapari.add_points(nodePoints, size=size, face_color=face_color, n_dimensional=False)
			nodeLayer = self.viewer.add_points(nodePoints, size=size, face_color=face_color, n_dimensional=False)
			nodeLayer.name = 'Dead Ends'

		#
		# make a selection layer
		self.nodeSelection = []
		self.edgeSelection = np.column_stack((np.nan,np.nan,np.nan,))
		if self.myStack.slabList is not None:
			slabList = self.myStack.slabList.getEdge(10)
			x = self.myStack.slabList.x[slabList]
			y = self.myStack.slabList.y[slabList]
			z = self.myStack.slabList.z[slabList]
			d = self.myStack.slabList.d[slabList]
			self.edgeSelection = np.column_stack((x,y,z,))
			size = d / 300
			face_color = 'yellow'
			self.selectionLayer = self.viewer.add_points(self.edgeSelection, size=size, face_color=face_color, n_dimensional=False)
			self.selectionLayer.name = 'Edge Selection'
			#print('nodeLayer.data:', nodeLayer.data)
		'''
		#
		# shapes layer (for drawing lines)
		line1 = np.array([[11, 13], [111, 113]])
		line2 = np.array([[200, 200], [400, 300]])
		lines = [line1, line2]
		self.shapeLayer = self.viewer.add_shapes(lines,
			shape_type='line',
			edge_width = 3+2,
			edge_color = 'coral',
			face_color = 'royalblue')
		self.shapeLayer.mode = 'direct' #'select'

		@self.shapeLayer.mouse_move_callbacks.append
		def shape_mouse_move_callback(layer, event):
			#print('shape_mouse_move_callback() event.type:', event.type)
			self.myMouseMove_Shape(layer, event)

		# this decorator cannot point to member function directly because it needs yield
		# put inline function with yield right after decorator
		# and then call member functions from within
		@self.shapeLayer.mouse_drag_callbacks.append
		def shape_mouse_drag_callback(layer, event):
			#print('shape_mouse_drag_callback() event.type:', event.type, 'event.pos:', event.pos, '')
			self.lineShapeChange_callback(layer, event)
			yield

			while event.type == 'mouse_move':
				self.lineShapeChange_callback(layer, event)
				yield
		'''

	def selectEdge(self, edgeIdx):
		slabList = self.myStack.slabList.getEdge(edgeIdx)
		x = self.myStack.slabList.x[slabList]
		y = self.myStack.slabList.y[slabList]
		z = self.myStack.slabList.z[slabList]
		d = self.myStack.slabList.d[slabList]
		edgeSelection = np.column_stack((x,y,z,))
		size = d / 300
		face_color = 'yellow'
		#nodeLayer = self.viewer.add_points(self.edgeSelection, size=size, face_color=face_color, n_dimensional=False)
		#nodeLayer.name = 'Edge Selection'
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
