import os, json
import argparse

import numpy as np
import skimage
import napari
import tifffile

from vascDen import myGetDefaultStackDict # vascDen.py needs to be in same folder

def crossChannelNapari(path):

	def _load(channel):
		if channel == 1:
			chStr = '_ch1_'
			stackDict = stackDict_ch1
		elif channel == 2:
			chStr = '_ch2_'
			stackDict = stackDict_ch2
		for idx, (stackName,v) in enumerate(stackDict.items()):
			fileIdx = idx #+ 1
			if not stackName in loadTheseStacks:
				continue
			fileName = baseFileName + chStr + stackName + '.tif'
			filePath = os.path.join(analysisPath, fileName)

			if not os.path.isfile(filePath):
				print('  Warning: did not find file', filePath)
				continue
			
			print('  loading:', fileName)
			#
			data = tifffile.imread(filePath)
			#
			stackDict[stackName]['data'] = data
	
	def _napariAdd(channel):

			colormap = 'gray'
			if channel == 1:
				stackDict = stackDict_ch1
				colormap = 'green'
			elif channel == 2:
				stackDict = stackDict_ch2
				colormap = 'red'
			
			for idx, (stackName,v) in enumerate(stackDict.items()):
				if not stackName in loadTheseStacks:
					continue

				type = v['type'] # (image, mask, label)
				data = v['data']
			
				if data is None:
					# not loaded
					print('  myNapari() stackName:', stackName, 'Warning: DID NOT FIND DATA')
					continue
			
				print('  myNapari() stackName:', stackName, data.shape)
			
				layerName = str(channel) + ' ' + stackName
				
				if type == 'image':
					minContrast= 0 
					maxContrast = np.nanmax(data)
					myImageLayer = viewer.add_image(data, contrast_limits=(minContrast, maxContrast), opacity=0.66, colormap=colormap, visible=False, name=layerName)
				if type == 'mask':
					minContrast= 0 
					maxContrast = 1
					myMaskLayer = viewer.add_image(data, contrast_limits=(minContrast, maxContrast), opacity=0.66, colormap=colormap, visible=False, name=layerName)
				elif type == 'label':
					myLabelsLayer = viewer.add_labels(data, opacity=0.66, visible=False, name=layerName)
				
					# switch this to _v2
					#editLabelData = self.editLabelData #data.copy()
					#self.myLabelsLayer = self.viewer.add_labels(editLabelData, opacity=0.7, visible=True, name=self.editLabelName)

	tmpFolder, tmpFilename = os.path.split(path)
	tmpFileNameNoExtension, tmpExtension = tmpFilename.split('.')
	
	baseFileName = tmpFileNameNoExtension
	baseFileName = baseFileName.replace('_ch1', '')
	baseFileName = baseFileName.replace('_ch2', '')
	baseFileName = baseFileName.replace('_ch3', '')

	if tmpFolder.endswith('analysis2'):
		# already in analysis folder
		analysisPath = tmpFolder
		if tmpFileNameNoExtension.endswith('_raw'):
			tmpFileNameNoExtension = tmpFileNameNoExtension.replace('_raw', '')
	else:
		analysisPath = os.path.join(tmpFolder, 'analysis2')
	
	stackDict_ch1 = myGetDefaultStackDict()
	stackDict_ch2 = myGetDefaultStackDict()

	# load
	loadTheseStacks = ['raw', 'threshold', 'finalMask', 'labeled']
	
	_load(1)
	_load(2)

	with napari.gui_qt():
		viewer = napari.Viewer(title=baseFileName)
		_napariAdd(2)
		_napariAdd(1) # so ch 1 is first
		
		
##############################################################################
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = 'xxx')
	parser.add_argument('tifPath', nargs='*', default='', help='path to original _ch1 .tif file')
	args = parser.parse_args() # args is a list of command line arguments

	if len(args.tifPath)>0:
		pathToRawTiff = args.tifPath[0]		
	else:
		#pathToRawTiff = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0007_ch1.tif'
		#pathToRawTiff = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0010_ch1.tif'
		#pathToRawTiff = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0011_ch1.tif'

		pathToRawTiff = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0014_ch1.tif'

	crossChannelNapari(pathToRawTiff)
