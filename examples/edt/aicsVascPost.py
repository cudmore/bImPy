"""
# 20200625

	Take the output folder of aicsVasc (usually anallysisAics) and post proccess raw/mask pairs
		- 0 out slices in mask where corresponding slice in raw has low SNR
"""

import os, sys, time, glob

import multiprocessing as mp

import numpy as np

import bimpy

def myRunPost(path, idx, saveFolder='analysisAicsPost'):
	"""
	path is path to raw analysisAics/ channel file, like
		/Users/cudmore/box/data/nathan/20200518/analysisAics/20200518__A01_G001_*_ch2.tif
	
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
	
	numSlices = rawData.shape[0]
	snrList = []
	maskCountList = []
	#print(numSlices, path)
	for i in range(numSlices):
		oneSlice = rawData[i,:,:]
		theMin = np.min(oneSlice)
		theMax = np.max(oneSlice)
		theRange = theMax - theMin + 1
		#print(theRange, i, path)

		maskCount = np.count_nonzero(maskData[i,:,:])
		
		snrList.append(theRange)
		maskCountList.append(maskCount)
		
	return snrList, maskCountList
	
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
		snrList, maskCountList = result.get()
				
	stopTime = time.time()
	print('finished in', round(stopTime-startTime,2), 'seconds')
	
	
