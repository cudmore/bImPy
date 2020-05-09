"""
	Author: Robert Cudmore
	Date: 20200501

	Purpose: median filter all .tif files in a folder
	
	Parameters:
		kernel_size: size of median filter kernel, default is (3,3,3)
		
	See:
		https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.signal.medfilt.html
	
	Requires:
		numpy: pip install numpy
		scipy: pip install scipy
		tifffile: pip install tifffile
		
	In General:
		Median filter is very slow. Thus, you will see 'median filter ... please wait'
		
"""

import os

import numpy as np
import scipy.signal # scipy imports are tricky, not sure why we need this but we do.
import tifffile

##############################################################################
def myMedianFilter(filePath, kernel_size=(3,3,3)):
	"""
	Given a .tif file path
		1) open the .tif
		2) run a median filter using kernel_size
		3) save the results as a .tif by appending _median.tif to the no-extension filename
	
	You need to specify the kernel_size, default is (3,3,3). Remember, numbers must be odd
	
	Notes: median filter is super slow.
	
	"""
	print('myMedianFilter()')

	print('  filePath:', filePath)
	
	#
	# load
	print('  loading')
	myStack = tifffile.imread(filePath) # could use scipy but directly using tifffile instead
	
	#
	# median filter
	print('  median filter ... please wait')
	medianFilteredStack = scipy.signal.medfilt(myStack, kernel_size=kernel_size)
	
	# median filter will usually return a np.float64 stack (which is huge)
	# convert to a more manageable size, keep in mind that with this step you can lose data ...
	# option 1: convert to np.float16
	#medianFilteredStack = medianFilteredStack.astype(np.float16)
	# option 2: if Fiji stitching does not like float16 then use this instead 
	medianFilteredStack = medianFilteredStack.astype(np.uint8)
	
	#
	# save
	
	# take apart filePath to make _median.tif save path
	tmpFolderPath, tmpFileName = os.path.split(filePath)
	# make a new 'analysis' folder
	saveFolderPath = os.path.join(tmpFolderPath, 'analysis2')
	if not os.path.isdir(saveFolderPath):
		os.mkdir(saveFolderPath)
	# build a save file path (with full filename)
	tmpFileNameNoExtension, tmpExtension = tmpFileName.split('.')
	saveFileName = tmpFileNameNoExtension + '_median.tif'
	saveFilePath = os.path.join(saveFolderPath, saveFileName)
	
	# do the save
	if os.path.isfile(saveFilePath):
		print('  not saving, already exists:', saveFilePath)
	else:
		print('  saving saveFilePath:', saveFilePath)
		tifffile.imsave(saveFilePath, medianFilteredStack)
	
	return medianFilteredStack

##############################################################################
if __name__ == '__main__':
	
	# you need to manually specify the folder path here
	# make sure it doen NOT end in '/'
	pathToFolder = '/Users/cudmore/box/data/nathan/20200420'
	
	# recurvely convert all file in all sub-folders
	'''
	if not os.path.isdir(pathToFolder):
		print('ERROR: did not find pathToFolder:', pathToFolder)
	else:
		# this nested for-loop is a general purpose engine to traverse a folder hierarchy
		# here, we are finding all files in all subfolders that end in .tif
		for dirpath, dirnames, files in os.walk(pathToFolder):
			for name in files:
				if name.endswith('.tif'):
					filePath = os.path.join(dirpath, name)
					myMedianFilter(filePath)
	'''
					
	# convert all .tif files in a single folder
	if os.path.isdir(pathToFolder):
		for item in os.listdir(pathToFolder):
			itemPath = os.path.join(pathToFolder, item)
			if os.path.isdir(itemPath):
				# skip all subdirectories
				continue
			elif os.path.isfile(itemPath) and itemPath.endswith('.tif'):
				print(itemPath)
				myMedianFilter(itemPath)
	else:
		print('ERROR: did not find pathToFolder:', pathToFolder)
				
					