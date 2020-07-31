"""
20200526
Robert H Cudmore

	Take a folder of raw _ch1 and _ch2 files

	Make a dask array block of all images in a grid

	Display with napari

	Install
        python -m venv dask_env
        source dask_env/bin/activate
        pip install tifffile
        pip install numpy
        pip install dask
        pip install napari
		
"""

import os, sys, math

import numpy as np

import tifffile

import dask
import dask.array as da

import napari

def trimStack(stackData):
	# trim lower right
	thisHeight = stackData.shape[1] - trimPixels
	thisWidth = stackData.shape[2] - trimPixels
	stackData = stackData[:, 0:thisHeight, 0:thisWidth]
	return stackData

'''
def trimFiles(path)
	"""
	34
	"""
	
	trimPixels = 34
	
	savePath = os.path.join(path, 'analysis3')
	
	if not os.path.isdir(savePath):
		os.mkdir(savePath)

	for file in os.listdir(path):
		if file.startswith('.'):
			continue
		if not file.endswith('.tif'):
			continue
		
		# load
		fileLoadPath = os.path.join(path, file)
		print(fileLoadPath)
		fileData = tifffile.imread(fileLoadPath)
		
		# trim lower right
		thisHeight = fileData.shape[1] - trimPixels
		thisWidth = fileData.shape[2] - trimPixels
		fileData = fileData[:, 0:thisHeight, 0:thisWidth]
		
		# save
		fileSavePath = os.path.join(savePath, file)
		print('  ', fileSavePath)
		tifffile.imsave(fileSavePath, fileData)
'''
		
def myFileRead(filename,commonShape, trimPixels):
	"""
	handle missing files in dask array
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
	
def myGetBlock(path, prefixStr, finalPrefixStr, commonShape, trimPixels, nRow, nCol, channel):
	"""
	path: path to raw folder with _ch1 and _ch2 .tif files
		like '/Users/cudmore/box/data/nathan/20200518'
	prefixStr:
		like '20200518__A01_G001_'
	finalPrefixStr: used for computed analysis in analysis2/
		like 'finalMask'
	commonShape: tuple of (slices, x pixels, yPixels)
		like (64,512,512)
	trimPixels: Number of pixels to remove in lower/right of x/y to remove grid overlap
	nRow, nCol: number of rows and columns in the grid
	channel: channel number, either 1 or 2
	"""
	
	if finalPrefixStr:
		finalPrefixStr = '_' + finalPrefixStr
	
	if channel == 1:
		postfixStr = '_ch1' + finalPrefixStr + '.tif'
	elif channel == 2:
		postfixStr = '_ch2' + finalPrefixStr + '.tif'
	elif channel == 3:
		postfixStr = '_ch3' + finalPrefixStr + '.tif'

	common_dtype = np.uint8 # assuming all stack are 8-bit
	
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
		if not os.path.isfile(file):
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
	
	#print('  x.shape:', x.shape)
	
	return x
	
if __name__ == '__main__':

	# file info
	path = '/Users/cudmore/box/data/nathan/20200518'
	prefixStr = '20200518__A01_G001_'
	finalPostfixStr = ''
	# stack info
	commonShape = (64,512,512)
	trimPercent = 15
	# grid info
	nRow = 8
	nCol = 6

	trimPixels = math.floor( trimPercent * commonShape[1] / 100 )
	trimPixels = math.floor(trimPixels / 2)
	print('trimPixels:', trimPixels)
	#print('manually tweeking trim pixels to 34')
	#trimPixels = 34
	
	# this is shape after I trimmed lower/right of each image by 34 pixels (512-34=478)
	#commonShape = (64,478,478)

	# this works
	#path = '/Users/cudmore/box/data/nathan/20200518'
	'''
	path = '/Users/cudmore/box/data/nathan/20200518/analysis3' # lower/right x/y trimmed to remove grid overlap
	prefixStr = '20200518__A01_G001_'
	finalPostfixStr = ''
	nRow = 8
	nCol = 6
	#commonShape = (64,512,512) # shape of each stack (slices, x, y) in pixels
	#commonShape = (64,256,256)
	'''
	
	ch1RawBlock = myGetBlock(path, prefixStr, finalPostfixStr, commonShape, trimPixels, nRow, nCol, channel=1)
	ch2RawBlock = myGetBlock(path, prefixStr, finalPostfixStr, commonShape, trimPixels, nRow, nCol, channel=2)
	
	'''
	# analysis_full/ has all analysis padded with zeros above/below firstSlice/lastSlice
	path = '/Users/cudmore/box/data/nathan/20200518/analysis_full' 	
	#trimFiles(path) # makes analysis3/
	path = '/Users/cudmore/box/data/nathan/20200518/analysis_full/analysis3' 	
	prefixStr = '20200518__A01_G001_'
	#finalPostfixStr = 'finalMask'
	finalPostfixStr = 'finalMask_edt'
	nRow = 8
	nCol = 6
	#commonShape = (64,512,512) # shape of each stack (slices, x, y) in pixels
	'''

	#
	# todo:
	# load file _0001_ch1.tif to get (z,x,y) shape
	
	'''
	path = '/Users/cudmore/box/data/nathan/20200519'
	prefixStr = '20200519__A01_G001_'
	finalPostfixStr = ''
	nRow = 12 #17 is real number of rows, napari/dask is TOO slow
	nCol = 7
	commonShape = (62,512,512)
	
	#trimFiles(path) # makes analysis3/
	'''
	
	ch1Block = None
	ch2Block = None
	if 0:
		ch1Block = myGetBlock(path, prefixStr, finalPostfixStr, commonShape, trimPixels, nRow, nCol, channel=1)
		#ch2Block = myGetBlock(path, prefixStr, finalPostfixStr, commonShape, trimPixels, nRow, nCol, channel=2)

	#
	# napari
	if 1:
		scale = (1, 0.621480865, 0.621480865)
		scale = (1, 0.6, 0.6) # scale in um/pixel (z, x, y)
		with napari.gui_qt():
			viewer = napari.Viewer(title='dask ' + path)

			# raw
			minContrast = 0
			maxContrast = 255
			name = 'ch1 raw'
			myImageLayer = viewer.add_image(ch1RawBlock, scale=scale, colormap='green', contrast_limits=(minContrast, maxContrast), opacity=0.6, visible=True, name=name)
			minContrast = 0
			maxContrast = 255
			name = 'ch2 raw'
			myImageLayer = viewer.add_image(ch2RawBlock, scale=scale, colormap='red', contrast_limits=(minContrast, maxContrast), opacity=0.6, visible=True, name=name)

			if ch1Block is not None:
				#minContrast = da.min(ch1Block)
				#maxContrast = da.max(ch1Block)
				minContrast = 0
				maxContrast = 255
				color = 'green'
				if finalPostfixStr == 'finalMask':
					minContrast = 0
					maxContrast = 1
					color = 'blue'
				print('minContrast:', minContrast, 'maxContrast:', maxContrast)
				name = 'ch1 ' + finalPostfixStr
				myImageLayer = viewer.add_image(ch1Block, scale=scale, colormap=color, contrast_limits=(minContrast, maxContrast), opacity=0.6, visible=True, name=name)
			if ch2Block is not None:
				#minContrast = da.min(ch2Block)
				#maxContrast = da.max(ch2Block)
				minContrast = 0
				maxContrast = 255
				color = 'red'
				if finalPostfixStr == 'finalMask':
					minContrast = 0
					maxContrast = 1
					color = 'blue'
				name = 'ch2 ' + finalPostfixStr
				myImageLayer = viewer.add_image(ch2Block, scale=scale, colormap=color, contrast_limits=(minContrast, maxContrast), opacity=0.6, visible=True, name=name)
	
