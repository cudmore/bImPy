# Robert Cudmore
# 20200228

import tifffile

verbose = True

path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/20191017/20191017__0001.tif'

with tifffile.TiffFile(path) as tif:
	xVoxel = 1
	yVoxel = 1
	zVoxel = 1
	
	print('tif.pages[0].tags:', tif.pages[0].tags)
	
	tag = tif.pages[0].tags['XResolution']
	if tag.value[0]>0 and tag.value[1]>0:
		xVoxel = tag.value[1] / tag.value[0]
	else:
		print('   error, got zero tag value?')
	if verbose: print('   bStack.loadStack() xVoxel from TIFF XResolutions:', xVoxel)

	tag = tif.pages[0].tags['YResolution']
	if tag.value[0]>0 and tag.value[1]>0:
		yVoxel = tag.value[1] / tag.value[0]
	else:
		print('   error, got zero tag value?')
	if verbose: print('   bStack.loadStack() yVoxel from TIFF YResolutions:', yVoxel)

	tag = tif.pages[0].tags['ResolutionUnit']
	print('ResolutionUnit:', tag.value)
	tag = tif.pages[0].tags['ImageWidth']
	print('ImageWidth:', tag.value)
	tag = tif.pages[0].tags['ImageLength']
	print('ImageLength:', tag.value)
	'''
	if tag.value[0]>0 and tag.value[1]>0:
		yVoxel = tag.value[1] / tag.value[0]
	else:
		print('   error, got zero tag value?')
	if verbose: print('   bStack.loadStack() yVoxel from TIFF YResolutions:', yVoxel)
	'''
	
	'''
	for tmpKey in tif.pages[0].tags.keys():
		tmpTag = tif.pages[0].tags[tmpKey]
		print('   tmpKey:', tmpKey, 'tmpTag:', tmpTag)
		if tmpKey == 'PageName':
			tmpTag2 = tif.pages[1].tags[tmpKey]
			print('      tmpTag2:', tmpTag2)
	'''
	
	#print('tif.NIH_IMAGE_HEADER:', tif.NIH_IMAGE_HEADER)

	# HOLY CRAP, FOUND IT QUICK
	imagej_metadata = tif.imagej_metadata
	#print('imagej_metadata:', imagej_metadata)
	print('imagej_metadata["spacing"]:', imagej_metadata['spacing'])
	