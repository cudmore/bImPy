"""
Make a final ch1 edt which is distance in ch1 mask to pixels in ch2 mask

Only include those pixels in ch2 convex hull

Requires:
	_ch1_finalMask.tif
	_ch2_finalMask_edt
	
saves
	_ch1_finalMask_edt.tif
		
"""

import os, sys, argparse

import numpy as np
import tifffile

def crossChannelEDT(path, doSave=False):
	"""
	return stack that is in cellMask (e.g. hcn4)
	
	path: /Users/cudmore/box/data/nathan/20200518/analysis2/20200518__A01_G001_0002_ch1_raw.tif
	"""
	
	tmpFolder, tmpFilename = os.path.split(path)
	fileNameNoExtension, tmpExtension = tmpFilename.split('.')
	
	baseFileName = fileNameNoExtension	
	baseFileName = baseFileName.replace('_ch1_raw', '')
	baseFileName = baseFileName.replace('_ch2_raw', '')
	baseFileName = baseFileName.replace('_ch3_raw', '')
	
	print('  baseFileName:', baseFileName)
	
	#
	# load ch1 finalMask
	ch1FinalMaskPath = os.path.join(tmpFolder, baseFileName + '_ch1_finalMask.tif')
	print('  loading ch1 final mask:', ch1FinalMaskPath)
	ch1FinalMask = tifffile.imread(ch1FinalMaskPath)
	
	#
	# load ch2 edt
	ch2EDTPath = os.path.join(tmpFolder, baseFileName + '_ch2_finalMask_edt.tif')
	print('  loading ch2 edt:', ch2EDTPath)
	ch2EDT = tifffile.imread(ch2EDTPath)

	these_hcn1_pixels = ch1FinalMask == 1 # pixels in hcn1 mask
	#_printStackParams('these_hcn1_pixels', these_hcn1_pixels)

	edtFinal = ch2EDT.copy()
	edtFinal[:] = np.nan
	
	edtFinal[these_hcn1_pixels] = ch2EDT[these_hcn1_pixels]	# grab hcn1 pixels from vascular edt
	_printStackParams('  ch1 edt', edtFinal)
	
	ch1EDTPath = os.path.join(tmpFolder, baseFileName + '_ch1_finalMask_edt.tif')
	if doSave:
		print('  saving ch1 edt:', ch1EDTPath)
		tifffile.imsave(ch1EDTPath, edtFinal)
	
	return edtFinal, ch1EDTPath
	
def crossChannelEDTFolder(folderPath):
	for file in os.listdir(folderPath):
		if file.startswith('.'):
			continue
		if file.endswith('_ch1_raw.tif'):
			filePath = os.path.join(folderPath, file)
			crossChannelEDT(filePath, doSave=True)
		
def _printStackParams(name, myStack):
	print('  ', name, myStack.shape, myStack.dtype, 'dtype.char:', myStack.dtype.char,
				'min:', round(np.min(myStack),2), 'max:', round(np.max(myStack),2), 'mean:', round(np.nanmean(myStack),2))


if __name__ == '__main__':

	parser = argparse.ArgumentParser(description = 'Process a vascular stack')
	parser.add_argument('tifPath', nargs='*', default='', help='path to _raw.tif file')
	args = parser.parse_args() # args is a list of command line arguments

	if len(args.tifPath)>0:
		path = args.tifPath[0]		
	else:
		path = '/Users/cudmore/box/data/nathan/20200518/analysis2/20200518__A01_G001_0002_ch1_raw.tif'
	
	#finalEDT, savePath = crossChannelEDT(path, doSave=True)
	
	path = '/Users/cudmore/box/data/nathan/20200518/analysis2'
	crossChannelEDTFolder(path)
	
	path = '/Users/cudmore/box/data/nathan/20200518/analysis_full'
	crossChannelEDTFolder(path)
	
	
	
	