"""
Script to process a folder of ch1/ch2 Tiff files into a visual grid
"""

import os, sys, math
import numpy as np
import tifffile

import matplotlib.pyplot as plt

def myMakeGrid(path, prefixStr, channel, nRow, nCol):
    
    if channel == 1:
        postfixStr = '_ch1.tif'
    elif channel == 2:
        postfixStr = '_ch2.tif'
        
    # make nRow X nCol grid of integers
    tmpIntegerGrid = np.arange(1,nRow*nCol+1) # Values are generated within the half-open interval [start, stop)
    tmpIntegerGrid = np.reshape(tmpIntegerGrid, (nRow, nCol)) # reshape into nRow X nCol
    # reverse numbers in every other row (to replicate 'snake' image acquisition)
    integerGrid = tmpIntegerGrid.copy()
    integerGrid[1::2] = tmpIntegerGrid[1::2,::-1] # this is obfuscated

    # make a list of file names following order of snake pattern in integerGrid
    filenames = [prefixStr + str(x).zfill(4) + postfixStr for x in integerGrid.ravel()]
    # make all file names be full path
    filenames = [os.path.join(path, x) for x in filenames]

    # check that all files exist, display will fail when loading file that does not exist
    tifDataList = []
    tifMaxList = []
    commonShape = None
    for idx, tiffPath in enumerate(filenames):
        if os.path.isfile(tiffPath):
            # raw data
            stackData = tifffile.imread(tiffPath)
            tifDataList.append(stackData)
            
            # max project
            theMax = np.max(stackData, axis=0)
            tifMaxList.append(theMax)
            
            # common shape
            if commonShape is None:
                commonShape = stackData.shape
                print('myMakeGrid() commonShape:', commonShape)
                
        else:
            # todo: This is a bug if we missing files
            print('  WARNING: Did not find file:', tiffPath)
            tifDataList.append(None)
            tifMaxList.append(None)
    
    #
    return tifDataList, tifMaxList, filenames, integerGrid

def plotGrid(folderPath, nRow, nCol, fileNameList, fileIdxList, tifMaxList, plotLabels, wSpace, hSpace):
	print('please wait ... folderPath:', folderPath)

	#plotLabels = True # plot the file index in the middle of the image

	# choose a width (in inches) and we will calculate a respective height
	figWidth = 10 #nCol
	#figHeight = nRow
	heightMult = nRow / nCol
	figHeight = figWidth * heightMult

	# make (nRow x nCol) subplots
	fig, axs = plt.subplots(nrows=nRow, ncols=nCol,
							sharex=True, sharey=True, figsize=(figWidth,figHeight), constrained_layout=False)
	axs = axs.ravel() # flatten all subplots into [0, 1, 2, ...]

	for idx, fileName in enumerate(fileNameList):
		fileIdx = fileIdxList[idx] # this list is snaked
		plotIdx = fileIdx - 1 # matplotlib is 0 based, our file names are 1 based

		#stackData = tifDataList[plotIdx]
		maxData = tifMaxList[plotIdx]

		# turn off axes labels
		axs[plotIdx].axis('off')

		if maxData is None:
			continue
			
		#axs[plotIdx].imshow(maxData, cmap=cmap) # looks awefull ???
		axs[plotIdx].imshow(maxData, aspect='equal')
	

		#print('plotIdx:', plotIdx, 'fileIdx:', fileIdx)
	
		# put label above image
	
		# put label in middle of image
		if plotLabels:
			fileIdxLabel = idx + 1 # snakes filename 0001, 0002, 0003, ...
			halfHeight = maxData.shape[0]/2
			halfWidth = maxData.shape[1]/2
			fontsize = 14
			axs[plotIdx].text(halfHeight, halfWidth, '{:d}'.format(fileIdxLabel), ha='center', va='center',
				fontsize=fontsize,
				color='k',
				bbox=dict(boxstyle='round', facecolor='white', edgecolor='0.3'))

	# Pad each stack with some border white space
	plt.subplots_adjust(wspace=wSpace, hspace=hSpace)

	# needed when we are in a script (not in Jupyter)
	plt.show()
	
if __name__ == '__main__':

	# either this
	if 1:
		folderPath = '/Users/cudmore/box/data/nathan/20200518'
		prefixStr = '20200518__A01_G001_'
		nRow = 8
		nCol = 6

	# or this
	if 0:
		folderPath = '/Users/cudmore/box/data/nathan/20200519'
		prefixStr = '20200519__A01_G001_'
		nRow = 17
		nCol = 7

	# specify the channel
	channel = 1
	#channel = 2 # does not look so good for CD-31 because of endocardium

	# myMakeGrid is defined above
	tifDataList, tifMaxList, fileNameList, fileIdxMatrix = myMakeGrid(folderPath, prefixStr, channel, nRow, nCol)

	print('fileIdxMatrix:')
	print(fileIdxMatrix)

	fileIdxList = fileIdxMatrix.ravel() # flatten 2d to 1d, we still need to know (nRow, nCol)

	print('done with myMakeGrid()')
	
	#
	# plot
	plotLabels = True
	wSpace = 0.02 # a little white space between stacks
	hSpace = 0.02
	#wSpace = -0.1 # to remove border
	#hSpace = -0.1
	plotGrid(folderPath, nRow, nCol, fileNameList, fileIdxList, tifMaxList, plotLabels, wSpace, hSpace)
	
	
	