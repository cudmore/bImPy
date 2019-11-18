# Robert Cudmore
# 20191115

import pyqtgraph as pg

class bShapeAnalysisWidget:
	"""
	handle interface of one shape roi at a time
	"""
	def __init__(self, myNapari, myStack):
		self.myNapari = myNapari
		self.myStack = myStack

		self.lineProfileImage = None

		#
		# pyqt graph plots
		self.pgWin = pg.GraphicsWindow(title="Shape Analysis Plugin") # creates a window
		# line intensity for one slice
		self.lineIntensityPlotItem = self.pgWin.addPlot(title="Line Intensity Profile", row=0, col=0)
		self.lineProfilePlot = self.lineIntensityPlotItem.plot(name='lineIntensityProfile')
		self.lineProfilePlot.setShadowPen(pg.mkPen((255,255,255), width=2, cosmetic=True))

		# fit
		x = y = []
		self.fitPlot = self.lineIntensityPlotItem.plot(x, y, pen=pg.mkPen('r', width=3), name='fit')
		self.fitPlot2 = self.lineIntensityPlotItem.plot(x, y, pen=pg.mkPen('b', symbol='.', symbolSize=10, width=5), name='fitPoints')

		# line intensity for entire stack (updated with xxx) e.g. an image of lines (y) through time (x)
		self.stackLineIntensityImage = self.pgWin.addViewBox(row=1, col=0)

		self.img = pg.ImageItem()
		self.stackLineIntensityImage.addItem(self.img)

		# add a vertical line for current slice (over image)
		self.verticalSliceLine = pg.InfiniteLine(pos=0, angle=90)
		self.stackLineIntensityImage.addItem(self.verticalSliceLine)

	def updateStackLineProfile(self, src, dst):
		"""
		generate a line profile for each image in a stack/timeseries

		src: source point
		dst: destination point
		"""
		self.lineProfileImage = self.myStack.analysis.stackLineProfile(src, dst)

		# why return ?
		#return self.lineProfileImage

		self.img.setImage(self.lineProfileImage)

	def updateVerticalSliceLine(self, sliceNum):
		"""
		Set vertical line indicating current slice
		"""
		self.verticalSliceLine.setValue(sliceNum)

	def updateLines(self, sliceNum, src, dst):
		"""
		"""
		lineProfile = self.myStack.analysis.lineProfile(sliceNum, src, dst, linewidth=1)
		x = [a for a in range(len(lineProfile))]
		yFit, fwhm, leftIdx, rightIdx = self.myStack.analysis.fitGaussian(x, lineProfile)

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
				print('plot_pg() xPnt:', xPnt, 'yPnt:', yPnt)
				self.fitPlot2.setData(xPnt, yPnt)

if __name__ == '__main__':
	pass
