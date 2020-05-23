import os, argparse

import numpy as np
import scipy

import bimpy

def myDistanceMap(maskStack, hullMask, scale): #, includeDistanceLessThan=5):	
	
	print('  .myDistanceMap() scale:', scale, '... please wait')
	
	edtMask = maskStack.copy().astype(float)

	#
	# only accept maskStack pixels in hullMask
	# do this after
	
	#
	# invert the mask, edt will calculate distance from 0 to 1
	edtMask[edtMask==1] = 10
	edtMask[edtMask==0] = 1
	edtMask[edtMask==10] = 0

	distanceMap = scipy.ndimage.morphology.distance_transform_edt(edtMask, sampling=scale, return_distances=True)
	
	distanceMap = distanceMap.astype(np.float32) # both (matplotlib, imagej) do not do float16 !!!

	# only accept edt that is also in hullMask
	distanceMap[hullMask==0] = np.nan
	
	_printStackParams('output edt', distanceMap)

	return distanceMap

def _printStackParams(name, myStack):
	#print('  ', name, type(myStack), myStack.shape, myStack.dtype, 'dtype.char:', myStack.dtype.char, 'min:', np.min(myStack), 'max:', np.max(myStack))
	print('  ', name, myStack.shape, myStack.dtype, 'dtype.char:', myStack.dtype.char,
		'min:', round(np.nanmin(myStack),2),
		'max:', round(np.nanmax(myStack),2),
		'mean:', round(np.nanmean(myStack),2),
		)

if __name__ == '__main__':

	# eventually load all data from local path specified in myDataPath
	from myDataPath import myDataPath
	print('myDataPath:', myDataPath)
	
	parser = argparse.ArgumentParser(description = 'raw _ch1 file')
	parser.add_argument('rawpath', nargs='*', default='', help='raw _ch1.tif')
	args = parser.parse_args() # args is a list of command line arguments

	if len(args.rawpath)>0:
		path = args.rawpath[0]		
	else:
		#path = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0007_ch1.tif'
		path = '20200116/20190116__A01_G001_0007_ch1.tif'

	
	# using local myDataPath
	if not path.startswith(myDataPath):
		path = os.path.join(myDataPath, path)
	
	folderpath, filename = os.path.split(path)
	filenamenoextension, tmpExt = filename.split('.')
	
	savePath = os.path.join(folderpath, 'analysis2')
	saveBase = os.path.join(savePath, filenamenoextension)
	
	print('  savePath:', savePath)
	print('  saveBase:', saveBase) # append _labeled.tif to this

	#
	# load finalMask (not edited)
	finalMaskPath = saveBase + '_finalMask.tif'
	print('  loading finalMask:', finalMaskPath)
	finalMaskData, tiffHeader = bimpy.util.bTiffFile.imread(finalMaskPath)
	_printStackParams('finalMaskData', finalMaskData)

	#
	# load hull
	hullPath = saveBase + '_finalMask_hull.tif'
	print('  loading finalMask_hull:', hullPath)
	hullData, ignoreThis = bimpy.util.bTiffFile.imread(hullPath)
	_printStackParams('hullData', hullData)

	#
	# distance map
	scale = (tiffHeader['zVoxel'], tiffHeader['xVoxel'], tiffHeader['yVoxel'])
	#distanceMap = None
	distanceMap = myDistanceMap(finalMaskData, hullData, scale=scale)
	
	#
	# save
	savePath = saveBase + '_finalMask_edt.tif'
	print('saving:', savePath)
	if distanceMap is not None:
		bimpy.util.bTiffFile.imsave(savePath, distanceMap, overwriteExisting=True)
	
	