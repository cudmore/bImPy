"""
Author: Robert Cudmore
Date: 20200424

Purpose:
	This is ImageJ/Fiji Jython code to convert Olympus .oir files to .tif files.

What it does:
	- given a folder, it will recursively seach that folder and all enclosing folders
	- for each .oir file it finds
		- open it
		- split the color channels
		- save each color channel as a different .tif file with ('_ch1.tif', '_ch2.tif', '_ch3.tif', ...)
		- save a single .csv text file with the acquisition parameters of each file
		
How to use:
	1) make sure "bSimpleFileInfo.py" is in the same folder as this file, e.g. "bSimpleConvert.py"
	2) Drag and drop this file ("bSimpleConvert.py") onto ImageJ/Fiji, just like a .tif file.
	3) Once this file is open in the editor, run it with either Menu 'Run - Run' or pressing keyboard 'command+r'
	4) Select a folder to convert and hit ok/select

Output:
	For each .oir file, single channle .tif files ('_ch1.tif', _ch2.tif', 'ch_3.tif', ...)
	A single .csv file saved into the selected folder.

Parameter:
	The user can set these parameters (near the end of the file) to control behavior

	thisFileEnding = None # to process all files ending with thisFileEnding
	#thisFileEnding = 'ADVMLEG1L1.oir' # deconvolved is like 12_5ADVMLEG1L1.oir
	#theseFileExtensions=['.tif']
	theseFileExtensions=['.oir']
	convertTo8Bit = True
	thisDirDepth = 0 # use float('inf') to recurse all subfolder
	allowOverwrite = False

Fiji API reference:
	ImagePlus: https://imagej.nih.gov/ij/developer/api/ij/ImagePlus.html
	ChannelSplitter: https://imagej.nih.gov/ij/developer/api/ij/plugin/ChannelSplitter.html
"""

from __future__ import print_function  # Only needed for Python 2, MUST be first import
import os, sys
import json

from ij import IJ
from ij.io import DirectoryChooser, OpenDialog
from ij.plugin import ChannelSplitter
from ij.process import ImageConverter

# lifeline version is 1.51n99, newer (April 2020) version is 1.52p99
fijiVersion = IJ.getFullVersion()
print('ImageJ/Fiji Version:', fijiVersion)

# allows us to import our own .py files, e.g. 'import bSimpleFileInfo
import inspect
print(' . ', inspect.getsourcefile(lambda:0))
myFilePath = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0)))
print('    myFilePath:', myFilePath)
sys.path.append(myFilePath)

# must be in same folder as this file 
# and folder needs an empty __init__.py file
try:
	import bSimpleFileInfo
except (ImportError) as e:
	print('ERROR: make sure the file "bSimpleFileInfo.py" is in the same folder as this file ("bSimpleConvert.py")')
	raise
	
def convertAndSaveFile(fullFilePath, convertTo8Bit=False, allowOverwrite=False):
	"""
	"""
	print('  convertAndSaveFile() fullFilePath:', fullFilePath)
	
	folderPath, fileName = os.path.split(fullFilePath)
	fileNameNoExtension = os.path.splitext(fileName)[0]
	saveFileNoExtension = os.path.join(folderPath, fileNameNoExtension)
	
	#
	# load file and build a dict of parameters like (channels, pixels, voxels)
	myFileInfo, imp = bSimpleFileInfo.myLoadFile(fullFilePath, doShow=True)
	
	if convertTo8Bit:
		# from (ImagePlus.GRAY8, ImagePlus.GRAY16, ImagePlus.GRAY32, ImagePlus.COLOR_256 or ImagePlus.COLOR_RGB)
		myType = imp.getType()
		if myType in [1,2]:
			ic = ImageConverter(imp) # converts channelImp in place
			scaleConversions = True
			ic.setDoScaling(scaleConversions) # scales inensities to fill 0...255
			ic.convertToGray8()		

	#
	# split channels
	channelArray = ChannelSplitter.split(imp) # returns an array of imp
	
	for channelIdx, channelImp in enumerate(channelArray):
		# channelImp is an imp, this will NOT have fileinfo (we just created it)
		#channelImp.show()
		
		saveFilePath = saveFileNoExtension + '_ch' + str(channelIdx+1) + '.tif'
		print('    ch:', channelIdx+1, 'saveFilePath:', saveFilePath)
		
		if not allowOverwrite and os.path.isfile(saveFilePath):
			print(' .   not saving, file already exists', saveFilePath)
		else:
			IJ.save(channelImp, saveFilePath)

	return myFileInfo
	
def convertFolder(folderPath, theseFileExtensions=['.oir'], thisFileEnding=None, convertTo8Bit=False, thisDirDepth=float('inf'), allowOverwrite=False):
	"""
	Recursively traverse down folderPath
	and open/process all files ending in one of [theseFileExtensions]

	save a _db.csv file in folderPath with image acquisition parameters 

	set thisDirDepth=0 to just do the given folder (no sub folders)
	"""
	
	if not os.path.isdir(folderPath):
		print('ERROR: convertFolder() did not get a folder path folderPath:', folderPath)
		return
	
	print('convertFolder() folderPath:', folderPath)
	
	myInfoDictList = []
	
	#for dirpath, dirnames, files in os.walk(folderPath):
	for dirDepth, (dirpath, dirnames, files) in enumerate(os.walk(folderPath)):
		if dirDepth > thisDirDepth:
			break
		for name in files:
			fileNameNoExtension, fileExtension = os.path.splitext(name)
			if fileExtension in theseFileExtensions:
				if thisFileEnding is not None:
					if name.endswith(thisFileEnding):
						pass
					else:
						continue
				filePath = os.path.join(dirpath, name)
				#
				myInfoDict = convertAndSaveFile(filePath, convertTo8Bit=convertTo8Bit, allowOverwrite=allowOverwrite)
				#
				myInfoDictList.append(myInfoDict)
	
	# number of files we processed
	numFiles = len(myInfoDictList)
	
	#
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

	###
	###
	### PARAMETERS
	###
	###
	thisFileEnding = None # to process all files ending with thisFileEnding
	#thisFileEnding = 'ADVMLEG1L1.oir' # deconvolved is like 12_5ADVMLEG1L1.oir
	#theseFileExtensions=['.tif']
	theseFileExtensions=['.oir']
	convertTo8Bit = True
	thisDirDepth = 0 # use float('inf') to recurse all subfolder
	allowOverwrite = False
	
	print(' . thisFileEnding:', thisFileEnding)
	print(' . theseFileExtensions:', theseFileExtensions)
	print(' . convertTo8Bit:', convertTo8Bit)
	
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
		convertFolder(folderPath,
			theseFileExtensions=theseFileExtensions,
			thisFileEnding=thisFileEnding,
			convertTo8Bit=convertTo8Bit,
			thisDirDepth=thisDirDepth,
			allowOverwrite=allowOverwrite)
		#

	print('simpleConvert is done !!!')
