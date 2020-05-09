"""
"""

import os, json
from collections import OrderedDict

import pandas as pd
import numpy as np

import tifffile
import napari

import bimpy

def myNapari(results):
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

def myDensity(path, genotype, sex, myCellNumber, doNapari=False):
	"""
	we really need to run this multiple times !!!

	subsets of:
		branch type
		branch length
	"""

	# so we can fetch skeleton .csv
	dataRoot = '/Users/cudmore/Sites/smMicrotubule/data'
	analysisRoot = '/Users/cudmore/Desktop/samiVolume' # remember, _ch1.tif DOES NOT have scale here !!!!!

	if not os.path.isfile(path):
		print('ERROR: myDensity did not find path:', path)
		return None
	
	stackDict = OrderedDict() # keep stack of all our stacks

	#
	# load image
	## NEED TO LOAD FROM RAW DATA
	pathToRawDataFile = path.replace(analysisRoot, dataRoot) #### using analysisRoot
	#
	imageStack = tifffile.imread(pathToRawDataFile)
	stackDict['imageStack'] = imageStack

	## NEED TO LOAD FROM RAW DATA
	# append k:v to this ordered dict
	resultDict = bimpy.util.getTiffFileInfo(pathToRawDataFile)
	voxelVolume = resultDict['zVoxel'] * resultDict['xVoxel'] * resultDict['yVoxel'] 
	resultDict['voxelVolume'] = voxelVolume
	#resultDict = OrderedDict() 
	
	resultDict['genotype'] = genotype
	resultDict['sex'] = sex
	resultDict['myCellNumber'] = myCellNumber

	tmpPath, tmpFileName = os.path.split(path) #### 
	tmpFileNameNoExtension, tmpExtension = tmpFileName.split('.')
	analysisBaseFilePath = os.path.join(tmpPath, tmpFileNameNoExtension) # append to this to get files
		
	#
	# load entire mask '_filledHolesMask.tif'
	fullMaskPath = analysisBaseFilePath + '_filledHolesMask.tif'
	fullMaskStack = tifffile.imread(fullMaskPath)
	numPixelsInFullMask = np.count_nonzero(fullMaskStack == 1)
	resultDict['nMask'] = numPixelsInFullMask # number of pixels in the mask
	resultDict['vMask'] = numPixelsInFullMask * voxelVolume
	stackDict['fullMaskStack'] = fullMaskStack
	
	#
	# load eroded mask '_erodedMask.tif'
	erodedMaskPath = analysisBaseFilePath + '_erodedMask.tif'
	erodedMaskStack = tifffile.imread(erodedMaskPath)
	numPixelsInErodedMask = np.count_nonzero(erodedMaskStack == 1)
	resultDict['nEroded'] = numPixelsInErodedMask # number of pixels in the mask
	resultDict['vEroded'] = numPixelsInErodedMask * voxelVolume
	stackDict['erodedMaskStack'] = erodedMaskStack
	
	#
	# load ring mask '_ringMask.tif'
	ringMaskPath = analysisBaseFilePath + '_ringMask.tif'
	ringMaskStack = tifffile.imread(ringMaskPath)
	numPixelsInRingMask = np.count_nonzero(ringMaskStack == 1)
	resultDict['nRing'] = numPixelsInRingMask # number of pixels in the mask
	resultDict['vRing'] = numPixelsInRingMask * voxelVolume
	stackDict['ringMaskStack'] = ringMaskStack
	
	'''
	print('  numPixelsInFullMask:', numPixelsInFullMask)
	print('  numPixelsInErodedMask:', numPixelsInErodedMask)
	print('  numPixelsInRingMask:', numPixelsInRingMask)
	'''
	
	#
	# load skel (ends in '_ch2_skel.csv')
	## NEED TO LOAD FROM RAW DATA
	analysisPath = path.replace(analysisRoot, dataRoot) #### using analysisRoot
	tmpPath, tmpFileName = os.path.split(analysisPath) #### 
	tmpFileNameNoExtension, tmpExtension = tmpFileName.split('.')
	skeleFileName = tmpFileNameNoExtension + '_skel.csv'
	skelFilePath = os.path.join(tmpPath, skeleFileName)
	#
	skileFileName = tmpFileNameNoExtension + '_skel.csv'
	skelFilePath = os.path.join(tmpPath, skileFileName)
	if not os.path.isfile(skelFilePath):
		print('ERROR: myDensity did not find skelFilePath:', skelFilePath)
		return None
	# load
	dfSkel = pd.read_csv(skelFilePath)
	
	#
	# append new columns
	'''
	dfSkel['genotype'] = genotype
	dfSkel['sex'] = sex
	dfSkel['myCellNumber'] = myCellNumber
	'''
	#
	dfSkel['inMask'] = np.nan
	dfSkel['inEroded'] = np.nan
	dfSkel['inRing'] = np.nan

	dfColumns = ['branch-distance', 'image-coord-src-0', 'image-coord-src-1', 'image-coord-src-2', 'image-coord-dst-0', 'image-coord-dst-1', 'image-coord-dst-2', 'euclidean-distance']
	print(dfSkel[dfColumns].head())
	
	#
	# put (rounded) skel in stack to make sure z/x/y is correct
	# this works !!!
	mySkelStack = imageStack.copy()
	mySkelStack[:] = 0
	# number of branches in each mask
	nInMask = 0
	nInEroded = 0
	nInRing = 0
	nInNoMask = 0 # keep track of branches that we not in any mask (mask, eroded, ring)
	# total branch length in each mask
	lenTotal = 0 # total len in our skel
	lenInMask = 0
	lenInEroded = 0
	lenInRing = 0
	#
	nBranches = dfSkel.shape[0]
	for rowIdx in range(nBranches):
		# each row is a skeleton branch/segment
		thisBranchLength = dfSkel.at[rowIdx, 'branch-distance']
		lenTotal += thisBranchLength
		
		# src
		z1 = dfSkel.at[rowIdx, 'image-coord-src-0']
		x1 = dfSkel.at[rowIdx, 'image-coord-src-1']
		y1 = dfSkel.at[rowIdx, 'image-coord-src-2']
		z1 = int(z1)
		x1 = int(x1)
		y1 = int(y1)
		mySkelStack[z1,x1,y1] = 1

		# dst
		z2 = dfSkel.at[rowIdx, 'image-coord-dst-0']
		x2 = dfSkel.at[rowIdx, 'image-coord-dst-1']
		y2 = dfSkel.at[rowIdx, 'image-coord-dst-2']
		z2 = int(z2)
		x2 = int(x2)
		y2 = int(y2)
		mySkelStack[z2,x2,y2] = 1

		# which masks are this branch/segment in ???
		srcInMask = fullMaskStack[z1, x1, y1] == 1
		srcInEroded = erodedMaskStack[z1, x1, y1] == 1
		srcInRing = ringMaskStack[z1, x1, y1] == 1
		
		dstInMask = fullMaskStack[z2, x2, y2] == 1
		dstInEroded = erodedMaskStack[z2, x2, y2] == 1
		dstInRing = ringMaskStack[z2, x2, y2] == 1
		
		inMask = False
		inEroded = False
		inRing = False
		if srcInMask and dstInMask:
			inMask = True
			dfSkel.at[rowIdx, 'inMask'] = 1 # update df
			lenInMask += thisBranchLength
			nInMask += 1
		if srcInEroded and dstInEroded:
			inEroded = True
			dfSkel.at[rowIdx, 'inEroded'] = 1 # update df
			lenInEroded += thisBranchLength
			nInEroded += 1
		if srcInRing and dstInRing:
			inRing = True
			dfSkel.at[rowIdx, 'inRing'] = 1 # update df
			lenInRing += thisBranchLength
			nInRing += 1
	
		# sanity
		if not inMask and not inEroded and not inRing:
			#print('  branch', rowIdx, 'was not in any mask?')
			#print('    ', x1, y1, z1, x2, y2, z2)
			nInNoMask += 1
			
	#
	stackDict['mySkelStack'] = mySkelStack

	# assert this is correct
	'''
	print('  nBranches:', nBranches, 'nInMask:', nInMask, 'nInEroded:', nInEroded, 'nInRing:', nInRing)
	print('            ', 'lenInMask:', lenInMask, 'lenInEroded:', lenInEroded, 'lenInRing:', lenInRing)
	'''
	
	# the discrepancy here is that some branches span both ring to eroded !!!!!

	resultDict['nBranches'] = nBranches
	# number of branches in each mask
	resultDict['nInNoMask'] = nInNoMask # branches that we not in any mask
	resultDict['nInMask'] = nInMask
	resultDict['nInEroded'] = nInEroded
	resultDict['nInRing'] = nInRing
	# length of branches in each mask
	resultDict['lenTotal'] = lenTotal # total length in our skel
	resultDict['lenInMask'] = lenInMask
	resultDict['lenInEroded'] = lenInEroded
	resultDict['lenInRing'] = lenInRing
	
	#
	# calculate density
	if resultDict['vMask'] > 0:
		resultDict['dInMask'] = lenInMask / resultDict['vMask']
	else:
		resultDict['dInMask'] = 0
	
	if resultDict['vEroded'] > 0:
		resultDict['dInEroded'] = lenInMask / resultDict['vEroded']
	else:
		resultDict['dInEroded'] = 0
	
	if resultDict['vRing'] > 0:
		resultDict['dInRing'] = lenInMask / resultDict['vRing']
	else:
		resultDict['dInRing'] = 0
	#
	
	'''
	if (nInEroded + nInRing) == nInMask:
		print('  got good assignment of branches into eroded/ring')
	else:
		print('  ERROR in assignment of branches into eroded/ring')
	'''
		
	resultDict['path'] = path # remember my copied analysis folder has _ch1.tif with NO VOXEL SIZE

	#
	# open in napari
	if doNapari:
		myNapari(stackDict)

	#print(json.dumps(resultDict, indent=4))

	return resultDict
		
if __name__ == '__main__':

	analysisRoot = '/Users/cudmore/Desktop/samiVolume' # remember, _ch1.tif DOES NOT have scale here !!!!!
	#dataPath = '/Users/cudmore/Sites/smMicrotubule/data'
	
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
	# is now broekn with getting (genotype, sex)
	#batchFileList = ['one-wt-female.txt']

	fileDictList = []
	numFiles = 0
	for batchFile in batchFileList:
		# get (genotype,sex) from batchFile
		if batchFile == 'one-wt-female.txt':
			genotype = 'wt'
			sex = 'female'
		else:
			baseName = os.path.basename(batchFile)
			tmpFileNoExtension, tmpExtension = baseName.split('.')
			genotype, sex = tmpFileNoExtension.split('-')
		
		fileList = bimpy.util.getFileListFromFile(batchFile)
	
		nFile = len(fileList)
		
		myCellNumber = 0
		for fileNum, file in enumerate(fileList):
			print('*** file', fileNum+1, 'of', nFile, 'file:', file)
			# my condition file start with ../data/ todo: clean upp paths in condition file
			file = file.replace('../data/', '')
			file = os.path.join(analysisRoot,file) # USING analysisRoot !!!
			print(file)
			
			##
			##
			tiffFileInfo = myDensity(file, genotype, sex, myCellNumber, doNapari=False)
			##
			##
			if tiffFileInfo is not None:
				fileDictList.append(tiffFileInfo)
			
			numFiles += 1
			myCellNumber += 1
			
	print('done processing numFiles:', numFiles)
	saveDensityResultsFile = '/Users/cudmore/Desktop/density-results.csv'
	print('saving:', saveDensityResultsFile)
	bimpy.util.dictListToFile(fileDictList, saveDensityResultsFile)		
		