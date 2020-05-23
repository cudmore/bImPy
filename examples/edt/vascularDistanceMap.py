"""
Robert Cudmore
20200429

	Usage:
		Given an original .oir, open _ch1.tif and _ch2.tif
		
	for thresholding, see:
		https://scikit-image.org/docs/0.13.x/auto_examples/xx_applications/plot_thresholding.html

	Notes:
		Fiji has no float 16 datatype, must use float 64 for it to be valid fiji stack
"""

import os, sys, time
import argparse
import numpy as np
from collections import OrderedDict

import napari

#from skimage.filters import threshold_otsu, threshold_local
import skimage.filters # threshold_otsu, threshold_local

import scipy

#from scipy.ndimage.morphology import binary_closing
#from scipy.ndimage import label
#from scipy import ndimage

#import tifffile

#import edt

import matplotlib.pyplot as plt
import seaborn as sns

import bimpy

def mySliceKeeper(path):
	"""
	Specify range of slices to keep per .tif file
	
	todo: put this into a .csv file, load it and use numbers from that ???
	"""
	first = None
	last = None
	if path.find('20200420_distalHEAD_') != -1:
		first = 27
		last = 52 #26
	elif path.find('20200420_MID_') != -1:
		first = 17 #1
		last = 39 #16
	elif path.find('20200420_HEAD_') != -1:
		first = 23 #1
		last = 58 #22
	
	#
	#2019016
	if path.find('20190116__A01_G001_0007_') != -1:
		# 20190116__A01_G001_0007_ch1.tif
		first = 3
		last = 84 #26

	return first, last
	
def myLoadStack(path):
	print('  .myLoadStack() path:', path)
	#imageStack = tifffile.imread(path)
	imageStack, tiffHeaderDict = bimpy.util.bTiffFile.imread(path)
	
	#print('  1 imageStack:', imageStack.shape, imageStack.dtype, 'min:', np.min(imageStack), 'max:', np.max(imageStack))
	_printStackParams('input remove slices', imageStack)
	
	first, last = mySliceKeeper(path)
	if first is not None and last is not None:
		print('  ', 'keeping slices, first:', first, 'last:', last, 'num:', last-first+1)
		imageStack = imageStack[first:last+1,:,:] # need +1 because numpy [1:5] returns element 1..4
	else:
		print('  ', 'keeping all slices')
			
	#print('  2 imageStack:', imageStack.shape, imageStack.dtype, 'min:', np.min(imageStack), 'max:', np.max(imageStack))
	_printStackParams('output remove slices', imageStack)

	#numSlices = imageStack.shape[0]
	
	return imageStack, tiffHeaderDict

def myMedianFilter(imageStack, size=(2,2,2)):
	"""
	see: https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.median_filter.html
	"""
	print('  .myMedianFilter() size:', size, '... please wait')
	_printStackParams('input', imageStack)
		
	startTime = time.time()
	
	result = scipy.ndimage.median_filter(imageStack, size=size)
	
	_printStackParams('output', result)

	stopTime = time.time()
	print('    myMedianFilter took', round(stopTime-startTime,2), 'seconds')
	
	return result
	
def myThreshold_min_max2(imageStack, min=None, max=None):
	
	print('  .', 'myThreshold_min_max()')
	
	'''
	theMin = np.nanmin(imageStack)
	theMax = np.nanmax(imageStack)
	
	min = (theMax-theMin) * 0.1 # lower 10 percent
	min = int(min)
	
	if min is not None:
		thresholdStack = np.where(imageStack>min, 1, 0)
	#if max is not None:
	#	thresholdStack = np.where(thresholdStack<min, 1, 0)
	'''
	
	thresholdStack = imageStack.copy()
	thresholdStack[:] = 0
	numSlices = thresholdStack.shape[0]
	for i in range(numSlices):
		oneSlice = imageStack[i,:,:]
		theMin = np.nanmin(oneSlice)
		theMax = np.nanmax(oneSlice)
		'''
		myScale = 0.1
		if theMax < 165:
			myScale = 0.05
		'''
		myScale = 0.06
		min = (theMax-theMin) * myScale # lower 10 percent
		min = int(min)
	
		#print('  i:', i, 'theMin:', theMin, 'theMax:', theMax, 'myScale:', myScale, 'min:', min)
		
		thresholdStack[i,:,:] = np.where(oneSlice>min, 1, 0)
		
	return thresholdStack.astype(np.uint8)

def myThreshold_min_max(imageStack, min=None, max=None):
	"""
	"""
	print('  .myThreshold_min_max() min:', min)
	_printStackParams('input', imageStack)

	if min is not None:
		thresholdStack = np.where(imageStack>min, 1, 0)
	#if max is not None:
	#	thresholdStack = np.where(thresholdStack<min, 1, 0)

	_printStackParams('output', thresholdStack)

	return thresholdStack

def myThreshold_Otsu(imageStack):
	"""
	todo: where did 3d otsu go?
	"""
	print('  .myThreshold_Otsu() ... no parameters using Otsu')
	_printStackParams('input', imageStack)

	thresholdStack = imageStack.copy()
	thresholdStack[:] = 0
	numSlices = thresholdStack.shape[0]
	for i in range(numSlices):
		oneSlice = imageStack[i,:,:]
		try:
			globalThreshold = skimage.filters.threshold_otsu(oneSlice)
			'''
			block_size = 7 # must be odd
			globalThreshold = skimage.filters.threshold_local(oneSlice, block_size=block_size)
			'''
			thresholdStack[i,:,:] = oneSlice > globalThreshold
		except (ValueError) as e:
			print('  exception in myThreshold_Otsu() at slice:', i, e)
	
	thresholdStack = thresholdStack.astype(np.uint8)
	_printStackParams('output', thresholdStack)
	
	return thresholdStack

def myThreshold_Local(imageStack, block_size=5):
	"""
	todo: where did 3d otsu go?
	
	block_size: Odd size of pixel neighborhood which is used to calculate the threshold value (e.g. 3, 5, 7, …, 21, …).
	
	this filter is overly complicated
	filter returns: Threshold image. All pixels in the input image higher than the corresponding pixel in the threshold image are considered foreground.
	"""
	
	#print('\n\nWARNING myThreshold_Local() is not working\n\n')
	
	print('  .myThreshold_Local() block_size:', block_size)
	_printStackParams('input', imageStack)

	thresholdStack = imageStack.copy()
	thresholdStack[:] = 0
	numSlices = thresholdStack.shape[0]
	for i in range(numSlices):
		oneSlice = imageStack[i,:,:]
		try:
			adaptive_thresh = skimage.filters.threshold_local(oneSlice, block_size=block_size,method='median')
		except (ValueError) as e:
			print('  exception in myThreshold_Local() at slice:', i, e)
		# tricky !!!
		thresholdStack[i,:,:] = imageStack[i,:,:] > adaptive_thresh
	#thresholdStack[thresholdStack==255] = 1
	_printStackParams('output', thresholdStack)
	
	return thresholdStack

def myFillHoles(maskStack):
	"""
	todo: This is return first/last slice as all 0 !!!!!!!!!!
	
	see: https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.ndimage.morphology.binary_fill_holes.html
	"""
	
	print('  .myFillHoles()')
	
	_printStackParams('input', maskStack)

	retStack = maskStack.copy()
	
	# first dilate
	retStack = scipy.ndimage.morphology.binary_dilation(retStack, structure=None, iterations=1).astype(np.uint8)

	#
	# in 3d
	retStack = scipy.ndimage.morphology.binary_fill_holes(retStack).astype(np.uint8)
	
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
	retStack = scipy.ndimage.morphology.binary_erosion(retStack, structure=None, iterations=1).astype(np.uint8)

	_printStackParams('output', retStack)
	
	return retStack

# don't use ?
def myClosing(maskStack, structure = (3,5,5)):
	"""
	Fill holes

	See:
		https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.ndimage.morphology.binary_closing.html
		see: https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.ndimage.morphology.binary_fill_holes.html
	"""
	
	iterations = 2
	
	print('  .myClosing() structure:', structure)
		
	# see: https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.ndimage.morphology.generate_binary_structure.html
	myStructure = np.ones(structure, dtype=np.int)

	'''
	rank = 3 # corresponds to 3d stack
	connectivity = 3 # when connectivity==rank, all connected
	structure = scipy.ndimage.generate_binary_structure(rank, connectivity)
	print('  structure:', structure.shape)
	print('  structure:', structure)
	'''

	_printStackParams('input', maskStack)

	retStack = scipy.ndimage.morphology.binary_closing(maskStack,
		iterations=iterations,
		structure=myStructure) 
	
	retStack = retStack.astype(np.uint8)
	_printStackParams('output', retStack)
	
	# removed 20200506 ????
	#retStack[retStack == 1] = 1
	
	return retStack

def myLabel(imageStack, structure=(3,3,3)):
	"""
	
	I was using 26 connectivity, a 3x3x3 cube of 1's with the center voxel set to 0
	
	see: https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.label.html
	"""

	print('  .myLabel() structure:', structure)
	_printStackParams('input myLabel', imageStack)

	myStructure = np.ones(structure, dtype=np.uint8)
	retStack, numLabels = scipy.ndimage.label(imageStack, structure=myStructure)
	
	retStack = retStack.astype(np.uint16) # assuming we might have more than 256 or 2^8 labels
	
	print('  ', 'numLabels:', numLabels)
	_printStackParams('output myLabel', retStack)

	return retStack

def myRemoveSmallLabels(labelStack, removeSmallerThan=20):
	"""
	When we have many small labels >5000, removing them gets slow
	Instead we will start empty and add large labels
	"""
	print('  .myRemoveSmallLabels() removeSmallerThan:', removeSmallerThan, '... please wait ...')
	
	_printStackParams('input labels', labelStack)

	# Array containing objects defined by different labels. Labels with value 0 are ignored.
	loc = scipy.ndimage.find_objects(labelStack) #
	
	print('  ', len(loc), 'labels') # labeled object 103 is at index 103 (0/background is not in labels)
		
	retStack = labelStack.copy()
	retStack[:] = 0 # fill in with labels size > removeSmallerThan
	#retStack = retStack.astype(np.uint8)
	
	numLabels = len(loc)
	
	labelSizeList = []
	#removeSliceList = []
	smallCount = 0 # count really small labels
	numAdded = 0
	for i in range(numLabels):

		tmpLoc = loc[i]

		# this is probably slow, how do i count number of pixels in label i?
		tmpStack = labelStack[tmpLoc]
		numPixelsInLabel = np.count_nonzero(tmpStack)
		
		labelSizeList.append(numPixelsInLabel)
		
		if numPixelsInLabel <= removeSmallerThan:
			smallCount += 1
		if numPixelsInLabel > removeSmallerThan:
			retStack[labelStack == i+1] = i + 1
			#removeSliceList.append(tmpLoc)
			numAdded += 1
	
	# does not work
	#retStack[removeSliceList] = 0
	
	print('  ', 'numAdded:', numAdded, 'smallCount', smallCount)
	
	#
	# print the 50 largest labels
	# REMEMBER: labels go from 1,2,3 NOT 0,1,2 !!!!!!!!!!!
	reverseIdx = np.argsort(labelSizeList) # reverse sort, gives us indices
	print('reverseIdx0:', type(reverseIdx), reverseIdx.dtype, reverseIdx.shape)
	reverseIdx = reverseIdx.tolist()
	print('reverseIdx1:', type(reverseIdx), reverseIdx[0:10])
	# increment by 1, labels do not start at 0, they start at 1
	reverseIdx = [int(npIdx)+1 for npIdx in reverseIdx]
	print('reverseIdx2:', reverseIdx[-50:])
	reverseIdx.reverse()	
	print('reverseIdx3:', reverseIdx[0:50])

	print('labelSizeList9:', labelSizeList[0:50])
	labelSizeList_sorted = sorted(labelSizeList, reverse=True)
	print('labelSizeList1:', labelSizeList[0:50])

	for i in range(50):
		print('   label', reverseIdx[i], labelSizeList_sorted[i])
		
	'''
	# not very informative as we have so many low pixel count labels
	g = sns.distplot(labelSizeList, kde=False, rug=True)
	g.axes.set_yscale('log')
	plt.show()
	'''
	
	_printStackParams('output', retStack)

	return retStack
	
def myDistanceMap(maskStack, scale): #, includeDistanceLessThan=5):	
	
	print('  .myDistanceMap() scale:', scale, '... please wait')
	
	# invert the mask, edt will calculate distance from 0 to 1
	edtMask = maskStack.copy()
	edtMask[edtMask==1] = 10
	edtMask[edtMask==0] = 1
	edtMask[edtMask==10] = 0
	_printStackParams('input mask', edtMask)
	#sampling= (1,1,1) # todo: change this to voxel
	distanceMap = scipy.ndimage.morphology.distance_transform_edt(edtMask, sampling=scale, return_distances=True)
	
	# was for sami
	'''
	# make mask from edt from distance [0, 3] #todo: fill in voxel and do this in um/pixel
	distanceMask = distanceMap.copy()
	distanceMask[distanceMask > includeDistanceLessThan] = 0 # anyone beyond includeDistanceLessThan will be 0
	distanceMask[np.nonzero(distanceMask)] = 1 # remaining non-zero are 1
	'''
	
	distanceMap = distanceMap.astype(np.float32) # both (matplotlib, imagej) do not do float16 !!!
	
	_printStackParams('output edt', distanceMap)

	return distanceMap
	
def processChannel(channel, path, saveBaseName=None, forceSlidingZ=False, forceMedianKernel=None):
	print('=== processChannel() channel:', channel, 'saveBaseName:', saveBaseName, 'path:', path)
	
	stackDict = OrderedDict()
	stackDict['raw'] = None
	stackDict['slidingz'] = None
	stackDict['filtered'] = None
	stackDict['thresh'] = None
	stackDict['filled'] = None
	stackDict['labeled'] = None
	stackDict['largelabeled'] = None
	stackDict['mask'] = None
	stackDict['edt'] = None
	stackDict['edt2'] = None
	
	retDict = OrderedDict()
	retDict['algorithmParams'] = OrderedDict() # keep track of parameters
	retDict['results'] = OrderedDict() # keep track of rought results like # pixels in mask

	# load
	imageStack, tiffHeaderDict = myLoadStack(path)
	stackDict['raw'] = imageStack
	retDict['tiffHeader'] = tiffHeaderDict
	
	xVoxel = retDict['tiffHeader']['xVoxel']
	yVoxel = retDict['tiffHeader']['yVoxel']
	zVoxel = retDict['tiffHeader']['zVoxel']
	print('  xVoxel:', xVoxel, 'yVoxel:', yVoxel, 'zVoxel:', zVoxel)
	
	retDict['algorithmParams']['medianKernel'] = ''
	retDict['algorithmParams']['minThreshold'] = ''
	retDict['algorithmParams']['labelStructure'] = '' # to keep dicts in sync
	retDict['algorithmParams']['removeSmallerThan'] = ''
	
	if forceSlidingZ or channel == 2:
		slidingz = mySlidingZ(imageStack, upDownSlices=1)
		stackDict['slidingz'] = slidingz
		imageStack = slidingz
		stackDict['slidingz'] = slidingz
		
	# median filter
	if channel == 1:
		# hcn1
		if forceMedianKernel is not None:
			medianKernel = forceMedianKernel
		else:
			medianKernel = (3, 10,10)
	
	elif channel == 2:
		# vascular
		if forceMedianKernel is not None:
			medianKernel = forceMedianKernel
		else:
			medianKernel = (3, 5, 5)

	retDict['algorithmParams']['medianKernel'] = medianKernel
	medianFiltered = myMedianFilter(imageStack, size=medianKernel) # not returned
	stackDict['filtered'] = medianFiltered
	
	#
	# save median filter and load on next run
	#mySave(channel, saveBaseName, stackDict, tiffHeaderDict, saveTheseStacks=['filtered'])
	
	#
	# threshold to mask
	if channel == 1:
		minThreshold = 10
		thresholdStack = myThreshold_min_max(medianFiltered, min=minThreshold)
		retDict['algorithmParams']['minThreshold'] = minThreshold
	elif channel == 2:
		#thresholdStack = myThreshold_Otsu(medianFiltered) # no params
		thresholdStack = myThreshold_min_max(medianFiltered) # no params
	stackDict['thresh'] = thresholdStack
	
	if channel == 1:
		filledHolesStack = myFillHoles(thresholdStack)
		stackDict['filled'] = filledHolesStack
		
	if channel == 1:
		print('  .ch1 finalMask')
		_printStackParams('ch1 finalMask', filledHolesStack)
		stackDict['mask'] = filledHolesStack # 
		#retDict['algorithmParams']['closingStructure'] = ''
		retDict['algorithmParams']['labelStructure'] = '' # to keep dicts in sync
		retDict['algorithmParams']['removeSmallerThan'] = ''
		#retDict['algorithmParams']['keepDistancesLongerThan'] = ''
		# euclidean distance transform (all pixels to mask, will be overwritten later for 2 channels)
		scale=(zVoxel, xVoxel, yVoxel)
		edtStack = myDistanceMap(filledHolesStack, scale=scale)
		stackDict['edt'] = edtStack
	elif channel == 2:
		# fill holes with 'closing' which is dilatin followed by erosion
		#closingStructure = (3,5,5)
		#retDict['algorithmParams']['closingStructure'] = closingStructure
		#filledHolesStack = myClosing(thresholdStack, structure=closingStructure)
		filledHolesStack = myFillHoles(thresholdStack)
		stackDict['filled'] = filledHolesStack

		###
		###
		## Need initial label step to remove MASSIVE ARTERY !!!!!!!!!!
		## search fiji for "connected"
		##
		##
		## in fiji using raw stack
		"""
		- raw stack
		- IJ.run(imp, "Erode", "stack");
		- IJ.run(imp, "Connected Components Labeling", "connectivity=26 type=float");
		- result seems to be large vessel is just one label
		"""
		##
		##
		###
		###
		
		# label connected segments 1,2,3
		labelStructure = (3,3,3)
		retDict['algorithmParams']['labelStructure'] = labelStructure
		labelStack = myLabel(filledHolesStack, structure=labelStructure) # only vesel ch2
		stackDict['labeled'] = labelStack

		# remove small connected segments
		removeSmallerThan = 20 # units???
		retDict['algorithmParams']['removeSmallerThan'] = removeSmallerThan
		largeLabelStack = myRemoveSmallLabels(labelStack, removeSmallerThan=removeSmallerThan) # only vessel ch2
		stackDict['largelabeled'] = largeLabelStack
		
		# convert labeled stack back to binary mask
		finalMask = largeLabelStack.copy()
		finalMask[finalMask>0] = 1
		finalMask = finalMask.astype(np.uint8)
		print('  .ch2 finalMask')
		_printStackParams('ch2 finalMask', finalMask)
		stackDict['mask'] = finalMask # copy of filledHolesStack ???
	
		# euclidean distance transform
		scale=(zVoxel, xVoxel, yVoxel)
		edtStack = myDistanceMap(finalMask, scale=scale)
		stackDict['edt'] = edtStack
		#
		'''
		keepDistancesLongerThan = 2
		edtStack2 = edtStack.copy()
		#edtStack2 = edtStack2[edtStack2>keepDistancesLongerThan]
		edtStack2[~np.isnan(edtStack2)] = edtStack2[~np.isnan(edtStack2)] > keepDistancesLongerThan
		retDict['algorithmParams']['keepDistancesLongerThan'] = keepDistancesLongerThan
		stackDict['edt2'] = edtStack2
		_printStackParams('ch2 edt2', edtStack2)
		'''
		
	# basic analysis of final mask
	# this is not that usefull as my masks are so bad (especially the vascular (ch2) mask)
	voxelVolume = xVoxel * yVoxel * zVoxel
	numPixelsInStack = stackDict['mask'].size # could also use raw, all stackDict have same size
	numPixelsInMask = np.count_nonzero(stackDict['mask'])
	retDict['results']['voxelVolume'] = voxelVolume
	retDict['results']['nStack'] = numPixelsInStack
	retDict['results']['vStack'] = numPixelsInStack * voxelVolume
	retDict['results']['nMask'] = numPixelsInMask
	retDict['results']['vMask'] = numPixelsInMask * voxelVolume
	
	return stackDict, retDict
		
	
def _printStackParams(name, myStack):
	#print('  ', name, type(myStack), myStack.shape, myStack.dtype, 'dtype.char:', myStack.dtype.char, 'min:', np.min(myStack), 'max:', np.max(myStack))
	print('  ', name, myStack.shape, myStack.dtype, 'dtype.char:', myStack.dtype.char, 'min:', np.min(myStack), 'max:', np.max(myStack))

def mySlidingZ(imageStack, upDownSlices=1):
	print('  .mySlidingZ() upDownSlices:', upDownSlices)

	_printStackParams('input', imageStack)

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
		
	_printStackParams('output', slidingz)

	return slidingz
	
def myLoad(channel, saveBaseName, stackDict, tiffHeader, loadTheseStacks=None):
	if channel == 1:
		chStr = '_ch1_'
	elif channel == 2:
		chStr = '_ch2_'
	
def mySave(channel, saveBaseName, stackDict, tiffHeader, saveTheseStacks=None):
	print('  .mySave() channel:', channel, 'saveBaseName:', saveBaseName)
	if channel == 1:
		chStr = '_ch1_'
	elif channel == 2:
		chStr = '_ch2_'

	# original tiff header
	#tiffHeader = resultDict['tiffHeader']
	
	if saveTheseStacks is None:
		saveTheseStacks = ['raw', 'mask', 'edt', 'edt2']
		saveTheseStacks = ['raw', 'slidingz', 'filled', 'labeled', 'largelabeled', 'mask', 'edt', 'edt2']

	for idx, (stackName, stackData) in enumerate(stackDict.items()):
		if stackData is None:
			continue
		# todo: should be better way of doing this
		inSaveTheseStacks = False
		for thisStack in saveTheseStacks:
			if stackName.find(thisStack) != -1:
				inSaveTheseStacks = True
				break
				
		#print('stackName:', stackName, 'inSaveTheseStacks:', inSaveTheseStacks)
		if inSaveTheseStacks:
			path = saveBaseName + chStr + str(idx+1) + '_' + stackName + '.tif'
			shape = stackData.shape
			dtype = stackData.dtype
			dtypechar = stackData.dtype.char
			print('  saving', 'idx:', idx, stackName, shape, dtype, dtypechar, path)
			bimpy.util.bTiffFile.imsave(path, stackData, tifHeader=tiffHeader, overwriteExisting=True)	

	
def myMain(oirpath, forceSlidingZ=False, forceMedianKernel=None, forceChannel2Analysis=False):
	"""
	"""
	folderPath, oirFileName = os.path.split(oirpath)
	filenameNoExtension, tmpExtension = oirFileName.split('.')
	
	filenameNoExtension = filenameNoExtension.replace('_ch1', '')
	filenameNoExtension = filenameNoExtension.replace('_ch2', '')

	ch1Path = os.path.join(folderPath, filenameNoExtension + '_ch1.tif')
	ch2Path = os.path.join(folderPath, filenameNoExtension + '_ch2.tif')

	print('  ', 'oirpath:', oirpath)
	print('  ', 'ch1Path:', ch1Path)
	print('  ', 'ch2Path:', ch2Path)
	
	savePath = os.path.join(folderPath, 'analysis')
	if not os.path.isdir(savePath):
		os.mkdir(savePath)
	saveBaseName = os.path.join(savePath, filenameNoExtension)
	print('  ', 'saveBaseName:', saveBaseName)
	
	
	# for 1-channel stacks
	#forceSlidingZ=False
	#forceMedianKernel=None
	
	#
	# pre-process ch1 and ch2 (in processChannel, for vascular ch2 we will remove small segments/blobs)
	stackDict1 = None
	resultDict1 = None
	stackDict2 = None
	resultDict2 = None
	if os.path.isfile(ch1Path):
		tmpChannel = 1
		if forceChannel2Analysis:
			tmpChannel = 2
		stackDict1, resultDict1 = processChannel(tmpChannel, ch1Path, saveBaseName=saveBaseName, forceSlidingZ=forceSlidingZ, forceMedianKernel=forceMedianKernel)
	if os.path.isfile(ch2Path):
		stackDict2, resultDict2 = processChannel(2, ch2Path, saveBaseName=saveBaseName, forceSlidingZ=forceSlidingZ, forceMedianKernel=forceMedianKernel)

	# 
	# make edt of values in ch1 mask
	if stackDict1 is not None and stackDict2 is not None:
		print('=== making euclidean distance transform for vasculature and grabbing distance values that are in hcn1 mask')
		these_hcn1_pixels = stackDict1['mask']==1 # pixels in hcn1 mask
		_printStackParams('these_hcn1_pixels', these_hcn1_pixels)
		edtFinal = stackDict2['edt'].copy()
		edtFinal[:] = np.nan
		edtFinal[these_hcn1_pixels] = stackDict2['edt'][these_hcn1_pixels]	# grab hcn1 pixels from vascular edt
		stackDict1['edt'] = edtFinal
		_printStackParams('  ch1 edt', edtFinal)
		# does not work? I end up losing the 3d into 1d?
		'''
		edtFinal2 = edtFinal.copy()
		keepDistancesLongerThan = 2
		#edtFinal2 = edtFinal2[edtFinal2>keepDistancesLongerThan]
		edtFinal2[~np.isnan(edtFinal2)] = edtFinal2[~np.isnan(edtFinal2)] > keepDistancesLongerThan
		stackDict1['edt2'] = edtFinal2
		_printStackParams('  ch1 edt2', edtFinal2)
		'''

	#
	# append final mask volume information
	
	#
	# save results
	print('=== saving results')
	if stackDict1 is not None:
		mySave(1, saveBaseName, stackDict1, resultDict1['tiffHeader'])
	if stackDict2 is not None:
		mySave(2, saveBaseName, stackDict2, resultDict2['tiffHeader'])
	
	#
	# merge ordered dictionaries from ['algorithmParams'] and ['tiffHeader']
	# this is super cryptic, not to be read by other humans
	#myDictList = OrderedDict(list(d1.items()) + list(d2.items())) #[resultDict1, resultDict2]
	myDictList = []
	if resultDict1 is not None:
		saveDict = OrderedDict(list(resultDict1['tiffHeader'].items()) + list(resultDict1['algorithmParams'].items()) + list(resultDict1['results'].items()))
		myDictList.append(saveDict)
	if resultDict2 is not None:
		saveDict = OrderedDict(list(resultDict2['tiffHeader'].items()) + list(resultDict2['algorithmParams'].items()) + list(resultDict2['results'].items()))
		myDictList.append(saveDict)
	
	csvFile = saveBaseName + '_results.csv'
	print('=== saving csvFile:', csvFile)
	bimpy.util.dictListToFile(myDictList, csvFile)
	
	stopTime = time.time()
	print(__file__, 'finished in', round(stopTime-startTime,2), 'seconds')

	#
	# todo: post analysis
	# 1) volume of masks
	# 2) write another file to get Skan skel !!!
	# 3) for edt, we want (i) mean +/- std but ALSO reload edt and plot histograms!!!
	
	#
	# show in napari ... use myNapari2.py instead ...
	#print('showing napari')
	#myNapari(resultDict1, resultDict2)
	
	print('view with edtNapari.py')

def batch(pathToBatchFile):
	"""
	not working
	"""
	if not os.path.isfile(pathToBatchFile):
		print('error: vascularDistanceMap.runBatch did not find file:', pathToBatchFile)
		return
	fileList = bimpy.util.getFileListFromFile(pathToBatchFile)
	for file in fileList:
		print(file)
		
if __name__ == '__main__':
	startTime = time.time()

	parser = argparse.ArgumentParser(description = 'Process 2 channel hcn1 and vascular files into edt')
	parser.add_argument('oirpath', nargs='*', default='', help='path to .oir file')
	args = parser.parse_args() # args is a list of command line arguments

	if len(args.oirpath)>0:
		oirpath = args.oirpath[0]		
	else:
		oirpath = '/Users/cudmore/box/data/nathan/20200420/20200420_HEAD_.oir' #really bad results
		oirpath = '/Users/cudmore/box/data/nathan/20200420/20200420_MID_.oir'
		oirpath = '/Users/cudmore/box/data/nathan/20200420/20200420_distalHEAD_.oir'

		# in vivo
		#oirpath = '/Users/cudmore/box/data/nathan/20200420/invivo/20190613__0028.tif'
		
		# other data from nathan
		#oirpath = '/Users/cudmore/box/data/nathan/20200122-gelatin/20200122__0001.tif'
		
	#
	# for 2-channel hcn4 + vasc
	#myMain(oirpath)
	
	# for 1-channel vasculature only
	forceSlidingZ = True
	forceMedianKernel = (5,5,3)
	myMain(oirpath, forceSlidingZ=forceSlidingZ, forceMedianKernel=forceMedianKernel, forceChannel2Analysis=True)
	
