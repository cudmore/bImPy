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

import os, time
import argparse
from collections import OrderedDict
from datetime import datetime

import numpy as np
import pandas as pd
import scipy

import napari

import bimpy

################################################################################
def _printStackParams(name, myStack):
	print('  ', name, myStack.shape, myStack.dtype, 'dtype.char:', myStack.dtype.char,
				'min:', round(np.min(myStack),2), 'max:', round(np.max(myStack),2), 'mean:', round(np.nanmean(myStack),2))

################################################################################
def mySave(saveBase, stackDict, tiffHeader):
	"""
	saveBase: is like '/Users/cudmore/box/data/nathan/20200116/analysis2/20190116__A01_G001_0007_ch1'
	"""
	print('  .', 'mySave() saveBase:', saveBase)
	
	#for idx, (k,v) in enumerate(stackDict.items()):
	for k,v in stackDict.items():
		# k in (raw, slidingz, ...)
		# v is a dict with keys (type, data)
		name = k
		type = v['type']
		data = v['data']

		if data is None:
			if name == 'finalMask_hull':
				print('  ', 'Warning: mySave() did find stack data for "', k, '"', 'need to calculate with scipy 1.4.1 using convexyHull.py')
			else:
				print('  ', 'Warning: mySave() did find stack data for "', k, '"')
			continue
		
		#idxStr = '_' + str(idx) + '_'
		#savePath = saveBase + idxStr + k + '.tif'
		savePath = saveBase + '_' + k + '.tif'
		print('  ', name, 'savePath:', savePath)
		bimpy.util.bTiffFile.imsave(savePath, data, tifHeader=tiffHeader, overwriteExisting=True)	
		
################################################################################
def myGetDefaultStackDict():
	"""
	Using order here to save files with _1_, _2_, _3_, ...
	"""
	stackDict = OrderedDict()
	stackDict['raw'] = {'type': 'image', 'data': None}
	stackDict['slidingz'] = {'type': 'image', 'data': None}
	stackDict['filtered'] = {'type': 'image', 'data': None}
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

	print('updateMasterCellDB() filename:', filename, 'masterFilePath:', masterFilePath)
	
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
		print('  ERROR: updateMasterCellDB() did not find uFilename:', filename, 'in masterFilePath:', masterFilePath)
		return
		
	for k,v in paramDict.items():
		if not k in df.columns:
			print('  *** updateMasterCellDB() is appending column named:', k)
			df[k] = ""
		
		df.loc[df['uFilename'] == filename, k] = str(v)
	
	#
	# resave
	print('  updateMasterCellDB() is saving', masterFilePath)
	df.to_csv(masterFilePath, index_label='index')
	
################################################################################
def pruneStackData(masterFilePath, filename, stackData):
	"""
	prune stack slices by filename (row) and (firstslice, lastslice) specified in .csv file masterFilePath
	"""
	print('  .', 'pruneStackData() masterFilePath:', masterFilePath)
	if not os.path.isfile(masterFilePath):
		print('  error: pruneStackData() did not find masterFilePath:', masterFilePath)
		return
	
	print('  loading .csv to get (firstslice, lastslice) for filename:', filename, 'from masterFilePath:', masterFilePath)
	df = pd.read_csv(masterFilePath)

	numSlices = stackData.shape[0]
	firstSlice = 0
	lastSlice = numSlices - 1
	#

	if df is not None:
		df2 = df.loc[df['uFilename'] == filename, 'uFirstSlice']
		if df2.shape[0] == 0:
			print('  ERROR: did not find dfMasterCellDB uFilename:', filename, 'uFirstSlice')
		else:
			print('  .', 'reading from .csv line:')
			thisLineDF = df[df['uFilename'] == filename]
			print(thisLineDF)
			
			# firstslice
			tmpFirstSlice = df.loc[df['uFilename'] == filename, 'uFirstSlice'].iloc[0]  
			if pd.notnull(tmpFirstSlice):
				firstSlice = int(tmpFirstSlice)
				print('    read uFilename:', filename, 'uFirstSlice:', firstSlice)
			else:
				print('    ERROR: did not find "uFirstSlice" for uFilename:', filename)
			# lastslice
			tmpLastSlice = df.loc[df['uFilename'] == filename, 'uLastSlice'].iloc[0]  
			if pd.notnull(tmpLastSlice):
				lastSlice = int(tmpLastSlice)
				print('    read uFilename:', filename, 'uLastSlice:', lastSlice)
			else:
				print('    ERROR: did not find "uLastSlice" for uFilename:', filename)
	else:
		print('ERROR: pruneStackData() did not read df from masterFilePath:', masterFilePath)
	
	if firstSlice > 0 and lastSlice < numSlices - 1:
		print('  ', 'pruning stackData slices')
		_printStackParams('from stackData', stackData)	
		stackData = stackData[firstSlice:lastSlice+1,:,:]
		_printStackParams('pruned stackData', stackData)	
	#stackDict['raw']['data'] = stackData
	return stackData
	
################################################################################
def setupAnalysis(path, masterFilePath='master_cell_db.csv'):
	"""
	"""
	print('setupAnalysis() path:', path)
	
	folderpath, filename = os.path.split(path)
	filenamenoextension, tmpExt = filename.split('.')
	
	savePath = os.path.join(folderpath, 'analysis2')
	saveBase = os.path.join(savePath, filenamenoextension)
	
	channel = None
	if filename.endswith('_ch1.tif'):
		channel = 1
	elif filename.endswith('_ch2.tif'):
		channel = 2
	elif filename.endswith('_ch3.tif'):
		channel = 3
	
	print('  channel:', channel)
	print('  savePath:', savePath)
	print('  saveBase:', saveBase) # append _labeled.tif to this
	
	#
	# make output folder
	if not os.path.isdir(savePath):
		os.mkdir(savePath)
	
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
	print('  loading stack:', path)
	stackData, tiffHeader = bimpy.util.bTiffFile.imread(path)
	paramDict['tiffHeader'] = tiffHeader
	_printStackParams('stackData', stackData)
	
	paramDict['zVoxel'] = tiffHeader['zVoxel']
	paramDict['xVoxel'] = tiffHeader['xVoxel']
	paramDict['yVoxel'] = tiffHeader['yVoxel']

	paramDict['zOrigPixel'] = stackData.shape[0]
	paramDict['xOrigPixel'] = stackData.shape[1] # rows
	paramDict['yOrigPixel'] = stackData.shape[2]
		
	#
	# keep slices
	stackData = pruneStackData(masterFilePath, filename, stackData)
	stackDict['raw']['data'] = stackData
	
	paramDict['zFinalPixel'] = stackData.shape[0]
	paramDict['xFinalPixel'] = stackData.shape[1] # rows
	paramDict['yFinalPixel'] = stackData.shape[2]

	paramDict['saveBase'] = saveBase

	return filename, paramDict, stackDict
	
################################################################################
def myRun(path, masterFilePath):

	print('vascDen.myRun() path:', path)
	
	filename, paramDict, stackDict = setupAnalysis(path, masterFilePath=masterFilePath)
	
	# set the algorithm
	paramDict['algorithm'] = 'vascDen'
	
	# get some local variables
	stackData = stackDict['raw']['data']
	tiffHeader = paramDict['tiffHeader']
	saveBase = paramDict['saveBase']
	
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
	filteredStack = bimpy.util.morphology.medianFilter(slidingz, kernelSize=medianKernelSize)
	stackDict['filtered']['data'] = filteredStack
	paramDict['medianKernelSize'] = medianKernelSize
	
	#
	# threshold
	thresholdPercent=0.06
	thresholdStack = bimpy.util.morphology.threshold_remove_lower_percent(filteredStack, removeBelowThisPercent=thresholdPercent)
	paramDict['thresholdAlgorithm'] = 'threshold_remove_lower_percent'
	paramDict['thresholdPercent'] = thresholdPercent
	
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
	print('                origNumLabels:', origNumLabels)
	stackDict['labeled']['data'] = labeledStack
	stackDict['small_labels']['data'] = removedLabelStack
	paramDict['removeSmallerThan'] = removeSmallerThan
	paramDict['origNumLabels'] = origNumLabels # used in most subsequent steps

	#
	# final mask
	finalMask = stackData.copy()
	_printStackParams('finalMask 1', finalMask)
	finalMask = np.where(labeledStack>0, 1, 0) # this casts to np.int64
	finalMask = finalMask.astype(np.uint8)
	_printStackParams('finalMask 2', finalMask)
	
	#
	# dilate final mask
	dilateFinalMaskIterations = 2
	finalMask = scipy.ndimage.morphology.binary_dilation(finalMask, structure=None, iterations=dilateFinalMaskIterations)
	finalMask = finalMask.astype(np.uint8)
	#finalMask = np.where(finalMask==True, 1, 0)

	stackDict['finalMask']['data'] = finalMask
	paramDict['dilateFinalMaskIterations'] = dilateFinalMaskIterations

	#
	# remaining image (after subtracting the final mask)
	remainingData = stackData.copy()
	remainingData[finalMask>0] = 0
	_printStackParams('remainingData', remainingData)
	
	stackDict['remainingRaw']['data'] = remainingData
	
	paramDict['path'] = path
	
	#
	# convex hull
	pythonPath = 'my_hull_env/bin/python'
	finalMaskPath = saveBase + '_finalMask.tif'
	os.system(pythonPath + ' myConvexHull.py ' + finalMaskPath)
	
	#
	# save
	mySave(saveBase, stackDict, tiffHeader)
	
	#
	# update master cell db
	updateMasterCellDB(masterFilePath, filename, paramDict)
	
################################################################################
if __name__ == '__main__':
	#
	# read master_cell_db.csv (same folder as this file, for now)
	masterFilePath = 'master_cell_db.csv'
	#dfMasterCellDB = pd.read_csv('master_cell_db.csv')
	
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
	
	myRun(path, masterFilePath)
	
	
	