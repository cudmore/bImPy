import os, sys
import json
from collections import OrderedDict

from . import readVoxelSize # must be in same folder

def getTiffFileInfo(path):
	theRet = OrderedDict()
	
	enclosingPath, filename = os.path.split(path)
	enclosingPath1, enclosingFolder1 = os.path.split(enclosingPath)
	enclosingPath2, enclosingFolder2 = os.path.split(enclosingPath1)
	enclosingPath3, enclosingFolder3 = os.path.split(enclosingPath2)
	
	theRet['enclosingFolder3'] = enclosingFolder3
	theRet['enclosingFolder2'] = enclosingFolder2
	theRet['enclosingFolder1'] = enclosingFolder1
	
	xVoxel, yVoxel, zVoxel, shape = readVoxelSize(path, getShape=True)

	theRet['filename'] = filename
	theRet['xVoxel'] = xVoxel
	theRet['yVoxel'] = yVoxel
	theRet['zVoxel'] = zVoxel
	theRet['xPixels'] = shape[0]
	theRet['yPixels'] = shape[1]
	theRet['zPixels'] = shape[2]
	'''
	theRet['folder3'] = enclosingPath3
	theRet['folder2'] = enclosingPath2
	theRet['folder1'] = enclosingPath1
	'''
	
	return theRet

if __name__ == '__main__':
	path = '/Users/cudmore/Sites/smMicrotubule/data/191230/BIN1_smKO_Male/Cell_12/12_5ADVMLEG1L1_ch2.tif'
	info = getTiffFileInfo(path)
	
	import json
	print(json.dumps(info, indent=4))