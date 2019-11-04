import os

import numpy as np
import pandas as pd

import tifffile

#from collections import OrderedDict
from xml.dom import minidom # to load vesselucida xml file

from bimpy import bSlabList

################################################################################

################################################################################
class bSimpleStack:
	def __init__(self, path, loadImages=True):
		self.path = path

		pointFilePath, ext = os.path.splitext(self.path)
		self.maskPath = pointFilePath + '_mask.tif' # DeepVess outut matrix V
		self.skelPath = pointFilePath + '_skel.tif' # DeepVess output matric C

		self._imagesMask = None
		self._imagesSkel = None

		self._voxelx = 1
		self._voxely = 1

		self._images = None
		self._imagesMask = None

		if loadImages:
			self.loadStack()

		# load vesselucida analysis from .xml file
		self.slabList = bSlabList(self.path)
		if self.slabList.x is None:
			self.slabList = None

	@property
	def voxelx(self):
		return self._voxelx

	@property
	def voxely(self):
		return self._voxely

	@property
	def pixelsPerLine(self):
		return self._images.shape[2]

	@property
	def linesPerFrame(self):
		return self._images.shape[1]

	@property
	def numSlices(self):
		if self._images is not None:
			return self._images.shape[0]
		else:
			return None

	@property
	def bitDepth(self):
		dtype = self._images.dtype
		if dtype == 'uint8':
			return 8
		else:
			return 16

	def slabMatrix_original(self):
		"""
		return all original slabs as a 2d numpy matrix
		for nathan convex hull
		"""
		x = self.slabList.orig_x
		y = self.slabList.orig_y
		z = self.slabList.orig_z
		# put 1d arrays of (x,y,z) into 2d matrix
		points = np.column_stack((x,y,z))
		return points

	def loadStack(self):
		# load original image
		thisPath = self.path
		print('bSimpleStack.loadStack() loading path:', thisPath)
		with tifffile.TiffFile(thisPath) as tif:
			self._images = tif.asarray()
		self.imageStats(thisStack='ch1')

		# load mask
		thisPath = self.maskPath
		if os.path.isfile(thisPath):
			print('bSimpleStack.loadStack() loading path:', thisPath)
			with tifffile.TiffFile(thisPath) as tif:
				self._imagesMask = tif.asarray()
			#self.imageStats(thisStack='mask')

		# load skel
		thisPath = self.skelPath
		if os.path.isfile(thisPath):
			print('bSimpleStack.loadStack() loading path:', thisPath)
			with tifffile.TiffFile(thisPath) as tif:
				self._imagesSkel = tif.asarray()
			#self.imageStats(thisStack='skel')

	'''
	def imageStats(self, thisStack='ch1', index=None):
		"""
		thisStack: not implemented
		"""

		if index == None:
			# whole stack
			print('   self._images.shape:', self._images.shape)
			print('   self._images.dtype:', self._images.dtype)
			print('   min:', np.min(self._images))
			print('   max:', np.max(self._images))
	'''

	def getSlidingZ(self, sliceNumber, thisStack, upSlices, downSlices, minContrast, maxContrast):

		startSlice = sliceNumber - upSlices
		if startSlice < 0:
			startSlice = 0
		stopSlice = sliceNumber + downSlices
		if stopSlice > self.numSlices - 1:
			stopSlice = self.numSlices - 1

		if thisStack == 'ch1':
			img = self._images[startSlice:stopSlice, :, :].copy()
		elif thisStack == 'mask':
			img = self._imagesMask[startSlice:stopSlice, :, :].copy()
		elif thisStack == 'skel':
			img = self._imagesSkel[startSlice:stopSlice, :, :].copy()
		else:
			print('error: getSlidingZ() got bad thisStack:', thisStack)

		img = np.max(img, axis=0)

		return self.setSliceContrast(sliceNumber, minContrast=minContrast, maxContrast=maxContrast, img=img)

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
				img = self._images[sliceNumber, :, :].copy()
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


	def saveAnnotations(self):
		if self.slabList is not None:
			self.slabList.save()

	def setAnnotation(self, this, value):
		if this == 'toggle bad edge':
			if self.slabList is not None:
				self.slabList.toggleBadEdge(value)

	#
	# I really have no idea what the next two functions are doing
	'''
	def _display0(self, image, display_min, display_max): # copied from Bi Rico
		# Here I set copy=True in order to ensure the original image is not
		# modified. If you don't mind modifying the original image, you can
		# set copy=False or skip this step.
		image = np.array(image, copy=True)
		image.clip(display_min, display_max, out=image)
		image -= display_min
		np.floor_divide(image, (display_max - display_min + 1) / 256,
						out=image, casting='unsafe')
		return image.astype(np.uint8)

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
			#return np.take(lut, self.getImage(channel=channel, sliceNum=sliceNum))
			return np.take(lut, self._images[sliceNum,:,:])
	'''
