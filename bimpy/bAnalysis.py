
import math
import numpy as np

from skimage.measure import profile
#import skimage.measure
#import skimage
#from skimage import measure
from scipy.optimize import curve_fit

class bAnalysis:
	def __init__(self, stack):
		self.stack = stack

	def fitGaussian(self, x, y):
		print('fitGaussian()')
		print('   x:', x)
		print('   y:', y)
		n = len(x)                          #the number of data
		mean = sum(x*y)/n                   #note this correction
		sigma = sum(y*(x-mean)**2)/n        #note this correction

		def gaus(x,a,x0,sigma):
			return a * math.exp(-(x-x0)**2 / (2 * sigma**2))

		popt,pcov = curve_fit(gaus,x,y,p0=[max(y),mean,sigma])
		# plot with
		# plt.plot(x,gaus(x,*popt),'ro:',label='fit')
		return gaus(x, *popt)

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
