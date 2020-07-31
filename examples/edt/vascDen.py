"""

	Calculate vascular density by constructing a vascular mask in _finalMask.tif
	
	Usage
	
		python vascDen.py /Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0007_ch1.tif
		
	Output
		A number of .tif files all saved in folder analysis2/
		
		In particular _finalMask.tif
		
	Other code uses stackDict=myGetDefaultStackDict() to get names of _[key].tif that were saved
	
	After running this
		
	0) Edit the mask in Napari with (generates analysis2/ labeled_edited.tif)

		python vascDenNapari.py /Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0007_ch1.tif
	
	1) Run vascDenConvexHull.py to generate convex hull in analysis2/ _finalMask_hull.tif

		python vascDenConvexHull.py /Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0007_ch1.tif
		
	2) Run vascDenEDT.py to generate edt image (uses all 3 (labeled, labeled edited, hull) in analysis2/ _finalMask_edt.tif

		python vascDenEDT.py /Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0007_ch1.tif
		
"""

#%%###
import os, sys, math, time
import argparse
from collections import OrderedDict
from datetime import datetime

import numpy as np
import pandas as pd
import scipy

import napari

import bimpy

#from .vascDenNapari import myLabelEdit
import vascDenNapari

#%%#############################################################################
def _printStackParams(name, myStack):
	print('  ', name, myStack.shape, myStack.dtype, 'dtype.char:', myStack.dtype.char,
				'min:', round(np.min(myStack),2), 'max:', round(np.max(myStack),2), 'mean:', round(np.nanmean(myStack),2))

#%%###############################################################################
# mySave(saveBase, stackDict, tiffHeader, paramDict)
def mySave(saveBase, saveBase2, stackDict, tiffHeader, paramDict):
	"""
	saveBase: is like '/Users/cudmore/box/data/nathan/20200116/analysis2/20190116__A01_G001_0007_ch1'
	saveBase2: pass '' to not save
	paramDict: use this to pad data firstSLice/lastSlice for saveBase2
	"""
	print('  .', 'mySave() saveBase:', saveBase)
	
	saveTheseStacks = ['raw', 'finalMask', 'finalMask_edt', 'finalMask_hull', 'labeled']
	saveTheseStacks = ['raw', 'filtered', 'threshold0', 'threshold1', 'threshold', 'finalMask', 'finalMask_edt', 'finalMask_hull', 'labeled']
	
	#for idx, (k,v) in enumerate(stackDict.items()):
	for k,v in stackDict.items():
		# k in (raw, slidingz, ...)
		# v is a dict with keys (type, data)
		name = k
		
		if name not in saveTheseStacks:
			continue
		
		type = v['type']
		data = v['data']

		if data is None:
			if name == 'finalMask_hull':
				# saved in main myRun()
				#print('    .', 'WARNING: mySave() did find stack data for "', k, '"', 'need to calculate with scipy 1.4.1 using myConvexyHull.py')
				pass
			else:
				#print('  ', 'Warning: mySave() did find stack data for "', k, '"')
				pass
			continue
		
		#idxStr = '_' + str(idx) + '_'
		#savePath = saveBase + idxStr + k + '.tif'
		savePath = saveBase + '_' + k + '.tif'
		print('    ', name, 'savePath:', savePath)
		bimpy.util.bTiffFile.imsave(savePath, data, tifHeader=tiffHeader, overwriteExisting=True)	
		
		#
		# rebuild stack including all 0 images above/below firstSlice/lastSlice
		if saveBase2:
			#dataCopy = data.copy()
			firstSlice = paramDict['firstSlice'] - 1
			lastSlice = paramDict['lastSlice'] # needs to be relative to num slices
			
			origNumSlices = paramDict['zOrigPixel']
			
			padTop = firstSlice - 1
			padBottom = origNumSlices - lastSlice + 1
			
			dataPadded = np.pad(data, ((padTop,padBottom), (0,0), (0,0)), 'constant', constant_values=0)  
			savePath2 = saveBase2 + '_' + k + '.tif'
			print('    ', name, 'savePath2:', savePath2)
			bimpy.util.bTiffFile.imsave(savePath2, dataPadded, tifHeader=tiffHeader, overwriteExisting=True)	
		
################################################################################
def myGetDefaultStackDict():
	"""
	Using order here to save files with _1_, _2_, _3_, ...
	"""
	stackDict = OrderedDict()
	stackDict['raw'] = {'type': 'image', 'data': None}
	stackDict['slidingz'] = {'type': 'image', 'data': None}
	stackDict['filtered'] = {'type': 'image', 'data': None}
	stackDict['threshold0'] = {'type': 'image', 'data': None} # added while working on 20200518, remove lower % of image
	stackDict['threshold1'] = {'type': 'image', 'data': None} # image remaining after threshold_sauvola
	stackDict['threshold'] = {'type': 'mask', 'data': None} # added while working on cellDen.py
	stackDict['labeled'] = {'type': 'label', 'data': None}
	stackDict['small_labels'] = {'type': 'label', 'data': None}
	stackDict['finalMask'] = {'type': 'mask', 'data': None}
	stackDict['remainingRaw'] = {'type': 'image', 'data': None}
	stackDict['finalMask_hull'] = {'type': 'mask', 'data': None}
	stackDict['finalMask_edt'] = {'type': 'edt', 'data': None}

	return stackDict

def myGetDefaultParamDict():
	"""
	Using order here to save files with _1_, _2_, _3_, ...
	"""
	paramDict = OrderedDict()
	paramDict['analysisDate'] = ''
	paramDict['analysisTime'] = ''

	paramDict['algorithm'] = ''
	paramDict['channel'] = ''
	
	paramDict['zVoxel'] = ''
	paramDict['xVoxel'] = ''
	paramDict['yVoxel'] = ''

	paramDict['zOrigPixel'] = ''
	paramDict['xOrigPixel'] = ''
	paramDict['yOrigPixel'] = ''
	
	paramDict['zFinalPixel'] = ''
	paramDict['xFinalPixel'] = ''
	paramDict['yFinalPixel'] = ''

	paramDict['upDownSlices'] = ''
	paramDict['medianKernelSize'] = ''

	paramDict['thresholdAlgorithm'] = '' 
	paramDict['thresholdPercent'] = '' # for bimpy.util.morphology.threshold_remove_lower_percent

	paramDict['removeSmallerThan'] = ''
	paramDict['origNumLabels'] = ''
	paramDict['dilateFinalMaskIterations'] = ''

	paramDict['tiffHeader'] = ''
	paramDict['saveBase'] = ''
	paramDict['path'] = ''

	return paramDict
	
################################################################################
def updateMasterCellDB(masterFilePath, filename, paramDict):

	print('  .updateMasterCellDB() filename:', filename, 'masterFilePath:', masterFilePath)
	
	#
	# load
	df = pd.read_csv(masterFilePath, index_col='index')

	#
	# important
	df.index.name = 'index' 
	
	#
	# check that filename exists
	dfTmp = df.loc[df['uFilename'] == filename]
	if len(dfTmp) == 0:
		# append after baseFilename
		
		# find row with baseFilname
		
		baseFilename = filename.replace('_ch1.tif', '')
		baseFilename = baseFilename.replace('_ch2.tif', '')
		baseFilename = baseFilename.replace('_ch3.tif', '')

		# find the row with basefilename (e.g. without (_ch1.tif, _ch2.tif)
		baseFileRow = df.loc[df['uFilename'] == baseFilename]
		baseFileIndex = baseFileRow.index[0]
		
		#line = pd.DataFrame([[np.nan] * len(df.columns)], columns=df.columns)
		#df2 = pd.concat([df.iloc[:baseFileIndex], line, df.iloc[baseFileIndex:]]).reset_index(drop=True)

		newIdx = baseFileIndex + 0.5
		newRow = pd.DataFrame([[np.nan] * len(df.columns)], index=[newIdx], columns=df.columns)
		newRow['uFilename'] = filename
		df = pd.concat([df, newRow]).sort_index()
		df = df.reset_index(drop=True)
		
		print('  appending row', newIdx)

		'''
		print('df:')
		print(df)
		'''
		
		#print('  ERROR: updateMasterCellDB() did not find uFilename:', filename, 'in masterFilePath:', masterFilePath)
		#return
		
	for k,v in paramDict.items():
		if not k in df.columns:
			print('    *** updateMasterCellDB() is appending column named:', k)
			df[k] = ""
		
		df.loc[df['uFilename'] == filename, k] = str(v)
	
	'''
	print('df after')
	print(df)
	'''
		
	#
	# resave
	print('    updateMasterCellDB() is saving', masterFilePath)
	df.to_csv(masterFilePath, index_label='index')
	
################################################################################
def pruneStackData(masterFilePath, filename, stackData):
	"""
	prune stack slices by filename (row) and (firstslice, lastslice) specified in .csv file masterFilePath
	
	filename: full file name with _ch and .tif
	"""
	print('  .', 'pruneStackData() masterFilePath:', masterFilePath)
	if not os.path.isfile(masterFilePath):
		print('  error: pruneStackData() did not find masterFilePath:', masterFilePath)
		return None
	
	print('    pruneStackData() loading .csv to get (firstslice, lastslice) for uFilename:', filename, 'from masterFilePath:', masterFilePath)
	df = pd.read_csv(masterFilePath)

	uInclude = None
	numSlices = stackData.shape[0]
	firstSlice = None #0
	lastSlice = None #numSlices - 1
	#

	baseFilename = filename.replace('_ch1.tif', '')
	baseFilename = baseFilename.replace('_ch2.tif', '')
	baseFilename = baseFilename.replace('_ch3.tif', '')
		
	if df is not None:
		df2 = df.loc[df['uFilename'] == baseFilename, 'uFirstSlice']
		if df2.shape[0] == 0:
			print('  ERROR: did not find dfMasterCellDB uFilename:', baseFilename, 'uFirstSlice')
		else:
			#print('  .', 'reading from .csv line:')
			thisLineDF = df[df['uFilename'] == baseFilename]
			#print(thisLineDF)
			
			#
			# this is not working
			#
			
			# is it in uInclude
			tmpInclude = df.loc[df['uFilename'] == baseFilename, 'uInclude'].iloc[0]  
			if pd.notnull(tmpInclude):
				uInclude = int(tmpInclude)
				print('    read uFilename:', baseFilename, 'uInclude:', uInclude)
			else:
				print('    ERROR: did not find "uInclude" for uFilename:', baseFilename)
			
			# firstslice
			tmpFirstSlice = df.loc[df['uFilename'] == baseFilename, 'uFirstSlice'].iloc[0]  
			if pd.notnull(tmpFirstSlice):
				firstSlice = int(tmpFirstSlice)
				print('    read uFilename:', baseFilename, 'uFirstSlice:', firstSlice)
			else:
				print('    ERROR: did not find "uFirstSlice" for uFilename:', baseFilename)
			# lastslice
			tmpLastSlice = df.loc[df['uFilename'] == baseFilename, 'uLastSlice'].iloc[0]  
			if pd.notnull(tmpLastSlice):
				lastSlice = int(tmpLastSlice)
				print('    read uFilename:', baseFilename, 'uLastSlice:', lastSlice)
			else:
				print('    ERROR: did not find "uLastSlice" for uFilename:', baseFilename)
				
			# uVascThreshold
			
	else:
		print('ERROR: pruneStackData() did not read df from masterFilePath:', masterFilePath)
	
	if uInclude is None or firstSlice is None or lastSlice is None:
			stackData = None
	elif firstSlice > 0 and lastSlice < numSlices - 1:
		#print('  ', 'pruning stackData slices')
		_printStackParams(' from stackData', stackData)	
		stackData = stackData[firstSlice:lastSlice+1,:,:] # remember +1 !!!!!
		_printStackParams(' pruned stackData', stackData)	
	else:
		stackData = None
		
	return stackData, firstSlice, lastSlice
	
################################################################################
def setupAnalysis(path, trimPercent = 15, masterFilePath='master_cell_db.csv'):
	"""
	"""
	print('  setupAnalysis() path:', path)
	
	folderpath, filename = os.path.split(path)
	filenamenoextension, tmpExt = filename.split('.')
	
	savePath = os.path.join(folderpath, 'analysis2')
	saveBase = os.path.join(savePath, filenamenoextension)
	
	savePath2 = os.path.join(folderpath, 'analysis_full')
	saveBase2 = os.path.join(savePath2, filenamenoextension)
	
	channel = None
	if filename.endswith('_ch1.tif'):
		channel = 1
	elif filename.endswith('_ch2.tif'):
		channel = 2
	elif filename.endswith('_ch3.tif'):
		channel = 3
	
	#print('  savePath:', savePath)
	print('    channel:', channel, 'saveBase:', saveBase) # append _labeled.tif to this
	
	#
	# make output folder
	if not os.path.isdir(savePath):
		os.mkdir(savePath)
	if not os.path.isdir(savePath2):
		os.mkdir(savePath2)
	
	#
	# make a dictionary of dictionaries to hold (type, data) for each step
	stackDict = myGetDefaultStackDict()
	
	#
	# save (stack pixels, pruned stack pixels, analysis parameters, number of original labels)
	paramDict = myGetDefaultParamDict()
	
	paramDict['analysisDate'] = datetime.today().strftime('%Y%m%d')
	paramDict['analysisTime'] = datetime.now().strftime('%H:%M:%S')
	
	paramDict['channel'] = channel

	#
	# load
	print('    setupAnalysis() loading stack:', path)
	stackData, tiffHeader = bimpy.util.bTiffFile.imread(path)
	paramDict['tiffHeader'] = tiffHeader
	_printStackParams('  stackData', stackData)
	
	paramDict['zVoxel'] = tiffHeader['zVoxel']
	paramDict['xVoxel'] = tiffHeader['xVoxel']
	paramDict['yVoxel'] = tiffHeader['yVoxel']

	paramDict['zOrigPixel'] = stackData.shape[0]
	paramDict['xOrigPixel'] = stackData.shape[1] # rows
	paramDict['yOrigPixel'] = stackData.shape[2]
		
	#
	# trim
	trimPixels = math.floor( trimPercent * stackData.shape[1] / 100 ) # ASSUMING STACKS ARE SQUARE
	trimPixels = math.floor(trimPixels / 2)
	if trimPixels > 0:
		print('  trimming', trimPixels, 'lower/right pixels')
		_printStackParams('from', stackData)
		thisHeight = stackData.shape[1] - trimPixels
		thisWidth = stackData.shape[2] - trimPixels
		stackData = stackData[:, 0:thisHeight, 0:thisWidth]
		_printStackParams('to', stackData)
	else:
		print('  WARNING: not trimming lower/right x/y !!!')
		
	#
	# keep slices
	# will return None when user has not specified first/last
	stackData, firstSlice, lastSlice = pruneStackData(masterFilePath, filename, stackData) # can be None
	stackDict['raw']['data'] = stackData
	
	paramDict['firstSlice'] = firstSlice
	paramDict['lastSlice'] = lastSlice

	if stackData is not None:
		paramDict['zFinalPixel'] = stackData.shape[0]
		paramDict['xFinalPixel'] = stackData.shape[1] # rows
		paramDict['yFinalPixel'] = stackData.shape[2]

	paramDict['saveBase'] = saveBase
	paramDict['saveBase2'] = saveBase2 # to save analysis padded with 0, above firstSLice, below lastSlice

	return filename, paramDict, stackDict
	
################################################################################
def myRun(path, trimPercent, masterFilePath):
	"""
	My Doc String
	"""
	
	print('vascDen.myRun() path:', path)
	
	filename, paramDict, stackDict = setupAnalysis(path, trimPercent, masterFilePath=masterFilePath)
	
	if stackDict['raw']['data'] is None:
		print('=== *** === vascDen.myRun() aborting, got None stack data  ... this happens when setupAnalysis/pruneStackData does not find uFirst/uLast slice')
		return
		
	# set the algorithm
	paramDict['algorithm'] = 'vascDen'
	
	# get some local variables
	stackData = stackDict['raw']['data']
	tiffHeader = paramDict['tiffHeader']
	saveBase = paramDict['saveBase']
	saveBase2 = paramDict['saveBase2']
	
	#
	# algorithm
	#
	
	# sliding z
	upDownSlices = 1
	slidingz = bimpy.util.morphology.slidingZ(stackData, upDownSlices=upDownSlices)
	stackDict['slidingz']['data'] = slidingz
	paramDict['upDownSlices'] = upDownSlices
	
	# median filter
	medianKernelSize = (3,5,5)
	medianKernelSize = (2,3,3)
	filteredStack = bimpy.util.morphology.medianFilter(slidingz, kernelSize=medianKernelSize)
	stackDict['filtered']['data'] = filteredStack
	paramDict['medianKernelSize'] = medianKernelSize
	
	#
	# threshold
	if 0:
		thresholdPercent = 0.06
		thresholdStack = bimpy.util.morphology.threshold_remove_lower_percent(filteredStack, removeBelowThisPercent=thresholdPercent)
		paramDict['thresholdAlgorithm'] = 'threshold_remove_lower_percent'
		paramDict['thresholdPercent'] = thresholdPercent
	
	# trying otsu because data from 20200518 looks like there are 2 sets of intensities???
	# Algorithm:
	# 1) remove lower percent of pixels
	# 2) sauvola threshold to return pixel intensities above threshold
	# 3) sauvola again to make binary
	if 1:
		# 1) remove lower percentage of pixels
		thresholdPercent = 0.07 #0.05
		thresholdStack = bimpy.util.morphology.threshold_remove_lower_percent2(filteredStack, removeBelowThisPercent=thresholdPercent)
		paramDict['thresholdAlgorithm'] = 'threshold_remove_lower_percent'
		paramDict['thresholdPercent'] = thresholdPercent
		stackDict['threshold0']['data'] = thresholdStack.copy()
		
		# 2) sauvola, to get image above threshold
		# window_size is diameter (maybe the line that has both background and forground, e.g. cappillarry diameter?)
		window_size = 23 #23 #23 # must be odd
		k = 0.3 #0.34 # 0.2
		asImage = True # don't return binary, return image pixels above threshold
		thresholdImageStack = bimpy.util.morphology.threshold_sauvola(thresholdStack, asImage=asImage, window_size=window_size, k=k)
		paramDict['thresholdAlgorithm'] = 'threshold_sauvola'
		stackDict['threshold1']['data'] = thresholdImageStack.copy()
		
		# otsu (otsu is shit for tie2 labeling)
		# orignal
		#thresholdStack = bimpy.util.morphology.threshold_otsu(thresholdStack)
		#paramDict['thresholdAlgorithm'] = 'threshold_otsu'
		
		# using sauvola threshold image (not binary)
		#thresholdStack = bimpy.util.morphology.threshold_otsu(thresholdImageStack)
		#paramDict['thresholdAlgorithm'] = 'threshold_otsu'
		
		# 3) sauvola to make a binary
		window_size = 23 #23 #23 #23 # must be odd
		k = 0.2 #0.34 # 0.2
		asImage = False # don't return binary, return image pixels above threshold
		thresholdStack = bimpy.util.morphology.threshold_sauvola(thresholdStack, asImage=asImage, window_size=window_size, k=k)

	stackDict['threshold']['data'] = thresholdStack
	
	#
	# fill holes
	#filledThresholdStack = myFillHoles(thresholdStack)
	filledThresholdStack = thresholdStack
		
	#
	# label
	labeledStack = bimpy.util.morphology.labelMask(filledThresholdStack)
	
	removeSmallerThan = 80
	labeledStack, removedLabelStack = bimpy.util.morphology.removeSmallLabels(labeledStack, removeSmallerThan=removeSmallerThan)	
	origNumLabels = np.nanmax(labeledStack)
	print('        num labels after removing small:', origNumLabels)
	stackDict['labeled']['data'] = labeledStack
	stackDict['small_labels']['data'] = removedLabelStack
	paramDict['removeSmallerThan'] = removeSmallerThan
	paramDict['origNumLabels'] = origNumLabels # used in most subsequent steps

	#
	# final mask
	print('  .', 'making final mask from labeled')
	finalMask = stackData.copy()
	#_printStackParams('finalMask 1', finalMask)
	finalMask = np.where(labeledStack>0, 1, 0) # this casts to np.int64
	finalMask = finalMask.astype(np.uint8)
	#_printStackParams('finalMask 2', finalMask)
	
	#_printStackParams('XXX finalMask 2', finalMask)

	#
	# dilate final mask
	dilateFinalMaskIterations = 2
	print('  .', 'dilating final mask with', dilateFinalMaskIterations, 'iterations')
	finalMask = scipy.ndimage.morphology.binary_dilation(finalMask, structure=None, iterations=dilateFinalMaskIterations)
	finalMask = finalMask.astype(np.uint8)
	#finalMask = np.where(finalMask==True, 1, 0)

	stackDict['finalMask']['data'] = finalMask
	paramDict['dilateFinalMaskIterations'] = dilateFinalMaskIterations

	#_printStackParams('XXX finalMask 2', finalMask)
	#sys.exit()
	
	#
	# remaining image (after subtracting the final mask)
	print('  .', 'calculating final remaining image by removing final mask pixels')
	remainingData = stackData.copy()
	remainingData[finalMask>0] = 0
	#_printStackParams('remainingData', remainingData)
	
	stackDict['remainingRaw']['data'] = remainingData
	
	paramDict['path'] = path
	
	#
	# save _finalMask.tif (for convex hull)
	tmpFinalMaskPath = saveBase + '_finalMask.tif'
	print('  .', 'saving _finalMask.tif for convex hull:', tmpFinalMaskPath)
	bimpy.util.bTiffFile.imsave(tmpFinalMaskPath, finalMask, tifHeader=tiffHeader, overwriteExisting=True)	

	#
	# convex hull
	# this is tricky, we are running in different environment
	# best we can do to share data is to save and then reload
	pythonPath = os.path.abspath('my_hull_env/bin/python')
	if os.path.isfile(pythonPath):
		finalMaskPath = saveBase + '_finalMask.tif'
		os.system(pythonPath + ' myConvexHull.py ' + finalMaskPath)
	else:
		print('ERROR: did not find', pythonPath, 'to run convex hull. NO CONVEX HULL GENERATED')	

	#
	# load the convex hull
	hullPath = saveBase + '_finalMask_hull.tif'
	print('  vascDen.myRun() loading finalMask_hull:', hullPath)
	hullMask, ignoreThis = bimpy.util.bTiffFile.imread(hullPath)
	_printStackParams('hullData', hullMask)

	#
	# generate edt
	maskStack = stackDict['finalMask']['data']
	scale = (paramDict['tiffHeader']['zVoxel'], paramDict['tiffHeader']['xVoxel'], paramDict['tiffHeader']['yVoxel'])
	edtData = myDistanceMap(maskStack, hullMask, scale=scale)
	stackDict['finalMask_edt']['data'] = edtData
	
	#
	# if there is a _labeled_edited.tif we need to remove it !!!
	labeledEditedPath = saveBase + '_labeled_edited.tif'
	if os.path.isfile(labeledEditedPath):
		# move
		bakLabeledEditedPath = labeledEditedPath + '.bak'
		print('=== MOVING EDITED LABELS')
		print('      from:', labeledEditedPath)
		print('      to:', bakLabeledEditedPath)
		os.rename(labeledEditedPath, bakLabeledEditedPath)
		
	#
	# save
	mySave(saveBase, saveBase2, stackDict, tiffHeader, paramDict)

	#
	# update master cell db
	updateMasterCellDB(masterFilePath, filename, paramDict)
	
def myDistanceMap(maskStack, hullMask=None, scale=[1,1,1]): #, includeDistanceLessThan=5):	
	"""
	only accept maskStack pixels in hullMask
	"""
	
	print('  .vascDen.myDistanceMap() scale:', scale, '... please wait')
	
	edtMask = maskStack.copy().astype(float)

	#
	# invert the mask, edt will calculate distance from 0 to 1
	edtMask[edtMask==1] = 10
	edtMask[edtMask==0] = 1
	edtMask[edtMask==10] = 0

	distanceMap = scipy.ndimage.morphology.distance_transform_edt(edtMask, sampling=scale, return_distances=True)
	
	distanceMap = distanceMap.astype(np.float32) # both (matplotlib, imagej) do not do float16 !!!

	# only accept edt that is also in hullMask
	distanceMap[hullMask==0] = np.nan
	
	_printStackParams('output edt', distanceMap)

	return distanceMap

################################################################################
if __name__ == '__main__':
	#
	# read master_cell_db.csv (same folder as this file, for now)
	#masterFilePath = 'master_cell_db.csv'
	masterFilePath = '20200518_cell_db.csv'
	
	parser = argparse.ArgumentParser(description = 'Process a vascular stack')
	parser.add_argument('tifPath', nargs='*', default='', help='path to original .tif file')
	args = parser.parse_args() # args is a list of command line arguments

	if len(args.tifPath)>0:
		path = args.tifPath[0]		
	else:
		#
		#
		path = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0007_ch1.tif'
		#path = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0010_ch1.tif'
		#path = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0011_ch1.tif'
	
	trimPercent = 15
	myRun(path, trimPercent, masterFilePath)
	
	doNapari = 1
	if doNapari == 1:
		vascDenNapari.myLabelEdit(path)
	
	