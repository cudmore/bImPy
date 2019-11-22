# Robert Cudmore
# 20191115

import os, time, json
import numpy as np
import h5py

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

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

		self.analysis = bimpy.bAnalysis2(self.imageData) # self.imageData is a property

		# make an empty shape layer
		self.shapeLayer = self.napariViewer.add_shapes(
			name=self.myImageLayer.name + '_shapes',
		)

		#
		# add shapes
		self.lineProfileImage = None
		self.FWHM = None

		'''
		'''
		'''
		# create default shapes
		line1 = np.array([[11, 13], [111, 113]])
		line2 = np.array([[200, 200], [400, 300]])
		lines = [line1, line2]
		self.shapeLayer = self.napariViewer.add_shapes(
			lines,
			name=self.myImageLayer.name + '_shapes',
			shape_type='line',
			edge_width = 3,
			edge_color = 'coral',
			face_color = 'royalblue')
		self.shapeLayer.mode = 'direct' #'select'
		'''
		'''
		'''

		# load existing shapes
		#self.save()
		#self.load()

		'''
		self.events.add(
		    mode=Event,
		    edge_width=Event,
		    edge_color=Event,
		    face_color=Event,
		    highlight=Event,
		)
		'''
		self.shapeLayer.events.mode.connect(self.layerChangeEvent)
		self.shapeLayer.events.edge_width.connect(self.layerChangeEvent)
		#self.shapeLayer.events.removed.connect(self.layerChangeEvent)

		# callback for user changing slices
		self.napariViewer.dims.events.axis.connect(self.my_update_slider)

		# keyboard 'u' will update selected shape through all slices/images
		@self.napariViewer.bind_key('u')
		def user_keyboard_u(viewer):
			print('=== user_keyboard_u')
			shapeType, data = self._getSelectedShape()
			if shapeType == 'line':
				src = data[0]
				dst = data[1]
				self.updateStackLineProfile(src, dst)
			if shapeType in ['rectangle', 'polygon']:
				self.updateStackPolygon(data)

		'''
		found delete_shape() and napari.layers.shapes.shapeList.remove()
		in napari.layers.shapes.
		def remove_selected(self):
        	"""Remove any selected shapes."""
        	to_remove = sorted(self.selected_data, reverse=True)
        	for index in to_remove:
            	self._data_view.remove(index)
        	self.selected_data = []
        	self._finish_drawing()
		'''
		# keyboard 'n' will spawn a new shape analysis plugin?
		'''
		@self.napariViewer.bind_key('n')
		def user_keyboar_n(viewer):
			print('=== user_keyboard_n')
			# viewer.active_layer
			#print('viewer.layers:', viewer.layers)
			for layer in self.napariViewer.layers:
				print('type(layer).__name__:', type(layer).__name__)
				print('   layer.name:', layer.name)
				print('   layer.selected:', layer.selected)
		'''

		@self.napariViewer.bind_key('l')
		def user_keyboar_l(viewer):
			print('=== user_keyboard_l')
			self.load()

		@self.napariViewer.bind_key('s')
		def user_keyboar_s(viewer):
			print('=== user_keyboard_s')
			self.save()

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

		self.buildPyQtGraphInterface()

	def save(self):
		"""
		todo: save each of (shape_types, edge_colors, etc) as a group attrs rather than a dict
		"""
		print('=== bShapeAnalysisWidget.save()')
		#print(type(self.shapeLayer.data[0]))
		shapeList = []
		for idx, shapeType in enumerate(self.shapeLayer.shape_types):
			print('   idx:', idx, shapeType)
			shapeDict = {
				#'data:', self.shapeLayer.data[idx],
				'shape_types': self.shapeLayer.shape_types[idx],
				'edge_colors': self.shapeLayer.edge_colors[idx],
				'face_colors': self.shapeLayer.face_colors[idx],
				'edge_widths': self.shapeLayer.edge_widths[idx],
				'opacities': self.shapeLayer.opacities[idx],
				#z_indices for polygon is int64 and can not be with json.dumps ???
				#'z_indices': int(self.shapeLayer.z_indices[idx]),
			}
			print('   shapeDict:', shapeDict)
			shapeList.append(shapeDict)

			# check the types
			# z_indices is int64 and is not serializable ???
			for k, v in shapeDict.items():
				print('***', k, v, type(v))

		print('writing file')
		with h5py.File("test.h5", "w") as f:
			for idx, shape in enumerate(shapeList):
				print('   shape:', shape)
				# each shape will have a group
				group = f.create_group('shape' + str(idx))
				# each shape group will have a shape dict with all parameters to draw ()
				shapeDict_json = json.dumps(shape)
				group.attrs['shapeDict'] = shapeDict_json
				# each shape group will have 'data' with coordinates of polygon
				shapeData = self.shapeLayer.data[idx]
				group.create_dataset("data", data=shapeData)

				# each group will have analysis
				# todo: do this later

		# debugging
		#self.load()

	def load(self):
		print('=== bShapeAnalysisWidget.load()')
		shape_type = []
		edge_width = []
		edge_color = []
		face_color = []
		with h5py.File("test.h5", "r") as f:
			# iterate through h5py groups (shapes)
			shapeList = []
			linesList = []
			for name in f:
				print('name:', name)
				json_str = f[name].attrs['shapeDict']
				json_dict = json.loads(json_str) # convert from string to dict
				'''
				print('   json_dict:', json_dict)
				print('   type(json_dict):', type(json_dict))
				print('   json_dict["edge_colors"]', json_dict['edge_colors'])
				'''
				# load the coordinates of polygon
				data = f[name + '/data'][()] # the wierd [()] converts it to numpy ndarray
				'''
				print('   data:', data)
				print('   type(data)', type(data))
				'''
				linesList.append(data)

				shapeDict = json_dict
				shapeDict['data'] = data

				shape_type.append(shapeDict['shape_types'])
				edge_width.append(shapeDict['edge_widths'])
				edge_color.append(shapeDict['edge_colors'])
				face_color.append(shapeDict['face_colors'])

				print("type(shapeDict['edge_colors'])", type(shapeDict['edge_colors']))

				shapeList.append(shapeDict)

		print('linesList:', linesList)
		print('edge_color:', edge_color)
		print('type(edge_color[0]):', type(edge_color[0]))

		# create a shape from what we loaded
		print('\n=== ===  appending loaded shapes to shapes layer')
		#add a shape to existing shape layer
		# this does not work because vispy is interpreting (edge_color, face_color) as a list
		# and thus expecting rgb (or rgba?) and not string like 'black'
		'''
		self.shapeLayer.add(
			linesList,
			shape_type = shape_type,
			edge_width = edge_width,
			edge_color = edge_color,
			face_color = face_color
			)
		'''
		self.shapeLayer.add(
			linesList,
			shape_type = shape_type,
			edge_width = edge_width,
			)

		#self.shapeLayer.edge_color = edge_color

		'''
		for tmp_edge_color in self.shapeLayer.edge_color:
			print('tmp_edge_color:', tmp_edge_color)
		'''

		"""
		for idx, shape in enumerate(shapeList):
			'''
			print('shape:', shape)
			print('shape.keys()', shape.keys())
			print('type(shape["shape_types"])', type(shape['shape_types']))
			'''
			self.shapeLayer = self.napariViewer.add_shapes(
				# not sure what this is??
				# was 'lines,
				linesList[idx],
				#name=self.myImageLayer.name + '_shapes',
				shape_type = shape['shape_types'],
				edge_width = shape['edge_widths'],
				# todo: finish this
				#edge_width = shape['edge_widths'],
				edge_color = shape['edge_colors'],
				face_color = shape['face_colors'],
				#edge_color = 'coral',
				#face_color = 'royalblue'
			)
		"""

	def buildPyQtGraphInterface(self):
		#
		# pyqt graph plots
		self.pgWin = pg.GraphicsWindow(title="Shape Analysis Plugin") # creates a window
		#self.pgWin = pg.QGraphicsLayoutWidget(title="Shape Analysis Plugin") # creates a window

		pgRow = 0 # row of pyqtgraph

		# keep a list of vertical lines to indicate slice in each plot
		self.sliceLinesList = []

		#
		# (1) line intensity profile for one slice
		self.lineIntensityPlotItem = self.pgWin.addPlot(title="Line Intensity Profile", row=pgRow, col=0)
		self.lineIntensityPlotItem.setLabel('left', 'Intensity', units='')
		self.lineIntensityPlotItem.setLabel('bottom', 'Line Profile', units='')
		self.lineProfilePlot = self.lineIntensityPlotItem.plot(name='lineIntensityProfile')
		self.lineProfilePlot.setShadowPen(pg.mkPen((255,255,255), width=2, cosmetic=True))
		# fit
		x = y = []
		self.fitPlot = self.lineIntensityPlotItem.plot(x, y, pen=pg.mkPen('r', width=3), name='fit')
		self.fitPlot2 = self.lineIntensityPlotItem.plot(x, y, pen=pg.mkPen('b', symbol='.', symbolSize=10, width=5), name='fitPoints')

		pgRow += 1

		#
		# (2) diameter for each slice
		self.analysisPlotItem = self.pgWin.addPlot(title='', row=pgRow, col=0)
		self.analysisPlotItem.setLabel('left', 'Diameter', units='')
		#self.analysisPlotItem.setLabel('bottom', 'Slices') #, units='s')
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
		self.polygonPlotItem = self.pgWin.addPlot(title='', row=pgRow, col=0)
		self.polygonPlotItem.setLabel('left', 'Mean Polygon Intensity') #, units='A)
		self.polygonPlotItem.setLabel('bottom', 'Slices') #, units='s')
		# vertical line showing slice number selection in napari viewer
		#self.verticalSliceLine3 = pg.InfiniteLine(pos=0, angle=90)
		#self.polygonPlotItem.addItem(self.verticalSliceLine3)
		sliceLine = pg.InfiniteLine(pos=0, angle=90)
		self.sliceLinesList.append(sliceLine)
		self.polygonPlotItem.addItem(sliceLine)
		#
		self.analysisPolygon = self.polygonPlotItem.plot(name='polygonintensity')

		# (5) tree view of all shapes
		w = pg.TreeWidget()
		w.setColumnCount(2)
		w.show()
		w.resize(500,500)
		w.setWindowTitle('pyqtgraph example: TreeWidget')

		i1  = QtGui.QTreeWidgetItem(["Item 1"])
		i2  = QtGui.QTreeWidgetItem(["Item 2"])
		i3  = QtGui.QTreeWidgetItem(["Item 3"])
		w.addTopLevelItem(i1)
		w.addTopLevelItem(i2)
		w.addTopLevelItem(i3)

		# does not work
		#self.pgWin.addItems(w)

	def layerChangeEvent(self, event):
		print(time.time(), 'layerChangeEvent() event:', event)

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
		print('updateStackLineProfile() src:', src, 'dst:', dst)
		#x, self.lineProfileImage, self.FWHM = self.myStack.analysis.stackLineProfile(src, dst)
		x, self.lineProfileImage, self.FWHM = self.analysis.stackLineProfile(src, dst)

		# why return ?
		#return self.lineProfileImage

		#
		# update plots with new results
		self.img.setImage(self.lineProfileImage)

		#print('todo: this is an error FIX IT !!!!!!!!!!!!!!!!!!!!!!!!!!!')
		#print('bShapeAnalysisWidget.updateStackLineProfile self.FWHM:', self.FWHM)

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
		print('bShapeAnalysisWidget.updateLines() sliceNum:', sliceNum, 'src:', src, 'dst:', dst)
		#x, lineProfile, yFit, fwhm, leftIdx, rightIdx = self.myStack.analysis.lineProfile(sliceNum, src, dst, linewidth=1, doFit=True)
		# this can fail
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