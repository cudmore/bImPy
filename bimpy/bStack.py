# Robert Cudmore
# 20190420

import os, sys
from collections import OrderedDict

import numpy as np

import skimage

import tifffile
import bioformats

from bimpy import bSlabList
from bimpy import bStackHeader
from bimpy import bFileUtil

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
	def __init__(self, path='', loadImages=True):
		self.path = path # path to file
		self._fileName = os.path.basename(path)

		self.currentSlice = 0

		self.fileNameWithoutExtension = ''
		if os.path.isfile(path):
			fileName = os.path.split(self.path)[1]
			self.fileNameWithoutExtension, tmpExtension = fileName.split('.')

		self.header = None #StackHeader.StackHeader(self.path)
		self.stack = None

		# load vesselucida analysis from .xml file
		self.slabList = bSlabList.bSlabList(self.path)
		if self.slabList.x is None:
			self.slabList = None

		if loadImages:
			self.loadStack()

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
	@property
	def xVoxel(self):
		return self.header.xVoxel
	@property
	def yVoxel(self):
		return self.header.yVoxel
	@property
	def zVoxel(self):
		return self.header.zVoxel
	@property
	def bitDepth(self):
		return self.header.bitDepth

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

	def setSliceContrast(self, sliceNumber, thisStack='ch1', minContrast=None, maxContrast=None, autoContrast=False, img=None):
		"""
		thisStack in ['ch1', 'ch2', 'ch3', 'mask', 'skel']

		img: pass this in to contrast adjust an existing image, e.g. from sliding z-projection

		autoContrast: probably not working
		"""

		#print('setSliceContrast()')

		# we are making a copy so we can modify the contrast
		if img is None:
			if thisStack == 'ch1':
				img = self.stack[0, sliceNumber, :, :].copy()
			elif thisStack == 'mask':
				img = self._imagesMask[sliceNumber, :, :].copy()
			elif thisStack == 'skel':
				img = self._imagesSkel[sliceNumber, :, :].copy()
			else:
				print('error: setSliceContrast() got bad thisStack:', thisStack)

		#print('setSliceContrast() BEFORE min:', img.min(), 'max:', img.max(), 'mean:', img.mean(), 'dtype:', img.dtype)

		# this works, removing it does not anything faster !!!
		maxInt = 2 ** self.bitDepth - 1

		if minContrast is None:
			minContrast = 0
		if maxContrast is None:
			maxContrast = 2 ** self.bitDepth - 1
		if autoContrast:
			minContrast = np.min(img)
			maxContrast = np.max(img)

		#print('   setSliceContrast() sliceNumber:', sliceNumber, 'maxInt:', maxInt, 'lowContrast:', lowContrast, 'highContrast:', highContrast)

		#mult = maxInt / abs(highContrast - lowContrast)
		denominator = abs(maxContrast - minContrast)
		if denominator != 0:
			mult = maxInt / denominator
		else:
			mult = maxInt

		img[img < minContrast] = minContrast
		img[img > maxContrast] = maxContrast
		img -= minContrast

		img = img * mult

		return img

		# if i remove all from above, this is not any faster?
		#return self._images[sliceNumber, :, :]

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

	#def setSliceContrast(self, sliceNumber, thisStack='ch1', minContrast=None, maxContrast=None, autoContrast=False, img=None):
	def getImage_ContrastEnhanced(self, display_min, display_max, channel=1, sliceNum=None, useMaxProject=False) :
		"""
		sliceNum: pass None to use self.currentImage
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
			channels = 1
			print('error: bStack.loadStack() -->> None channels')

		#self.stack = np.zeros((channels, slices, rows, cols), dtype=np.int16)

		#todo: this will only work for one channel

		# if it is a Tiff file use tifffile, otherwise, use bioformats
		if self.path.endswith('.tif'):
			print('   bStack.loadStack() is using tifffile...')
			with tifffile.TiffFile(self.path) as tif:
				print('   tif.imagej_metadata:', tif.imagej_metadata)
				print('   tif.tags:', tif.is_nih)
				#print('   tif[0].image_description:', tif.image_description)
				print('   tif.nih_metadata:', tif.nih_metadata)
				thisChannel = 0
				loaded_shape = tif.asarray().shape
				loaded_dtype = tif.asarray().dtype
				print('      loaded_shape:', loaded_shape, 'loaded_dtype:', loaded_dtype)
				newShape = (channels,) + loaded_shape
				self.stack = np.zeros(newShape, dtype=loaded_dtype)

				self.stack[thisChannel, :, :, :] = tif.asarray()

				self.header.assignToShape(self.stack)
				print('      after load tiff, self.stack.shape:', self.stack.shape)
		else:
			print('   bStack.loadStack() using bioformats ...', 'channels:', channels, 'slices:', slices, 'rows:', rows, 'cols:', cols)
			#with bioformats.GetImageReader(self.path) as reader:
			with bioformats.ImageReader(self.path) as reader:
				for channelIdx in range(self.numChannels):
					c = channelIdx
					for imageIdx in range(self.numImages):
						if self.header.stackType == 'ZStack':
							z = imageIdx
							t = 0
						elif self.header.stackType == 'TSeries':
							z = 0
							t = imageIdx
						else:
							print('      ****** Error: bStack.loadStack() did not get valid self.header.stackType:', self.header.stackType)
						#print('imageIdx:', imageIdx)
						image = reader.read(c=c, t=t, z=z, rescale=False) # returns numpy.ndarray
						loaded_shape = image.shape # we are loading single image, this will be something like (512,512)
						loaded_dtype = image.dtype
						newShape = (channels,self.numImages) + loaded_shape
						# resize
						if imageIdx == 0:
							print('      loaded_shape:', loaded_shape, 'loaded_dtype:', loaded_dtype, 'newShape:', newShape)
							self.stack = np.zeros(newShape, dtype=loaded_dtype)
						# assign
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
		# save each channel using tifffile
		for channelIdx in range(self.numChannels):
			saveFilePath = self.convert_getSaveFile(channelNumber=channelIdx+1)
			# self.stack is czxy
			#tifffile.imwrite(saveFilePath, self.stack[channelIdx,:,:,:], imagej=True, resolution=resolution, metadata=metadata, ijmetadata=ijmetadata)
			self._save(saveFilePath, self.stack[channelIdx,:,:,:])

	def _save(self, fullFilePath, imageData, includeSpacing=True):
		"""
		Save a volume with xyz voxel size 2.6755 x 2.6755 x 3.9474 µm^3 to an ImageJ file:

		>>> volume = numpy.random.randn(57*256*256).astype('float32')
		>>> volume.shape = 1, 57, 1, 256, 256, 1  # dimensions in TZCYXS order
		>>> imwrite('temp.tif', volume, imagej=True, resolution=(1./2.6755, 1./2.6755), metadata={'spacing': 3.947368, 'unit': 'um'})
		"""

		#print('imageData.dtype:', imageData.dtype)

		# get metadata from StackHeader
		ijmetadata = {}
		ijmetadataStr = self.header.getMetaData()
		ijmetadata['Info'] = ijmetadataStr

		resolution = (1./self.header.xVoxel, 1./self.header.yVoxel)
		zVoxel = self.header.zVoxel
		metadata = {
			'spacing': zVoxel if includeSpacing else 1,
			'unit': 'um'
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
			print('error, we can only save 2d or 3d images and stacks!')
		tmpStack = imageData
		tmpStack.shape = 1, numSlices, 1, numx, numy, 1
		tifffile.imwrite(fullFilePath, tmpStack, imagej=True, resolution=resolution, metadata=metadata, ijmetadata=ijmetadata)

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
			#tifffile.imwrite(maxFilePath, maxIntensityProjection)
			self._save(maxFilePath, maxIntensityProjection, includeSpacing=False)

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
		path = '/Users/cudmore/Sites/bImpy-Data/ca-smooth-muscle-oir/ca-smooth-muscle-oir_tif/20190514_0003_ch1.tif'
		path = '/Users/cudmore/Sites/bImpy-Data/ca-smooth-muscle-oir/20190514_0003.oir'
		# good to test caiman alignment
		#path = '/Users/cudmore/box/data/nathan/030119/030119_HCN4-GCaMP8_SAN_phen10uM.oir'

		path = '/Users/cudmore/box/data/nathan/vesselucida/20191017__0001.tif'
		path = '/Users/cudmore/box/data/nathan/vesselucida/vesselucida_tif/20191017__0001_ch1.tif'

		print('--- bstack main is constructing stack')
		myStack = bStack(path)

		print('--- bstack main is loading max')
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

			print('--- bstack main is calling convert()')
			myStack.convert()

	finally:
		#print('__main__ finally')
		javabridge.kill_vm()
		pass

	print('bstack main finished')
