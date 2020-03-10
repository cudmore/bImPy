# 20200310
# Robert Cudmore

import math

import numpy as np

from skimage.measure import profile
import scipy
from scipy.optimize import curve_fit

import bimpy

class bLineProfile:
	def __init__(self, stack):
		self.mySimpleStack = stack


	def getLine(self, slabIdx, radius=None):
		"""
		given a slab, return coordinates of line

		taken from: bStackView.drawSlab()
		"""
		if radius is None:
			radius = 30 # pixels

		edgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(slabIdx)
		if edgeIdx is None:
			print('warning: bStackView.selectSlab() got bad edgeIdx:', edgeIdx)
			return
		edgeSlabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
		thisSlabIdx = edgeSlabList.index(slabIdx) # index within edgeSlabList
		#print('   edgeIdx:', edgeIdx, 'thisSlabIdx:', thisSlabIdx, 'len(edgeSlabList):', len(edgeSlabList))
		# todo: not sure but pretty sure this will not fail?
		if thisSlabIdx==0 or thisSlabIdx==len(edgeSlabList)-1:
			# we were at a slab that was also a node
			return
		prevSlab = edgeSlabList[thisSlabIdx - 1]
		nextSlab = edgeSlabList[thisSlabIdx + 1]
		this_x, this_y, this_z = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)
		prev_x, prev_y, prev_z = self.mySimpleStack.slabList.getSlab_xyz(prevSlab)
		next_x, next_y, next_z = self.mySimpleStack.slabList.getSlab_xyz(nextSlab)
		dy = next_y - prev_y
		dx = next_x - prev_x
		slope = dy/dx
		slope = dx/dy # flipped
		inverseSlope = -1/slope
		x_ = radius / math.sqrt(slope**2 + 1) #
		y_ = x_ * slope
		#y_ = radius / math.sqrt(slope**2 + 1) # flipped
		#x_ = y_ * slope
		xLine1 = this_x - x_ #
		xLine2 = this_x + x_
		yLine1 = this_y + y_
		yLine2 = this_y - y_
		xSlabPlot = [xLine1, xLine2]
		ySlabPlot = [yLine1, yLine2]
		'''
		print('selectSlab() slabIdx:', slabIdx, 'slope:', slope, 'inverseSlope:', inverseSlope)
		print('   slope:', slope, 'inverseSlope:', inverseSlope)
		print('   xSlabPlot:', xSlabPlot)
		print('   ySlabPlot:', ySlabPlot)
		'''

		# draw
		'''
		self.mySlabLinePlot.set_xdata(ySlabPlot) # flipped
		self.mySlabLinePlot.set_ydata(xSlabPlot)
		'''

		lineProfileDict = {
			'ySlabPlot': ySlabPlot,
			'xSlabPlot': xSlabPlot,
			'slice': int(this_z),
		}
		return lineProfileDict

	def getIntensity(self, lineProfileDict, lineWidth, medianFilter):
		"""
		taken from bLinePRofile.update()
		"""
		xSlabPlot = lineProfileDict['xSlabPlot']
		ySlabPlot = lineProfileDict['ySlabPlot']
		slice = lineProfileDict['slice']
		#print('bLineProfileWidget.update() xSlabPlot:', xSlabPlot, 'ySlabPlot:', ySlabPlot, 'slice:', slice)

		imageSlice = self.mySimpleStack.getImage(sliceNum=slice)

		src = (xSlabPlot[0], ySlabPlot[0])
		dst = (xSlabPlot[1], ySlabPlot[1])
		intensityProfile = profile.profile_line(imageSlice, src, dst, linewidth=lineWidth)

		# smooth it
		if medianFilter > 0:
			intensityProfile = scipy.ndimage.median_filter(intensityProfile, medianFilter)

		x = np.asarray([a for a in range(len(intensityProfile))]) # make alist of x points (todo: should be um, not points!!!)

		if np.isnan(intensityProfile[0]):
			print('\nERROR: line profile was nan?\n')
			return
		'''
		print('   intensityProfile:', type(intensityProfile), intensityProfile.shape, intensityProfile)
		print('   x:', type(x), x.shape, x)
		'''

		yFit, FWHM, leftIdx, rightIdx = self._fit(x,intensityProfile)
		#print('   yFit:', yFit, 'FWHM:', FWHM, 'leftIdx:', leftIdx, 'rightIdx:', rightIdx)

		goodFit = not np.isnan(leftIdx)

		minVal = round(np.nanmin(intensityProfile),2)
		maxVal = round(np.nanmax(intensityProfile),2)
		snrVal = round(maxVal - minVal, 2)
		minStr = 'Min: ' + str(minVal)
		self.myMin.setText(minStr)
		maxStr = 'Max: ' + str(maxVal)
		self.myMax.setText(maxStr)
		snrStr = 'SNR: ' + str(snrVal)
		self.mySNR.setText(snrStr)

		if goodFit:
			left_y = intensityProfile[leftIdx]
			# cludge because left/right threshold detection has different y ...
			#right_y = oneProfile[rightIdx]
			right_y = left_y
			xPnt = [leftIdx, rightIdx]
			yPnt = [left_y, right_y]

			# interface
			'''
			diamStr = 'Diameter (pixels): ' + str(int(rightIdx-leftIdx)) # points !!!
			self.myDiameter.setText(diamStr) # points !!!
			'''
		else:
			print('warning: fit failed')
			# interface
			'''
			self.myDiameter.setText('Diameter (pixels): None')
			'''

	def _fit(self, x, y):
		"""
		taken from: bLineProfileWidget._fit()

		x: np.ndarray of x, e.g. pixels or um
		y: np.ndarray of line intensity profile
		returns:
			yfit: ndarray of gaussian file
			fwhm: scalar with full width at half maximal (heuristic calculation)
			left_idx:
			right_idx:
		for fitting a gaussian, see:
		https://stackoverflow.com/questions/44480137/how-can-i-fit-a-gaussian-curve-in-python
		for finding full width half maximal, see:
		https://stackoverflow.com/questions/10582795/finding-the-full-width-half-maximum-of-a-peak
		"""
		n = len(x)                          #the number of data
		mean = sum(x*y)/n                   #
		sigma = sum(y*(x-mean)**2)/n        #
		#mean = sum(y)/n                   #
		#sigma = sum((y-mean)**2)/n        #
		'''
		print('fitGaussian mean:', mean)
		print('fitGaussian sigma:', sigma)
		'''

		def myGaussian(x, amplitude, mean, stddev):
		    return amplitude * np.exp(-((x - mean) / 4 / stddev)**2)

		# see: https://stackoverflow.com/questions/10582795/finding-the-full-width-half-maximum-of-a-peak
		def FWHM(X,Y):
			#Y = scipy.signal.medfilt(Y, 3)
			#half_max = max(Y) / 2.
			half_max = max(Y) * self.halfHeight

			# for explanation of this wierd syntax
			# see: https://docs.scipy.org/doc/numpy/reference/generated/numpy.where.html
			#whr = np.where(Y > half_max)
			#print('   half_max:', half_max)
			whr = np.asarray(Y > half_max).nonzero()
			if len(whr[0]) > 2:
				left_idx = whr[0][0]
				right_idx = whr[0][-1]
				fwhm = X[right_idx] - X[left_idx]
			else:
				left_idx = np.nan
				right_idx = np.nan
				fwhm = np.nan
			return fwhm, left_idx, right_idx #return the difference (full width)

		try:
			#print('x.shape:', x.shape)
			popt,pcov = curve_fit(myGaussian,x,y)
			yFit = myGaussian(x,*popt)
			myFWHM, left_idx, right_idx = FWHM(x,y)
			return yFit, myFWHM, left_idx, right_idx
		except RuntimeError as e:
			#print('... fitGaussian() error: ', e)
			return np.full((x.shape[0]), np.nan), np.nan, np.nan, np.nan
		except:
			print('\n... ... fitGaussian() error: exception in bAnalysis.fitGaussian() !!!')
			raise
			return np.full((x.shape[0]), np.nan), np.nan, np.nan, np.nan
			#return None, None, None, None


if __name__ == '__main__':
	path = '/Users/cudmore/box/Sites/DeepVess/data/20200228/blur/20200228__0001_z.tif'

	stack = bimpy.bStack(path=path, loadImages=True)

	lp = bLineProfile(stack)

	lpDict = lp.getLine(198)

	lp.getIntensity(lpDict, lineWidth=5, medianFilter=3)

	print('lpDict:', lpDict)
