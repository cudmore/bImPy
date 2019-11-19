# Robert Cudmore
# 20191115

import numpy as np
import pyqtgraph as pg

class bShapeAnalysisWidget:
	"""
	handle interface of one shape roi at a time
	"""
	def __init__(self, napariViewer, myStack):
		self.napariViewer = napariViewer
		self.myStack = myStack

		self.lineProfileImage = None
		self.FWHM = None

		'''
		@self.napariViewer.bind_key('u')
		def updateStackLineProfile(viewer):
			shapeType, data = self._getSelectedLine()
			if shapeType == 'line':
				src = data[0]
				dst = data[1]
				self.bShapeAnalysisWidget.updateStackLineProfile(src, dst)
			if shapeType in ['rectangle', 'polygon']:
				self.bShapeAnalysisWidget.updateStackPolygon(data)
		'''

		#
		# pyqt graph plots
		self.pgWin = pg.GraphicsWindow(title="Shape Analysis Plugin") # creates a window

		#
		# (1) line intensity for one slice
		self.lineIntensityPlotItem = self.pgWin.addPlot(title="Line Intensity Profile", row=0, col=0)
		self.lineProfilePlot = self.lineIntensityPlotItem.plot(name='lineIntensityProfile')
		self.lineProfilePlot.setShadowPen(pg.mkPen((255,255,255), width=2, cosmetic=True))
		# fit
		x = y = []
		self.fitPlot = self.lineIntensityPlotItem.plot(x, y, pen=pg.mkPen('r', width=3), name='fit')
		self.fitPlot2 = self.lineIntensityPlotItem.plot(x, y, pen=pg.mkPen('b', symbol='.', symbolSize=10, width=5), name='fitPoints')

		#
		# (2) meta analysis with diam (for line profile), mean/min/max for polygon (e.g. ractangular) roi
		self.analysisPlotItem = self.pgWin.addPlot(title="Diameter/mean/min/max etc", row=1, col=0)
		#self.analysisPlotItem.setLabel('left', 'Y Axis', units='A')
		self.analysisPlotItem.setLabel('bottom', 'Slices') #, units='s')
		#
		self.analysisDiameter = self.analysisPlotItem.plot(name='lineintensitydiameter')
		self.analysismean = self.analysisPlotItem.plot(name='mean')
		self.analysismin = self.analysisPlotItem.plot(name='min')
		self.analysismax = self.analysisPlotItem.plot(name='max')
		self.analysismedian = self.analysisPlotItem.plot(name='meadian')
		self.analysisstd = self.analysisPlotItem.plot(name='std')

		# vertical line showing slice number selection in napari viewer
		self.verticalSliceLine2 = pg.InfiniteLine(pos=0, angle=90)
		self.analysisPlotItem.addItem(self.verticalSliceLine2)

		#
		# (3) image with slices on x, and intensity of each line on y
		# line intensity for entire stack (updated with xxx) e.g. an image of lines (y) through time (x)
		self.stackLineIntensityImage = self.pgWin.addViewBox(row=2, col=0)
		# setLabel does not work for view box?
		#self.stackLineIntensityImage.setLabel('left', 'Line Intensity Profile') #, units='A')
		#self.stackLineIntensityImage.setLabel('bottom', 'Slices') #, units='s')

		self.img = pg.ImageItem()
		self.stackLineIntensityImage.addItem(self.img)

		# add a vertical line for current slice (over image)
		self.verticalSliceLine3 = pg.InfiniteLine(pos=0, angle=90)
		self.stackLineIntensityImage.addItem(self.verticalSliceLine3)

	def updateStackPolygon(self, data):
		"""
		data is a list of points specifying vertices of a polygon
		a rectangle is just a polygon with 4 evenly spaces vertices
		"""
		print('bShapeAnalysisWidget.updateStackPolygon() data:', data)
		theMin, theMax, theMean = self.myStack.analysis.stackPolygonAnalysis(data)

		xPlot = np.asarray([slice for slice in range(len(theMean))])
		self.analysisDiameter.setData(xPlot, theMean, connect='finite')

	def updateStackLineProfile(self, src, dst):
		"""
		generate a line profile for each image in a stack/timeseries

		src: source point
		dst: destination point
		"""
		x, self.lineProfileImage, self.FWHM = self.myStack.analysis.stackLineProfile(src, dst)

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

	def updateVerticalSliceLine(self, sliceNum):
		"""
		Set vertical line indicating current slice
		"""
		self.verticalSliceLine2.setValue(sliceNum)
		self.verticalSliceLine3.setValue(sliceNum)

	def updatePolygon(self, sliceNum, data):
		"""
		data is a list of vertex points
		"""
		print('bShapeAnalysisWidget.updatePolygon() data:', data)
		theMin, theMax, theMean = self.myStack.analysis.polygonAnalysis(sliceNum, data)
		print('   slice:', sliceNum, 'theMin:', theMin, 'theMax:', theMax, 'theMean:', theMean)

	def updateLines(self, sliceNum, src, dst):
		"""
		"""
		x, lineProfile, yFit, fwhm, leftIdx, rightIdx = self.myStack.analysis.lineProfile(sliceNum, src, dst, linewidth=1, doFit=True)
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
	pass
