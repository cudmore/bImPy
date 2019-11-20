# Robert Cudmore
# 20191115

import os
import numpy as np
import pyqtgraph as pg

import napari

import bimpy

class bShapeAnalysisWidget:
	"""
	handle interface of one shape roi at a time
	"""
	#def __init__(self, napariViewer, path=None, myStack=None):
	def __init__(self, napariViewer, imageLayer=None):
		"""
		napariViewer: existing napari viewer
		imageLayer: napari image layer to use as image
			e.g. imageLayer.data

		Assuming:
			imageLayer.data is (slices, rows, col)
		"""
		self.sliceNum = 0

		self.napariViewer = napariViewer
		self.myImageLayer = imageLayer

		self.analysis = bimpy.bAnalysis2(self.imageData)

		#
		# add shapes
		self.lineProfileImage = None
		self.FWHM = None

		line1 = np.array([[11, 13], [111, 113]])
		line2 = np.array([[200, 200], [400, 300]])
		lines = [line1, line2]
		self.shapeLayer = self.napariViewer.add_shapes(lines,
			shape_type='line',
			edge_width = 3+2,
			edge_color = 'coral',
			face_color = 'royalblue')
		self.shapeLayer.mode = 'direct' #'select'

		# callback for user changing slices
		self.napariViewer.dims.events.axis.connect(self.my_update_slider)

		# keyboard 'u' will update selected shape through all slices/images
		@self.napariViewer.bind_key('u')
		def updateStackLineProfile(viewer):
			shapeType, data = self._getSelectedShape()
			if shapeType == 'line':
				src = data[0]
				dst = data[1]
				self.updateStackLineProfile(src, dst)
			if shapeType in ['rectangle', 'polygon']:
				self.updateStackPolygon(data)

		#
		# pyqt graph plots
		self.pgWin = pg.GraphicsWindow(title="Shape Analysis Plugin") # creates a window

		pgRow = 0 # row of pyqtgraph

		# keep a list of vertical lines to indicate slice in each plot
		self.sliceLinesList = []

		#
		# (1) line intensity profile for one slice
		self.lineIntensityPlotItem = self.pgWin.addPlot(title="Line Intensity Profile", row=pgRow, col=0)
		self.lineProfilePlot = self.lineIntensityPlotItem.plot(name='lineIntensityProfile')
		self.lineProfilePlot.setShadowPen(pg.mkPen((255,255,255), width=2, cosmetic=True))
		# fit
		x = y = []
		self.fitPlot = self.lineIntensityPlotItem.plot(x, y, pen=pg.mkPen('r', width=3), name='fit')
		self.fitPlot2 = self.lineIntensityPlotItem.plot(x, y, pen=pg.mkPen('b', symbol='.', symbolSize=10, width=5), name='fitPoints')

		pgRow += 1

		#
		# (2) diameter for each slice
		self.analysisPlotItem = self.pgWin.addPlot(title="Diameter", row=pgRow, col=0)
		self.analysisPlotItem.setLabel('left', 'Diameter', units='A')
		self.analysisPlotItem.setLabel('bottom', 'Slices') #, units='s')
		# vertical line showing slice number selection in napari viewer
		#self.sliceLineDiameter = pg.InfiniteLine(pos=0, angle=90)
		sliceLine = pg.InfiniteLine(pos=0, angle=90)
		self.sliceLinesList.append(sliceLine)
		self.analysisPlotItem.addItem(sliceLine)
		#
		self.analysisDiameter = self.analysisPlotItem.plot(name='lineintensitydiameter')

		pgRow += 1

		#
		# (3) image with slices on x, and intensity of each line profile on y
		self.stackLineIntensityImage = self.pgWin.addViewBox(row=pgRow, col=0)
		# setLabel does not work for view box?
		#self.stackLineIntensityImage.setLabel('left', 'Line Intensity Profile') #, units='A')
		#self.stackLineIntensityImage.setLabel('bottom', 'Slices') #, units='s')

		self.img = pg.ImageItem()
		self.stackLineIntensityImage.addItem(self.img)

		# add a vertical line for current slice (over image)
		#self.sliceLineProfileImage = pg.InfiniteLine(pos=0, angle=90)
		#self.stackLineIntensityImage.addItem(self.sliceLineProfileImage)
		sliceLine = pg.InfiniteLine(pos=0, angle=90)
		self.sliceLinesList.append(sliceLine)
		self.stackLineIntensityImage.addItem(sliceLine)

		pgRow += 1

		# (4) intensity of polygon for each slice
		self.polygonPlotItem = self.pgWin.addPlot(title="Diameter", row=pgRow, col=0)
		self.polygonPlotItem.setLabel('left', 'Intensity') #, units='A)
		self.polygonPlotItem.setLabel('bottom', 'Slices') #, units='s')
		# vertical line showing slice number selection in napari viewer
		#self.verticalSliceLine3 = pg.InfiniteLine(pos=0, angle=90)
		#self.polygonPlotItem.addItem(self.verticalSliceLine3)
		sliceLine = pg.InfiniteLine(pos=0, angle=90)
		self.sliceLinesList.append(sliceLine)
		self.polygonPlotItem.addItem(sliceLine)
		#
		self.analysisPolygon = self.polygonPlotItem.plot(name='polygonintensity')

		#
		#
		#@self.shapeLayer.mouse_move_callbacks.append
		@self.shapeLayer.mouse_drag_callbacks.append
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

	@property
	def imageData(self):
		return self.myImageLayer.data

	def myMouseMove_Shape(self, layer, event):
		"""
		Detect mouse move in shape layer (not called when mouse is down).

		event is type vispy.app.canvas.MouseEvent
		see: http://api.vispy.org/en/v0.1.0-0/event.html
		"""
		print('myMouseMove_Shape()', layer, event.type)
		# check the shape layer for a new shape
		# this works !!!
		for shapeType in self.shapeLayer.shape_types:
			print('   shapeType:', shapeType)

	def lineShapeChange_callback(self, layer, event):
		"""
		Callback for when user clicks+drags to resize a line shape.

		Responding to @self.shapeLayer.mouse_drag_callbacks
		"""

		"""
		update pg plots with line intensity profile

		get one selected line from list(self.shapeLayer.selected_data)
		"""
		# loop through all lines?
		#for data in self.shapeLayer.data:
		shapeType, data = self._getSelectedShape()
		if shapeType == 'line':
			src = data[0]
			dst = data[1]
			self.updateLines(self.sliceNum, src, dst)
		if shapeType in ['rectangle', 'polygon']:
			self.updatePolygon(self.sliceNum, data)

	def _getSelectedShape(self):
		"""
		return the selected shape with a tuple (shapeType, data)
			shapeType: ('line', 'polygon')
			data: the data from a shape layer, generally the coordinates of a shape
				- for a line it is a list of two points
				- for a polygon it is a list of N vertex points
		"""
		# selected_data is a list of int with the index into self.shapeLayer.data of all selected shapes
		selectedDataList = self.shapeLayer.selected_data
		#print('selectedDataList:', selectedDataList)
		if len(selectedDataList) > 0:
			index = selectedDataList[0] # just the first selected shape
			shapeType = self.shapeLayer.shape_types[index]
			'''
			print('shapeType:', shapeType) #('line', 'rectangle', 'polygon')
			print('   self.shapeLayer.data[index]:', self.shapeLayer.data[index])
			'''
			return shapeType, self.shapeLayer.data[index]
		else:
			return (None, None)

	def my_update_slider(self, event):
		"""
		Respond to user changing slice/image slider
		"""
		#print('my_update_slider() event:', event)
		if (event.axis == 0):
			# todo: not sure if this if foolproof
			self.sliceNum = self.napariViewer.dims.indices[0]

			self.updateVerticalSliceLines(self.sliceNum)

			# todo: this does not feal right ... fix this !!!
			shapeType, data = self._getSelectedShape()
			if shapeType == 'line':
				src = data[0]
				dst = data[1]
				self.updateLines(self.sliceNum, src, dst)
			if shapeType in ['rectangle', 'polygon']:
				self.updatePolygon(self.sliceNum, data)

	def updateStackPolygon(self, data):
		"""
		data is a list of points specifying vertices of a polygon
		a rectangle is just a polygon with 4 evenly spaces vertices
		"""
		print('bShapeAnalysisWidget.updateStackPolygon() data:', data)
		#theMin, theMax, theMean = self.myStack.analysis.stackPolygonAnalysis(data)
		theMin, theMax, theMean = self.analysis.stackPolygonAnalysis(data)

		xPlot = np.asarray([slice for slice in range(len(theMean))])
		#self.analysisDiameter.setData(xPlot, theMean, connect='finite')
		self.analysisPolygon.setData(xPlot, theMean, connect='finite')

	def updateStackLineProfile(self, src, dst):
		"""
		generate a line profile for each image in a stack/timeseries

		src: source point
		dst: destination point
		"""
		#x, self.lineProfileImage, self.FWHM = self.myStack.analysis.stackLineProfile(src, dst)
		x, self.lineProfileImage, self.FWHM = self.analysis.stackLineProfile(src, dst)

		# why return ?
		#return self.lineProfileImage

		#
		# update plots with new results
		self.img.setImage(self.lineProfileImage)

		print('todo: this is an error FIX IT !!!!!!!!!!!!!!!!!!!!!!!!!!!')
		print('bShapeAnalysisWidget.updateStackLineProfile self.FWHM:', self.FWHM)

		#
		# x will be 2d, x points for each line profile in a stack
		# here we are plotting only 1d so reduce x
		'''
		print('   x.shape:', x.shape)
		print('   self.FWHM.shape:', self.FWHM.shape)
		print('   x[:,0]:', x[:,0])
		print('   self.FWHM:', self.FWHM)
		'''
		#self.analysisDiameter.setData(x[:,0], self.FWHM, connect='finite')
		xPlot = np.asarray([slice for slice in range(len(self.FWHM))])
		self.analysisDiameter.setData(xPlot, self.FWHM, connect='finite')

	def updateVerticalSliceLines(self, sliceNum):
		"""
		Set vertical line indicating current slice
		"""
		for line in self.sliceLinesList:
			line.setValue(sliceNum)

	def updatePolygon(self, sliceNum, data):
		"""
		data is a list of vertex points
		"""
		print('bShapeAnalysisWidget.updatePolygon() data:', data)
		#theMin, theMax, theMean = self.myStack.analysis.polygonAnalysis(sliceNum, data)
		theMin, theMax, theMean = self.analysis.polygonAnalysis(sliceNum, data)
		print('   slice:', sliceNum, 'theMin:', theMin, 'theMax:', theMax, 'theMean:', theMean)

	def updateLines(self, sliceNum, src, dst):
		"""
		"""
		#x, lineProfile, yFit, fwhm, leftIdx, rightIdx = self.myStack.analysis.lineProfile(sliceNum, src, dst, linewidth=1, doFit=True)
		x, lineProfile, yFit, fwhm, leftIdx, rightIdx = self.analysis.lineProfile(sliceNum, src, dst, linewidth=1, doFit=True)
		#x = [a for a in range(len(lineProfile))]
		#yFit, fwhm, leftIdx, rightIdx = self.myStack.analysis.fitGaussian(x, lineProfile)

		self.updateLineIntensityPlot(x, lineProfile, yFit, leftIdx, rightIdx)

	def updateLineIntensityPlot(self, x, oneProfile, fit=None, left_idx=np.nan, right_idx=np.nan): #, ind_lambda):
		"""
		Update the pyqt graph (top one) with a new line profile

		Parameters:
			oneProfile: ndarray of line intensity
		"""
		'''
		print('updateLineIntensityPlot type(left_idx):', left_idx)
		print('updateLineIntensityPlot type(right_idx):', right_idx)
		'''
		if (oneProfile is not None):
			#
			self.lineProfilePlot.setData(x, oneProfile)
		if (fit is not None):
			#
			self.fitPlot.setData(x, fit)
		if (oneProfile is not None and not np.isnan(left_idx) and not np.isnan(right_idx)):
			left_y = oneProfile[left_idx]
			# cludge because left/right threshold detection has different y ...
			#right_y = oneProfile[right_idx]
			right_y = left_y
			xPnt = [left_idx, right_idx]
			yPnt = [left_y, right_y]
			#print('plot_pg() xPnt:', xPnt, 'yPnt:', yPnt)
			self.fitPlot2.setData(xPnt, yPnt)

if __name__ == '__main__':

	with napari.gui_qt():
		# path to a tif file. Assuming it is 3D with dimensions of (slice, rows, cols)
		path = '/Users/cudmore/box/data/bImpy-Data/high-k-video/HighK-aligned-8bit-short.tif'
		filename = os.path.basename(path)
		title = filename
		viewer = napari.Viewer(title=title)

		# add image as layer
		colormap = 'green'
		scale = (1,1,1) #(1,0.2,0.2)
		myImageLayer = viewer.add_image(
			#self.myStack.stack[0,:,:,:],
			path = path,
			colormap=colormap,
			scale=scale)#,
			#title=title)

		# run the plugin
		bShapeAnalysisWidget(viewer, imageLayer=myImageLayer)
