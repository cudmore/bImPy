import os, sys, argparse

import numpy as np
import pandas as pd

import bimpy

from vascDen import myGetDefaultStackDict
from vascDen import myGetDefaultParamDict
from vascDen import setupAnalysis
from vascDen import updateMasterCellDB
from vascDen import mySave
from vascDen import _printStackParams

################################################################################
# see: https://stackoverflow.com/questions/6190331/how-to-implement-an-ordered-default-dict
'''
mySetDict(dict, key, value):
	if key in dict.keys():
		# set
	else:
		# error
'''
		
################################################################################
def myRun(path, masterFilePath):
	print('cellDen.myRun() path:', path)
		
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
	
	#
	# median filter
	#medianKernelSize = (3, 10,10)
	medianKernelSize = (3, 5, 5)
	filteredStack = bimpy.util.morphology.medianFilter(stackData, kernelSize=medianKernelSize)
	stackDict['filtered']['data'] = filteredStack
	paramDict['medianKernelSize'] = medianKernelSize

	#
	# threshold
	myScale = 0.15 # vasc channel is 0.06
	thresholdStack = bimpy.util.morphology.threshold_min_max(filteredStack, myScale=myScale)
	paramDict['thresholdAlgorithm'] = 'threshold_min_max'
	paramDict['thresholdScale'] = myScale
	
	# trying otsu because data from 20200518 looks like there are 2 sets of intensities???
	#thresholdStack = bimpy.util.morphology.threshold_otsu(filteredStack)
	#paramDict['thresholdAlgorithm'] = 'threshold_otsu'
	
	stackDict['threshold']['data'] = thresholdStack

	#
	# fill holes
	#filledHolesStack = myFillHoles(thresholdStack)
	finalMask = bimpy.util.morphology.fillHoles(thresholdStack)
	stackDict['finalMask']['data'] = finalMask
	_printStackParams('finalMask 2', finalMask)
	
	#
	# edt
	# edt ? distance from background to hcn4 cells?
	# edt requires (finalMask AND convex hull)
	
	"""
		need a cross channel edt, something like this
		
		these_hcn1_pixels = stackDict1['mask']==1 # pixels in hcn1 mask
		_printStackParams('these_hcn1_pixels', these_hcn1_pixels)
		edtFinal = stackDict2['edt'].copy()
		edtFinal[:] = np.nan
		edtFinal[these_hcn1_pixels] = stackDict2['edt'][these_hcn1_pixels]	# grab hcn1 pixels from vascular edt
		stackDict1['edt'] = edtFinal
		_printStackParams('  ch1 edt', edtFinal)
	"""

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
	
	parser = argparse.ArgumentParser(description = 'Process an hcn4 .tif file')
	parser.add_argument('tifPath', nargs='*', default='', help='path to original .tif file')
	args = parser.parse_args() # args is a list of command line arguments

	if len(args.tifPath)>0:
		path = args.tifPath[0]		
	else:
		#
		#
		path = '/Users/cudmore/box/data/nathan/20200518/20200518__A01_G001_0002_ch1.tif'
		#path = '/Users/cudmore/box/data/nathan/20200518/20200518__A01_G001_0003_ch1.tif'
		path = '/Users/cudmore/box/data/nathan/20200518/20200518__A01_G001_0004_ch1.tif'
	
	myRun(path, masterFilePath)
