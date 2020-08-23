"""
Robert Cudmore
20200516

General purpose morphology operations to manipulate 3d image stacks

"""

import os, time

import numpy as np
import pandas as pd
import scipy
import skimage

# for erosion
#from scipy.ndimage import morphology

import bimpy

def gaussianFilter(imageStack, kernelSize=(2,2,2), verbose=False):
	"""
	"""
	if verbose: print('  .', 'myGaussianFilter() kernelSize:', kernelSize, '... please wait')
	
	result = scipy.ndimage.gaussian_filter(imageStack, sigma=kernelSize)
	
	if verbose: _printStackParams('output', result)
	
	return result

def medianFilter(imageStack, kernelSize=(2,2,2), verbose=False):
	"""
	"""
	if verbose:
		print('  .myMedianFilter() kernelSize:', kernelSize, '... please wait')
	
	if verbose: _printStackParams('input', imageStack)
		
	startTime = time.time()
	
	result = scipy.ndimage.median_filter(imageStack, size=kernelSize)
	
	if verbose: _printStackParams('output', result)

	if verbose:
		stopTime = time.time()
		print('    myMedianFilter took', round(stopTime-startTime,2), 'seconds')
	
	return result

def _printStackParams(name, myStack):
	#print('  ', name, type(myStack), myStack.shape, myStack.dtype, 'dtype.char:', myStack.dtype.char, 'min:', np.min(myStack), 'max:', np.max(myStack))
	print('  ', name, myStack.shape, myStack.dtype, 'dtype.char:', myStack.dtype.char, 'min:',
		round(np.min(myStack),2), 'max:', round(np.max(myStack),2), 'mean:', round(np.mean(myStack),2)
		)

def slidingZ(imageStack, upDownSlices=1, verbose=False):
	if verbose: print('  .slidingZ() upDownSlices:', upDownSlices)

	if verbose: _printStackParams('input', imageStack)

	slidingz = imageStack.copy()
	m = imageStack.shape[0]
	for i in range(m):
		firstSlice = i - upDownSlices
		lastSlice = i + upDownSlices
		if firstSlice < 0:
			firstSlice = 0
		if lastSlice > m-1:
			lastSlice = m-1
		
		slidingz[i,:,:] = np.max(imageStack[firstSlice:lastSlice+1,:,:], axis=0)
		
	if verbose: _printStackParams('output', slidingz)

	return slidingz

def binary_dilation(maskStack, iterations=1, return_uint8=True):
	result = scipy.ndimage.morphology.binary_dilation(maskStack, structure=None, iterations=iterations).astype(np.uint8)
	if return_uint8:
		return result.astype(np.uint8)
	else:
		return result
	
def binary_erosion(imageStack, iterations=1, return_uint8=True):
	result = scipy.ndimage.morphology.binary_erosion(imageStack, structure=None, iterations=iterations) # returns a true/false mask?
	if return_uint8:
		return result.astype(np.uint8)
	else:
		return result
	
def binary_fill_holes(maskStack):
	retStack = scipy.ndimage.morphology.binary_fill_holes(maskStack).astype(np.uint8)
	return retStack
	
def fillHoles(maskStack, doDilation=True, verbose=False):
	"""
	Fix this, remove initial dilation
	"""
	
	if verbose: print('  .myFillHoles()')
	
	if verbose: _printStackParams('input', maskStack)

	retStack = maskStack.copy()
	
	# first dilate
	retStack = scipy.ndimage.morphology.binary_dilation(retStack, structure=None, iterations=1).astype(np.uint8)

	'''
	print('-')
	print('0 fillHoles 0:', np.nanmean(retStack[0,:,:]))
	print('0 fillHoles -1:', np.nanmean(retStack[-1,:,:]))
	print('0 fillHoles -2:', np.nanmean(retStack[-2,:,:]))
	'''
	
	#
	# in 3d
	retStack = scipy.ndimage.morphology.binary_fill_holes(retStack).astype(np.uint8)
	
	'''
	print('-')
	print('2 fillHoles 0:', np.nanmean(retStack[0,:,:]))
	print('2 fillHoles -1:', np.nanmean(retStack[-1,:,:]))
	print('2 fillHoles -2:', np.nanmean(retStack[-2,:,:]))
	'''
	
	'''
	n = retStack.shape[0]
	for i in range(n):
		slice = retStack[i,:,:]
		retStack[i,:,:] = scipy.ndimage.morphology.binary_fill_holes(slice).astype(np.uint8)
	'''
	
	'''
	structure = np.ones((3,25,25))
	retStack = morphology.binary_fill_holes(retStack, structure=structure)
	'''

	# then erode
	# erosion is making the first and last slice all 0???
	#retStack = scipy.ndimage.morphology.binary_erosion(retStack, structure=None, iterations=1).astype(np.uint8)

	'''
	print('-')
	print('3 fillHoles 0:', np.nanmean(retStack[0,:,:]))
	print('3 fillHoles -1:', np.nanmean(retStack[-1,:,:]))
	print('3 fillHoles -2:', np.nanmean(retStack[-2,:,:]))
	'''
	
	retStack = retStack.astype(np.uint8)
	
	if verbose: _printStackParams('output', retStack)
	
	return retStack

def threshold_sauvola(imageStack, asImage = False, window_size=23, k=0.2):
	"""
	trying to follow Skan algorithm for masking using gaussian then xxx
	
	asImage:
	window_size: 
	k:
	"""
	print('  .threshold_sauvola() window_size:', window_size, 'k:', k)

	if (window_size % 2) == 0:
		print('Warning: threshold_sauvola() requires window_size to be odd, got:', window_size)
		window_size -= 1
	else:
		pass
				
	#
	# smooth
	# sigma is ceil 0.1 of window_size (in skan)
	#sigma = 3
	#imageData = filters.gaussian(imageData, sigma=sigma)
	
	# k is brightnessOffset
	# window_size is diameter (maybe the line that has both background and forground, e.g. cappillarry diameter?)
	#window_size = 23 #23 # must be odd
	#k = 0.2 #0.34 # 0.2
	
	threshData = skimage.filters.threshold_sauvola(imageStack, window_size=window_size, k=k, r=None) # returns np.float64
	
	if asImage:
		threshData = np.where(imageStack > threshData, imageStack, 0)
	else:
		# as binary
		threshData = imageStack > threshData # make it binary
	threshData = threshData.astype(np.uint8)
	
	return threshData

def threshold_otsu(imageStack, verbose=False):
	"""
	Parameters:
		imageStack: numpy ndarray of shape (slice,x,y) 
	Returns:
		Binary threshold stack, same shape as imageStack, with foreground=1 and background=0
	"""
	if verbose: print('  .threshold_otsu()')

	thresholdStack = imageStack.copy() # put the binary thresholded stack in here
	numSlices = thresholdStack.shape[0]
	for i in range(numSlices):
		oneImage = imageStack[i,:,:]
		try:
			thisThresh = skimage.filters.threshold_otsu(oneImage)
			thresholdStack[i,:,:] = oneImage >= thisThresh # returning pixels ABOVE threshold
			if np.sum(thresholdStack[i,:,:]) == thresholdStack[i,:,:].shape[0] * thresholdStack[i,:,:].shape[1]:
				if verbose: print('  error: threshold_otsu all ones for slice:', i)
				thresholdStack[i,:,:] = 0
		except (ValueError) as e:
			if verbose: print('  my exception in threshold_otsu() slice', i, 'e:', e)
			
	return thresholdStack
		
def threshold_min(imageStack, min=None, max=None):
	"""
	min: return image stack where pixels are srictly greater than min
	"""
	if min is not None:
		thresholdStack = np.where(imageStack>min, 1, 0)
	#if max is not None:
	#	thresholdStack = np.where(thresholdStack<min, 1, 0)
	return thresholdStack.astype(np.uint8)

def threshold_remove_lower_percent2(imageStack, removeBelowThisPercent=0.06):
	"""
	REMOVE BELOW THRESHOLD, OTHERS STAY IN TACT
	
	Parameters:
		imageStack: numpy ndarray of shape (slice,x,y)
		removeBelowThisPercent: specifies the lower percent of pixel intensities to remove
			if removeBelowThisPercent = 0.1 then remove lower 10% of pixel intensities
	Returns:
		Binary threshold stack, same shape as imageStack, with foreground=1 and background(=0
	"""	
	print('  .threshold_remove_lower_percent2() removeBelowThisPercent:', removeBelowThisPercent)

	thresholdStack = imageStack.copy() # put the binary thresholded stack in here
	numSlices = thresholdStack.shape[0]
	for i in range(numSlices):
		oneImage = imageStack[i,:,:]
		theMin = np.nanmin(oneImage)
		theMax = np.nanmax(oneImage)
		theIntensityRange = theMax- theMin
		removeBelowThisIntensity = theIntensityRange * removeBelowThisPercent # lower percent intensity
		#removeBelowThisIntensity = int(removeBelowThisIntensity) # make sure it is an int(), image intensities are always int()	
		thresholdStack[i,:,:] = np.where(oneImage<=removeBelowThisIntensity, 0, oneImage)
	return thresholdStack

def threshold_remove_lower_percent(imageStack, removeBelowThisPercent=0.06):
	"""
	Parameters:
		imageStack: numpy ndarray of shape (slice,x,y)
		removeBelowThisPercent: specifies the lower percent of pixel intensities to remove
			if removeBelowThisPercent = 0.1 then remove lower 10% of pixel intensities
	Returns:
		Binary threshold stack, same shape as imageStack, with foreground=1 and background(=0
	"""	
	print('  .threshold_remove_lower_percent() removeBelowThisPercent:', removeBelowThisPercent)

	thresholdStack = imageStack.copy() # put the binary thresholded stack in here
	numSlices = thresholdStack.shape[0]
	for i in range(numSlices):
		oneImage = imageStack[i,:,:]
		theMin = np.nanmin(oneImage)
		theMax = np.nanmax(oneImage)
		theIntensityRange = theMax- theMin
		removeBelowThisIntensity = theIntensityRange * removeBelowThisPercent # lower percent intensity
		#removeBelowThisIntensity = int(removeBelowThisIntensity) # make sure it is an int(), image intensities are always int()	
		thresholdStack[i,:,:] = np.where(oneImage<=removeBelowThisIntensity, 0, 1)
	return thresholdStack

def labelMask(thresholdStack, verbose=False):
	"""
	label connected components in a mask
	"""
	
	if verbose: print('  .', 'labelMask()')

	#
	# erode
	# originally did this to try and islate large label as one object ... does not work
	#iterations = 3 # NO !!! we are keeping too much of large vessel
	# this step makes it so we do not include spots (in endocardium)
	
	#border_value = 1
	#iterations = 2
	#erodedStack = scipy.ndimage.morphology.binary_erosion(thresholdStack, structure=None, border_value=border_value, iterations=iterations).astype(np.uint8)
	
	erodedStack = thresholdStack

	#
	# label the stack
	structure = (3,3,3)
	myStructure = np.ones(structure, dtype=np.uint8)
	labeledStack, numLabels = scipy.ndimage.label(erodedStack, structure=myStructure)
	labeledStack = labeledStack.astype(np.uint16) # assuming we might have more than 2^8 labels (often 2^16 is not enough)
	if verbose: print('    morphology.labelMask() numLabels:', numLabels)
	
	'''
	#
	loc = scipy.ndimage.find_objects(labeledStack)
	
	labelSizeList = []
	for i in range(numLabels):
		#labelNumber = i + 1
		
		tmpLoc = loc[i]

		# this is probably slow, how do i count number of pixels in label i?
		tmpStack = labeledStack[tmpLoc] # tmpStack is a very small stack with just this label
		numPixelsInLabel = np.count_nonzero(tmpStack)
		
		labelSizeList.append(numPixelsInLabel)

	# get the index to labels sorted by size
	reverseIdx = np.argsort(labelSizeList).tolist() # reverse sort, gives us indices
	reverseIdx.reverse() # in place
	reverseIdx = [tmpIdx+1 for tmpIdx in reverseIdx] # need to add one because labels are not 0,1,2 but 1,2,3
	
	labelSizeList = sorted(labelSizeList, reverse=True)
		
	largeLabelStack = thresholdStack.copy()
	largeLabelStack[:] = 0 # fill in with labels size > removeSmallerThan

	keepLargestLabel = 10 # keep this number of largest labels
	for i in range(keepLargestLabel):
		labelIdx = reverseIdx[i]
		numPixels = labelSizeList[i]
		
		print('  idx:', i, 'label #', reverseIdx[i], 'pixels:', labelSizeList[i])

		largeLabelStack[labeledStack == labelIdx] = 1
		
	'''

	#iterations = 2
	#erodedStack = scipy.ndimage.morphology.binary_dilation(thresholdStack, structure=None, border_value=border_value, iterations=iterations).astype(np.uint8)
	
	#return labeledStack, largeLabelStack
	return labeledStack

def removeSmallLabels2(labeledStack, removeSmallerThan=20, timeIt=False, verbose=False):
	"""
	remove small labels from labeledStack and put in labeledStackRemoved
	
	Return:
		returnLabels: remaining labels
		returnSmallLabels: removed labels
		labelIndices: list of original labels
		labelCounts: list of counts for original labels
	"""
	
	if timeIt:
		myTimer = bimpy.util.bTimer('bimpy.util.morphology.removeSmallLabels2')
	
	returnLabels = labeledStack.copy()

	returnSmallLabels = labeledStack.copy()
	#returnSmallLabels[:] = 0
	
	labelIndices, labelCounts = np.unique(labeledStack, return_counts=True)

	removedCount = 0
	
	removeList = []
	keepList = []
	
	for idx, labelIdx in enumerate(labelIndices):
		#print('removeSmallLabels2() idx:', idx, 'labelIdx:', labelIdx, 
		#		'labelCounts[idx]:', labelCounts[idx], 'labelCounts[labelIdx]:', labelCounts[labelIdx])
		labelSize = labelCounts[idx]
		if labelSize < removeSmallerThan:
			#print('  removing')
			
			removeList.append(idx) # remove label number 'idx'
			
			# remove
			#returnLabels[labeledStack == idx] = 0
			
			# add
			#returnSmallLabels[labeledStack == idx] = idx
			
			removedCount += 1
		else:
			keepList.append(idx)
						
	keepMatrix = np.isin(labeledStack, keepList)
	removeMatrix = np.isin(labeledStack, removeList)
	
	returnLabels[removeMatrix] = 0
	returnSmallLabels[keepMatrix] = 0
	
	if verbose: print('removeSmallLabels2() removed', removedCount, 'labels')
	
	if timeIt:
		myTimer.elapsed()

	return returnLabels, returnSmallLabels, labelIndices, labelCounts
		
def removeSmallLabels(labelStack, removeSmallerThan=20, verbose=False):
	"""
	When we have many small labels >5000, removing them gets slow
	Instead we will start empty and add large labels
	
	algorithm:
	
	labelIndices, labelCounts = np.unique(a, return_counts=True)
	
	"""
	print('  .removeSmallLabels() removeSmallerThan:', removeSmallerThan, '... please wait ...')
	
	if verbose: _printStackParams('input labels', labelStack)

	# Array containing objects defined by different labels. Labels with value 0 are ignored.
	loc = scipy.ndimage.find_objects(labelStack) #
	
	#print('  ', len(loc), 'labels') # labeled object 103 is at index 103 (0/background is not in labels)
		
	retStack2 = labelStack.copy()
	retStack = labelStack.copy()
	retStack[:] = 0 # fill in with labels size > removeSmallerThan
	#retStack = retStack.astype(np.uint8)
	
	numLabels = len(loc)
	
	labelSizeList = []
	#removeSliceList = []
	smallCount = 0 # count really small labels
	numAdded = 0
	
	labelIndices, labelCounts = np.unique(a, return_counts=True)
	
	for i in range(numLabels):

		tmpLoc = loc[i]

		# this is probably slow, how do i count number of pixels in label i?
		tmpStack = labelStack[tmpLoc]
		numPixelsInLabel = np.count_nonzero(tmpStack)
		
		labelSizeList.append(numPixelsInLabel)
		
		# we start empty and add large labels
		if numPixelsInLabel <= removeSmallerThan:
			smallCount += 1
		if numPixelsInLabel > removeSmallerThan:
			retStack[labelStack == i+1] = i + 1 # add
			#removeSliceList.append(tmpLoc)
			retStack2[labelStack == i+1] = 0 # remove
			numAdded += 1
	
	# does not work
	#retStack[removeSliceList] = 0
	
	print('  ', len(loc), 'original labels, number of large labels:', numAdded, 'smallCount', smallCount)
	
	#
	# print the 50 largest labels
	# REMEMBER: labels go from 1,2,3 NOT 0,1,2 !!!!!!!!!!!
	reverseIdx = np.argsort(labelSizeList) # reverse sort, gives us indices
	#print('reverseIdx0:', type(reverseIdx), reverseIdx.dtype, reverseIdx.shape)
	reverseIdx = reverseIdx.tolist()
	#print('reverseIdx1:', type(reverseIdx), reverseIdx[0:10])
	# increment by 1, labels do not start at 0, they start at 1
	reverseIdx = [int(npIdx)+1 for npIdx in reverseIdx]
	#print('reverseIdx2:', reverseIdx[-50:])
	reverseIdx.reverse()	
	#print('reverseIdx3:', reverseIdx[0:50])

	#print('labelSizeList9:', labelSizeList[0:50])
	labelSizeList_sorted = sorted(labelSizeList, reverse=True)
	#print('labelSizeList1:', labelSizeList[0:50])

	# print label size from largest to smallest
	if verbose:
		printNumLabels = min(len(loc), 10)
		for i in range(printNumLabels):
			print('   label idx:', reverseIdx[i], 'size:', labelSizeList_sorted[i])
		
	'''
	# not very informative as we have so many low pixel count labels
	g = sns.distplot(labelSizeList, kde=False, rug=True)
	g.axes.set_yscale('log')
	plt.show()
	'''
	
	if verbose: _printStackParams('output', retStack)

	return retStack, retStack2, labelSizeList

def euclidean_distance_transform(maskStack, hullMask=None, scale=(1,1,1)): #, includeDistanceLessThan=5):	
	
	print('  .euclidean_distance_transform() scale:', scale, '... please wait')
	
	edtMask = maskStack.copy().astype(float)

	#
	# only accept maskStack pixels in hullMask
	# do this after
	
	#
	# invert the mask, edt will calculate distance from 0 to 1
	edtMask[edtMask==1] = 10
	edtMask[edtMask==0] = 1
	edtMask[edtMask==10] = 0

	distanceMap = scipy.ndimage.morphology.distance_transform_edt(edtMask, sampling=scale, return_distances=True)
	
	distanceMap = distanceMap.astype(np.float32) # both (matplotlib, imagej) do not do float16 !!!

	# only accept edt that is also in hullMask
	if hullMask is not None:
		distanceMap[hullMask==0] = np.nan
	
	_printStackParams('output edt', distanceMap)

	return distanceMap

