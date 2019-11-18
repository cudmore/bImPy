
import time, math
import numpy as np

from skimage.measure import profile
from scipy.optimize import curve_fit
from scipy import asarray
import scipy.signal

#from multiprocessing import Pool
import multiprocessing

class bAnalysis:
	def __init__(self, stack):
		self.stack = stack

	def fitGaussian(self, x, y):
		"""
		for fitting a gaussian, see:
		https://stackoverflow.com/questions/44480137/how-can-i-fit-a-gaussian-curve-in-python
		for finding full width half maximal, see:
		https://stackoverflow.com/questions/10582795/finding-the-full-width-half-maximum-of-a-peak
		"""
		x = asarray(x)
		y = asarray(y)

		n = len(x)                          #the number of data
		mean = sum(x*y)/n                   #
		sigma = sum(y*(x-mean)**2)/n        #

		def myGaussian(x, amplitude, mean, stddev):
		    return amplitude * np.exp(-((x - mean) / 4 / stddev)**2)

		# see: https://stackoverflow.com/questions/10582795/finding-the-full-width-half-maximum-of-a-peak
		def FWHM(X,Y):
			Y = scipy.signal.medfilt(Y, 3)
			half_max = max(Y) / 2.
			#find when function crosses line half_max (when sign of diff flips)
			#take the 'derivative' of signum(half_max - Y[])
			d = np.sign(half_max - asarray(Y[0:-1])) - np.sign(half_max - asarray(Y[1:]))
			#plot(X[0:len(d)],d) #if you are interested
			#find the left and right most indexes
			left_idx = np.where(d > 0)[0]
			right_idx = np.where(d < 0)[-1]
			#abb, take the first
			if left_idx is not None and len(left_idx)==0:
				left_idx = None
			if right_idx is not None and len(right_idx)==0:
				right_idx = None
			if left_idx is not None and len(left_idx)>0:
				left_idx = left_idx[-1]
			if right_idx is not None and len(right_idx)>0:
				right_idx = right_idx[-1]
			print('fitGaussian() ... FWHM() ... left_idx:', left_idx, 'right_idx:', right_idx)
			return X[right_idx] - X[left_idx], left_idx, right_idx #return the difference (full width)

		try:
			popt,pcov = curve_fit(myGaussian,x,y)
			yFit = myGaussian(x,*popt)
			myFWHM, left_idx, right_idx = FWHM(x,y)
			return yFit, myFWHM, left_idx, right_idx
		except RuntimeError as e:
			print('... fitGaussian() error: ', e)
			return None, None, None, None
		except:
			print('... fitGaussian() error: exception in bAnalysis.fitGaussian() !!!')
			raise
			#return None, None, None, None

	def lineProfile(self, slice, src, dst, linewidth=3):
		""" one slice """
		#print('lineProfile() slice:', slice)
		channel = 0
		intensityProfile = profile.profile_line(self.stack.stack[channel,slice,:,:], src, dst, linewidth=linewidth)
		return intensityProfile

	def stackLineProfile(self, src, dst, linewidth=3):
		""" entire stack """
		print('stackLineProfile() src:', src, 'dst:', dst)
		self.stack.print()

		numSlices = self.stack.numImages # will only work for [color,slice,x,y]
		print('   line length:', self.euclideanDistance(src, dst))

		# not sure what is going on here
		# a 3d stack of cd31 staining takes 3x longer when using multiprocessing?
		if numSlices < 500:
			intensityProfileList = []
			startTime = time.time()
			for idx, slice in enumerate(range(numSlices-1)): # why do i need -1 ???
				if idx % 300 == 0:
					# print every 100 slices
					print('   idx:', idx, 'of', numSlices)
				intensityProfile = self.lineProfile(slice, src, dst, linewidth=linewidth)
				intensityProfileList.append(intensityProfile)
			stopTime = time.time()
			print('1) single-thread line profile for', numSlices, 'slices took', round(stopTime-startTime,3))
		else:
			# threaded
			intensityProfileList = []
			print('   multiprocessing.cpu_count():', multiprocessing.cpu_count())
			numCPU = multiprocessing.cpu_count()
			# create a list of parameters to function self.lineProfile as a tuple (slice, src, dst, linewidth)
			poolParams = [(i, src, dst, linewidth) for i in range(numSlices-1)]
			startTime = time.time()
			with multiprocessing.Pool(processes=numCPU-1) as p:
				#starmap() allows passing a paremeter list, map() does not
				intensityProfileList = p.starmap(self.lineProfile, poolParams)
			stopTime = time.time()
			print('2 multi-thread line-profile for', numSlices, 'slices took', round(stopTime-startTime,3))

		intensityProfileList = np.array(intensityProfileList)
		return intensityProfileList

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
