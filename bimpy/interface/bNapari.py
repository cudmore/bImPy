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
		# try and plot a 2d image
		mu = 100
		sigma = 50
		self.lineProfileImage = np.random.normal(mu, sigma, (100,100))
		#tmp_np = np.ndarray([100,100])
		print('self.lineProfileImage.shape:', self.lineProfileImage.shape)
		#pg.image(tmp_np)
		#self.pgPlots[1].addItem(tmp_np)
		#myImg = pg.ImageView(view=self.pgPlots[1])
		#myImg.setImage(tmp_np)
		#myImg.show()

		pgNum = 2
		self.pgWin = pg.GraphicsWindow(title="Stokes profiles") # creates a window
		self.pgPlots = [None] * pgNum
		self.curve_stokes = [None] * pgNum
		self.lambda_pos = [None] * pgNum
		self.pgPlots[0] = self.pgWin.addPlot(title="Stokes I", row=0, col=0)
		#self.pgPlots[1] = self.pgWin.addPlot(title="Stokes I", row=1, col=0)
		self.pgPlots[1] = self.pgWin.addViewBox(row=1, col=0)

		self.img = pg.ImageItem(border='w')
		self.img.setImage(self.lineProfileImage)

		self.pgPlots[1].addItem(self.img)

		'''
		for i in range(pgNum):
			self.lambda_pos[i] = pg.InfiniteLine(pos=0, angle=90)
			self.pgPlots[i].addItem(self.lambda_pos[i])
		for i in range(pgNum):
			self.curve_stokes[i] = self.pgPlots[i].plot()
			self.curve_stokes[i].setShadowPen(pg.mkPen((255,255,255), width=2, cosmetic=True))
		'''
		self.lambda_pos[1] = pg.InfiniteLine(pos=0, angle=90)
		self.pgPlots[1].addItem(self.lambda_pos[1])
		'''
		for i in range(pgNum):
			self.curve_stokes[i] = self.pgPlots[i].plot()
			self.curve_stokes[i].setShadowPen(pg.mkPen((255,255,255), width=2, cosmetic=True))
		'''
		self.curve_stokes[0] = self.pgPlots[0].plot()
		self.curve_stokes[0].setShadowPen(pg.mkPen((255,255,255), width=2, cosmetic=True))


		#
		# napari
		colormap = 'green'
		scale = (1,1,1) #(1,0.2,0.2)
		title = filename

		self.viewer = napari.Viewer(title=title)

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

		x = self.myStack.slabList.x
		y = self.myStack.slabList.y
		z = self.myStack.slabList.z

		# this has nans which I assume will lead to some crashes ...
		points = np.column_stack((z,x,y,))
		#points = points[~np.isnan(points).any(axis=1)] # remove nan rows
		print('   points.shape:', points.shape)

		size = 10

		#points = np.array([[100, 100], [200, 200], [333, 111]])
		#size = np.array([10, 20, 20])

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

		# remember, (size, face_color), etc. Can be a sclar to set one value
		#pointLayer = self.myNapari.add_points(points, size=size, face_color=face_color, n_dimensional=False)
		pointLayer = self.viewer.add_points(points, size=size, face_color=face_color, n_dimensional=False)
		pointLayer.name = 'All Points'

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
		# shapes layer
		line1 = np.array([[11, 13], [111, 113]])
		line2 = np.array([[200, 200], [400, 300]])
		lines = [line1, line2]
		self.shapeLayer = self.viewer.add_shapes(lines,
			shape_type='line',
			edge_width = 5,
			edge_color = 'coral',
			face_color = 'royalblue')
		self.shapeLayer.mode = 'select'
		self.shapeLayer.events.set_data.connect(self.lineShapeChange_callback)
		'''
		print('type(self.shapeLayer.data):', type(self.shapeLayer.data))
		print('self.shapeLayer.data:', self.shapeLayer.data)
		'''

		# see:
		# https://github.com/napari/napari/pull/544# make a callback for all mouse moves

		'''
		@self.shapeLayer.mouse_move_callbacks.append
		def shape_mouse_move_callback(viewer, event):
			self.myMouseMove_Shape(viewer, event)
		'''

		'''@self.shapeLayer.mouse_drag_callbacks.append
		def shape_mouse_drag_callback(viewer, event):
			self.myMouseDrag_Shape(viewer, event)
		'''

		# callback for user changing slices
		#self.myNapari.dims.events.axis.connect(self.my_update_slider)

		# make a selection layer

	def my_update_slider(self, event):
		"""Respond to user changing slice/image slider"""
		print('my_update_slider() event:', event)
		if (event.axis == 0):
			self.sliceNum = self.viewer.dims.indices[0]
			self.plot_pg_slice(self.sliceNum)
			#self.plot_pg(None, ind_lambda)
			self.updateLines()

	def plot_pg(self, oneProfile): #, ind_lambda):

		if (oneProfile is not None):
			for i in range(2):
				if (i == 0):
					self.curve_stokes[i].setData(oneProfile)
				#else:
				#	self.curve_stokes[i].setData(stokes[i,:] / stokes[0,0])
		'''
		for i in range(2):
			self.lambda_pos[i].setValue(ind_lambda)
		'''

	def plot_pg_slice(self, sliceNum):
		"""Set vertical line on pg plots to slice number"""
		'''
		for i in range(2):
			self.lambda_pos[i].setValue(sliceNum)
		'''
		self.lambda_pos[1].setValue(sliceNum)

	def updateLines(self):
		""" update pg plots with line intensity profile"""
		for data in self.shapeLayer.data:
			src = data[0]
			dst = data[1]
			lineProfile = self.myStack.analysis.lineProfile(self.sliceNum, src, dst, linewidth=1)
			#print('lineProfile:', lineProfile)
			self.plot_pg(lineProfile)

			# todo: This works put is too slow, add button to calculate !!!
			'''
			# stackLineProfile(self, slice, src, dst, linewidth=1):
			self.lineProfileImage = self.myStack.analysis.stackLineProfile(src, dst)
			self.img.setImage(self.lineProfileImage)
			'''

	def lineShapeChange_callback(self, event):
		print('=== lineShapeChange_callback()')
		print('   type(event)', type(event))
		print('   event.source:', event.source)
		print('   event.type:', event.type)

		print('   self.shapeLayer.selected_data:', self.shapeLayer.selected_data)

		# self.shapeLayer.selected_data is a list of int tell us index into self.shapeLayer.data of all selected shapes
		selected_data = self.shapeLayer.selected_data
		if len(selected_data) > 0:
			index = selected_data[0] # just the first selected shape
			print('   shape at index', index, 'in self.shapeLayer.data changed and is now:', self.shapeLayer.data[index])
			# line profile analysis !
			slice = 0
			src = self.shapeLayer.data[index][0]
			dst = self.shapeLayer.data[index][1]
			lineProfile = self.myStack.analysis.lineProfile(slice, src, dst, linewidth=1)
			#print('lineProfile:', lineProfile)
			# this works
			#self.plot_pg(lineProfile)
			self.updateLines()

	'''def myMouseDrag_Shape(self, viewer, event):
		"""
		event is type vispy.app.canvas.MouseEvent
		see: http://api.vispy.org/en/v0.1.0-0/event.html
		"""

		ind_x, ind_y = np.round(viewer.coordinates).astype('int')
		print('******',
			'myMouseDrag_Shape() viewer:', viewer,
			'event:', event, type(event), 'type:', event.type, 'button', event.button)
		print('   x:', ind_x, 'y:', ind_y)

		#"dragging"
		if event.type == 'mouse_press':
			yield

		# on move
		#while event.type == 'mouse_move':
		while event.type == 'mouse_move':
			print(event.pos)
			yield

		# on release
		print('goodbye world ;(')
	'''

	'''
	def myMouseMove_Action(self, viewer, event):
		print('myMouseMove_Action() viewer:', viewer, 'event:', event)
		ind_z, ind_x, ind_y = np.round(viewer.coordinates).astype('int')
		print('   myMouseMove_Action()', ind_z, ind_x, ind_y)
	'''

'''
class myShapes(napari.xxx):
	def __init__(self):
		super.__init__(myShapes)
'''

if __name__ == '__main__':
	#from PyQt5 import QtGui, QtCore, QtWidgets
	path = '/Users/cudmore/box/data/nathan/vesselucida/20191017__0001.tif'
	app = QtWidgets.QApplication(sys.argv)
	mn = bNapari(path)
	sys.exit(app.exec_())
