import tifffile

def readVoxelSize(path, verbose=False):

	with tifffile.TiffFile(path) as tif:
		xVoxel = 1
		yVoxel = 1
		zVoxel = 1

		try:
			tag = tif.pages[0].tags['XResolution']
			if tag.value[0]>0 and tag.value[1]>0:
				xVoxel = tag.value[1] / tag.value[0]
			else:
				print('   bStackHeader.loadHeader() error, got zero tag value?')
			if verbose: print('   bStackHeader.loadStack() xVoxel from TIFF XResolutions:', xVoxel)
		except (KeyError) as e:
			print('warning: bStackHeader.loadHeader() did not find XResolution')

		try:
			tag = tif.pages[0].tags['YResolution']
			if tag.value[0]>0 and tag.value[1]>0:
				yVoxel = tag.value[1] / tag.value[0]
			else:
				print('   bStackHeader.loadHeader() error, got zero tag value?')
			if verbose: print('   bStackHeader.loadStack() yVoxel from TIFF YResolutions:', yVoxel)
		except (KeyError) as e:
			print('warning: bStackHeader.loadHeader() did not find YResolution')

		# HOLY CRAP, FOUND IT QUICK
		imagej_metadata = tif.imagej_metadata
		if imagej_metadata is not None:
			try:
				#print('    imagej_metadata["spacing"]:', imagej_metadata['spacing'], type(imagej_metadata['spacing']))
				zVoxel = imagej_metadata['spacing']
				if verbose: print('    zVoxel from imagej_metadata["spacing"]:', imagej_metadata['spacing'])
			except (KeyError) as e:
				print('warning: bStackHeader.loadHeader() did not find spacing')

		'''
		tag = tif.pages[0].tags['ResolutionUnit']
		print('ResolutionUnit:', tag.value)
		'''

		numImages = len(tif.pages)

		tag = tif.pages[0].tags['ImageWidth']
		xPixels = tag.value

		tag = tif.pages[0].tags['ImageLength']
		yPixels = tag.value

		return xVoxel, yVoxel, zVoxel

if __name__ == '__main__':
	import os

	'''
	path = '/Users/cudmore/box/data/sami/191230/WT_Male/Cell_4_/4_1_5ADVMLEG1L1_ch2.tif'
	readVoxelSize(path, verbose=True)
	'''

	folderPath = '/Users/cudmore/box/data/sami/191230'

	print('folderPath:', folderPath)

	for dirpath, dirnames, files in os.walk(folderPath):
		for name in files:
			if name.endswith('_ch2.tif'):
				filePath = os.path.join(dirpath, name)
				x,y,z = readVoxelSize(filePath, verbose=False)
				print('    ', filePath, x, y, z)
