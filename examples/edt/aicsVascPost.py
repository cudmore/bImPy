"""
	Date: 20200625
	Author: Robert Cudmore
	
	Take the output folder of aicsVasc (usually analysisAics/) and post proccess raw/mask pairs
		- 0 out slices in mask where corresponding slice in raw has low SNR
"""

import os, sys, time, glob

import multiprocessing as mp

import numpy as np

import bimpy

def myRunPost(path, idx, snrThresh=None, sliceThresh=None, maskPercentThreshold=None, saveFolder='analysisAicsPost'):
	"""
	path: the path to raw analysisAics/ channel file, like
		/Users/cudmore/box/data/nathan/20200518/analysisAics/20200518__A01_G001_*_ch2.tif
	idx: abs file idx 0, 1, 2
	snrThresh: remove mask slices when image is below this snr
	sliceThresh: remove mask slices when greater than this slice (and snr < snrThresh)
	
	return:
		snrList
		maskCountList
	"""
	#print('path:', path)
	
	tmpPath, tmpFileName = os.path.split(path)
	tmpPath2, tmpfolder = os.path.split(tmpPath)
	
	fileNameNoExtension = tmpFileName.split('.')[0]
	
	savePath = os.path.join(tmpPath2, saveFolder)
	if not os.path.isdir(savePath):
		try:
			os.mkdir(savePath)
		except (FileExistsError) as e:
			pass
	savePath = os.path.join(savePath, fileNameNoExtension)
	#print('  savePath:', savePath)
	
	#
	# load the raw
	rawData, rawHeader = bimpy.util.imread(path)
	
	# load the mask
	loadMaskPath = os.path.join(tmpPath, fileNameNoExtension)
	loadMaskPath = loadMaskPath + '_mask.tif'
	#print('loadMaskPath:', loadMaskPath)
	maskData, maskHeader = bimpy.util.imread(loadMaskPath)
	
	finalMaskData = maskData.copy()
	
	numSlices = rawData.shape[0]
	snrList = []
	maskCountList = []
	maskPercentList = []
	#print(numSlices, path)
	for i in range(numSlices):
		oneSlice = rawData[i,:,:]
		if i ==0:
			pixelsInSlice = oneSlice.shape[0] * oneSlice.shape[1]
		theMin = np.min(oneSlice)
		theMax = np.max(oneSlice)
		theRange = theMax - theMin + 1
		#print(theRange, i, path)

		maskCount = np.count_nonzero(maskData[i,:,:])
		maskPercent = maskCount / pixelsInSlice

		# strip out mask (and save)
		if snrThresh is not None and sliceThresh is not None:
			if theRange<snrThresh and i>sliceThresh:
				#print('mask out slice', i, idx, path)
				maskCount = 0
				maskPercent = 0
				finalMaskData[i,:,:] = 0
		if maskPercentThreshold is not None:
			if maskPercent > maskPercentThreshold:
				maskCount = 0
				maskPercent = 0
				finalMaskData[i,:,:] = 0
				
		snrList.append(theRange)
		maskCountList.append(maskCount)
		maskPercentList.append(maskPercent)
					
	doSave = snrThresh is not None and sliceThresh is not None
	if doSave:
		# raw
		saveRawPath = savePath + '.tif'
		bimpy.util.imsave(saveRawPath, rawData, tifHeader=rawHeader, overwriteExisting=True)
		# mask
		saveMaskPath = savePath + '_mask.tif'
		bimpy.util.imsave(saveMaskPath, finalMaskData, tifHeader=rawHeader, overwriteExisting=True)
		
	return idx, snrList, maskCountList, maskPercentList
	
if __name__ == '__main__':

	path = '/Users/cudmore/box/data/nathan/20200518/analysisAics/20200518__A01_G001_*_ch2.tif'
	filenames = glob.glob(path)
	print('proccessing', len(filenames), 'files')
	
	startTime = time.time()
	
	cpuCount = mp.cpu_count()
	cpuCount -= 2
	pool = mp.Pool(processes=cpuCount)
	results = [pool.apply_async(myRunPost, args=(file,myIdx+1)) for myIdx, file in enumerate(filenames)]
	for idx, result in enumerate(results):
		#print(result.get())
		returnIdx, snrList, maskCountList, maskPercentList = result.get()
				
	stopTime = time.time()
	print('finished in', round(stopTime-startTime,2), 'seconds')
	
	
