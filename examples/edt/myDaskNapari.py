"""
Author: Robert Cudmore
Date: 20200528

Purpose:
	Open a Napari viewer for a grid of _ch1.tif and _ch2.tif files
	
	This is using dask arrays and blocks
	
Command Line Usage

	Modify parameters in __main__ block and run with
		python myDaskNApari.py

Using in a custon script

	import myDaskNapari

	myGridParams = myDaskNapari.getDaskGridDict()
	myGridParams['path'] = '/Users/cudmore/box/data/nathan/20200518'
	myGridParams['prefixStr'] = '20200518__A01_G001_'
	myGridParams['channelList'] = [1, 2]
	myGridParams['commonShape'] = (64,512,512)
	myGridParams['commonVoxelSize'] = (1, 0.621480865, 0.621480865)
	myGridParams['trimPercent'] = 15
	myGridParams['trimPixels'] = None # calculated
	myGridParams['nRow'] = 8
	myGridParams['nCol'] = 6

	myDaskNapari.openDaskNapari(myGridParams)
	
"""
import os, sys, math, json
from collections import OrderedDict

import numpy as np
import tifffile

import dask
import dask.array as da

import napari

def myFileRead(filename,commonShape, trimPixels):
	"""
	File loading triggered from dask from_delayed and delayed
	handle missing files in dask array by returning correct shape
	"""
	if os.path.isfile(filename):
		stackData = tifffile.imread(filename)
	else:
		stackData = np.zeros(commonShape, dtype=np.uint8)
	if trimPixels is not None:
		thisHeight = stackData.shape[1] - trimPixels
		thisWidth = stackData.shape[2] - trimPixels
		stackData = stackData[:, 0:thisHeight, 0:thisWidth]

	return stackData
	
def myGetBlock(path, prefixStr, finalPrefixStr, commonShape, trimPercent, trimPixels, nRow, nCol, channel, verbose=True):
	"""
	Get a dask block representing a tile/grid of .tif files
	Assuming acquisition follows a snake pattern, for example
	
	Parameters:
		path: path to raw folder with _ch1 and _ch2 .tif files
			like '/Users/cudmore/box/data/nathan/20200518'
		prefixStr:
			like '20200518__A01_G001_'
		finalPrefixStr: used for computed analysis in analysis2/
			like 'finalMask'
		commonShape: tuple of (slices, x pixels, yPixels)
			like (64,512,512)
		trimPercent: Integer of percent overlap
		trimPixels: Number of pixels to remove in lower/right of x/y to remove grid overlap
					Pass None to calculate from trimPercent
		nRow, nCol: number of rows and columns in the grid
		channel: channel number, either 1 or 2
		
	Returns:
		A dask block of (nRow, nCol)
		A dask block is really a numpy ndarray of shape:
			(commonShape[0], commonShape[1]*nRow, commonShape[2]*nCol)
	"""
	
	if finalPrefixStr:
		finalPrefixStr = '_' + finalPrefixStr
	
	if channel == 1:
		postfixStr = '_ch1' + finalPrefixStr + '.tif'
	elif channel == 2:
		postfixStr = '_ch2' + finalPrefixStr + '.tif'
	elif channel == 3:
		postfixStr = '_ch3' + finalPrefixStr + '.tif'
	else:
		print('error: myGetBlock() got bad channel:', channel)
		
	common_dtype = np.uint8 # assuming all stack are 8-bit
	
	# trip bottom/right (e.g. x/y) of common stack shape
	if trimPixels is None:
		trimPixels = math.floor( trimPercent * commonShape[1] / 100 )
		trimPixels = math.floor(trimPixels / 2)
	if trimPixels > 0:
		commonShape = (commonShape[0], commonShape[1]-trimPixels, commonShape[2]-trimPixels)

	# make nRow X nCol grid of integers
	tmpIntegerGrid = np.arange(1,nRow*nCol+1) # Values are generated within the half-open interval [start, stop)
	tmpIntegerGrid = np.reshape(tmpIntegerGrid, (nRow, nCol))
	# reverse numbers in every other row (to replicate 'snake' image acquisition)
	integerGrid = tmpIntegerGrid.copy()
	integerGrid[1::2] = tmpIntegerGrid[1::2,::-1]

	# make a list of file names following order of snake pattern in integerGrid
	filenames = [prefixStr + str(x).zfill(4) + postfixStr for x in integerGrid.ravel()]
	filenames = [os.path.join(path, x) for x in filenames]

	# check that all files exist, display will fail when loading file that does not exist
	for idx, file in enumerate(filenames):
		if verbose and not os.path.isfile(file):
			print('error: myGetBlock() did not find file:', file)
	
	#lazy_arrays = [dask.delayed(tifffile.imread)(fn) for fn in filenames]
	lazy_arrays = [dask.delayed(myFileRead)(fn, commonShape, trimPixels) for fn in filenames]
	lazy_arrays = [da.from_delayed(x, shape=commonShape, dtype=common_dtype)
				   for x in lazy_arrays]
	# reshape 1d list into list of lists (nCol items list per nRow lists)
	lazy_arrays = [lazy_arrays[i:i+nCol] for i in range(0, len(lazy_arrays), nCol)]
	
	#
	# make a block
	x = da.block(lazy_arrays)
		
	return x
	
def getDaskGridDict():
	"""
	Used by external scripts
	"""
	myGridParams = OrderedDict()
	
	# file info
	myGridParams['path'] = ''
	myGridParams['prefixStr'] = ''
	myGridParams['finalPostfixStr'] = ''
	# stack info
	myGridParams['channelList'] = [] # e.g. [1,2] or [1] or [2]
	myGridParams['commonShape'] = None # pixels (slices, x, y)
	myGridParams['commonVoxelSize'] = None # voxel size in um/pixel (slices, x, y)
	# grid info
	# percent of overlap between tiles, final trim pixels is
	myGridParams['trimPercent'] = 15 
	myGridParams['trimPixels'] = None
	# size of the grid
	myGridParams['nRow'] = None
	myGridParams['nCol'] = None
	
	myGridParams['finalPostfixList'] = []
	
	return myGridParams
	
def openDaskNapari2(myGridParams):
	"""
	Show analysis_full in Napari
	
	analysis_full/ is a second set of analysis with black slice above/below firstSLice/lastSLice
	
	Use:
		myGridParams['finalPostfixList'] = ['raw', 'finalMask', 'finalMask_edt']
		
	Given grid parameters corresponding to _ch1 and _ch2 stacks in folder (path)
	1) construct a dask block with all files
	2) open a Napari viewer
	"""
	
	print('myDaskNapari()')
	print(json.dumps(myGridParams, indent=4))
	
	# extract information from myGridParams
	path = myGridParams['path']
	prefixStr = myGridParams['prefixStr']

	#finalPostfixStr = myGridParams['finalPostfixStr'] # always '' for raw data
	finalPostfixList = myGridParams['finalPostfixList'] # always '' for raw data

	channelList = myGridParams['channelList']
	commonShape = myGridParams['commonShape']
	commonVoxelSize = myGridParams['commonVoxelSize']
	trimPercent = myGridParams['trimPercent']
	trimPixels = myGridParams['trimPixels']
	nRow = myGridParams['nRow']
	nCol = myGridParams['nCol']
	
	rawBlockList = []
	napariChannelList = []
	napariPostfixList = []
	for channel in channelList:
		for tmpFinalPostfixStr in finalPostfixList:
			rawBlock = myGetBlock(path, prefixStr, tmpFinalPostfixStr, commonShape, trimPercent, trimPixels, nRow, nCol, channel=channel, verbose=False)
			
			'''
			theMax = rawBlock.max()
			print(tmpFinalPostfixStr, 'theMax:', theMax)
			'''
			
			rawBlockList.append(rawBlock)
			napariChannelList.append(channel)
			napariPostfixList.append(tmpFinalPostfixStr)
			
	# for napari
	tmpPath, windowTitle = os.path.split(path)
	scale = commonVoxelSize

	#
	# napari
	with napari.gui_qt():
		viewer = napari.Viewer(title='dask: ' + windowTitle)

		for idx, rawBlock in enumerate(rawBlockList):
			channelIdx = napariChannelList[idx]
			if channelIdx == 1:
				color = 'green'
			elif channelIdx == 2:
				color = 'red'
			thisPostfix = napariPostfixList[idx]
			minContrast = 0
			maxContrast = 255
			if thisPostfix in ['finalMask', 'mask']:
				minContrast = 0
				maxContrast = 1
				#
				# blank out mask slices when raw has low snr, where snr=max-min
				# this does not work, this gets min/max of ENTIRE grid
				theMin = rawBlockList[idx-1].min().compute()
				theMax = rawBlockList[idx-1].max().compute()
				print(rawBlockList[idx-1].shape, 'theMin:', theMin, 'theMax:', theMax)
				
			if thisPostfix == 'finalMask_edt':
				minContrast = 0
				maxContrast = 120
				color = 'fire'
			name = 'ch' + str(channelIdx) + ' ' + str(thisPostfix)
			myImageLayer = viewer.add_image(rawBlock, scale=scale, colormap=color,
						contrast_limits=(minContrast, maxContrast), opacity=0.6, visible=True,
						name=name)

	#tmp = rawBlockList[0].max()
	#print(tmp)
	
def openDaskNapari(myGridParams):
	"""
	Show raw _ch1/_ch2 in napari
	
	Given grid parameters corresponding to _ch1 and _ch2 stacks in folder (path)
	1) construct a dask block with all files
	2) open a Napari viewer
	"""
	
	print('myDaskNapari()')
	print(json.dumps(myGridParams, indent=4))
	
	# extract information from myGridParams
	path = myGridParams['path']
	prefixStr = myGridParams['prefixStr']
	finalPostfixStr = myGridParams['finalPostfixStr'] # always '' for raw data
	channelList = myGridParams['channelList']
	commonShape = myGridParams['commonShape']
	commonVoxelSize = myGridParams['commonVoxelSize']
	trimPercent = myGridParams['trimPercent']
	trimPixels = myGridParams['trimPixels']
	nRow = myGridParams['nRow']
	nCol = myGridParams['nCol']
	
	rawBlockList = []
	for channel in channelList:
		rawBlock = myGetBlock(path, prefixStr, finalPostfixStr, commonShape, trimPercent, trimPixels, nRow, nCol, channel=channel)
		
		# trying to get original stack from a block of stacks
		#print(rawBlock[0][0])
		print(rawBlock[0])
		
		rawBlockList.append(rawBlock)
		
	# for napari
	tmpPath, windowTitle = os.path.split(path)
	scale = commonVoxelSize
	
	#vLabel = commonShape[1] / 2
	#hLabel = commonShape[2] / 2
	
	#
	# napari
	with napari.gui_qt():
		viewer = napari.Viewer(title='dask: ' + windowTitle)

		for idx, rawBlock in enumerate(rawBlockList):
			channelIdx = channelList[idx]
			if channelIdx == 1:
				color = 'green'
			elif channelIdx == 2:
				color = 'red'
				
			minContrast = 0
			maxContrast = 255
			name = 'ch' + str(channelIdx) + ' raw'
			myImageLayer = viewer.add_image(rawBlock, scale=scale, colormap=color,
						contrast_limits=(minContrast, maxContrast), opacity=0.6, visible=True,
						name=name)

			#
			# add labels
			#vLabel = commonShape[1] / 2
			#hLabel = commonShape[2] / 2
		#
		# add labels
		
if __name__ == '__main__':

	#
	# specify parameters for a given folder with a grid
	
	# file info
	path = '/Users/cudmore/box/data/nathan/20200518'
	prefixStr = '20200518__A01_G001_'
	# stack info
	channelList = [1, 2]
	commonShape = (64,512,512)
	commonVoxelSize = (1, 0.621480865, 0.621480865)
	# grid info
	trimPercent = 15
	nRow = 8
	nCol = 6

	#
	# main
	trimPixels = None
	#trimPixels = math.floor( trimPercent * commonShape[1] / 100 )
	#trimPixels = math.floor(trimPixels / 2)
	
	myGridParams = OrderedDict()
	myGridParams['path'] = path
	myGridParams['prefixStr'] = prefixStr
	myGridParams['finalPostfixStr'] = '' #finalPostfixStr # always empty for raw data
	myGridParams['channelList'] = channelList
	myGridParams['commonShape'] = commonShape
	myGridParams['commonVoxelSize'] = commonVoxelSize
	myGridParams['trimPercent'] = trimPercent
	myGridParams['trimPixels'] = trimPixels
	myGridParams['nRow'] = nRow
	myGridParams['nCol'] = nCol

	openDaskNapari(myGridParams)
	
	
	
