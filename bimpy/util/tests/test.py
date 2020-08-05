"""
unit tests
"""

import time

import numpy as np

import tifffile

import bimpy

def test_removeSmallLabels2():
	print('test_removeSmallLabels2()')
	
	path = '/Volumes/ThreeRed/nathan/20200717/analysisAics/20200717__A01_G001_0014_ch2_labeled.tif'
	labeledData = tifffile.imread(path)
	
	print('  labeledData:', np.min(labeledData), np.max(labeledData))
	
	removeSmallerThan = 100
	
	myTimer = bimpy.util.bTimer('removeSmallLabels2')
	
	labeledDataWithout, labeledDataRemoved, labelIdx, labelCount = \
			bimpy.util.morphology.removeSmallLabels2(labeledData, removeSmallerThan, timeIt=True, verbose=True)
			
	#
	# save the labeled stacks
	tifffile.imsave('/Users/cudmore/Desktop/labeledDataWithout.tif', labeledDataWithout)
	tifffile.imsave('/Users/cudmore/Desktop/labeledDataRemoved.tif', labeledDataRemoved)
	
	np.save('/Users/cudmore/Desktop/labelIndices', labelIdx) # index of each label (may be out of order?)
	np.save('/Users/cudmore/Desktop/labelCount', labelCount) # count for each label
	
	print(myTimer.elapsed())
	
if __name__ == '__main__':
	
	test_removeSmallLabels2()