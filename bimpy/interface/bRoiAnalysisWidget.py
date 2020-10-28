# Robert Cudmore
# 20191220

import numpy as np

from qtpy import QtGui, QtSql, QtCore, QtWidgets

import pyqtgraph as pg

class bRoiAnalysisWidget(QtWidgets.QWidget):
	"""
	Display shape anaysis plugin window with 4 plots. 1-3 are for line shapes, 4 is for polygon (rectangle) shapes
		1) Line intensity profile + gaussian fit + heuristic fit.
			This is updated in real time while user drags a line shape
		2) Plot of calculated diameter (y) for each slice/frame in the image
		3) 'Kymograph' image plot of line intensity profile (y) versus each slice/frame in the image
		4) The mean intensity in each polygon/ractangle shape (y) versus each  slice/frame in the image
	"""
	#def __init__(self, shapeLayer):
	def __init__(self, annotationList):
		"""
		annotationList: bAnnotationList
		"""
		super(bRoiAnalysisWidget, self).__init__()

		xPos = 100
		yPos = 100
		width = 900
		height = 900
		self.setGeometry(xPos, yPos, width, height)

		#self.shapeLayer = shapeLayer
		self.annotationList = annotationList
		self.polygonMeanListPlot = []
		self.sliceLinesList = []

		self.initUI()

	def initUI(self):
		""" Initialize the user interface """

		# horizontal layout to hold
		# | vertical layout with qt widgets | vertical layout with pyqtgraph plots |
		self.setWindowTitle('Shape Analysis Widget')

		self.myHBoxLayout = QtWidgets.QHBoxLayout(self)

		# vertical layout with qt widgets
		leftVBoxLayout = QtWidgets.QVBoxLayout(self)
		self.myHBoxLayout.addLayout(leftVBoxLayout)

		leftVBoxLayout.addWidget(QtWidgets.QPushButton('My Button'))
		#todo: derive QTreeView class and make it send/receive events on shape changes
		leftVBoxLayout.addWidget(QtWidgets.QTreeView())

		# vertical layout with pyqtgraph plot (eventually vispy)
		rightVBoxLayout = QtWidgets.QVBoxLayout(self)
		self.myHBoxLayout.addLayout(rightVBoxLayout)

		#
		# 1) line intensity profile (white), gaussuian fit (red) , heuristic fit (blue)
		self.lineIntensityWindow = pg.PlotWidget()
		self.lineIntensityWindow.setLabel('left', 'Intensity', units='')
		self.lineIntensityWindow.setLabel('bottom', 'Line Profile', units='')
		self.lineIntensityPlot = self.lineIntensityWindow.plot([], [], pen=pg.mkPen('w', width=3),
			row=0, col=0)
		self.lineItensityFit1 = self.lineIntensityWindow.plot([], [], pen=pg.mkPen('r', width=3),
			row=0, col=0)
		self.lineItensityFit2 = self.lineIntensityWindow.plot([], [], pen=pg.mkPen('b', symbol='.', symbolSize=10, width=5),
			row=0, col=0)
		rightVBoxLayout.addWidget(self.lineIntensityWindow)

		#
		# (2) diameter for each slice
		self.diameterWindow = pg.PlotWidget()
		self.diameterWindow.setLabel('left', 'Diameter', units='')

		sliceLine = pg.InfiniteLine(pos=0, angle=90)
		self.sliceLinesList.append(sliceLine) # keep a list of vertical slice lines so we can update all at once
		self.diameterWindow.addItem(sliceLine)
		#
		self.diameterPlot = self.diameterWindow.plot(name='lineintensitydiameter')

		rightVBoxLayout.addWidget(self.diameterWindow)

		#
		# (3) kymograph image of line intensity (y) for each slice (x)
		self.kymographWindow = pg.PlotWidget()
		self.kymographWindow.setLabel('left', 'Line Intensity Profile', units='')

		self.img = pg.ImageItem()
		self.kymographWindow.addItem(self.img)

		sliceLine = pg.InfiniteLine(pos=0, angle=90)
		self.sliceLinesList.append(sliceLine) # keep a list of vertical slice lines so we can update all at once
		self.kymographWindow.addItem(sliceLine)

		rightVBoxLayout.addWidget(self.kymographWindow)

		#
		# (4) intensity of polygon for each slice
		self.polygonPlotWidget = pg.PlotWidget()
		self.polygonPlotWidget.setLabel('left', 'Mean Polygon Intensity') #, units='A)
		self.polygonPlotWidget.setLabel('bottom', 'Slices') #, units='s')

		sliceLine = pg.InfiniteLine(pos=0, angle=90)
		self.sliceLinesList.append(sliceLine) # keep a list of vertical slice lines so we can update all at once
		self.polygonPlotWidget.addItem(sliceLine)
		# the selected shapes mean (through all slices)
		self.selectedPolygonMeanPlot = self.polygonPlotWidget.plot(symbolSize=3, name='analysisPolygonMean')

		# all polygon mean across all shapes/rois
		self.polygonMeanListPlot = []

		rightVBoxLayout.addWidget(self.polygonPlotWidget)

		# qt, show the window
		self.show()

	def shape_delete(self, index):
		""" Remove a polygon from the list """
		#type = self.shapeLayer.shape_types[index]
		itemDict = self.annotationList.getItemDict(index)
		type = itemDict['type']
		if type == 'rectROI':
			# we can't use index as it includes all shapes, we need index into rectangle to remove?
			rectangleIndex = self._getRectangleIndex(index)
			print('*** shape_delete() deleting rectangle at shape index', index, 'rectangleIndex', rectangleIndex)

			try:
				# before we delete, clear the plot
				self.polygonMeanListPlot[rectangleIndex].setData([], [], connect='finite')
				# remove the plot
				self.polygonMeanListPlot.pop(rectangleIndex) # remove from self.polygonMeanListPlot

				# clear the white selection
				self.selectedPolygonMeanPlot.setData([], [])
			except (IndexError) as e:
				print('Exception in shape_delete() e:', str(e))

	def updateShapeSelection(self, index):
		"""
		On user selecting a shape
		"""

		#print('myQtGraphWidget.updateShapeSelection() index:', index)
		if index is None:
			return

		#type = self.shapeLayer.shape_types[index]
		itemDict = self.annotationList.getItemDict(index)
		type = itemDict['type']

		metaDataDict = self.annotationList.getMetadataDict(index)

		if type == 'lineROI':
			# line profile

			# diameter plot
			#lineDiameter = self.shapeLayer.metadata[index]['lineDiameter']
			lineDiameter = itemDict['lineWidth']
			xPlot = np.asarray([slice for slice in range(len(lineDiameter))])
			self.diameterPlot.setData(xPlot, lineDiameter, connect='finite')
			# kymograph
			#print('  bRoiAnalysis.updateShapeSelection() ERROR, I have no itemDict["lineKymograph"]')
			# todo: put this back in
			#lineKymograph = self.shapeLayer.metadata[index]['lineKymograph']
			lineKymograph = metaDataDict['lineKymograph']
			self.img.setImage(lineKymograph)

			# cancel any polygon selections
			self.selectedPolygonMeanPlot.setData([], [])
			#self.plotAllPolygon(index)
		elif type == 'rectROI':
			try:
				#polygonMean = self.shapeLayer.metadata[index]['polygonMean']
				polygonMean = metaDataDict['polygonMean']
				#print('  bRoiAnalysis.updateShapeSelection() ERROR, I have no itemDict["polygonMean"]')
				# todo: put this back in
				# normalize to first few points
				tmpMean = np.nanmean(polygonMean[0:10])
				polygonMean = polygonMean / tmpMean * 100
				polygonMean += index * 20

				xPlot = np.asarray([slice for slice in range(len(polygonMean))])

				# the selection
				self.selectedPolygonMeanPlot.setData(xPlot, polygonMean)

				# all other polygons, will become slow when we have lots
				self.plotAllPolygon(index)
			except (IndexError) as e:
				print('exception in updateShapeSelection() e:', str(e))

		else:
			print('updateShapeSelection() unknown type:', type)

	def updateLinePlot(self, x, oneProfile, fit=None, leftIdx=np.nan, rightIdx=np.nan):
		"""
		Update the line intensity profile plot (real time as user drags)

		All parameters represent the current line intensity profile and its analysis
		as the user drags the line around and when slices/images are scrolled

		Parameters:
			x: slices, usually 0..n-1, where n is the number of slices/images
			oneProfile: ndarray of pixel intensity along the line. Number of points gives us length of line
			fit: ndarray containing gaussian fit along the line profile (len is same as oneProfile)
			leftIdx, rightIdx: scalar that gives us x position of a heuristic diameter fit

		Call this with answer from
		x, oneProfile, fit, fwhm, leftIdx, rightIdx = bRoiAnalysis.lineProfile(sliceNum, src, dst, linewidth=1, doFit=True)
		"""
		print('bRoiAnalysisWidget.updateLinePlot()')
		if (oneProfile is not None):
			print('   oneProfile.shape', oneProfile.shape)
			print('   x.shape', x.shape)
			self.lineIntensityPlot.setData(x,oneProfile)
			self.lineIntensityPlot.update()

		if (fit is not None):
			self.lineItensityFit1.setData(x, fit) # gaussian

		if (oneProfile is not None and not np.isnan(leftIdx) and not np.isnan(rightIdx)):
			left_y = oneProfile[leftIdx]
			# cludge because left/right threshold detection has different y ...
			#right_y = oneProfile[rightIdx]
			right_y = left_y
			xPnt = [leftIdx, rightIdx]
			yPnt = [left_y, right_y]
			self.lineItensityFit2.setData(xPnt, yPnt) # heuristic

	#def updateVerticalSliceLines(self, sliceNum):
	def slot_updateSlice(self, signalName, signalValue):
		"""
		Set vertical line indicating current slice/image

		We keep a self.sliceLinesList list of all vertical lines in plots of (diameter, kymograph, and rectangle mean)
		"""
		sliceNum = signalValue
		for line in self.sliceLinesList:
			line.setValue(sliceNum)

	def plotAllPolygon(self, selectedIndex):
		"""
		Plot all analysis for all polygons

		selectedIndex : the currently selected shape
		"""

		#print('bRoiAnalysisWidget.plotAllPolygon() selectedIndex:', selectedIndex)

		# first clear all
		for idx in range(len(self.polygonMeanListPlot)):
			self.polygonMeanListPlot[idx].setData([], [], connect='finite')
		# then replot
		rectangleIdx = 0 # keep track of rectangle number 0, 1, 2, ... to index into self.polygonMeanListPlot
		#for idx, type in enumerate(self.shapeLayer.shape_types):
		for idx in range(self.annotationList.numItems()):
			itemDict = self.annotationList.getAnnotationDict(idx)
			type = itemDict['type']

			metaDataDict = self.annotationList.getMetadataDict(index)

			if type == 'rectangle':
				#print('  bRoiAnalysis.plotAllPolygon() ERROR, I have no itemDict["polygonMean"]')
				#polygonMean = self.shapeLayer.metadata[idx]['polygonMean']
				polygonMean = metaDataDict['polygonMean']
				# todo: put this back in
				xPlot = np.asarray([slice for slice in range(len(polygonMean))])
				#print(idx, 'polygonMean.shape:', polygonMean.shape)
				if len(polygonMean)<1:
					# there is no analysis
					xPlot = []
					polygonMean = []
				else:
					# normalize to first few points
					tmpMean = np.nanmean(polygonMean[0:10])
					polygonMean = polygonMean / tmpMean * 100
					polygonMean += idx * 20

				if len(self.polygonMeanListPlot) < rectangleIdx+1:
					# append a new polygon ...
					self.polygonMeanListPlot.append(self.polygonPlotWidget.plot(pen=(255,0,0), name='polygonMeanListPlot'+str(idx)))
					print('   plotAllPolygon() appended rectangle for shape idx:', idx, rectangleIdx, len(self.polygonMeanListPlot))
				self.polygonMeanListPlot[rectangleIdx].setData(xPlot, polygonMean, connect='finite')

				rectangleIdx += 1

	def _getRectangleIndex(self, shapeIndex):
		"""
		Given the absolute index of a shape, return the index based on number of rectangles

		Parameters:
			shapeIndex: absolute shape index
		"""
		theRectangleIndex = None
		rectangleIdx = 0
		#for idx, shapeType in enumerate(self.shapeLayer.shape_types):
		for idx in range(self.annotationList.numItems()):
			itemDict = self.annotationList.getAnnotationDict(idx)
			type = itemDict['type']
			#print('looking for rectangle at shapeIndex:', shapeIndex, 'idx:', idx, 'shapeType:', shapeType)
			if type == 'rectROI':
				if idx == shapeIndex:
					theRectangleIndex = rectangleIdx
					break
				rectangleIdx += 1
		#print('_getRectangleIndex() returning theRectangleIndex:', theRectangleIndex)
		return theRectangleIndex
