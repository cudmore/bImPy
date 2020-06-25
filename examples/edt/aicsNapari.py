import os, sys, glob

import napari
import bimpy

import myDaskNapari

if __name__ == '__main__':

	# this works
	if 1:
		daskDict = myDaskNapari.getDaskGridDict()
		daskDict['path'] = '/Users/cudmore/box/data/nathan/20200518/analysisAics'
		daskDict['prefixStr'] = '20200518__A01_G001_'
		daskDict['finalPostfixList'] = ['', 'mask']
		daskDict['channelList'] = [2]

		daskDict['commonShape'] = (64,512, 512)

		daskDict['commonVoxelSize'] = (1, 0.621480865, 0.621480865)

		# analysis is already trimmed
		daskDict['trimPercent'] = 15
		daskDict['trimPixels'] = None # calculated
		daskDict['nRow'] = 8
		daskDict['nCol'] = 6
	
		myDaskNapari.openDaskNapari2(daskDict)
	
	
