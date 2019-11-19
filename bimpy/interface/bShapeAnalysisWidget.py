# Robert Cudmore
# 20191115

import pyqtgraph as pg

"""
to generate a mask of an arbitrary polygon

    from skimage.draw import polygon
    skimage.draw.polygon(r, c, shape=None)

r: list of rows
c: list of columns
shape: (maxRows, maxCols) to constrain the results to within a given image
returns: (rr, cc) : ndarray of int
   Pixel coordinates of polygon. May be used to directly index into an array, e.g. img[rr, cc] = 1.

see: https://scikit-image.org/docs/dev/api/skimage.draw.html#skimage.draw.polygon
see sandbox/bPolygonMask.py
"""

class bShapeAnalysisWidget:
	"""
	handle interface of one shape roi at a time
	"""
	def __init__(self, myNapari, myStack):
		self.myNapari = myNapari
		self.myStack = myStack

		self.lineProfileImage = None
		self.FWHM = None

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

	def updateStackLineProfile(self, src, dst):
		"""
		generate a line profile for each image in a stack/timeseries

		src: source point
		dst: destination point
		"""
		self.lineProfileImage, self.FWHM = self.myStack.analysis.stackLineProfile(src, dst)

		# why return ?
		#return self.lineProfileImage

		#
		# update plots with new results
		self.img.setImage(self.lineProfileImage)

		print('todo: this is an error FIX IT !!!!!!!!!!!!!!!!!!!!!!!!!!!')
		print('updateStackLineProfile self.FWHM:', self.FWHM)
		print(type(self.FWHM))
		self.FWHM = self.FWHM[0,:]
		print(type(self.FWHM))
		#fwhmList = self.FWHM.tolist()
		x = [i for i in range(len(fwhmList))]
		#print(x.shape)
		#print(self.FWHM.shape)
		self.analysisDiameter.setData(x, fwhmList)

	def updateVerticalSliceLine(self, sliceNum):
		"""
		Set vertical line indicating current slice
		"""
		self.verticalSliceLine2.setValue(sliceNum)
		self.verticalSliceLine3.setValue(sliceNum)

	def updateLines(self, sliceNum, src, dst):
		"""
		"""
		lineProfile, yFit, fwhm, leftIdx, rightIdx = self.myStack.analysis.lineProfile(sliceNum, src, dst, linewidth=1, doFit=True)
		#x = [a for a in range(len(lineProfile))]
		#yFit, fwhm, leftIdx, rightIdx = self.myStack.analysis.fitGaussian(x, lineProfile)

		self.updateLineIntensityPlot(lineProfile, yFit, leftIdx, rightIdx)

	def updateLineIntensityPlot(self, oneProfile, fit=None, left_idx=None, right_idx=None): #, ind_lambda):
		"""
		Update the pyqt graph (top one) with a new line profile

		Parameters:
			oneProfile: ndarray of line intensity
		"""
		if (oneProfile is not None):
			#
			self.lineProfilePlot.setData(oneProfile)
		if (fit is not None):
			#
			self.fitPlot.setData(fit)
		if (oneProfile is not None and left_idx is not None and right_idx is not None):
			#if len(left_idx)>0 and len(right_idx)>0:
			if 1:
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
