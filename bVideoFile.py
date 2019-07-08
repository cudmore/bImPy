import os
import numpy as np
import tifffile

class bVideoFile:
	def __init__(self, theCanvas, videoFilePath):
		self._videoFilePath = videoFilePath

		self._fileName = os.path.basename(videoFilePath)
		
		self._ndarray = self.openVideoFile(videoFilePath)
		
		# for now, tiff tags don't work
		# todo: make them work
		fullFileName = os.path.basename(self._videoFilePath)
		baseFileName, extension = os.path.splitext(fullFileName)
		#self._header = fakeMotorPositons[self._fileName] ### !!! ###
		if baseFileName in theCanvas.import_stackDict.keys():
			self._header = theCanvas.import_stackDict[baseFileName] # may fail
		else:
			print('bVIdeoFile.__init__() did not find imported header information for video file:videoFilePath')
			
	def getHeader(self):
		return self._header
	
	def getVideoImage(self):
		return self._ndarray
		
	def openVideoFile(self, path):
		with tifffile.TiffFile(path) as tif:	
			return tif.asarray()

	def getContrastEnhanced(self, theMin, theMax):
		"""
		return image as ndarray after contrast enhance
		"""
		return self.lut_display0(self._ndarray, theMin, theMax)
		
	def display0(self, image, display_min, display_max): # copied from Bi Rico
		# Here I set copy=True in order to ensure the original image is not
		# modified. If you don't mind modifying the original image, you can
		# set copy=False or skip this step.
		image = np.array(image, copy=True)
		image.clip(display_min, display_max, out=image)
		image -= display_min
		np.floor_divide(image, (display_max - display_min + 1) / 256,
						out=image, casting='unsafe')
		return image.astype(np.uint8)

	def lut_display0(self, image, display_min, display_max) :
		#lut = np.arange(2**16, dtype='uint16')
		lut = np.arange(2**8, dtype='uint8')
		lut = self.display0(lut, display_min, display_max)
		return np.take(lut, image)
