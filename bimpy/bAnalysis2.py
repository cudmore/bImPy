
# Robert Cudmore
# 20191119

"""
created to be used with raw image data from napari bShapeAnalysisWidget
"""

import time, math
import numpy as np

from skimage.measure import profile
from scipy.optimize import curve_fit
from skimage.draw import polygon
import scipy.signal

#from multiprocessing import Pool
import multiprocessing

class bAnalysis2:
	def __init__(self, data):
		"""
		data: 3d image data
		"""
		self.data = data

	def fitGaussian(self, x, y):
		"""
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
			Y = scipy.signal.medfilt(Y, 3)
			half_max = max(Y) / 2.
			half_max = max(Y) * 0.7

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

	@property
	def imageShape(self):
		""" return the shape of an individual image """
		if len(self.data==2):
			return self.data.shape
		elif len(self.data==3):
			return self.data[0,:,:].shape
		elif len(self.data==4):
			return self.data[0,0,:,:].shape

	@property
	def numImages(self):
		"""
		return number of images, either number of slice images in a stack or frames in a time-series
		"""
		if len(self.data.shape)==2:
			return 1
		elif len(self.data.shape)==3:
			# assuming (slice, row, col)
			return self.data.shape[0]
		elif len(self.data.shape)==4:
			# assuming (color, slice, row, col)
			return self.data.shape[1]

	def polygonAnalysis(self, slice, data):
		"""
		data: list of vertex points
		"""
		'''
		print('bAnalysis.polygonAnalysis() slice:', slice, 'data:', data)
		print('   type(data):', type(data))
		'''
		dataList = data.tolist()
		r = list(zip(*dataList))[0]
		c = list(zip(*dataList))[1]
		#channel = 0
		#myImageShape = self.stack.stack[channel,slice,:,:].shape
		#myImageShape = self.data[slice,:,:].shape
		(rr, cc) = polygon(r, c, shape=self.imageShape)
		if len(rr)==0 or len(cc)==0:
			return np.nan, np.nan, np.nan
		'''
		print('rr:', rr)
		print('cc:', cc)
		'''
		#roiImage = self.stack.stack[channel,slice,rr,cc] # extract the roi
		try:
			roiImage = self.data[slice,rr,cc] # extract the roi
			#print('roiImage:', roiImage, 'roiImage.shape', roiImage.shape, 'type(roiImage):', type(roiImage))
			theMin = np.nanmin(roiImage)
			theMax = np.nanmax(roiImage)
			theMean = np.nanmean(roiImage)
			return theMin, theMax, theMean
		except IndexError as e:
			print('*** IndexError exception in bAnalysis2.polygonAnalysis() e:', e)
			raise

	def polygonAnalysis2(self, slice, rr, cc):
		"""
		data: list of vertex points
		"""
		if slice % 300 == 0:
			print('   slice:', slice, 'of', self.numImages)
		try:
			roiImage = self.data[slice,rr,cc] # extract the roi
			#print('roiImage:', roiImage, 'roiImage.shape', roiImage.shape, 'type(roiImage):', type(roiImage))
			theMin = np.nanmin(roiImage)
			theMax = np.nanmax(roiImage)
			theMean = np.nanmean(roiImage)
			return theMin, theMax, theMean
		except IndexError as e:
			print('*** IndexError exception in bAnalysis2.polygonAnalysis() e:', e)
			raise

	def stackPolygonAnalysis(self, data):
		"""
		data: list of vertex points
		"""
		#numSlices = self.stack.numImages # will only work for [color,slice,x,y]
		minList = []
		maxList = [] # each element is intensity profile for one slice/image
		meanList = [] # each element is intensity profile for one slice/image
		#if numSlices < 500:
		doSingleThread= False
		if doSingleThread or self.numImages < 500:
			print('   stackPolygonAnalysis performing loop through images')
			startTime = time.time()
			for idx, slice in enumerate(range(self.numImages)): # why do i need -1 ???
				if idx % 300 == 0:
					print('   idx:', idx, 'of', self.numImages)
				theMin, theMax, theMean = self.polygonAnalysis(slice, data)
				minList.append(theMin)
				maxList.append(theMax)
				meanList.append(theMean)
			stopTime = time.time()
			print(   '1) single-thread ', self.numImages, 'slices took', round(stopTime-startTime,3))
		else:
			numCPU = multiprocessing.cpu_count()
			print('   stackPolygonAnalysis using multiprocessing pool starmap, num cpu is', numCPU)
			print('   ', self.data.shape, self.data.dtype)# create a list of parameters to function self.lineProfile as a tuple (slice, src, dst, linewidth)
			dataList = data.tolist()
			r = list(zip(*dataList))[0]
			c = list(zip(*dataList))[1]
			#channel = 0
			#myImageShape = self.stack.stack[channel,slice,:,:].shape
			#myImageShape = self.data[slice,:,:].shape
			(rr, cc) = polygon(r, c, shape=self.imageShape)
			numImages = self.numImages
			poolParams = [(slice, rr, cc) for slice in range(numImages)]
			startTime = time.time()
			#with multiprocessing.Pool(processes=int(numCPU/2)) as p:
			with multiprocessing.Pool(processes=numCPU-1) as p:
				#starmap() allows passing a paremeter list, map() does not
				minList, maxList, meanList = zip(*p.starmap(self.polygonAnalysis2, poolParams, chunksize=numCPU*10)) # between ncpu*10 and ncpu*100
			stopTime = time.time()
			print('2) multi-thread stackPolygonAnalysis for', self.numImages, 'slices took', round(stopTime-startTime,3))
		return np.asarray(minList), np.asarray(maxList), np.asarray(meanList)

	def lineProfile(self, slice, src, dst, linewidth=3, doFit=True):
		""" one slice

		Returns:

		x: ndarray, one point for each point in the profile (NOT images/slice in stack)
		"""
		'''
		print('!!!! lineProfile() slice:', slice, 'src:', src, 'dst:', dst)
		print('   slice:', slice)
		print('   src:', src, type(src))
		print('   dst:', dst, type(dst))
		print('   self.data.shape:', self.data.shape)
		print('   linewidth:', linewidth, type(linewidth))
		'''
		#channel = 0
		#intensityProfile = profile.profile_line(self.stack.stack[channel,slice,:,:], src, dst, linewidth=linewidth)
		try:
			#print('self.data[slice,:,:].shape', self.data[slice,:,:].shape)
			intensityProfile = profile.profile_line(self.data[slice,:,:], src, dst, linewidth=linewidth)
			x = np.asarray([a for a in range(len(intensityProfile))]) # make alist of x points (todo: should be um, not points!!!)
			yFit, FWHM, left_idx, right_idx = self.fitGaussian(x,intensityProfile)
		except ValueError as e:
			print('!!!!!!!!!! *********** !!!!!!!!!!!!! my exception in lineProfile() ... too many values to unpack (expected 2)')
			print('e:', e)
			return (None, None, None, None, None, None)
		'''
		print('lineProfile() slice:', slice)
		print('   x.shape:', x.shape)
		print('   intensityProfile.shape:', intensityProfile.shape)
		print('   yFit.shape:', yFit.shape)
		print('   FWHM:', FWHM, 'left_idx:', left_idx, 'right_idx:', right_idx)
		'''
		return (x, intensityProfile, yFit, FWHM, left_idx, right_idx)

	def stackLineProfile(self, src, dst, linewidth=3):
		"""
		calculate line profile for each slice in a stack
		todo: fix the logic here, my self.lineProfile is returning too much
		"""
		print('stackLineProfile() src:', src, 'dst:', dst)
		print('   line length:', self.euclideanDistance(src, dst))

		xList = []
		intensityProfileList = [] # each element is intensity profile for one slice/image
		fwhmList = [] # each element is intensity profile for one slice/image
		# not sure what is going on here
		# a 3d stack of cd31 staining takes 3x longer when using multiprocessing?
		doSingleThread= True
		if doSingleThread or self.numImages < 500:
			print('   stackLineProfile performing loop through images')
			startTime = time.time()
			for idx, slice in enumerate(range(self.numImages)): # why do i need -1 ???
				if idx % 300 == 0:
					print('   idx:', idx, 'of', self.numImages)
				x, intensityProfile, yFit, fwhm, left_idx, right_idx = self.lineProfile(slice, src, dst, linewidth=linewidth, doFit=True)
				xList.append(x)
				intensityProfileList.append(intensityProfile)
				fwhmList.append(fwhm)
				#print(idx, fwhm)
			stopTime = time.time()
			print('1) single-thread line profile for', self.numImages, 'slices took', round(stopTime-startTime,3))
		else:
			# threaded
			print('   running line profile for all slices in PARALLEL, numImages:', self.numImages)
			print('   multiprocessing.cpu_count():', multiprocessing.cpu_count())
			numCPU = multiprocessing.cpu_count()
			# create a list of parameters to function self.lineProfile as a tuple (slice, src, dst, linewidth)
			doFit = True # do the fit of each line
			poolParams = [(i, src, dst, linewidth, doFit) for i in range(self.numImages)]
			#for poolParam in poolParams:
			#	print(poolParam)
			startTime = time.time()
			with multiprocessing.Pool(processes=numCPU-1) as p:
				#starmap() allows passing a paremeter list, map() does not
				#xList, intensityProfileList, yFit, fwhm, left_idx, right_idx = p.starmap(self.lineProfile, poolParams)
				xList, intensityProfileList, yFit, fwhmList, left_idx, right_idx = zip(*p.starmap(self.lineProfile, poolParams))
				#tmpRet = p.starmap(self.lineProfile, poolParams)
			print(type(fwhmList))
			print(len(fwhmList))
			'''
			print('type(tmpRet):', type(tmpRet))
			print('len(tmpRet):', len(tmpRet))
			print('len(tmpRet[0]):', len(tmpRet[0]))
			print('tmpRet[0]:', tmpRet[0])
			print('tmpRet[-1]:', tmpRet[-1])
			for tmpIdx, tmp in enumerate(tmpRet):
				if len(tmp) != 6:
					print(tmpIdx, tmp)
			'''
			stopTime = time.time()
			print('2) multi-thread line-profile for', self.numImages, 'slices took', round(stopTime-startTime,3))

		#xArray = np.array(xList)
		#intensityProfileList = np.array(intensityProfileList)
		#fwhm = np.array(fwhm)
		return np.asarray(xList), np.asarray(intensityProfileList), np.asarray(fwhmList)

	def euclideanDistance(self, pnt1, pnt2):
		"""
		given 2d/3d points, return the straight line (euclidean) distance btween them

		remeber, this is not accurate for 3d points as our Z is huge in scanning microscopy!!!
		"""
		if len(pnt1) == 2:
			return math.sqrt((pnt1[0]-pnt2[0])**2 + (pnt1[1]-pnt2[1])**2)
		elif len(pnt1) == 3:
			return math.sqrt((pnt1[0]-pnt2[0])**2 + (pnt1[1]-pnt2[1])**2 + + (pnt1[2]-pnt2[2])**2)

if __name__ == '__main__':
	import bimpy
	path = '/Users/cudmore/box/data/nathan/EC-GCaMP-Test-20190920/ach-analysis/ach-aligned-8bit.tif'
	path = '/Users/cudmore/box/data/nathan/EC-GCaMP-Test-20190920/ach-analysis/ach-aligned-8bit-short2.tif'
	bs = bimpy.bStack(path)
	ba = bAnalysis(bs)
	slice = 0
	src = [0, 0]
	dst = [100, 100]
	ans = ba.lineProfile(slice, src, dst, linewidth=2)
	print('ans:', ans)
