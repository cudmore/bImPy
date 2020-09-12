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
		path = '/Users/cudmore/Box/data/canvas/512by512by1zoom5/xy512z1zoom5bi_00001_00001.tif'
		si = ScanImageTiffReader(path)
		print(si)

		with tifffile.TiffFile(path) as f:
			isScanImage = f.is_scanimage
			if isScanImage:
				scanimage_metadata = f.scanimage_metadata
				#print('scanimage_metadata:', scanimage_metadata)
				for idx, (k,v) in enumerate(scanimage_metadata.items()):
					print(idx)
					print('  ', k, v)

		# works (per image)
		#siDescriptions = ScanImageTiffReader(path).description(0)
		#print(siDescriptions)


		# works
		siMetadata = ScanImageTiffReader(path).metadata()
		print(type(siMetadata))
		#print(siMetadata)

		#myJson = json.loads(siMetadata)
		#print('myJson:', myJson)

		# SI.VERSION_MAJOR = '5.6'
		# SI.VERSION_MINOR = '1'
		# SI.hMotors.motorPosition = [-186541 -180967 -651565]
		# SI.hRoiManager.scanZoomFactor = 5
		# SI.hStackManager.stackZStepSize = 1.04

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
