import os, math

import numpy as np
import pandas as pd

import tifffile

################################################################################
class bSlabList:
	"""
	full list of all points in a vascular tracing
	"""
	def __init__(self, tifPath):

		self.id = None # to count edges
		self.x = None
		self.y = None
		self.z = None

		self.edgeList = [] # this should be .annotationList

		# todo: change this to _slabs.txt
		pointFilePath, ext = os.path.splitext(tifPath)
		pointFilePath += '_slabs.txt'

		if not os.path.isfile(pointFilePath):
			print('bSlabList error, did not find', pointFilePath)
			return
		else:
			df = pd.read_csv(pointFilePath)

			nSlabs = len(df.index)
			#self.id = np.full(nSlabs, np.nan) #df.iloc[:,0].values # each point/slab will have an edge id
			self.id = np.full(nSlabs, 0) #df.iloc[:,0].values # each point/slab will have an edge id

			self.x = df.iloc[:,0].values
			self.y = df.iloc[:,1].values
			self.z = df.iloc[:,2].values

			print('tracing z max:', np.nanmax(self.z))

		self.analyze()

	@property
	def numSlabs(self):
		return len(self.x)

	@property
	def numEdges(self):
		return len(self.edgeList)

	def save(self):
		"""
		Save _ann.txt file from self.annotationList
		"""
		print('bSlabList.save()')

		# headers are keys of xxxx

		# each element in xxx is a comma seperated row

	def load(self):
		"""
		Load _ann.txt file
		Store in self.annotationList
		"""
		print('bSlabList.load()')

	def toggleBadEdge(self, edgeIdx):
		print('bSlabList.toggleBadEdge() edgeIdx:', edgeIdx)
		self.edgeList[edgeIdx]['Good'] = not self.edgeList[edgeIdx]['Good']
		print('   edge', edgeIdx, 'is now', self.edgeList[edgeIdx]['Good'])

	def getEdge(self, edgeIdx):
		"""
		return a list of slabs in an edge
		"""
		theseIndices = np.argwhere(self.id == edgeIdx)
		return theseIndices

	def analyze(self):
		def euclideanDistance(x1, y1, z1, x2, y2, z2):
			if z1 is None and z2 is None:
				return math.sqrt((x2-x1)**2 + (y2-y1)**2)
			else:
				return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)

		self.edgeList = []

		edgeIdx = 0
		edgeDict = {'type': 'edge', 'n':0, 'Length 3D':0, 'Length 2D':0, 'z':None, 'Good': True}
		n = self.numSlabs
		for pointIdx in range(n):
			self.id[pointIdx] = edgeIdx

			x1 = self.x[pointIdx]
			y1 = self.y[pointIdx]
			z1 = self.z[pointIdx]

			if np.isnan(z1):
				# move on to a new edge/vessel
				edgeDict['Length 3D'] = round(edgeDict['Length 3D'],2)
				edgeDict['Length 2D'] = round(edgeDict['Length 2D'],2)
				self.edgeList.append(edgeDict)
				edgeDict = {'type':'edge', 'n':0, 'Length 3D':0, 'Length 2D':0, 'z':None, 'Good':True} # reset
				edgeIdx += 1
				continue

			edgeDict['n'] = edgeDict['n'] + 1
			if pointIdx > 0:
				edgeDict['Length 3D'] = edgeDict['Length 3D'] + euclideanDistance(prev_x1, prev_y1, prev_z1, x1, y1, z1)
				edgeDict['Length 2D'] = edgeDict['Length 2D'] + euclideanDistance(prev_x1, prev_y1, None, x1, y1, None)
			edgeDict['z'] = int(z1)
			prev_x1 = x1
			prev_y1 = y1
			prev_z1 = z1

		#print(self.edgeList)

		'''
		for idx, id in enumerate(self.id):
			print(self.id[idx], ',', self.x[idx], ',', self.y[idx], ',', self.z[idx])
		'''

################################################################################
class bSimpleStack:
	def __init__(self, path):
		self.path = path

		pointFilePath, ext = os.path.splitext(self.path)
		self.maskPath = pointFilePath + '_mask.tif' # DeepVess outut matrix V
		self.skelPath = pointFilePath + '_skel.tif' # DeepVess output matric C
		
		self._voxelx = 1
		self._voxely = 1

		self._images = None
		self._imagesMask = None
		self.loadStack()

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
		
		# load mask
		thisPath = self.skelPath
		if os.path.isfile(thisPath):
			print('bSimpleStack.loadStack() loading path:', thisPath)
			with tifffile.TiffFile(thisPath) as tif:
				self._imagesSkel = tif.asarray()
			#self.imageStats(thisStack='skel')
		
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
		
		img: pass this in to contrast adjust an existing image, e.g. from slidinz z-projection
		
		autoContrast: probably not working
		"""
		
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
