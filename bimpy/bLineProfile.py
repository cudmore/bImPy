# 20200310
# Robert Cudmore

import math
from collections import OrderedDict

import numpy as np

from skimage.measure import profile
import scipy
from scipy.optimize import curve_fit

import bimpy

class bLineProfile:
	def __init__(self, stack):
		self.mySimpleStack = stack
		self.detectionDict = self.getDefaultDetectionParams()

	def setDetectionParam(self, key, value):
		if key not in self.detectionDict:
			print(f'error: bLineProfile.setDetectionParam() did not find {key} in {self.detectionDict.keys()}')
			return False
		self.detectionDict[key] = value

	'''
	def updateDetectionDict(self, newDict):
		self.detectionDict = newDict
	'''

	def getDefaultDetectionParams(self):
		detectionDict = OrderedDict()
		detectionDict['displayThisStack'] = None
		detectionDict['slice'] = None

		detectionDict['xSlabPlot'] = None # get this from bLineProfile.getSlabLine2
		detectionDict['ySlabPlot'] = None
		detectionDict['lineRadius'] = 12 # radius of orthogonal slab along the line
		detectionDict['medianFilter'] = 5 # 0 to turn off, o.w. pre-filter with kernel
		detectionDict['lineWidth'] = 5 # pixels used to extract intensities along line profile
		detectionDict['halfHeight'] = 0.5 # half height of gaussian
		detectionDict['plusMinusSlidingZ'] = 1

		return detectionDict

	def getSlabLine2(self, slabIdx, verbose=True):
		"""
		get line to take intensity analysis and draw in widget

		return (xSlabPlot, ySlabPlot)
		"""

		radius = self.detectionDict['lineRadius']

		if verbose:
			print('bLineProfile.getSlabLine2() slabIdx:', slabIdx, 'radius:', radius)

		if slabIdx is None:
			return None
		edgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(slabIdx)
		if edgeIdx is None:
			print('warning: bLineProfile.getSlabLine2() got bad edgeIdx:', edgeIdx)
			return None

		edgeSlabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
		thisSlabIdx = edgeSlabList.index(slabIdx) # index within edgeSlabList

		if thisSlabIdx==0 or thisSlabIdx==len(edgeSlabList)-1:
			# we were at a slab that was also a node
			return None

		prevSlab = edgeSlabList[thisSlabIdx - 1]
		nextSlab = edgeSlabList[thisSlabIdx + 1]
		this_x, this_y, this_z = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)
		prev_x, prev_y, prev_z = self.mySimpleStack.slabList.getSlab_xyz(prevSlab)
		next_x, next_y, next_z = self.mySimpleStack.slabList.getSlab_xyz(nextSlab)
		# as I look at image,
		#  y is left/right
		#  x is up/down
		dy = next_y - prev_y
		dx = next_x - prev_x

		# abb removed
		#delta_x = np.cos(np.arctan2(dy, dx)) * radius # flipped
		#delta_y = np.sin(np.arctan2(dy, dx)) * radius # flipped

		# slope is 'rise / travel', in this case 'x / y'
		# calling arctan2() with inverse slope, arctan2(dy, dz)
		# angle from slope is 'arctan2(dy, dx)''
		theAngle = np.arctan2(dy, dx)
		# cos(theta) = adjacent / hyp -->> adjacent = sin(theta) * hyp
		delta_y = np.cos(theAngle) * radius # y is left/right
		# sin(theta) = opposite / hyp -->> opposite = sin(theta) * hyp
		delta_x = np.sin(theAngle) * radius  # x is up/down

		xLine1 = this_x - delta_x
		xLine2 = this_x + delta_x
		yLine1 = this_y + delta_y
		yLine2 = this_y - delta_y

		xSlabPlot = [xLine1, xLine2]
		ySlabPlot = [yLine1, yLine2]

		return (xSlabPlot, ySlabPlot)

	def old_getLine(self, slabIdx, radius=None):
		"""
		given a slab, return coordinates of line

		taken from: bStackView.drawSlab()
		"""
		print('bLineProfile.getLine()')
		if radius is None:
			print('  !!!using hard coded radius 30')
			radius = 30 # pixels

		#print('bLineProfile.getLine()')
		#print('  radius:', radius)

		edgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(slabIdx)
		if edgeIdx is None:
			#print('warning: bLineProfile.getLine() got bad edgeIdx:', edgeIdx)
			return None
		edgeSlabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
		thisSlabIdx = edgeSlabList.index(slabIdx) # index within edgeSlabList
		#print('   edgeIdx:', edgeIdx, 'thisSlabIdx:', thisSlabIdx, 'len(edgeSlabList):', len(edgeSlabList))
		# todo: not sure but pretty sure this will not fail?
		if thisSlabIdx==0 or thisSlabIdx==len(edgeSlabList)-1:
			# we were at a slab that was also a node
			return None
		prevSlab = edgeSlabList[thisSlabIdx - 1]
		nextSlab = edgeSlabList[thisSlabIdx + 1]
		this_x, this_y, this_z = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)
		prev_x, prev_y, prev_z = self.mySimpleStack.slabList.getSlab_xyz(prevSlab)
		next_x, next_y, next_z = self.mySimpleStack.slabList.getSlab_xyz(nextSlab)
		dy = next_y - prev_y
		dx = next_x - prev_x
		#slope = dy/dx
		if dy == 0:
			slope = 0
		else:
			slope = dx/dy # flipped
		#inverseSlope = -1/slope
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
			'slabIdx': slabIdx,
			'ySlabPlot': ySlabPlot,
			'xSlabPlot': xSlabPlot,
			'slice': int(this_z),
		}
		return lineProfileDict

	def getLineProfile2(self, lineProfileDict, verbose=False):
		"""
		extract a line profile and return the fit
		"""

		if verbose:
			print('bLineProfile.getLineProfile2()')
			for k,v in lineProfileDict.items():
				print('  ', k, ':', v)

		# this is what user is looking at
		slabIdx = lineProfileDict['slabIdx']
		displayThisStack = lineProfileDict['displayThisStack'] # (1,2,3, ...)
		slice = lineProfileDict['slice'] # can be None

		if displayThisStack == 'rgb':
			print('warning: getLineProfile2() does not work for rgb !!!')
			return None

		xSlabPlot = lineProfileDict['xSlabPlot'] # todo: calculate this here, it depends on radius!!!
		ySlabPlot = lineProfileDict['ySlabPlot']

		if xSlabPlot is None or ySlabPlot is None:
			xSlabPlot, ySlabPlot = self.getSlabLine2(slabIdx)
		if slice is None:
			xSlab, ySlab, zSlab = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)
			slice = int(zSlab)

		# dynamic
		medianFilter = lineProfileDict['medianFilter']
		lineWidth = lineProfileDict['lineWidth']
		halfHeight = lineProfileDict['halfHeight']
		plusMinusSlidingZ = lineProfileDict['plusMinusSlidingZ']

		src = (xSlabPlot[0], ySlabPlot[0])
		dst = (xSlabPlot[1], ySlabPlot[1])

		# get the image to analyze
		#print('todo: bLineProfile.getLineProfile2() ... extend this to sliding-z')
		if plusMinusSlidingZ > 0:
			upSlices = plusMinusSlidingZ
			downSlices = plusMinusSlidingZ
			imageSlice = self.mySimpleStack.getSlidingZ2(channel=displayThisStack,
											sliceNumber=slice,
											upSlices=upSlices,
											downSlices=downSlices)
		else:
			imageSlice = self.mySimpleStack.getImage2(channel=displayThisStack, sliceNum=slice)

		# get the line profile
		try:
			# abb aics added mode='constant'
			# Specifies how to compute any values falling outside of the image.
			intensityProfile = profile.profile_line(imageSlice, src, dst, linewidth=lineWidth, mode='constant')
		except(ValueError) as e:
			print('ERROR: bLineProfile.getLineProfile2() got nan calling profile.profile_line()')
			return None

		# smooth the line profile
		if medianFilter > 0:
			intensityProfile = scipy.ndimage.median_filter(intensityProfile, medianFilter)

		# make alist of x points (todo: should be um, not points!!!)
		xFit = np.asarray([a for a in range(len(intensityProfile))])

		if np.isnan(intensityProfile[0]):
			print('\nERROR: bLineProfile.getLineProfile2() got line profile nan?\n')
			return
		'''
		print('   intensityProfile:', type(intensityProfile), intensityProfile.shape, intensityProfile)
		print('   x:', type(x), x.shape, x)
		'''

		# do the fit
		yFit, FWHM, leftIdx, rightIdx = self._fit(xFit,intensityProfile, halfHeight=halfHeight)
		#print('   yFit:', yFit, 'FWHM:', FWHM, 'leftIdx:', leftIdx, 'rightIdx:', rightIdx)

		goodFit = not np.isnan(leftIdx)
		minVal = round(np.nanmin(intensityProfile),2)
		maxVal = round(np.nanmax(intensityProfile),2)

		# abb oct2020
		# was this
		#snrVal = round(maxVal - minVal, 2)
		# now this
		if goodFit:
			yTmpInt_left = intensityProfile[leftIdx]
			yTmpInt_right = intensityProfile[rightIdx]
			yTmpInt = max(yTmpInt_left, yTmpInt_right)
			snrVal = yTmpInt - minVal
			snrVal = round(snrVal,2)
		else:
			snrVal = np.nan
		'''
		tmpMinVal = minVal
		if tmpMinVal==0:
			tmpMinVal = 1
		snrVal = round(maxVal/tmpMinVal, 2)
		'''

		myDiam = np.nan
		if goodFit:
			myDiam = rightIdx - leftIdx + 1

		returnDict = OrderedDict()
		returnDict['intensityProfile'] = intensityProfile
		returnDict['diam'] = myDiam # pixels
		returnDict['minVal'] = minVal
		returnDict['maxVal'] = maxVal
		returnDict['goodFit'] = goodFit
		returnDict['leftIdx'] = leftIdx
		returnDict['rightIdx'] = rightIdx
		returnDict['snrVal'] = snrVal # depends on good fit
		returnDict['yFit'] = yFit
		returnDict['xFit'] = xFit

		return returnDict

	def old_getIntensity(self, lineProfileDict, lineWidth, medianFilter):
		"""
		diameter is in pixels

		taken from bLineProfileWidget.update()
		"""
		slabIdx = lineProfileDict['slabIdx'] # just used in return
		xSlabPlot = lineProfileDict['xSlabPlot']
		ySlabPlot = lineProfileDict['ySlabPlot']
		slice = lineProfileDict['slice']
		#print('bLineProfileWidget.update() xSlabPlot:', xSlabPlot, 'ySlabPlot:', ySlabPlot, 'slice:', slice)

		imageSlice = self.mySimpleStack.getImage2(channel=2, sliceNum=slice)

		src = (xSlabPlot[0], ySlabPlot[0])
		dst = (xSlabPlot[1], ySlabPlot[1])
		# abb added mode='constant'
		intensityProfile = profile.profile_line(imageSlice, src, dst, linewidth=lineWidth, mode='constant')

		# smooth it
		if medianFilter > 0:
			intensityProfile = scipy.ndimage.median_filter(intensityProfile, medianFilter)

		# abb oct2020
		# see below, playing with SNR, maybe use (left/right intensity) / min
		# put these in return dict
		lpMin = np.nanmin(intensityProfile)
		lpMax = np.nanmax(intensityProfile)
		'''
		lpMin_denom = lpMin
		if lpMin_denom == 0:
			lpMin_denom = 1
		lpSNR = lpMax / lpMin_denom # redundant, just max/min
		'''

		# make alist of x points (todo: should be um, not points!!!)
		x = np.asarray([a for a in range(len(intensityProfile))])

		if np.isnan(intensityProfile[0]):
			print('\nERROR: line profile was nan?\n')
			return None
		'''
		print('   intensityProfile:', type(intensityProfile), intensityProfile.shape, intensityProfile)
		print('   x:', type(x), x.shape, x)
		'''

		yFit, FWHM, leftIdx, rightIdx = self._fit(x,intensityProfile)
		goodFit = not np.isnan(leftIdx)

		# interface
		'''
		minVal = round(np.nanmin(intensityProfile),2)
		maxVal = round(np.nanmax(intensityProfile),2)
		snrVal = round(maxVal - minVal, 2)
		minStr = 'Min: ' + str(minVal)
		self.myMin.setText(minStr)
		maxStr = 'Max: ' + str(maxVal)
		self.myMax.setText(maxStr)
		snrStr = 'SNR: ' + str(snrVal)
		self.mySNR.setText(snrStr)
		'''

		if goodFit:
			left_y = intensityProfile[leftIdx]
			# cludge because left/right threshold detection has different y ...
			#right_y = oneProfile[rightIdx]
			right_y = left_y
			xPnt = [leftIdx, rightIdx]
			yPnt = [left_y, right_y]

			diam = rightIdx-leftIdx # points
			#print('   yFit:', yFit, 'FWHM:', FWHM, 'diam:', diam, 'leftIdx:', leftIdx, 'rightIdx:', rightIdx)
			#print('FWHM:', FWHM, 'diam:', diam, 'leftIdx:', leftIdx, 'rightIdx:', rightIdx)

			# abb oct2020
			# trying to get a meaningful SNR
			tmp_left_y = intensityProfile[leftIdx]
			tmp_right_y = intensityProfile[rightIdx]
			tmpMax = max(tmp_left_y, tmp_left_y)
			# as ratio
			#lpSNR = tmpMax / lpMin_denom # todo: clean this up
			# as difference
			lpSNR = tmpMax - lpMin # todo: clean this up

			retDict = OrderedDict()
			retDict['slabIdx'] = slabIdx
			retDict['FWHM'] = FWHM
			retDict['diam'] = diam # pixels
			retDict['leftIdx'] = leftIdx
			retDict['rightIdx'] = rightIdx
			# abb oct2020
			retDict['lpMin'] = lpMin # actual min along line profile
			retDict['lpMax'] = tmpMax #lpMax # max between left/right of fit
			retDict['lpSNR'] = lpSNR # redundant, just max/min

			return retDict
			# interface
			'''
			diamStr = 'Diameter (pixels): ' + str(int(rightIdx-leftIdx)) # points !!!
			self.myDiameter.setText(diamStr) # points !!!
			'''
		else:
			#print('warning: fit failed')
			return None
			# interface
			'''
			self.myDiameter.setText('Diameter (pixels): None')
			'''

	def _fit(self, x, y, halfHeight=0.5):
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
		def FWHM(X, Y, halfHeight):
			#Y = scipy.signal.medfilt(Y, 3)
			#half_max = max(Y) / 2.
			half_max = max(Y) * halfHeight

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
			myFWHM, left_idx, right_idx = FWHM(x,y,halfHeight)
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

	print('loading stack')
	stack = bimpy.bStack(path=path, loadImages=True)

	# reanalize edges (needed after adding 'tort', was not save in h5f)
	print('_analyze()')
	stack.slabList._analyze()

	stack.slabList._printStats()

	lp = bLineProfile(stack)

	print('analyzing intensity of all slabs ... ...')
	startTime = bimpy.util.bTimer()
	nEdges = stack.slabList.numEdges()
	meanDiamList = [] # mean diam per segment based on Vesselucida
	meanDiamList2 = [] # my intensity calculation
	lengthList = []
	tortList = []
	for edgeIdx in range(nEdges):
		edgeDict = stack.slabList.getEdge(edgeIdx)

		thisDiamList = []

		for slabIdx in edgeDict['slabList']:
			lpDict = lp.getLine(slabIdx, radius=20) # default is radius=30

			if lpDict is not None:
				retDict = lp.getIntensity(lpDict, lineWidth=5, medianFilter=3)
				if retDict is not None:
					thisDiamList.append(retDict['diam']) # bImPy diameter
			else:
				pass

		if len(thisDiamList) > 0:
			thisDiamMean = np.nanmean(thisDiamList)
		else:
			thisDiamMean = np.nan
		meanDiamList2.append(thisDiamMean)
		meanDiamList.append(edgeDict['Diam']) # vessellucida
		lengthList.append(edgeDict['Len 3D'])
		tortList.append(edgeDict['Tort'])

	print('   bImpy number of slabs analyzed:', len(thisDiamList), startTime.elapsed())

	#
	# stat
	def getStat(aList):
		theMean = np.nanmean(aList)
		theSD = np.nanstd(aList)
		theN = np.count_nonzero(~np.isnan(aList))
		theSE = theSD / math.sqrt(theN)
		return theMean, theSD, theSE, theN

	m,sd,se,n = getStat(meanDiamList2)
	print('bImpy vessel diameter: mean', m, 'sd:', sd, 'se:', se, 'n:', n)
	m,sd,se,n = getStat(meanDiamList)
	print('Vesselucida vessel diameter: mean', m, 'sd:', sd, 'se:', se, 'n:', n)
	m,sd,se,n = getStat(lengthList)
	print('Vessel length: mean', m, 'sd:', sd, 'se:', se, 'n:', n)
	m,sd,se,n = getStat(tortList)
	print('Vessel Tortuosity: mean', m, 'sd:', sd, 'se:', se, 'n:', n)

	from scipy import stats
	clean1 = [x for x in meanDiamList2 if str(x) != 'nan']
	clean2 = [x for x in meanDiamList if str(x) != 'nan']
	t, p = stats.ttest_ind(clean1, clean2) # vessel diameter from Vesselucida vs bImPy
	print('ttest t:', t, 'p:', p)

	#
	# plot
	print('plot')
	alpha = 0.8 #0.75

	from matplotlib import pyplot as plt
	fig = plt.figure()

	plt.subplot(141)
	n, bins, patches = plt.hist(meanDiamList, 50, density=False, facecolor='k', alpha=alpha)
	plt.xlabel('Vesselucida Vessel Diameter (points)')
	plt.ylabel('Count')

	plt.subplot(142)
	n, bins, patches = plt.hist(meanDiamList2, 50, density=False, facecolor='k', alpha=alpha)
	plt.xlabel('bImPy Vessel Diameter (points)')
	plt.ylabel('Count')

	plt.subplot(143)
	n, bins, patches = plt.hist(lengthList, 50, density=False, facecolor='k', alpha=alpha)
	plt.xlabel('Vessel Length (points)')
	plt.ylabel('Count')

	plt.subplot(144)
	n, bins, patches = plt.hist(tortList, 50, density=False, facecolor='k', alpha=alpha)
	plt.xlabel('Vessel Tortuosity')
	plt.ylabel('Count')

	plt.grid(True)
	plt.show()
