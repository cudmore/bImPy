"""
Author: Robert Cudmore
Date: 20200424

	How to use:
		1) Drag and drop onto Fiji, just like you owuld do for a stack
		2) in the text editor, select menu 'Run -Run'
		3) Select a folder with ('.oir', '.tif')

	Output:
		Will recursively look into specified folder and create a comma-seperated-file (e.g. .csv)
		with pixel and voxel information
	
	Fiji API reference:
		ImagePlus: https://imagej.nih.gov/ij/developer/api/ij/ImagePlus.html
		FileInfo: https://imagej.nih.gov/ij/developer/api/ij/io/FileInfo.html
		Calibration: https://imagej.nih.gov/ij/developer/api/ij/measure/Calibration.html

"""

from __future__ import print_function  # Only needed for Python 2, MUST be first import
import os
import json
from collections import OrderedDict

from ij import IJ, WindowManager
from ij.io import DirectoryChooser

import loci.formats
from loci.plugins import BF

###
###
### Parameters
###
###

# only process files with these extension
#gTheseFileExtensions = ['.tif']
#gTheseFileExtensions = ['.oir']
gTheseFileExtensions = ['.oir', '.tif']
	

def getDefaultDict():
	"""
	Use this so getImpInfo() always returns the same dict
	"""
	retDict = OrderedDict()
	retDict['enclosingFolder3'] = None
	retDict['enclosingFolder2'] = None
	retDict['enclosingFolder1'] = None
	retDict['fileName'] = None
	retDict['xPixel'] = ''
	retDict['yPixel'] = ''
	retDict['numSlices'] = ''
	retDict['numChannels'] = ''
	retDict['numFrames'] = ''
	retDict['xVoxel'] = ''
	retDict['yVoxel'] = ''
	retDict['zVoxel'] = ''
	retDict['unit'] = ''
	retDict['folderPath'] = ''
	retDict['filePath'] = ''
	return retDict
	
def getImpInfo(imp, filePath):
	"""
	If imp is not None then use imp exclusively, ignoring filePath
	If imp is None we will at least get file and path information from filePath
	
	Return: an Ordered Dictionary with file information like pixel and voxel size
	"""
		
	retDict = getDefaultDict()
	
	if imp is None:
		directory, fileName = os.path.split(filePath)
		
	else:
		#
		# use file info to get filanme and folder path
		fileinfo = imp.getOriginalFileInfo() # don't use getFileInfo()
		fileName = fileinfo.fileName
		directory = fileinfo.directory # don't use getFilePath()
		# remove trailing /  or \
		if directory.endswith(os.sep):
			directory = directory[:-1]
	
	# get the three enclosing folder
	enclosingFolder, enclosingFolder1 = os.path.split(directory)
	enclosingFolder, enclosingFolder2 = os.path.split(enclosingFolder)
	enclosingFolder, enclosingFolder3 = os.path.split(enclosingFolder)

	retDict['enclosingFolder3'] = enclosingFolder3
	retDict['enclosingFolder2'] = enclosingFolder2
	retDict['enclosingFolder1'] = enclosingFolder1
	retDict['fileName'] = fileName
	# put these at end
	#retDict['folderPath'] = directory
	#retDict['filePath'] = os.path.join(directory, fileName)

	#
	# Returns the dimensions of this image (width, height, nChannels, nSlices, nFrames) as a 5 element int array.
	if imp is not None:
		dimensions = imp.getDimensions()
		retDict['xPixel'] = dimensions[0]
		retDict['yPixel'] = dimensions[1]
		retDict['numChannels'] = dimensions[2]
		retDict['numSlices'] = dimensions[3]
		retDict['numFrames'] = dimensions[4]
	
	#
	# use calibratio to get x/y/z voxel size
	if imp is not None:
		cal = imp.getCalibration()

		xVoxel = cal.pixelWidth
		yVoxel = cal.pixelHeight
		zVoxel = cal.pixelDepth
		unit = cal.getUnit()

		retDict['xVoxel'] = xVoxel
		retDict['yVoxel'] = yVoxel
		retDict['zVoxel'] = zVoxel
		retDict['unit'] = unit

	retDict['folderPath'] = directory
	retDict['filePath'] = os.path.join(directory, fileName)

	return retDict

def myLoadFile(filePath, doShow=False):
	"""
	Load a file from filePath and call getImpInfo()
	
	Return: Ordered dictionary of basic parameters
	"""

	print('    myLoadFile() filePath:', filePath)
	
	imp = None
	if filePath.endswith('.tif'):
		imp = IJ.openImage(filePath) #IJ.open(filePath) opens an image window and does NOT return anything
	else:
		try:
			imps = BF.openImagePlus(filePath) # list with one imp
			if len(imps)==1:
				imp = imps[0]
			else:
				print('ERROR: myLoadOIR() BF.openImagePlus got more than one imp in path:', path)
				return None
		except (loci.formats.UnknownFormatException) as e:
			print('        ERROR: ', e)
			
	# if imp is None we will at least get proper file paths
	myInfoDict = getImpInfo(imp, filePath)
	
	#print(json.dumps(myInfoDict, indent=4))

	if doShow:
		return myInfoDict, imp
	else:
		return myInfoDict
	
def myRun(folderPath, theseFileExtensions=['.oir']):
	"""
	Recursively traverse down folderPath
	and open/process all files ending in one of [theseFileExtensions]
	"""
	
	if not os.path.isdir(folderPath):
		print('ERROR: myRun() did not get a folder path folderPath:', folderPath)
		return
	
	print('myRun() folderPath:', folderPath)
	
	myInfoDictList = []
	
	for dirpath, dirnames, files in os.walk(folderPath):
		for name in files:
			fileNameNoExtension, fileExtension = os.path.splitext(name)
			if fileExtension in theseFileExtensions:
				filePath = os.path.join(dirpath, name)
				#
				myInfoDict = myLoadFile(filePath)
				#
				myInfoDictList.append(myInfoDict)
	
	# number of files we processed
	numFiles = len(myInfoDictList)
	
	# save
	enclosingFolderName = os.path.split(folderPath)[1]
	saveDatabaseFilePath = os.path.join(folderPath, enclosingFolderName + '_db.csv')
	
	print('    processed', numFiles, 'files, saving database in', saveDatabaseFilePath)
	
	with open(saveDatabaseFilePath, 'w') as f:
		for rowIdx, myInfoDict in enumerate(myInfoDictList):
			if rowIdx==0:
				# headers
				headerStr = ''
				for k,v in myInfoDict.items():
					headerStr += k + ','
				print(headerStr, file=f)
			rowStr = ''
			for k,v in myInfoDict.items():
				rowStr += str(v) + ','
			print(rowStr, file=f)
			
if __name__ in ['__main__', '__builtin__']:

	# debug file open errors
	#gTheseFileExtensions = ['.oir', '.tif', '.csv']

	#
	# ask user for a folder path
	userFolder = DirectoryChooser('Choose a folder')
	folderPath = userFolder.getDirectory()
	if folderPath is None:
		print('Warning: User did not choose a folder')	
	else:
		# remove trailing /  or \
		if folderPath.endswith(os.sep):
			folderPath = folderPath[:-1]		
		#
		myRun(folderPath, gTheseFileExtensions)
		#

	print('    simpleFileInfo is done !!!')
