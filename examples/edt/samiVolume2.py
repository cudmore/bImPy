"""
Robert Cudmore
20200429

	Mask each raw .tif with 3x masks (full, eroded, ring)
	
	for thresholding, see:
		https://scikit-image.org/docs/0.13.x/auto_examples/xx_applications/plot_thresholding.html
		
	Notes:
		Fiji has no float 16 datatype, must use float 64 for it to be valid fiji stack
		
"""

import os, sys, time, json
import csv
import numpy as np
from collections import OrderedDict

import napari

from skimage.filters import threshold_otsu, threshold_local

#from scipy.ndimage.morphology import binary_closing
from scipy.ndimage import label
from scipy import ndimage
from scipy.ndimage import morphology

import scipy

#import edt

import tifffile

import bimpy

def myGaussianFilter(imageStack, sigma=(2,2,2)):
	"""
	see: https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html
	"""
	print('myGaussianFilter() ... please wait')
	result = ndimage.gaussian_filter(imageStack, sigma=sigma)
	return result

def myMedianFilter(imageStack, size=(2,2,2)):
	"""
	see: https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.signal.medfilt.html
	"""
	print('myMedianFilter() ... please wait')
	result = scipy.signal.medfilt(imageStack, kernel_size=size).astype(np.uint8)
	return result

def myThreshold_Otsu(imageStack):
	"""
	"""
	print('myThreshold()')
	print('  imageStack:', imageStack.shape, imageStack.dtype, 'min:', np.min(imageStack), 'max:', np.max(imageStack))

	thresholdStack = imageStack.copy()
	thresholdStack[:] = 0
	numSlices = thresholdStack.shape[0]
	for i in range(numSlices):
		oneSlice = imageStack[i,:,:]
		try:
			globalThreshold = threshold_otsu(oneSlice)
			thresholdStack[i,:,:] = oneSlice > globalThreshold
		except (ValueError) as e:
			print('  exception at slice:', i, e)
	thresholdStack[thresholdStack==1] = 1
	print('  thresholdStack:', thresholdStack.shape, thresholdStack.dtype, 'min:', np.min(thresholdStack), 'max:', np.max(thresholdStack))
	
	return thresholdStack

def myThreshold_min_max(imageStack, min=None, max=None):
	if min is not None:
		thresholdStack = np.where(imageStack>min, 1, 0)
	#if max is not None:
	#	thresholdStack = np.where(thresholdStack<min, 1, 0)
	return thresholdStack.astype(np.uint8)

def myFillHoles(imageStack):
	"""
	see: https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.ndimage.morphology.binary_fill_holes.html
	"""
	
	print('myFillHoles()')
	
	retStack = morphology.binary_fill_holes(imageStack)
	retStack = retStack.astype(np.uint8)
	
	n = retStack.shape[0]
	for i in range(n):
		slice = retStack[i,:,:]
		retStack[i,:,:] = morphology.binary_fill_holes(slice).astype(np.uint8)
	'''
	structure = np.ones((3,25,25))
	retStack = morphology.binary_fill_holes(retStack, structure=structure)
	'''
	
	return retStack
	
# not used in sami analysis
def myClosing(imageStack, structure = (3,5,5)):
	"""
	Fill holes
	
	I was using (x,y,z)=(4,4,2)
	
	see:
		https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.ndimage.morphology.binary_closing.html
	"""
	
	iterations = 5
	print('myClosing() iterations:', iterations)
	
	# see: https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.ndimage.morphology.generate_binary_structure.html
	myStructure = np.ones(structure, dtype=np.int)
	rank = 3 #3 # corresponds to 3d stack
	connectivity = rank #3 # when connectivity==rank, all connected
	structure = ndimage.generate_binary_structure(rank, connectivity)
	
	'''
	print('  structure:', structure.shape)
	print('  structure:', structure)
	'''
	#retStack = morphology.binary_closing(imageStack, structure=myStructure) #.astype(np.int)
	retStack = morphology.binary_closing(imageStack, iterations=iterations, structure=structure) #.astype(np.int)
	
	retStack = retStack.astype(np.uint8)
	print('  ', retStack.shape, retStack.dtype, 'min:', np.min(retStack), 'max:', np.max(retStack))
	#retStack[retStack == 1] = 1 # todo: not needed
	
	return retStack

def myLabel(imageStack, structure=(3,3,3)):
	"""
	
	I was using 26 connectivity, a 3x3x3 cube of 1's with the center voxel set to 0
	
	see: https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.label.html
	"""

	print('myLabel()')
	print('  ', imageStack.shape, imageStack.dtype, 'min:', np.min(imageStack), 'max:', np.max(imageStack))

	myStructure = np.ones(structure, dtype=np.int)
	retStack, numLabels = label(imageStack, structure=myStructure)
	
	print('  numLabels:', numLabels)
	print('  ', retStack.shape, retStack.dtype, 'min:', np.min(retStack), 'max:', np.max(retStack))

	return retStack

def myDistanceMap(maskStack, scale=(1,1,1), includeDistanceLessThan=5):	
	#
	# try a distance map
	#edtMask = thresholdStack.copy()
	#edtMask = finalMask.copy()
	
	# invert the mask, edt will calculate distance from 0 to 1
	edtMask = maskStack.copy()
	edtMask[edtMask==1] = 10
	edtMask[edtMask==0] = 1
	edtMask[edtMask==10] = 0
	_printStackParams('edtMask', edtMask)
	#sampling= (1,1,1) # todo: change this to voxel
	distanceMap = scipy.ndimage.morphology.distance_transform_edt(edtMask, sampling=scale, return_distances=True)
	#results['distanceMap'] = distanceMap
	
	# make mask from edt from distance [0, 3] #todo: fill in voxel and do this in um/pixel
	distanceMask = distanceMap.copy()
	distanceMask[distanceMask > includeDistanceLessThan] = 0 # anyone beyond includeDistanceLessThan will be 0
	distanceMask[np.nonzero(distanceMask)] = 1 # remaining non-zero are 1
	# does not work
	#distanceMask[distanceMask <= includeDistanceLessThan] = 1 # order matters
	#distanceMask[distanceMask > includeDistanceLessThan] = 0
	#results['distanceMask'] = distanceMask.astype(np.uint8)

	return distanceMap.astype(np.float16), distanceMask.astype('uint8')
	
def _printStackParams(name, myStack):
	print(' ', name, type(myStack), myStack.shape, myStack.dtype, 'min:', np.min(myStack), 'max:', np.max(myStack))

def myNapari(results):
	print('myNapari()')
	#
	# napari
	#numLabels = np.max(labeledStack)
	#myScale = (5, 3, 3)
	myScale = (3, 1, 1)
	with napari.gui_qt():
		viewer = napari.Viewer(ndisplay=2)
		for k,v in results.items():
			minContrast = 0
			maxContrast = 1
			theMax = np.max(v)
			if theMax == 1:
				maxContrast = 1 # binary mask
			elif theMax>250:
				maxContrast = 60 # 8-bit image
			else:
				maxContrast = theMax + 1 # labeled stack
			colormap = 'gray'
			if k == 'distanceMap':
				colormap = 'inferno'
			elif k == 'imageStack':
				colormap = 'green'
			# colormap
			viewer.add_image(v, scale=myScale, contrast_limits=(minContrast,maxContrast), opacity=0.5, colormap=colormap, visible=False, name=k)
		
		'''
		# channel 2
		viewer.add_image(imageStack, scale=myScale, contrast_limits=(0, 60), visible=False, name='raw stack')
		viewer.add_image(thresholdStack, scale=myScale, contrast_limits=(0, 1), visible=False, name='thresholded')
		viewer.add_image(filledHolesStack, scale=myScale, contrast_limits=(0, 1), visible=False, name='filled holes')
		viewer.add_image(labeledStack, scale=myScale, contrast_limits=(0, numLabels+1), visible=False, name='labeled')
		viewer.add_image(finalMask, scale=myScale, contrast_limits=(0, 1), visible=False, name='final mask')
		viewer.add_image(erodedMask, scale=myScale, contrast_limits=(0, 1), visible=False, name='eroded mask')
		'''
    
def myVolume(path, doNapari=True):
	"""
	assuming path is a _ch2.tif
	"""
	
	if not os.path.isfile(path):
		print('myVolume() did not find path:', path)
		return None
		
	doMedian = True # for debugging
	doSave = True
	
	results = OrderedDict()

	folderPath, filename = os.path.split(path)
	fileNameNoExtension, tmpExt = filename.split('.')
	
	outPath = '/Users/cudmore/Desktop/samiVolume'
	
	#
	# save all analysis in a parallel directory tree
	tiffFileInfo = bimpy.util.getTiffFileInfo(path)
	
	xVoxel = tiffFileInfo['xVoxel']
	yVoxel = tiffFileInfo['yVoxel']
	zVoxel = tiffFileInfo['zVoxel']
	enclosingFolder1 = tiffFileInfo['enclosingFolder1'] # outermost folder
	enclosingFolder2 = tiffFileInfo['enclosingFolder2']
	enclosingFolder3 = tiffFileInfo['enclosingFolder3']
	enclosingPath3 = os.path.join(outPath, enclosingFolder3) # outPath !!!!!!!!!
	enclosingPath2 = os.path.join(enclosingPath3, enclosingFolder2)
	enclosingPath1 = os.path.join(enclosingPath2, enclosingFolder1)
	if not os.path.isdir(enclosingPath3):
		os.mkdir(enclosingPath3)
	if not os.path.isdir(enclosingPath2):
		os.mkdir(enclosingPath2)
	if not os.path.isdir(enclosingPath1):
		os.mkdir(enclosingPath1)

	baseSavePath = os.path.join(enclosingPath1, fileNameNoExtension)
	print('  baseSavePath:', baseSavePath)
	
	# load raw data
	print('loading path:', path)

	imageStack = tifffile.imread(path)
	results['imageStack'] = imageStack

	print('  imageStack:', xVoxel, yVoxel, zVoxel, imageStack.shape, imageStack.dtype, 'min:', np.min(imageStack), 'max:', np.max(imageStack))

	if doSave:
		tmpOutPath = baseSavePath + '.tif'
		tifffile.imsave(tmpOutPath, imageStack)
		
	#
	# filter raw image
	#
	startSeconds = time.time()
	medianParams = (3,11,11)
	loadedMedian = False
	if doMedian:
		'''
		medianPath = baseSavePath + '_median.tif'
		if os.path.isfile(medianPath):
			print('  LOADING MEDIAN FROM', medianPath)
			medianFilteredStack = tifffile.imread(medianPath)
			tiffFileInfo['medianParams'] = medianParams
			loadedMedian = True
		else:
			medianFilteredStack = myMedianFilter(imageStack, size=medianParams)
			tiffFileInfo['medianParams'] = medianParams
		'''
		medianFilteredStack = myMedianFilter(imageStack, size=medianParams)
		tiffFileInfo['medianParams'] = medianParams
	else:
		#
		# try and load median
		medianPath = baseSavePath + '_median.tif'
		if os.path.isfile(medianPath):
			print('  LOADING MEDIAN FROM', medianPath)
			medianFilteredStack = tifffile.imread(medianPath)
			tiffFileInfo['medianParams'] = medianParams
			loadedMedian = True
		'''
		else:
			# makes code fast, for debugging
			medianFilteredStack = imageStack.copy()
			tiffFileInfo['medianParams'] = (None,None,None)
		'''
	_printStackParams('medianFilteredStack', medianFilteredStack)
	results['medianFilteredStack'] = medianFilteredStack
	stopSeconds = time.time()
	print('  took', round(stopSeconds-startSeconds,2), 'seconds')
	#
	if doSave and not loadedMedian:
		tmpOutPath = baseSavePath + '_median.tif'
		tifffile.imsave(tmpOutPath, medianFilteredStack)
		
	#
	# threshold
	thresholdMin = 2
	thresholdMax = 255
	medianMask = myThreshold_min_max(medianFilteredStack, min=thresholdMin, max=thresholdMax)
	tiffFileInfo['thresholdMin'] = thresholdMin
	tiffFileInfo['thresholdMax'] = thresholdMax
	_printStackParams('medianMask', medianMask)
	results['medianMask'] = medianMask
	if doSave:
		tmpOutPath = baseSavePath + '_medianMask.tif'
		tifffile.imsave(tmpOutPath, medianMask)

	# distance map mask is too big, when we get ring mask it will be super biased
	includeDistanceLessThan = 2 * xVoxel #1
	distanceMap, distanceMask = myDistanceMap(medianMask, scale=(zVoxel, xVoxel, yVoxel), includeDistanceLessThan=includeDistanceLessThan)	
	_printStackParams('distanceMap', distanceMap)
	_printStackParams('distanceMask', distanceMask)
	tiffFileInfo['includeDistanceLessThan'] = includeDistanceLessThan
	results['distanceMap'] = distanceMap
	results['distanceMask'] = distanceMask
	if doSave:
		tmpOutPath = baseSavePath + '_distanceMap.tif'
		tifffile.imsave(tmpOutPath, distanceMap)
		#
		tmpOutPath = baseSavePath + '_distanceMask.tif'
		tifffile.imsave(tmpOutPath, distanceMask)
	
	# fill holes
	filledHolesMask = myFillHoles(distanceMask)
	_printStackParams('filledHolesMask', filledHolesMask)
	results['filledHolesMask'] = filledHolesMask
	# count the number of pixels
	nMask = filledHolesMask[np.nonzero(filledHolesMask)].size
	tiffFileInfo['nMask'] = nMask
	#
	if doSave:
		tmpOutPath = baseSavePath + '_filledHolesMask.tif'
		tifffile.imsave(tmpOutPath, filledHolesMask)

	# erode mask by um distance
	erodedIterations = 5
	erodedMask = morphology.binary_erosion(filledHolesMask, iterations=erodedIterations).astype(np.uint8) # returns a true/false mask?
	_printStackParams('erodedMask', erodedMask)
	tiffFileInfo['erodedIterations'] = erodedIterations
	results['erodedMask'] = erodedMask
	# count the number of pixels
	nEroded = erodedMask[np.nonzero(erodedMask)].size
	tiffFileInfo['nEroded'] = nEroded
	#
	if doSave:
		tmpOutPath = baseSavePath + '_erodedMask.tif'
		tifffile.imsave(tmpOutPath, erodedMask)
	
	#
	# ring/membrane mask
	ringMask = np.subtract(filledHolesMask, erodedMask)
	ringMask[ringMask == -1] = 0
	ringMask = ringMask.astype(np.uint8)
	_printStackParams('ringMask', ringMask)
	results['ringMask'] = ringMask
	# count the number of pixels
	nRing = ringMask[np.nonzero(ringMask)].size
	tiffFileInfo['nRing'] = nRing
	#
	if doSave:
		tmpOutPath = baseSavePath + '_ringMask.tif'
		tifffile.imsave(tmpOutPath, ringMask)
	
	tiffFileInfo['filePath'] = path
	
	print(json.dumps(tiffFileInfo, indent=4))

	if doNapari:
		myNapari(results)

	return tiffFileInfo
	
if __name__ == '__main__':

	dataPath = '/Users/cudmore/Sites/smMicrotubule/data'
	
	batchFileList = []
	batchFile = '/Users/cudmore/Sites/smMicrotubule/analysis/wt-female.txt'
	batchFileList.append(batchFile)
	batchFile = '/Users/cudmore/Sites/smMicrotubule/analysis/wt-male.txt'
	batchFileList.append(batchFile)
	batchFile = '/Users/cudmore/Sites/smMicrotubule/analysis/ko-female.txt'
	batchFileList.append(batchFile)
	batchFile = '/Users/cudmore/Sites/smMicrotubule/analysis/ko-male.txt'
	batchFileList.append(batchFile)

	# debugging
	#batchFileList = ['one-wt-female.txt']

	fileDictList = []
	for batchFile in batchFileList:
		fileList = bimpy.util.getFileListFromFile(batchFile)
	
		nFile = len(fileList)
		
		for fileNum, file in enumerate(fileList):
			print('*** file', fileNum+1, 'of', nFile, 'file:', file)
			# my condition file start with ../data/ todo: clean upp paths in condition file
			file = file.replace('../data/', '')
			file = os.path.join(dataPath,file)
			print(file)
			
			tiffFileInfo = myVolume(file, doNapari=False)
			if tiffFileInfo is not None:
				fileDictList.append(tiffFileInfo)

	dictListToFile(fileDictList, '/Users/cudmore/Desktop/volume-results.csv')