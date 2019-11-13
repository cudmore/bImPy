# Robert Cudmore
# 20191108

import os, sys, math, time
import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

import bimpy
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
	def __init__(self, path):

		print('bNapari() path:', path)

		filename = os.path.basename(path)

		self.myStack = bimpy.bStack(path)

		print('   self.myStack.stack.shape:', self.myStack.stack.shape)

		self.sliceNum = 0

		#
		# pyqt graph plots
		pgNum = 2
		self.pgWin = pg.GraphicsWindow(title="Stokes profiles") # creates a window
		self.pgPlots = [None] * pgNum
		self.curve_stokes = [None] * pgNum
		self.lambda_pos = [None] * pgNum
		# line intensity for one slice
		self.pgPlots[0] = self.pgWin.addPlot(title="Line Intensity Profile", row=0, col=0)
		# line intensity for entire stack (updated with xxx)
		self.pgPlots[1] = self.pgWin.addViewBox(row=1, col=0)

		self.img = pg.ImageItem()
		self.pgPlots[1].addItem(self.img)

		self.lambda_pos[1] = pg.InfiniteLine(pos=0, angle=90)
		self.pgPlots[1].addItem(self.lambda_pos[1])

		self.curve_stokes[0] = self.pgPlots[0].plot()
		self.curve_stokes[0].setShadowPen(pg.mkPen((255,255,255), width=2, cosmetic=True))

		#
		# napari
		colormap = 'green'
		scale = (1,1,1) #(1,0.2,0.2)
		title = filename

		self.viewer = napari.Viewer(title=title)

		@self.viewer.bind_key('u')
		def updateStackLineProfile(viewer):
			(src, dst) = self._getSelectedLine()
			if src is not None:
				self.lineProfileImage = self.myStack.analysis.stackLineProfile(src, dst)
				print('   got line profile')
				self.img.setImage(self.lineProfileImage)

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

			# this has nans which I assume will lead to some crashes ...
			points = np.column_stack((z,x,y,))
			print('   points.shape:', points.shape)

			# all points will be one size
			size = 10

			# this allows us to color different points with different colors
			#use this to label: ('nodes')
			# we can also change the size of different points
			slabSize = 5
			nodeSize = 9

			size = []
			face_color = []
			foundNan = False
			for i, idx in enumerate(range(len(x))):
				if foundNan:
					size.append(nodeSize)
					face_color.append('red')
					foundNan = False
				else:
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
			size = 10
			face_color = 'yellow'
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
			face_color = 'magenta'
			nodePoints = np.column_stack((z,x,y,))
			#nodeLayer = self.myNapari.add_points(nodePoints, size=size, face_color=face_color, n_dimensional=False)
			nodeLayer = self.viewer.add_points(nodePoints, size=size, face_color=face_color, n_dimensional=False)
			nodeLayer.name = 'Dead Ends'

		#
		# make a selection layer

		#
		# shapes layer (for drawing lines)
		line1 = np.array([[11, 13], [111, 113]])
		line2 = np.array([[200, 200], [400, 300]])
		lines = [line1, line2]
		self.shapeLayer = self.viewer.add_shapes(lines,
			shape_type='line',
			edge_width = 3,
			edge_color = 'coral',
			face_color = 'royalblue')
		self.shapeLayer.mode = 'direct' #'select'

		@self.shapeLayer.mouse_move_callbacks.append
		def shape_mouse_move_callback(viewer, event):
			self.myMouseMove_Shape(viewer, event)

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
			self.plot_pg_slice(self.sliceNum)
			# using new slice, update the intensity of a line
			self.updateLines()

	def plot_pg(self, oneProfile): #, ind_lambda):
		"""
		Update the pyqt graph (top one) with a new line profile

		Parameters:
			oneProfile: ndarray of line intensity
		"""
		if (oneProfile is not None):
			# todo: fix this
			self.curve_stokes[0].setData(oneProfile)

	def plot_pg_slice(self, sliceNum):
		"""
		Set vertical line on pg plots to slice number

		Slice is indicated by a vertical bar
		"""
		self.lambda_pos[1].setValue(sliceNum)

	def _getSelectedLine(self):
		"""
		return (src, dst), the coordinates of the selected line
		"""
		# self.shapeLayer.selected_data is a list of int tell us index into self.shapeLayer.data of all selected shapes
		selected_data = self.shapeLayer.selected_data
		if len(selected_data) > 0:
			index = selected_data[0] # just the first selected shape
			src = self.shapeLayer.data[index][0]
			dst = self.shapeLayer.data[index][1]
			return (src, dst)
		else:
			return (None, None)

	def updateLines(self):
		"""
		update pg plots with line intensity profile

		get one selected line from list(self.shapeLayer.selected_data)
		"""
		# loop through all lines?
		#for data in self.shapeLayer.data:
		(src, dst) = self._getSelectedLine()
		if src is not None:
			lineProfile = self.myStack.analysis.lineProfile(self.sliceNum, src, dst, linewidth=1)
			#print('lineProfile:', lineProfile)
			self.plot_pg(lineProfile)

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
	path = '/Users/cudmore/box/data/nathan/vesselucida/20191017__0001.tif'
	# this file s too big, 1.2 GB, keep slices 4166, 9416
	path = '/Users/cudmore/box/data/bImpy-Data/high-k-video/HighK-aligned-8bit-short.tif'
	app = QtWidgets.QApplication(sys.argv)
	mn = bNapari(path)
	sys.exit(app.exec_())
