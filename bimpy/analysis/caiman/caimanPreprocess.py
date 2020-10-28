"""
in Fiji

	1) max grouped z-projection (2 slices per group)
	Make sure new stack starts with 'MAX_'

	2) align with caimainAlign.py

	3) back in Fiji, do a 3d median filter
	Requires 'Java 8' and 'Image xxx' to be installed
	Use Plugin from https://imagejdocu.tudor.lu/plugin/stacks/3d_ij_suite/start


"""
import os, math
import numpy as np
import tifffile

import scipy.ndimage #.ndimage.filters.median_filter

#import bimpy

def slidingZ(imageStack, downSlices=1, verbose=False):
	"""
	rewrite to take frame [i] and [i+1] max
	"""
	if verbose: print('  .slidingZ() downSlices:', downSlices)

	if verbose: print('    imageStack:', imageStack.shape, imageStack.dtype)

	dtype = imageStack.dtype
	(z, m, n) = imageStack.shape
	zNew = z / (downSlices+1) # needs to be int
	zNew = math.floor(zNew)
	print('  zNew:', zNew)

	newShape = (zNew, m, n)
	slidingz = np.zeros(newShape, dtype=dtype)

	outIdx = 0
	for i in np.arange(0, z, downSlices+1):
		print('i:', i, 'outIdx:', outIdx)
		firstSlice = i
		lastSlice = i + downSlices
		if lastSlice > m-1:
			lastSlice = m-1

		slidingz[outIdx,:,:] = np.max(imageStack[firstSlice:lastSlice+1,:,:], axis=0)

		outIdx += 1

	if verbose: print('    slidingz:', slidingz.shape, slidingz.dtype)

	return slidingz

def myMedianFilter(imageStack, size=2, verbose=False):
	"""
	size is 2, then the actual size used is (2,2,2).
	"""
	if verbose: print('  .myMedianFilter() imageStack:', imageStack.shape, imageStack.dtype, 'please wait ...')

	filteredData = scipy.ndimage.filters.median_filter(imageStack, size=size)

	print('    filteredData:', filteredData.shape, filteredData.dtype)

	return filteredData

if __name__ == '__main__':
	# (1) group z-project
	path = '/media/cudmore/data/20201014/superior_2p/tiff/20201014__0001_ch1.tif'

	imageData = tifffile.imread(path)

	imageData = slidingZ(imageData, verbose=True)

	# (2) run caimanAlign

	# (3) run 3d median filter
	if 1:
		imageData = myMedianFilter(imageData, size=2, verbose=True)

	# (4) save
	if 1:
		savePathBase, tmpExt = os.path.splitext(path)
		savePathBase += '_pre.tif'
		print('  savePathBase:', savePathBase)
		tifffile.imsave(savePathBase, imageData)
