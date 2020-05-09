import os, sys
import argparse
from collections import OrderedDict

import numpy as np

import napari

import bimpy.util.bTiffFile
"""
	Load output of hcnToVascDistance.py and display with Napari

	path: full path to analysis/ _ch1_ or _ch2_ .tif file 
"""

def edtNapari(path):
	"""
	path: to _ch2.tif analysis/
	"""
	
	print('edtNapari() path:', path)
	
	basePath, fileName = os.path.split(path)
	baseFileName, extension = fileName.split('.') # used below
	baseFileName = baseFileName.replace('_ch1_', '')
	baseFileName = baseFileName.replace('_ch2_', '')
	baseFilePath = os.path.join(basePath, baseFileName)

	print('  baseFileName:', baseFileName)
	
	stackDict = OrderedDict()
	tiffHeaderDict = OrderedDict()
	
	#
	# load all files in directory
	for file in os.listdir(basePath):
		if not file.endswith('.tif'):
			continue
		if file.find(baseFileName) == -1:
			continue
		channel = None
		if file.find('_ch1_') != -1:
			channel = 1
		elif file.find('_ch2_') != -1:
			channel = 2
		else:
			continue
			
		filePath = os.path.join(basePath, file)
		print('  loading file:', file, 'filePath:', filePath)
		imageStack, tiffHeader = bimpy.util.bTiffFile.imread(filePath)

		stackDict[file] = imageStack
		tiffHeaderDict[file] = tiffHeader

		# x/y/z voxel from ch1 header
		if channel==1 and file.endswith('raw.tif'):
			xVoxel = tiffHeader['xVoxel']
			yVoxel = tiffHeader['yVoxel']
			zVoxel = tiffHeader['zVoxel']
			myScale = (zVoxel, xVoxel, yVoxel) # numpy order (z,x,y)
			print('  myScale:', myScale)
	#
	# show with napari
	print('  opening napari window')
	with napari.gui_qt():
		viewer = napari.Viewer(ndisplay=2, title=baseFileName)

		for fileName, stackData in stackDict.items():
			name = fileName.replace('.tif', '')
			name = name.replace(baseFileName, '')			
			if name.startswith('_'):
				name = name[1:]
			print('    adding name:', name)

			channel = None
			if fileName.find('_ch1_') != -1:
				channel = 1
			elif fileName.find('_ch2_') != -1:
				channel = 2

			colormap = 'gray'
			if fileName.endswith('raw.tif'):
				if channel == 1:
					colormap = 'green'
				elif channel == 2:
					colormap = 'red'
			elif fileName.endswith('edt.tif'):
				if channel == 1:
					colormap = 'inferno'
				elif channel == 2:
					colormap = 'inferno'
			
			minContrast = 0
			maxContrast = np.nanmax(stackData)
				
			viewer.add_image(stackData,
				scale=myScale,
				contrast_limits=(minContrast,maxContrast),
				opacity=0.5,
				colormap=colormap,
				visible=False,
				name=name)
		
		
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = 'Show edt results in Napari')
	parser.add_argument('ch2Path', nargs='*', default='', help='path to _ch2 .tif file')
	args = parser.parse_args() # args is a list of command line arguments

	if len(args.ch2Path)>0:
		path = args.ch2Path[0]		
	else:
		path = '/Users/cudmore/box/data/nathan/20200420/analysis/20200420_HEAD__ch2_.tif'
		path = '/Users/cudmore/box/data/nathan/20200420/analysis/20200420_MID__ch2_.tif'
		path = '/Users/cudmore/box/data/nathan/20200420/analysis/20200420_distalHEAD__ch2_.tif'
	
	edtNapari(path)