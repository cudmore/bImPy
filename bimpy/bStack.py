# Robert Cudmore
# 20190420

import os, sys
from collections import OrderedDict
import numpy as np
import skimage

import tifffile

try:
	import bioformats
except (ImportError) as e:
	bioformats = None

'''
# not sure in which file we want to log? maybe log in the /interface files?
import logging
logLevel = 'DEBUG' #('ERROR, WARNING', 'INFO', 'DEBUG')
filename = 'bimpy.log'
logging.basicConfig(filename=filename,
	filemode='w',
	level=logLevel,
	format='%(levelname)s - %(module)s.%(funcName)s() line %(lineno)d - %(message)s')
'''

import bimpy

class bStack:
	"""
	Manages a 3D image stack or time-series movie of images

	Image data is in self.stack
	"""
	def __init__(self, path='', loadImages=True, loadTracing=True):
		"""
		path:
		"""
		print('bStack.__init__() path:', path)
		#logging.info('constructor')
		self.path = path # path to file

		self._numChannels = None
		self.slabList = None

		# header
		self.header = bimpy.bStackHeader(self.path) #StackHeader.StackHeader(self.path)

		self._maxNumChannels = 3 # leave this for now
		# pixel data, each channel is element in list
		# *3 because we have (raw, mask, skel) for each stack#
		self._stackList = [None for tmp in range(self._maxNumChannels * 3)]
		self._maxList = [None for tmp in range(self._maxNumChannels * 3)]

		#
		# load image data
		if loadImages:
			self.loadStack2() # loads data into self._stackList
			self.loadLabeled() # loads data into _labeledList
			self.loadSkel() # loads data into _labeledList

		#
		# load _annotationList.csv
		self.annotationList = bimpy.bAnnotationList(self.path)
		self.annotationList.load() # will fail when not already saved

		# load vesselucida analysis from .xml file
		self.slabList = bimpy.bVascularTracing(self, self.path, loadTracing=loadTracing)

		self.analysis = bimpy.bAnalysis(self)

	def saveAs(self, newPath=None):
		"""
		save entire stack/tracing as a new file name
		"""
		if newPath is None:
			# ask user for new file name/path
			pass

	def print(self):
		self.printHeader()
		for idx, stack in enumerate(self._stackList):
			if stack is None:
				#print('    ', idx, 'None')
				pass
			else:
				print('    channel:', idx, stack.shape)
		'''
		print('  slabList')
		if self.slabList is None:
			print('self.slabList is None')
		else:
			print(self.slabList._printInfo2())
		'''

	def printHeader(self):
		#print('bStack.printHeader() path:', self.path)
		#print(self.header.header)
		#for k,v in self.header.header.items():
		#	print('  ', k, v)
		#
		self.header.print()

	def _getSavePath(self):
		"""
		return full path to filename without extension
		"""
		path, filename = os.path.split(self.path)
		savePath = os.path.join(path, os.path.splitext(filename)[0])
		return savePath


	@property
	def maxNumChannels(self):
		return self._maxNumChannels
	@property
	def fileName(self):
		# abb canvas
		# return self._fileName
		return os.path.split(self.path)[1]
	def getFileName(self):
		# abb canvas
		# return self._fileName
		return os.path.split(self.path)[1]
	@property
	def numChannels(self):
		#return self.header.numChannels
		return self._numChannels # abb aics
	@property
	def numSlices(self):
		# see also numImages
		return self.header.numImages
	@property
	def numImages(self):
		# see also numSLices
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

	#
	# Display
	#
	def getPixel(self, channel, sliceNum, x, y):
		"""
		channel is 1 based !!!!

		channel: (1,2,3, ... 5,6,7)
		"""
		#print('bStack.getPixel()', channel, sliceNum, x, y)

		theRet = np.nan

		# channel can be 'RGB'
		if not isinstance(channel, int):
			return theRet

		channelIdx = channel - 1

		if self._stackList[channelIdx] is None:
			#print('getPixel() returning np.nan'
			theRet = np.nan
		else:
			nDim = len(self._stackList[channelIdx].shape)
			if nDim == 2:
				m = self._stackList[channelIdx].shape[0]
				n = self._stackList[channelIdx].shape[1]
			elif nDim == 3:
				m = self._stackList[channelIdx].shape[1]
				n = self._stackList[channelIdx].shape[2]
			else:
				print('bStack.getPixel() got bad dimensions:', self._stackList[channelIdx].shape)
			if x<0 or x>m-1 or y<0 or y>n-1:
				theRet = np.nan
			else:
				if nDim == 2:
					theRet = self._stackList[channelIdx][x,y]
				elif nDim == 3:
					theRet = self._stackList[channelIdx][sliceNum,x,y]
				else:
					pass
					# never get here
					#print('bStack.getPixel() got bad dimensions:', self._stackList[channelIdx].shape)

		#
		return theRet

	def getStack(self, type, channel):
		"""
		Can be none

		Parameters:
			type: (raw, mask, skel)
			channel: 1 based
		"""
		if not type in ['raw', 'mask', 'skel', 'video']:
			print('  error: bStack.getStack() expeting type in [raw, mask, skel], got:', type)
			return None

		channelIdx =  channel - 1
		maxChannel = self.maxNumChannels
		if type == 'mask':
			channelIdx += maxChannel
		elif type == 'skel':
			channelIdx += 2 * maxChannel
		theRet = self._stackList[channelIdx]
		return theRet

	def getImage2(self, channel=1, sliceNum=None):
		"""
		new with each channel in list self._stackList

		channel: (1,2,3,...) maps to channel-1
					(5,6,7,...) maps to self._maskList
		"""
		#print('  getImage2() channel:', channel, 'sliceNum:', sliceNum)

		channelIdx = channel - 1
		if self._stackList[channelIdx] is None:
			#print('   error: 0 bStack.getImage2() got None _stackList for channel:', channel, 'sliceNum:', sliceNum)
			return None
		elif len(self._stackList[channelIdx].shape)==2:
			# single plane image
			return self._stackList[channelIdx]
		elif len(self._stackList[channelIdx].shape)==3:
			return self._stackList[channelIdx][sliceNum,:,:]
		else:
			#print('   error: 1 bStack.getImage2() got bad _stackList shape for channel:', channel, 'sliceNum:', sliceNum)
			return None

	def old_getImage_ContrastEnhanced(self, display_min, display_max, channel=1, sliceNum=None, useMaxProject=False) :
		"""
		sliceNum: pass None to use self.currentImage
		"""
		#lut = np.arange(2**16, dtype='uint16')
		lut = np.arange(2**self.bitDepth, dtype='uint8')
		lut = self.old_display0(lut, display_min, display_max) # get a copy of the image
		if useMaxProject:
			# need to specify channel !!!!!!
			#print('self.maxProjectImage.shape:', self.maxProjectImage.shape, 'max:', np.max(self.maxProjectImage))
			maxProject = self.loadMax(channel=channel)
			if maxProject is not None:
				return np.take(lut, maxProject)
			else:
				print('warning: bStack.old_getImage_ContrastEnhanced() did not get max project for channel:', channel)
				return None
		else:
			return np.take(lut, self.getImage2(channel=channel, sliceNum=sliceNum))

	def old_display0(self, image, display_min, display_max): # copied from Bi Rico
		# Here I set copy=True in order to ensure the original image is not
		# modified. If you don't mind modifying the original image, you can
		# set copy=False or skip this step.
		image = np.array(image, dtype=np.uint8, copy=True)
		image.clip(display_min, display_max, out=image)
		image -= display_min
		np.floor_divide(image, (display_max - display_min + 1) / (2**self.bitDepth), out=image, casting='unsafe')
		#np.floor_divide(image, (display_max - display_min + 1) / 256,
		#				out=image, casting='unsafe')
		#return image.astype(np.uint8)
		return image

	def hasChannelLoaded(self, channel):
		channel -= 1
		theRet = self._stackList[channel] is not None
		return theRet

	def getSlidingZ2(self, channel, sliceNumber, upSlices, downSlices):
		"""
		leaving thisStack (ch1, ch2, ch3, rgb) so we can implement rgb later

		channel: 1 based
		"""

		channelIdx = channel - 1

		if self._stackList[channelIdx] is None:
			return None

		if self.numImages>1:
			startSlice = sliceNumber - upSlices
			if startSlice < 0:
				startSlice = 0
			stopSlice = sliceNumber + downSlices
			if stopSlice > self.numImages - 1:
				stopSlice = self.numImages - 1

			print('    getSlidingZ2() startSlice:', startSlice, 'stopSlice:', stopSlice)

			img = self._stackList[channelIdx][startSlice:stopSlice, :, :] #.copy()
			img = np.max(img, axis=0)
		else:
			print('  bStack.getSlidingZ2() is broken !!!')
			# single image stack
			img = self._stackList[0][sliceNumber,:,:].copy()

		return img


	#
	# Loading
	#
	def loadHeader(self):
		if self.header is None:
			if os.path.isfile(self.path):
				self.header = bimpy.bStackHeader(self.path)
			else:
				print('bStack.loadHeader() did not find self.path:', self.path)

	# abb aics
	def loadLabeled(self):
		"""
		load _labeled.tif for each (_ch1, _ch2, _ch3)
		make mask from labeled
		"""

		maxNumChannels = self._maxNumChannels # 4

		baseFilePath, ext = os.path.splitext(self.path)
		baseFilePath = baseFilePath.replace('_ch1', '')
		baseFilePath = baseFilePath.replace('_ch2', '')

		# load mask
		#labeledPath = dvMaskPath + '_mask.tif'
		#labeledData = tifffile.imread(labeledPath)

		maskFromLabelGreaterThan = 0

		# load labeled
		for channelIdx in range(maxNumChannels):
			channelNumber = channelIdx + 1 # for _ch1, _ch2, ...
			stackListIdx = maxNumChannels + channelIdx # for index into self._stackList

			chStr = '_ch' + str(channelNumber)
			labeledPath = baseFilePath + chStr + '_labeled.tif'

			if os.path.isfile(labeledPath):
				print('  bStack.loadLabeled() loading channelNumber:', channelNumber, 'labeledPath:', labeledPath)
				labeledData = tifffile.imread(labeledPath)
				# mask is made of all labels
				self._stackList[stackListIdx] = labeledData > maskFromLabelGreaterThan
			else:
				#print('  bStack.loadLabeled() did not find _labeled path:', labeledPath)
				pass

		# erode _mask by 1 (before skel) as skel was getting mized up with z-collisions
		#self._dvMask = bimpy.util.morphology.binary_erosion(self._dvMask, iterations=2)

		# bVascularTracing.loadDeepVess() uses mask to make skel

	def loadSkel(self):
		"""
		load _skel.tif for each (_ch1, _ch2, _ch3)

		_skel.tif is 1-pixel skeleton stack returned from
			skimage.morphology.skeletonize_3d(maskData)
		"""

		maxNumChannels = self._maxNumChannels # 4

		baseFilePath, ext = os.path.splitext(self.path)
		baseFilePath = baseFilePath.replace('_ch1', '')
		baseFilePath = baseFilePath.replace('_ch2', '')

		# load _skel
		for channelIdx in range(maxNumChannels):
			channelNumber = channelIdx + 1 # for _ch1, _ch2, ...
			stackListIdx = 2 * maxNumChannels + channelIdx # for index into self._stackList

			chStr = '_ch' + str(channelNumber)
			skelPath = baseFilePath + chStr + '_skel.tif'

			if os.path.isfile(skelPath):
				print('  bStack.loadSkel() loading channelNumber:', channelNumber, 'skelPath:', skelPath)
				skelData = tifffile.imread(skelPath)
				# mask is made of all labels
				self._stackList[stackListIdx] = skelData
			else:
				#print('  bStack.loadSkel() did not find _skel path:', skelPath)
				pass

		# erode _mask by 1 (before skel) as skel was getting mized up with z-collisions
		#self._dvMask = bimpy.util.morphology.binary_erosion(self._dvMask, iterations=2)

	# abb canvas
	def getMaxFile(self, channel):
		"""
		get full path to max file
		"""
		maxSavePath, fileName = os.path.split(self.path)
		baseFileName = os.path.splitext(fileName)[0]
		maxSavePath = os.path.join(maxSavePath, 'max')
		maxFileName = 'max_' + baseFileName + '_ch' + str(channel) + '.tif'
		maxFilePath = os.path.join(maxSavePath, maxFileName)
		return maxFilePath

	# abb canvas
	def loadMax(self):
		"""
		todo: this needs to use self.numChannel !!!

		assumes:
			1) self.saveMax
			2) self.numChannels is well formed
		"""
		nMax = len(self._maxList)
		for idx in range(nMax):
			channelNumber = idx + 1
			maxFilePath = self.getMaxFile(channelNumber)
			if os.path.isfile(maxFilePath):
				print('  bStack.loadMax() loading channel', channelNumber, 'maxFilePath:', maxFilePath)
				maxData = tifffile.imread(maxFilePath)
				self._maxList[idx] = maxData
			else:
				#print('  warning: bStack.loadMax() did not find max file:', maxFilePath)
				pass

	# abb canvas
	def saveMax(self):
		"""
		assumes self._makeMax()
		"""
		maxSavePath, tmpFileName = os.path.split(self.path)
		maxSavePath = os.path.join(maxSavePath, 'max')
		print('  bStack.saveMax() maxSavePath:', maxSavePath)
		if not os.path.isdir(maxSavePath):
			os.mkdir(maxSavePath)

		nMax = len(self._maxList)
		for idx in range(nMax):
			maxData = self._maxList[idx]
			if maxData is None:
				continue
			channel = idx + 1
			maxFilePath = self.getMaxFile(channel)
			print('  bStack.saveMax() saving', idx, 'maxFilePath:', maxFilePath)
			tifffile.imsave(maxFilePath, maxData)

	# abb canvas
	def getMax(self, channel=1):
		"""
		channel: 1 based
		"""
		channel -= 1
		theRet = self._maxList[channel]
		return theRet

	# abb canvas
	def _makeMax(self, channelIdx, convertTo8Bit=False):
		"""
		channelIdx: 0 based
		convertTo8Bit: not used
		"""
		theMax = None
		stackData = self._stackList[channelIdx]
		if stackData is None:
			print('bStack._makeMax() is returning None for channelIdx:', channelIdx)
			pass
		else:
			nDim = len(stackData.shape)
			if nDim == 2:
				theMax = stackData
			elif nDim == 3:
				theMax = np.max(stackData, axis=0)
			else:
				print('bStack._makeMax() got bad dimensions for channelIdx', channelIdx, 'nDim:', nDim)
		#if theMax is not None and convertTo8Bit:
		#	theMax = theMax.astype(np.uint8)
		self._maxList[channelIdx] = theMax

	# abb aics
	def loadStack2(self, verbose=False):
		basename, tmpExt = os.path.splitext(self.path)
		basename = basename.replace('_ch1', '')
		basename = basename.replace('_ch2', '')

		#self._stackList = []

		self._numChannels = 0

		# no channel
		path_noChannel = basename + '.tif'
		#print('  bStack.loadStack2() path_noChannel:', path_noChannel)
		if os.path.exists(path_noChannel):
			print('    loadStack2() path_noChannel:', path_noChannel)
			try:
				stackData = tifffile.imread(path_noChannel)
			except (tifffile.TiffFileError) as e:
				print('\nEXCEPTION: bStack.loadStack2() e:', e)
				print('  self.path:', self.path, '\n\n')
			else:
				# if ScanImage and numChannels>1 ... deinterleave
				if self.header.stackType == 'ScanImage':
					numChannels = self.header.numChannels
					self._numChannels = numChannels
					if numChannels > 1:
						for channelIdx in range(numChannels):
							start = channelIdx
							if stackData.shape[0] % numChannels != 0:
								prnit('error: bStack.load() scanimage num slices error')
							#stop = int(stackData.shape[0] / numChannels) # assuming we get an integer
							stop = stackData.shape[0]
							step = numChannels
							sliceRange = range(start, stop, step)

							setNumSlices = len(sliceRange)
							self.header.header['numImages'] = setNumSlices
							'''
							print('bStack.load() ScanImage channelIdx:', channelIdx)
							print('  ', 'start:', start, 'stop:', stop, 'step:', step)
							print('  sliceRange:', list(sliceRange))
							'''
							self._stackList[channelIdx] = stackData[sliceRange, :, :]
							self._makeMax(channelIdx)
					else:
						self._stackList[0] = stackData
						self._makeMax(0)
						#self._numChannels = 1 #+= 1
				else:
					self._stackList[0] = stackData
					self._makeMax(0)
					self._numChannels = 1 #+= 1
		# 1
		path_ch1 = basename + '_ch1.tif'
		#print('  bStack.loadStack2() path_ch1:', path_ch1)
		if os.path.exists(path_ch1):
			print('    loadStack2() path_ch1:', path_ch1)
			stackData = tifffile.imread(path_ch1)
			self._stackList[0] = stackData
			self._makeMax(0)
			self._numChannels = 1 #+= 1
		# 2
		path_ch2 = basename + '_ch2.tif'
		#print('  bStack.loadStack2() path_ch2:', path_ch2)
		if os.path.exists(path_ch2):
			print('    loadStack2() path_ch2:', path_ch2)
			stackData = tifffile.imread(path_ch2)
			self._stackList[1] = stackData
			self._makeMax(1)
			self._numChannels = 2 #+= 1

		# oir
		path_oir = basename + '.oir'
		if os.path.exists(path_oir):
			print('  bStack.loadStack2() path_oir:', path_oir)
			self.loadBioFormats_Oir() # sinfle oir file (can have multiple channels)

	def loadBioFormats_Oir(self):
		if bioformats is None:
			print('error: bStack.loadBioFormats_Oir() bioformats was not imported, can only open .tif files.')
			return False

		self.loadHeader()

		rows = self.linesPerFrame
		cols = self.pixelsPerLine
		#slices = self.numImages

		# get channel from oir header
		# channels = self.numChannels
		numChannels = self.header.numChannels
		numImages = self.header.numImages

		verbose = True
		if verbose: print('bStack.loadBioFormats_Oir() using bioformats ...', 'numChannels:', numChannels, 'numImages:', numImages, 'rows:', rows, 'cols:', cols)

		#with bioformats.GetImageReader(self.path) as reader:
		with bioformats.ImageReader(self.path) as reader:
			for channelIdx in range(numChannels):
				c = channelIdx
				numImagesLoaded = 0
				for imageIdx in range(numImages):
					if self.header.stackType == 'ZStack':
						z = imageIdx
						t = 0
					elif self.header.stackType == 'TSeries':
						z = 0
						t = imageIdx
					else:
						print('      ****** Error: bStack.loadStack() did not get valid self.header.stackType:', self.header.stackType)
						z = 0
						t = imageIdx
					#print('imageIdx:', imageIdx)
					image = reader.read(c=c, t=t, z=z, rescale=False) # returns numpy.ndarray
					#image = reader.read(c=c, rescale=False) # returns numpy.ndarray
					loaded_shape = image.shape # we are loading single image, this will be something like (512,512)
					loaded_dtype = image.dtype
					newShape = (numImages, loaded_shape[0], loaded_shape[1])
					# resize
					#print('      oir loaded_shape:', loaded_shape, self.path)

					# abb canvas removed
					#if channelIdx==0 and imageIdx == 0:
					#	print('      loaded_shape:', loaded_shape, 'loaded_dtype:', loaded_dtype, 'newShape:', newShape)
					#	self.stack = np.zeros(newShape, dtype=loaded_dtype)
					if imageIdx == 0:
						self._stackList[channelIdx] = np.zeros(newShape, dtype=loaded_dtype)
					# assign
					#self.stack[channelIdx,imageIdx,:,:] = image
					self._stackList[channelIdx][imageIdx,:,:] = image
					self._numChannels = channelIdx + 1

					numImagesLoaded += 1

				#
				# abb canvas, this is redundant
				self.header.assignToShape2(self._stackList[channelIdx])
		#
		#self.header.assignToShape(self.stack)

		print('  bStack.loadBioFormats_Oir() is done with ...')
		self.print()
		#sys.exit()

		return True

	def saveAnnotations(self):
		h5FilePath = None
		if self.slabList is not None:
			h5FilePath = self.slabList.save()
		else:
			print('WARNING: bStack.saveAnnotations() did not save as annotation slabList is None')

		# 20200831, save generic bAnnotationList
		self.annotationList.save()

		return h5FilePath

	def loadAnnotations(self):
		#todo: this is wrong
		loadedFile = None
		if self.slabList is not None:
			loadedFile = self.slabList.load()
		else:
			print('WARNING: bStack.loadAnnotations() did not load as annotation slabList is not None')
		return loadedFile

	def loadAnnotations_xml(self):
		if self.slabList is not None:
			self.slabList.loadVesselucida_xml()


if __name__ == '__main__':

	"""
	debugging
	"""

	#import javabridge

	path = '/Users/cudmore/data/canvas/20200911/20200911_aaa/xy512z1zoom5bi_00001_00010.tif'
	path = '/Users/cudmore/data/canvas/20200913/20200913_aaa/xy512z1zoom5bi_00001_00009.tif'

	if 0:
		print('--- bstack __main__ is instantiating stack')
		myStack = bStack(path)

	if 1:
		myStack = bStack(path, loadImages=False)

		myStack.print()
		#myStack.printHeader()

		myStack.loadStack2()

		maxFile = myStack.getMaxFile(1)
		print('maxFile:', maxFile)

		#myStack.saveMax()

		myStack.loadMax()

		theMax = myStack.getMax(1)
		print('theMax:', theMax)

	if 0:
		from bJavaBridge import bJavaBridge

		myJavaBridge = bJavaBridge()
		myJavaBridge.start()

		try:
			myStack = bStack(path)

			myStack.print()
			myStack.printHeader()

		finally:
			myJavaBridge.stop()

	print('bstack __main__ finished')
