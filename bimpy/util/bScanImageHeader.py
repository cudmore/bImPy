"""
see:
	https://vidriotech.gitlab.io/scanimagetiffreader-python/

install:
	pip install scanimage-tiff-reader
"""

import json

import tifffile
from ScanImageTiffReader import ScanImageTiffReader

if __name__ == '__main__':

	if 0:
		folderPath = '/Users/cudmore/Box/data/canvas/512by512by1zoom5'

		#data1 = tifffile.imread(folderPath)
		#print(data1)

		si = ScanImageTiffReader(folderPath)
		print(Si)

		data2=ScanImageTiffReader(folderPath).data()
		print(data2)

	if 1:
		path = '/Users/cudmore/data/canvas/20200911/20200911_aaa/xy512z1zoom5bi_00001_00010.tif'

		# works
		#si = ScanImageTiffReader(path)
		#print(si)

		with tifffile.TiffFile(path) as f:
			isScanImage = f.is_scanimage
			if isScanImage:
				scanimage_metadata = f.scanimage_metadata
				#print('scanimage_metadata:', scanimage_metadata)
				'''
				for idx, (k,v) in enumerate(scanimage_metadata.items()):
					print(idx)
					print('k:', k)
					for k2,v2 in v.items():
						print('k2:', k2, 'v2:', v2)
				'''

				k2 = 'SI.VERSION_MAJOR'
				VERSION_MAJOR = scanimage_metadata['FrameData'][k2]

				k2 = 'SI.VERSION_MINOR'
				VERSION_MINOR = scanimage_metadata['FrameData'][k2]

				k2 = 'SI.hChannels.channelSave' # like [[1], [2]]
				channelSave = scanimage_metadata['FrameData'][k2]

				k2 = 'SI.hChannels.channelAdcResolution'
				adcResolution = scanimage_metadata['FrameData'][k2]

				k2 = 'SI.hRoiManager.linesPerFrame'
				linesPerFrame = scanimage_metadata['FrameData'][k2]

				k2 = 'SI.hRoiManager.pixelsPerLine'
				pixelsPerLine = scanimage_metadata['FrameData'][k2]

				k2 = 'SI.hRoiManager.scanZoomFactor'
				zoom = scanimage_metadata['FrameData'][k2]

				k2 = 'SI.hMotors.motorPosition'
				motorPosition = scanimage_metadata['FrameData'][k2]

				print('VERSION_MAJOR:', VERSION_MAJOR)
				print('VERSION_MINOR:', VERSION_MINOR)
				print('channelSave:', channelSave)
				print('  num channels:', len(channelSave))
				print('adcResolution:', adcResolution) # list of channels
				print('linesPerFrame:', linesPerFrame)
				print('pixelsPerLine:', pixelsPerLine)
				print('zoom:', zoom)
				print('motorPosition:', motorPosition)

		# works (per image)
		#siDescriptions = ScanImageTiffReader(path).description(0)
		#print(siDescriptions)


		# works
		if 0:
			siMetadata = ScanImageTiffReader(path).metadata()
			print('\n\nsiMetadata:')
			print(siMetadata)

		#myJson = json.loads(siMetadata)
		#print('myJson:', myJson)

		# SI.VERSION_MAJOR = '5.6'
		# SI.VERSION_MINOR = '1'
		# SI.hMotors.motorPosition = [-186541 -180967 -651565]
		# SI.hRoiManager.scanZoomFactor = 5
		# SI.hStackManager.stackZStepSize = 1.04
		# SI.hChannels.channelAdcResolution = {14 14}

		# works
		siData = ScanImageTiffReader(path).data()
		print('siData:', siData.shape)

		'''
		frameNumberAcquisition = 1
		frameTimestamps_sec = 0.000000000
		acqTriggerTimestamps_sec = -0.000082190
		nextFileMarkerTimestamps_sec = -1.000000000
		endOfAcquisition = 1
		endOfAcquisitionMode = 0
		dcOverVoltage = 0
		epoch = [2020  2 26 15  3 38.682]
		auxTrigger0 = []
		auxTrigger1 = []
		auxTrigger2 = []
		auxTrigger3 = []
		I2CData = {}
		'''
