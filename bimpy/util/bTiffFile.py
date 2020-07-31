"""
Author: Robert Cudmore
Date: 20200504

Purpose:
	Read and write .tif files along with their respective ImageJ/Fiji headers.
	
	Header includes
		x/y/z voxel size
		units: ('pixels', micron', 'um')
		x/y/z pixels

"""

import os, sys, json
from collections import OrderedDict

import tifffile

def imsave(path, imageData, tifHeader=None, overwriteExisting=False):
	"""
	Save the 3d data into file path with tif header information
	
	path: full path to file to save
	imageData: 3d numpy ndarray with order (slices, x, y)
	tifHeader: dictionary with keys ['xVoxel'], ['yVoxel'], ['zVoxel'] usually in um/pixel
	"""

	if os.path.isfile(path) and not overwriteExisting:
		print('error: bTiffFile.imsave() file already exists and overwriteExisting is False, path:', path)
		return None
		
	# get metadata from StackHeader
	#ijmetadata = {}
	#ijmetadataStr = self.header.getMetaData()
	#ijmetadata['Info'] = ijmetadataStr

	# default
	resolution = (1., 1.)
	metadata = {'spacing':1, 'unit':'pixel'}
	
	if tifHeader is not None:
		xVoxel = tifHeader['xVoxel']
		yVoxel = tifHeader['yVoxel']
		zVoxel = tifHeader['zVoxel']

		resolution = (1./xVoxel, 1./yVoxel)
		metadata = {
			'spacing': zVoxel,
			'unit': tifHeader['unit'] # could be ('micron', 'um', 'pixel')
		}

	# my volumes are zxy, fiji wants TZCYXS
	#volume.shape = 1, 57, 1, 256, 256, 1  # dimensions in TZCYXS order
	if len(imageData.shape) == 2:
		numSlices = 1
		numx = imageData.shape[0]
		numy = imageData.shape[1]
	elif len(imageData.shape) == 3:
		numSlices = imageData.shape[0]
		numx = imageData.shape[1]
		numy = imageData.shape[2]
	else:
		print('error, bTiffFile.imsave() can only save 2d or 3d images and stacks!')
		return False
		
	dtypeChar = imageData.dtype.char
	if dtypeChar == 'e':
		# see: https://github.com/matplotlib/matplotlib/issues/15432
		print('warning: bTiffFile.imsave() is NOT saving as ImageJ .tif file (There will be no header information.')
		print('    This happend with np.float16, dtype.char is "e". np.float16 will not open in Fiji or Matplotlib !!!')
		tifffile.imwrite(path, imageData) #, ijmetadata=ijmetadata)
	else:
		# this might change in caller?
		# this DOES change caller
		imageData = imageData.copy()
		imageData.shape = 1, numSlices, 1, numx, numy, 1
		
		if tifffile.__version__ == '0.15.1':
			# older interface, used by aics-segmentation
			tifffile.imsave(path, imageData, imagej=True, resolution=resolution, metadata=metadata) #, ijmetadata=ijmetadata)
		else:
			# newer interface, changed on 2018.11.6
			tifffile.imwrite(path, imageData, imagej=True, resolution=resolution, metadata=metadata) #, ijmetadata=ijmetadata)
	
	return True
	
def imread(path, verbose=False):
	"""
	Given a path to a .tif file, load the image data and the Fiji/ImageJ header
	
	Return:
		imageData
		tifHeaderDict
	"""
	
	#
	# check file exists
	if not os.path.isfile(path):
		print('ERROR: bTiffFile.imread() did not find file:', path)
		return None, None
	
	if not path.endswith('.tif'):
		print('ERROR: bTiffFile.imread() expects a .tif file and got',  os.path.basename(path))
		return None, None
	
	#
	# read the header
	tifHeaderDict = getTiffFileInfo(path)
	
	#
	# load the tiff
	imageData = tifffile.imread(path)
	
	if verbose:
		print('imread:', imageData.shape, imageData.dtype, 'zVoxel:', tifHeaderDict['zVoxel'], 'xVoxel:', tifHeaderDict['xVoxel'], 'yVoxel:', tifHeaderDict['yVoxel'], path)
		
	return imageData, tifHeaderDict
	
def getTiffFileInfo(path):
	"""
	Given a path to a .tif file, return a dict with Fiji/ImageJ header information
	"""
	
	theRet = OrderedDict()
	
	enclosingPath, filename = os.path.split(path)
	enclosingPath1, enclosingFolder1 = os.path.split(enclosingPath)
	enclosingPath2, enclosingFolder2 = os.path.split(enclosingPath1)
	enclosingPath3, enclosingFolder3 = os.path.split(enclosingPath2)
	
	theRet['enclosingFolder3'] = enclosingFolder3
	theRet['enclosingFolder2'] = enclosingFolder2
	theRet['enclosingFolder1'] = enclosingFolder1
	
	#xVoxel, yVoxel, zVoxel, shape = readVoxelSize(path, getShape=True)
	voxelDict = readVoxelSize(path, returnDict=True)

	theRet['filename'] = filename
	theRet['xVoxel'] = voxelDict['xVoxel']
	theRet['yVoxel'] = voxelDict['yVoxel']
	theRet['zVoxel'] = voxelDict['zVoxel']
	theRet['unit'] = voxelDict['unit']
	theRet['xPixels'] = voxelDict['shape'][1]
	theRet['yPixels'] = voxelDict['shape'][2]
	theRet['zPixels'] = voxelDict['shape'][0]
	
	theRet['path'] = path # so we always know where the info/header came from

	return theRet

def readVoxelSize(path, getShape=False, getMetaData=False, verbose=False, returnDict=False):
	"""
	Get metadata from a Fiji/ImageJ .tif files
	
	x resolution is in tif.pages[0].tags['XResolution']
	y resolution is in tif.pages[0].tags['YResolution']
	z resolution is in tif.imagej_metadata['spacing']
	unit is in tif.imagej_metadata['unit']
	"""
	
	with tifffile.TiffFile(path) as tif:
		xVoxel = 1
		yVoxel = 1
		zVoxel = 1
		unit = 'pixels'
		
		try:
			'''
			for k,v in tif.pages[0].tags.items():
				print(k,v)				
			'''			
			tag = tif.pages[0].tags['XResolution']
			if tag.value[0]>0 and tag.value[1]>0:
				xVoxel = tag.value[1] / tag.value[0]
			else:
				print('  error: bTiffFile.readVoxelSize() error, got zero tag value?')
			if verbose: print('   bTiffFile.readVoxelSize() xVoxel from TIFF XResolutions:', xVoxel)
		except (KeyError) as e:
			print('  warning: bTiffFile.readVoxelSize() did not find XResolution')

		try:
			tag = tif.pages[0].tags['YResolution']
			if tag.value[0]>0 and tag.value[1]>0:
				yVoxel = tag.value[1] / tag.value[0]
			else:
				print('  error: bTiffFile.readVoxelSize() error, got zero tag value?')
			if verbose: print('   bTiffFile.readVoxelSize() yVoxel from TIFF YResolutions:', yVoxel)
		except (KeyError) as e:
			print('  warning: bTiffFile.readVoxelSize() did not find YResolution')

		# HOLY CRAP, FOUND IT QUICK
		imagej_metadata = tif.imagej_metadata
		if imagej_metadata is not None:
			'''
			print('imagej_metadata:')
			for k,v in imagej_metadata.items():
				print(k,v)
			'''		
			try:
				#print('    imagej_metadata["spacing"]:', imagej_metadata['spacing'], type(imagej_metadata['spacing']))
				zVoxel = imagej_metadata['spacing']
				if verbose: print('    zVoxel from imagej_metadata["spacing"]:', imagej_metadata['spacing'])
			except (KeyError) as e:
				print('  warning: bTiffFile.readVoxelSize() did not find "spacing" in imagej_metadata')

			try:
				unit = imagej_metadata['unit']
				if verbose: print('    unit from imagej_metadata["unit"]:', imagej_metadata['unit'])
			except (KeyError) as e:
				print('  warning: bTiffFile.readVoxelSize() did not find "unit" in imagej_metadata')

		numImages = len(tif.pages)

		tag = tif.pages[0].tags['ImageWidth']
		xPixels = tag.value

		tag = tif.pages[0].tags['ImageLength']
		yPixels = tag.value

		myShape = (numImages, xPixels, yPixels)
					
		#
		# return
		if returnDict:
			returnDict = OrderedDict()
			returnDict['xVoxel'] = xVoxel
			returnDict['yVoxel'] = yVoxel
			returnDict['zVoxel'] = zVoxel
			returnDict['shape'] = myShape
			returnDict['unit'] = unit
			return returnDict
		else:
			if getShape:
				theRet = xVoxel, yVoxel, zVoxel, (myShape)
			else:
				theRet = xVoxel, yVoxel, zVoxel
			return theRet
			
if __name__ == '__main__':

	path = '/Users/cudmore/Sites/smMicrotubule/data/191230/BIN1_smKO_Male/Cell_12/12_5ADVMLEG1L1_ch2.tif'
	
	savePath = '/Users/cudmore/Desktop/myTiff.tif'
	savePath2 = '/Users/cudmore/Desktop/myTiff_no_units.tif'
	
	# run different tests of the code
	if 1:
		print('=== 1) test reading a .tif header of path:', path)
		tiffHeader = getTiffFileInfo(path)
		print(json.dumps(tiffHeader, indent=4))
		
	if 1:
		# test reading .tif with header
		print('=== 2) test loading a .tif and reading header of path:', path)
		imageData, tiffHeader = imread(path)
		print('  imageData.shape:', imageData.shape)
		print('  tiffHeader:', json.dumps(tiffHeader, indent=4))
		
	if 1:
		# test saving
		print('=== 3) test save a numpy ndarray as a .tif')
		imageData, tiffHeader = imread(path) # first load
		didSave = imsave(savePath, imageData, tiffHeader)
		if didSave:
			print('  save to path:', savePath)
		else:
			print('  did not save')

	if 1:
		# test saving with no header and overwrite
		didSave = imsave(savePath2, imageData, overwriteExisting=True)
		if didSave:
			print('  save to path:', savePath)
		else:
			print('  did not save')
			
	if 1:
		# test load of a stack with no FIji/ImageJ header
		# todo: this is a problem, saving with no header (With tifffile.imsave) set voxels to 1/1/1 ???
		print('=== 4) test loading a .tif with bogus ImageJ/Fiji header ... pay attention to this ...')
		imageData, tiffHeader = imread(path) # first load
		imsave(savePath2, imageData, overwriteExisting=True) # save with no header
		imageData, tiffHeader = imread(savePath2) # load a .tif with no header
		print('  imageData.shape:', imageData.shape)
		print('  tiffHeader:', json.dumps(tiffHeader, indent=4))
			
		
		
 