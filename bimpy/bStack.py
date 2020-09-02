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
	def __init__(self, path='', loadImages=True):
		#logging.info('constructor')
		self.path = path # path to file

		self._numChannels = None

		# header
		self.header = bimpy.bStackHeader(self.path) #StackHeader.StackHeader(self.path)

		self._maxNumChannels = 3 # leave this for now
		# pixel data, each channel is element in list
		# *3 because we have (raw, mask, skel) for each stack#
		self._stackList = [None for tmp in range(self._maxNumChannels * 3)]

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
		self.slabList = bimpy.bVascularTracing(self, self.path)

		self.analysis = bimpy.bAnalysis(self)

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
		return self._fileName
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
			m = self._stackList[channelIdx].shape[1]
			n = self._stackList[channelIdx].shape[2]
			if x<0 or x>m-1 or y<0 or y>n-1:
				theRet = np.nan
			else:
				theRet = self._stackList[channelIdx][sliceNum,x,y]

		#
		return theRet

	def getStack(self, type, channel):
		"""
		Can be none

		Parameters:
			type: (raw, mask, skel)
			channel: 1 based
		"""
		if not type in ['raw', 'mask', 'skel']:
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
				print('  bStack.loadLabeled() did not find _labeled path:', labeledPath)


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
				print('  bStack.loadSkel() did not find _skel path:', skelPath)


		# erode _mask by 1 (before skel) as skel was getting mized up with z-collisions
		#self._dvMask = bimpy.util.morphology.binary_erosion(self._dvMask, iterations=2)

	# abb aics
	def loadStack2(self, verbose=False):
		basename, tmpExt = os.path.splitext(self.path)
		basename = basename.replace('_ch1', '')
		basename = basename.replace('_ch2', '')

		#self._stackList = []

		self._numChannels = 0

		path_ch1 = basename + '_ch1.tif'
		print('  bStack.loadStack2() path_ch1:', path_ch1)
		if os.path.exists(path_ch1):
			print('    loadStack2() path_ch1:', path_ch1)
			stackData = tifffile.imread(path_ch1)
			self._stackList[0] = stackData
			self._numChannels += 1
		path_ch2 = basename + '_ch2.tif'
		print('  bStack.loadStack2() path_ch2:', path_ch2)
		if os.path.exists(path_ch2):
			print('    loadStack2() path_ch2:', path_ch2)
			stackData = tifffile.imread(path_ch2)
			self._stackList[1] = stackData
			self._numChannels += 1


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
		#path = '/Users/cudmore/box/data/nathan/vesselucida/vesselucida_tif/20191017__0001_ch1.tif'

		path = '/Users/cudmore/box/data/bImpy-Data/rr30a/raw/rr30a_s1_ch1.tif'

		path = '/Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch2.tif'

		print('--- bstack __main__ is instantiating stack')
		myStack = bStack(path)

		#print('--- bstack __main__ is printing stack')
		#myStack.print()

		#print('--- bstack main is loading max')
		#myStack.loadMax()

		'''
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
		'''

	finally:
		#print('__main__ finally')
		#javabridge.kill_vm()
		pass

	print('bstack __main__ finished')
