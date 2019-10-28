# Robert Cudmore
# 20190420

import os, sys
from collections import OrderedDict

import numpy as np

import skimage

import tifffile
import bioformats

import bStackHeader
import bFileUtil

class bLockFile:
	"""
	Create a .lock file while processing an input file.
	Other programs (e.g. Igor Pro) use this to determine if work is being done on an input file
	   and can wait until .lock file is gone (e.g. work is done)
	"""
	def __init__(self, filePath):
		self.myLockFile = filePath + '.lock'
		fid = open(self.myLockFile, 'a')
		fid.close()

	def unlock(self):
		os.remove(self.myLockFile)

class bStack:
	"""
	Manages a stack or time-series of images
	"""
	def __init__(self, path=''):
		self.path = path # path to file
		self._fileName = os.path.basename(path)

		self.currentSlice = 0

		self.fileNameWithoutExtension = ''
		if os.path.isfile(path):
			fileName = os.path.split(self.path)[1]
			self.fileNameWithoutExtension, tmpExtension = fileName.split('.')

		self.header = None #StackHeader.StackHeader(self.path)

	@property
	def numChannels(self):
		return self.header.numChannels
	@property
	def numImages(self):
		return self.header.numImages
	@property
	def pixelsPerLine(self):
		return self.header.pixelsPerLine
	@property
	def linesPerFrame(self):
		return self.header.linesPerFrame

	def getHeaderVal(self, key):
		if key in self.header.header.keys():
			return self.header.header[key]
		else:
			print('error: bStack.getHeaderVal() did not find key "' + key + '" in self.header.header. Available keys are:', self.header.header.keys())
			return None

	def convert(self):
		try:
			myLock = bLockFile(self.path)

			self.loadHeader()
			self.header.prettyPrint()

			self.loadStack()

			self.saveHeader()
			self.saveStack()
			self.saveMax()

		finally:
			myLock.unlock()

	#
	# Display
	#
	def setSlice(self, sliceNum):
		if sliceNum < self.header.numImages:
			self.currentSlice = sliceNum
		else:
			print('warning bStack.setSlice()', sliceNum, 'but stack only has', self.header.numImages)

	def getImage(self, channel=1, sliceNum=None):
		channelIdx = channel - 1
		if sliceNum is None:
			sliceNum = self.currentSlice
		return self.stack[channelIdx,sliceNum,:,:]

	def _display0(self, image, display_min, display_max): # copied from Bi Rico
		# Here I set copy=True in order to ensure the original image is not
		# modified. If you don't mind modifying the original image, you can
		# set copy=False or skip this step.
		image = np.array(image, dtype=np.uint8, copy=True)
		image.clip(display_min, display_max, out=image)
		image -= display_min
		np.floor_divide(image, (display_max - display_min + 1) / 256,
						out=image, casting='unsafe')
		#return image.astype(np.uint8)
		return image

	def getImage_ContrastEnhanced(self, display_min, display_max, channel=1, sliceNum=None, useMaxProject=False) :
		"""
		sliceNum: pass NOne to use self.currentImage
		"""
		#lut = np.arange(2**16, dtype='uint16')
		lut = np.arange(2**8, dtype='uint8')
		lut = self._display0(lut, display_min, display_max)
		if useMaxProject:
			# need to specify channel !!!!!!
			return np.take(lut, self.maxProjectImage)
		else:
			return np.take(lut, self.getImage(channel=channel, sliceNum=sliceNum))

	#
	# Loading
	#
	def loadHeader(self):
		if self.header is None:
			if os.path.isfile(self.path):
				self.header = bStackHeader.bStackHeader(self.path)
			else:
				print('bStack.loadHeader() did not find self.path:', self.path)

	def loadMax(self, channel=1, convertTo8Bit=False):
		#print('bStack.loadMax() channel:', channel, 'self.path:', self.path)
		fu = bFileUtil.bFileUtil()
		maxFile = fu.getMaxFileFromRaw(self.path, theChannel=channel)
		#print('bStack.loadMax() maxFile:', maxFile)

		# load the file
		if os.path.isfile(maxFile):
			with tifffile.TiffFile(maxFile) as tif:
				theArray = tif.asarray()
			if convertTo8Bit:
				theArray = skimage.img_as_ubyte(theArray, force_copy=False)
			# need to specify channel !!!!!!
			self.maxProjectImage = theArray
			return theArray
		else:
			return None

	def loadStack(self):
		#print('   bStack.loadStack() Images:', self.numImages, 'pixelsPerLine:', self.pixelsPerLine, 'linesPerFrame:', self.linesPerFrame, 'path:', self.path)
		print('   bStack.loadStack()', self.path)

		self.loadHeader()
		#if self.header is None:
		#	self.header = StackHeader.StackHeader(self.path)

		c = 0 # ???
		z = 0
		t = 0
		channel_names = None

		print('   self.header:', self.header.header)

		rows = self.linesPerFrame
		cols = self.pixelsPerLine
		slices = self.numImages
		channels = self.numChannels

		if rows is None:
			print('error: bStack.loadStack() -->> None rows')
		if cols is None:
			print('error: bStack.loadStack() -->> None cols')
		if slices is None:
			print('error: bStack.loadStack() -->> None slices')
		if channels is None:
			print('error: bStack.loadStack() -->> None channels')

		self.stack = np.zeros((channels, slices, rows, cols), dtype=np.int16)

		#todo: this will only work for one channel

		# if it is a Tiff file use tifffile, otherwise, use bioformats
		if self.path.endswith('.tif'):
			print('bStack.loadStack() is using tifffile...')
			with tifffile.TiffFile(self.path) as tif:
				self.stack[0, :, :, :] = tif.asarray()

		else:
			print('bStack.loadStack() is using bioformats...')
			#with bioformats.GetImageReader(self.path) as reader:
			with bioformats.ImageReader(self.path) as reader:
				for channelIdx in range(self.numChannels):
					c = channelIdx
					for imageIdx in range(self.numImages):
						if self.header.stackType == 'ZStack':
							z = imageIdx
						elif self.header.stackType == 'TSeries':
							t = imageIdx
						image = reader.read(c=c, z=z, t=t, rescale=False) # returns numpy.ndarray
						self.stack[channelIdx,imageIdx,:,:] = image

	#
	# Saving
	#
	def saveHeader(self):
		"""
		Save header as .txt file
		"""
		savePath = self.convert_makeSavePath()
		headerFileName = self.fileNameWithoutExtension + '.txt'
		headerFilePath = os.path.join(savePath, headerFileName)

		self.header.saveHeader(headerFilePath)

	def saveStack(self, path=''):
		"""
		Save stack as .tif file

		to add meta data, see
		   https://github.com/CellProfiler/python-bioformats/issues/106
		"""

		#
		# get metadata from StackHeader
		ijmetadata = {}
		ijmetadataStr = self.header.getMetaData()
		ijmetadata['Info'] = ijmetadataStr

		#
		# save each channel using tifffile
		for channelIdx in range(self.numChannels):
			saveFilePath = self.convert_getSaveFile(channelNumber=channelIdx+1)
			print('   bStack.saveStack() path:', saveFilePath)
			# self.stack is czxy
			tifffile.imwrite(saveFilePath, self.stack[channelIdx,:,:,:], ijmetadata=ijmetadata)

	def saveMax(self):
		savePath = self.convert_makeSavePath()
		savePath = os.path.join(savePath, 'max')
		if not os.path.isdir(savePath):
			os.makedirs(savePath, exist_ok=True)

		for channelIdx in range(self.numChannels):
			maxFileName = 'max_' + self.fileNameWithoutExtension + '_ch' + str(channelIdx+1) + '.tif'
			maxFilePath = os.path.join(savePath, maxFileName)

			#
			# self.stack is czxy, we specify axis=0 because we are explicitly slicing by channel channelIdx (c)
			maxIntensityProjection = np.max(self.stack[channelIdx,:,:,:],axis=0)
			#

			#tifffile.imwrite(maxFilePath, maxIntensityProjection, ijmetadata=ijmetadata)
			tifffile.imwrite(maxFilePath, maxIntensityProjection)

	#
	# File name utilities
	#
	def convert_makeSavePath(self):
		"""
		Given full path to src file, return full path to destination directory.
		The destination directory is a new folder inside the enclosing src folder <srcFolder>.
		Its name is '<srcFolder>_tif'

		"""
		enclosingPath, fileName = os.path.split(self.path)
		tmpPath, enclosingFolder = os.path.split(enclosingPath)

		dstFolder = enclosingFolder + '_tif'
		savePath = os.path.join(enclosingPath, dstFolder)
		if not os.path.isdir(savePath):
			print('   bStack.convert_makeSavePath() making output folder:', savePath)
			os.mkdir(savePath)

		return savePath

	def convert_getSaveFile(self, channelNumber):
		"""
		Return full path to the dst file
		"""
		savePath = self.convert_makeSavePath() # full path to output folder we will save in
		saveFileName = self.fileNameWithoutExtension + '_ch' + str(channelNumber) + '.tif'
		return os.path.join(savePath, saveFileName)

if __name__ == '__main__':

	"""
	debugging
	"""

	import javabridge

	try:

		# work
		path = '/Volumes/fourt0/Dropbox/data/arsalan/20190416/20190416_b_0021.oir'

		# home
		path = '/Users/cudmore/Dropbox/data/arsalan/20190416/20190416_b_0021.oir'
		#path = '/Users/cudmore/Dropbox/data/arsalan/20190416/20190416_b_0001.oir'
		#path = '/Users/cudmore/Dropbox/data/arsalan/20190416/20190416_b_0019.oir'
		path = '/Users/cudmore/Dropbox/data/arsalan/20190416/20190416_b_0005.oir'

		# ZStack
		path = '/Users/cudmore/Dropbox/data/nathan/20190401/tmp/20190401__0011.oir'

		path = '/Volumes/t3/data/20190429/20190429_tst2/20190429_tst2_0006.oir'

		path = 'E:\\cudmore\\data\\20190429\\20190429_tst2\\20190429_tst2_0002.oir'

		path = '/Users/cudmore/box/data/testoir/20190514_0001.oir'

		# good to test caiman alignment
		#path = '/Users/cudmore/box/data/nathan/030119/030119_HCN4-GCaMP8_SAN_phen10uM.oir'

		#print('path:', path)


		myStack = bStack(path)

		myStack.loadMax()

		with javabridge.vm(
				run_headless=True,
				class_path=bioformats.JARS
				):

			# turn off logging, see:
			# ./bStack_env/lib/python3.7/site-packages/bioformats/log4j.py
			log4j = javabridge.JClassWrapper("loci.common.Log4jTools")
			log4j.enableLogging()
			log4j.setRootLevel("WARN")

			myStack.convert()

	finally:
		#print('__main__ finally')
		javabridge.kill_vm()
		pass

	print('bstack main finished')
