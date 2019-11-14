
import math
import numpy as np

from skimage.measure import profile
from scipy.optimize import curve_fit
from scipy import asarray

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
			half_max = max(Y) / 2.
			#find when function crosses line half_max (when sign of diff flips)
			#take the 'derivative' of signum(half_max - Y[])
			d = np.sign(half_max - asarray(Y[0:-1])) - np.sign(half_max - asarray(Y[1:]))
			#plot(X[0:len(d)],d) #if you are interested
			#find the left and right most indexes
			left_idx = np.where(d > 0)[0]
			right_idx = np.where(d < 0)[-1]
			#abb, take the first
			if len(left_idx)>0:
				left_idx = left_idx[0]
			if len(right_idx)>0:
				right_idx = right_idx[0]
			print('fitGaussian() ... FWHM() ... left_idx:', left_idx, 'right_idx:', right_idx)
			return X[right_idx] - X[left_idx] #return the difference (full width)

		try:
			popt,pcov = curve_fit(myGaussian,x,y)
			yFit = myGaussian(x,*popt)
			myFWHM = FWHM(x,y)
			return yFit, myFWHM
		except:
			print('... fitGaussian() error: exception in bAnalysis.fitGaussian() !!!')
			return None, None

	def lineProfile(self, slice, src, dst, linewidth=3):
		""" one slice """
		#print('lineProfile() slice:', slice)
		channel = 0
		intensityProfile = profile.profile_line(self.stack.stack[channel,slice,:,:], src, dst, linewidth=linewidth)
		return intensityProfile

	def stackLineProfile(self, src, dst, linewidth=3):
		""" entire stack """
		print('stackLineProfile()')
		print('   src:', src)
		print('   dst:', dst)
		print('   ', self.stack.stack.shape)
		numSlices = self.stack.stack.shape[1] # will only work for [color,slice,x,y]
		print('   stackLineProfile() numSlices:', numSlices)
		intensityProfileList = []
		for idx, slice in enumerate(range(numSlices-1)): # why do i need -1 ???
			if idx % 300 == 0:
				# print every 100 slices
				print('   idx:', idx, 'of', numSlices)
			intensityProfile = self.lineProfile(slice, src, dst, linewidth=linewidth)
			intensityProfileList.append(intensityProfile)
		#print('   1) intensityProfile.shape:', intensityProfile.shape)
		intensityProfileList = np.array(intensityProfileList)
		#print('   2) intensityProfile.shape:', intensityProfile.shape)
		return intensityProfileList

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
