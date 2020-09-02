"""
20200901

try to fix non-isomorphic shape, x/y/z
"""
import os
import numpy as np

import skimage

import skan # see: https://jni.github.io/skan/

import bimpy

################################################################################
def makeSkel(path):
	"""
	path: full path to _ch1.tif or _ch2.tif
	"""
	print('=== makeSkel() path:', path)

	def getBasePathNoChannels(path):
		if not path.endswith('_ch1.tif'):
			return None
		if not path.endswith('_ch2.tif'):
			return None
		if not path.endswith('_ch2.tif'):
			return None
		basePath, tmpExt = os.path.splitext(path)
		basePath = basePath.replace('_ch1', '')
		basePath = basePath.replace('_ch2', '')
		return basePath

	def getFileNameNoChannels(path):
		"""
		path needs to end in ch 1/2/3 .tif
		like _ch1.tif
		"""
		goodFile = False
		if path.endswith('_ch1.tif'):
			goodFile = True
		elif path.endswith('_ch2.tif'):
			goodFile = True
		elif path.endswith('_ch2.tif'):
			goodFile = True
		if not goodFile:
			return None

		basePath, tmpExt = os.path.splitext(path)
		basePath2, baseFileName = os.path.split(basePath)

		baseFileName = baseFileName.replace('_ch1', '')
		baseFileName = baseFileName.replace('_ch2', '')
		baseFileName = baseFileName.replace('_ch3', '')
		return baseFileName

	# load raw
	print('  loading raw:', path)
	stackData, stackHeader = bimpy.util.bTiffFile.imread(path)
	print('    stackData:', stackData.shape)

	# load max
	maskPath, tmpExt = os.path.splitext(path)
	maskPath += '_mask.tif'
	print('  loading mask:', maskPath)
	maskData, maskHeader = bimpy.util.bTiffFile.imread(maskPath)
	print('    maskData:', stackData.shape)

	baseFileName = getFileNameNoChannels(path)
	uFirstSlice = None
	uLastSlice = None
	try:
		print('  looking in bVascularTracingAics.stackDatabase for baseFileName:', baseFileName)
		trimDict = bimpy.bVascularTracingAics.stackDatabase[baseFileName]
		uFirstSlice = trimDict['uFirstSlice']
		uLastSlice = trimDict['uLastSlice']
	except (KeyError) as e:
		print('  warning: did not find stack baseFileName:', baseFileName, 'in bVascularTracingAics.stackDatabase ---->>>> NO PRUNING/BLANKING')

	doFirstLast = False
	if doFirstLast and uFirstSlice is not None and uLastSlice is not None:
		print('  makeSkel() pruning/blanking slices:', uFirstSlice, uLastSlice)
		maskData[0:uFirstSlice-1,:,:] = 0
		maskData[uLastSlice:-1,:,:] = 0

	#
	print('  - generating 1-pixel skeleton from mask using skimage.morphology.skeletonize_3d ...')
	myTimer = bimpy.util.bTimer('skeletonizeTimer')
	skeletonData = skimage.morphology.skeletonize_3d(maskData)
	print('    skeletonData:', skeletonData.shape, skeletonData.dtype)
	print('  ', myTimer.elapsed())

	# save 1-pixel skel stack
	skelPath, tmpExt = os.path.splitext(path)
	skelPath += '_skel.tif'
	print('  saving 1-pixel skel skelPath:', skelPath)
	bimpy.util.bTiffFile.imsave(skelPath, skeletonData)

	#
	print('  - generating skeleton graph from mask using skan.Skeleton ...')
	myTimer = bimpy.util.bTimer('skan Skeleton')
	#skanSkel = skan.Skeleton(skeletonData, source_image=stackData.astype('float'))
	skanSkel = skan.Skeleton(skeletonData, source_image=stackData)
	print('  ', myTimer.elapsed())

	# not needed but just to remember
	branch_data = skan.summarize(skanSkel) # branch_data is a pandas dataframe
	print('    branch_data.shape:', branch_data.shape)
	print(branch_data.head())

################################################################################
def zExpandStack(path):
	"""
	expand a raw stack in z by adding/copying slices above/below each original slice
	"""
	stackData, stackHeader = bimpy.util.bTiffFile.imread(path)
	print('zExpandStack() path:', path)
	print('  original path', stackData.shape)

	xVoxel = stackHeader['xVoxel']
	zVoxel = stackHeader['zVoxel']
	print('  xVoxel:', xVoxel)
	print('  zVoxel:', zVoxel)

	zMult = zVoxel / xVoxel
	print('  zMult:', zMult)
	zMult = round(zMult) # if zMult==3 we add 1 above and one below
	'''
	if (zMult % 2) == 0:
		# already even
		pass
	else:
		zMult += 1
	'''
	m = stackData.shape[1]
	n = stackData.shape[2]
	numSlices = stackData.shape[0]
	newNumSlices = numSlices * zMult # assuming zMult is even
	print('  newNumSlices:', newNumSlices)

	newShape = (newNumSlices, m, n)
	newData = np.ndarray(newShape, dtype=np.uint8)
	for i in range(numSlices):
		newIdx = 1 + i * zMult # assuming zMult==3
		#print('  newIdx:', newIdx)
		newData[newIdx-1] = stackData[i]
		newData[newIdx] = stackData[i]
		newData[newIdx+1] = stackData[i]

	#
	# save
	savePath, tmpExt = os.path.splitext(path)
	if savePath.endswith('_ch1'):
		channel = 1
		chStr = '_ch1'
	elif savePath.endswith('_ch2'):
		channel = 2
		chStr = '_ch2'
	savePath = savePath.replace('_ch1', '')
	savePath = savePath.replace('_ch2', '')

	savePath += 'a' + chStr + '.tif'

	print('  saving:', savePath)
	bimpy.util.bTiffFile.imsave(savePath, newData, overwriteExisting=True)

if __name__ == '__main__':
	if 1:
		path = '/Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch1.tif'
		path = '/Users/cudmore/data/testing/20200717__A01_G001_0014_ch1.tif'
		zExpandStack(path)

		path = '/Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch2.tif'
		path = '/Users/cudmore/data/testing/20200717__A01_G001_0014_ch2.tif'
		zExpandStack(path)

	if 0:
		path = '/Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch2.tif'
		path = '/Users/cudmore/data/testing/20200717__A01_G001_0014_ch2.tif'
		#stackObj, stackHeader = bimpy.util.bTiffFile.imread(path)
		#stackObj = bimpy.bStack(path)
		makeSkel(path)
