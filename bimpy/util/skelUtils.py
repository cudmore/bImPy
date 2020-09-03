"""
20200901

try to fix non-isomorphic shape, x/y/z
"""
import os
import numpy as np

import skimage

import skan # see: https://jni.github.io/skan/

import bimpy


def getChannelStr(path):
	chStr = None
	if path.endswith('_ch1.tif'):
		chStr = '_ch1'
	elif path.endswith('_ch2.tif'):
		chStr = '_ch2'
	elif path.endswith('_ch2.tif'):
		chStr = '_ch3'
	if chStr is None:
		return None
	else:
		return chStr

def getBasePathNoChannels(path):
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


################################################################################
def makeSkel(path):
	"""
	path: full path to _ch1.tif or _ch2.tif
	"""
	print('=== makeSkel() path:', path)

	# load raw
	print('  loading raw:', path)
	stackData, stackHeader = bimpy.util.bTiffFile.imread(path)
	print('    stackData:', stackData.shape)

	# load mask
	maskPath, tmpExt = os.path.splitext(path)
	maskPath += '_mask.tif'
	print('  loading mask:', maskPath)
	maskData, maskHeader = bimpy.util.bTiffFile.imread(maskPath)
	print('    maskData:', stackData.shape)

	# erode mask before making 1-pixel skeleton
	iterations = 1
	print('  binary_erosion with iterations:', iterations)
	maskData = bimpy.util.morphology.binary_erosion(maskData, iterations=iterations)

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
	stackData, tifHeader = bimpy.util.bTiffFile.imread(path)
	print('zExpandStack() path:', path)
	print('  original path', stackData.shape)

	xVoxel = tifHeader['xVoxel']
	zVoxel = tifHeader['zVoxel']
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
	bimpy.util.bTiffFile.imsave(savePath, newData, tifHeader=tifHeader, overwriteExisting=True)

################################################################################
def zCompressStack(path):
	"""
	path: to expanded .tif, something like 'a'

	assuming we ran aicsVasc, also compress (labeled, labeled_removed, mask)
	"""
	chStr = getChannelStr(path)
	basePath = getBasePathNoChannels(path)
	print('zCompressStack() path:', path)
	print('  chStr:', chStr)
	print('  basePath:', basePath)

	# raw
	stackData, tiffHeader = bimpy.util.bTiffFile.imread(path)
	print('  stackData', stackData.shape)

	xVoxel = tiffHeader['xVoxel']
	zVoxel = tiffHeader['zVoxel']
	print('  xVoxel:', xVoxel)
	print('  zVoxel:', zVoxel)

	zMult = zVoxel / xVoxel
	print('  zMult:', zMult)
	zMult = round(zMult) # if zMult==3 we add 1 above and one below

	# mask
	maskPath = basePath + chStr + '_mask.tif'
	print('  maskPath:', maskPath)
	maskData, maskHeader = bimpy.util.bTiffFile.imread(maskPath)

	# labeled
	labeledPath = basePath + chStr + '_labeled.tif'
	print('  labeledPath:', labeledPath)
	labeledData, labeledHeader = bimpy.util.bTiffFile.imread(labeledPath)

	# labeled_removed
	labeledPath2 = basePath + chStr + '_labeled_removed.tif'
	print('  labeledPath2:', labeledPath2)
	labeledData2, labeledHeader2 = bimpy.util.bTiffFile.imread(labeledPath2)

	m = stackData.shape[1]
	n = stackData.shape[2]
	oldNumSlices = stackData.shape[0]

	numExpandedBy = 3 # assuming we expanded by 3
	remainder = oldNumSlices % numExpandedBy
	if remainder != 0:
		print('error in compressing')
		return None
	newNumSlices = int(oldNumSlices / 3 )
	print('  newNumSlices:', newNumSlices)

	newShape = (newNumSlices, m, n)
	newStackData = np.ndarray(newShape, np.uint8)
	newMaskData = np.ndarray(newShape, np.uint8)
	newLabeledData = np.ndarray(newShape, np.uint8)
	newLabeledData2 = np.ndarray(newShape, np.uint8)

	newIdx = 0
	for oldIdx in range(1,oldNumSlices,numExpandedBy): # (start,stop,step)
		print('  oldIdx:', oldIdx, 'newIdx:', newIdx)
		newStackData[newIdx] = stackData[oldIdx]
		newMaskData[newIdx] = maskData[oldIdx]
		newLabeledData[newIdx] = labeledData[oldIdx]
		newLabeledData2[newIdx] = labeledData2[oldIdx]
		newIdx += 1

	#
	# save

	rawSavePath = basePath + 'b' + chStr + '.tif'
	print('  saving rawSavePath:', rawSavePath)
	bimpy.util.bTiffFile.imsave(rawSavePath, newStackData, tifHeader=tiffHeader, overwriteExisting=True)

	# mask
	maskSavePath = basePath + 'b' + chStr + '_mask.tif'
	print('  saving maskSavePath:', maskSavePath)
	bimpy.util.bTiffFile.imsave(maskSavePath, newMaskData, overwriteExisting=True)

	# labeled
	labeledSavePath = basePath + 'b' + chStr + '_labeled.tif'
	print('  saving labeledSavePath:', labeledSavePath)
	bimpy.util.bTiffFile.imsave(labeledSavePath, newLabeledData, overwriteExisting=True)

	# labeled2
	labeledSavePath2 = basePath + 'b' + chStr + '_labeled_removed.tif'
	print('  saving labeledSavePath2:', labeledSavePath2)
	bimpy.util.bTiffFile.imsave(labeledSavePath2, newLabeledData2, overwriteExisting=True)

if __name__ == '__main__':
	if 0:
		path = '/Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch1.tif'
		path = '/Users/cudmore/data/testing/20200717__A01_G001_0014_ch1.tif'
		zExpandStack(path)

		path = '/Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch2.tif'
		path = '/Users/cudmore/data/testing/20200717__A01_G001_0014_ch2.tif'
		zExpandStack(path)

	if 0:
		path = '/Users/cudmore/data/testing/aicsAnalysis/20200717__A01_G001_0014a_ch2.tif'
		zCompressStack(path)

	if 1:
		path = '/Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch2.tif'
		path = '/Users/cudmore/data/testing/aicsAnalysis/20200717__A01_G001_0014ab_ch2.tif'
		#stackObj, stackHeader = bimpy.util.bTiffFile.imread(path)
		#stackObj = bimpy.bStack(path)
		makeSkel(path)
