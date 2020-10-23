"""
20201016

read in a caiman h5f file
	this does not contain original images

to interpret contents of file, see:
	https://github.com/flatironinstitute/CaImAn/wiki/Interpreting-Results

estimates.F_dff: Set of DF/F normalized temporal components.
					Saved as a numpy array with dimensions (# of components X # of timesteps).
					Each row corresponds to the DF/F fluorescence for the corresponding component.

"""

##
##
## Make sure this does NOT use bimpy, I want to call it from simple external scripts
##
##

import numpy as np
import scipy
import scipy.ndimage
import matplotlib.pyplot as plt

def getImage(caimanDict, idx):
	originalShape = caimanDict['originalShape']
	caimanData = np.reshape(caimanDict['A'][:,idx].toarray(), originalShape, order='F')
	return caimanData

def getRing(caimanDict, idx, iterations=1):
	"""
	get an roi as an image mask with one pixel outline
	"""
	caimanData = getImage(caimanDict, idx)
	caimanDataMask = caimanData > 0
	caimanDataMask[caimanDataMask] = 255

	# erode, returns a true/false mask?
	erodedMask = scipy.ndimage.morphology.binary_erosion(caimanDataMask,
											structure=None,
											iterations=iterations)
	caimanDataMask[erodedMask] = 0
	'''
	print('  caimanData:', caimanData.shape)
	print('  caimanDataMask:', caimanDataMask.shape, caimanDataMask.dtype)
	print('  erodedMask:', erodedMask.shape, erodedMask.dtype)
	'''
	
	# when we overlay the image (with opacity=0.5 for example)
	# 0 values actually dim the image
	#caimanDataMask[caimanDataMask==0] = np.nan

	return caimanDataMask

def getCentroid(caimanDict, idx):
	"""
	get the (x,y) center of mass of an roi
	"""
	caimanData = getImage(caimanDict, idx)
	(x,y) = scipy.ndimage.measurements.center_of_mass(caimanData)
	return (x,y)

def plotCaimanImage(caimanDict, plotTheseComponents=None, ax=None):
	"""
	use matplotlib to plot the components/spots detected by caiman
	"""

	originalShape = caimanDict['originalShape']
	numROI = caimanDict['A'].shape[1]

	if plotTheseComponents is None or len(plotTheseComponents)==0:
		plotTheseComponents = range(numROI)

	print(f'plotCaimanImage() is plotting {len(plotTheseComponents)} components')

	#
	# view the i-th component
	#dims = (1200, 456) # original image size
	tmpImage = np.zeros(originalShape, dtype=np.float64)
	for roiIdx in plotTheseComponents:
		# each component is shape of original image (dims)
		oneComponent = np.reshape(caimanDict['A'][:,roiIdx].toarray(), originalShape, order='F')
		tmpImage += oneComponent
	#
	if ax is None:
		plt.figure()
		plt.imshow(tmpImage)
		#plt.show()
	else:
		ax.imshow(tmpImage)

def caimanAlignSpikes(caimanDict, plotTheseComponents=None, thresh=0.1, refractoryPoints=10):
	prePoints = 6
	postPoints = 30

	# rawPlotList is a list of np array
	idxList, rawPlotList, spikeTimeList = caimanAnalyze(
											caimanDict,
											plotTheseComponents=plotTheseComponents,
											thresh=thresh,
											refractoryPoints=refractoryPoints
											)
	spikeClipList = []
	for idx, roiIdx in enumerate(idxList):
		oneRawPlot = rawPlotList[idx]
		spikeTimes = spikeTimeList[idx]
		n = len(oneRawPlot) # all are same
		for spikeTime in spikeTimes:
			startPoint = spikeTime - prePoints
			stopPoint = spikeTime + postPoints
			numPointsInClip = stopPoint - startPoint #+ 1
			oneSpikeClip = np.zeros(numPointsInClip) # set up nan in case clip under/over runs trace
			oneSpikeClip[:] = np.nan
			if startPoint < 0:
				# abort
				pass
			elif stopPoint > n-1:
				# abort
				pass
			else:
				oneSpikeClip = oneRawPlot[startPoint:stopPoint]
			# append
			#print('caimanAlignSpikes', idx, 'oneSpikeClip:', oneSpikeClip.shape)
			spikeClipList.append(oneSpikeClip)

	#
	return spikeClipList

def caimanAnalyze(caimanDict, plotTheseComponents=None, thresh=0.1, refractoryPoints=10):
	"""
	returns analysis of a number of caiman rois

	returns:
		idxList: list of ROI index
		rawPlotList: list of raw data (all frames) for each roi, each idx is np array
		spikeTimeList: list of spike times
	"""
	if plotTheseComponents is None or len(plotTheseComponents)==0:
		numROI = caimanDict['A'].shape[1]
		plotTheseComponents = range(numROI)

	idxList = []
	rawPlotList = []
	spikeTimesList = []
	for idx, roiIdx in enumerate(plotTheseComponents):
		rawPlot, spikeTimes = getCaimanTrace(caimanDict, roiIdx,
								thresh=thresh, refractoryPoints=refractoryPoints)
		idxList.append(roiIdx)
		rawPlotList.append(rawPlot)
		spikeTimesList.append(spikeTimes)

	return idxList, rawPlotList, spikeTimesList

def getCaimanTrace(caimanDict, roiIdx, thresh=0.12, refractoryPoints=10, doDetect=True):
	"""
	return:
		rawPlot: np array
		spikeTimes: list of spike times
	"""
	rawPlot = caimanDict['F_dff'][roiIdx]
	if doDetect:
		spikeTimes = spikeDetect(rawPlot, thresh, refractoryPoints=refractoryPoints)
	else:
		spikeTimes = []

	return rawPlot, spikeTimes

def plotCaimanTrace(caimanDict, thresh=0.12, plotTheseComponents=None, ax=None):
	"""
	use matplotlib to plot the time series of each components/spots detected by caiman
	this is plotting the final int/int_0 in F_dff
	"""
	if plotTheseComponents is None or len(plotTheseComponents)==0:
		numROI = caimanDict['A'].shape[1]
		plotTheseComponents = range(numROI)

	print(f'plotCaimanTrace() is plotting {len(plotTheseComponents)} components')

	if ax is None:
		plt.figure()
	myOffset = 0.5
	for idx, roiIdx in enumerate(plotTheseComponents):
		rawPlot = caimanDict['F_dff'][roiIdx]
		finalPlot = caimanDict['F_dff'][roiIdx].copy() # we will modify this, need a copy !!!
		finalPlot += idx * myOffset # plot each trace at an offset (max y for dataset is 0.5)

		# plot
		if ax is None:
			plt.plot(finalPlot, 'k-')
		else:
			ax.plot(finalPlot, 'k-')

		#thresh = 0.12
		n = len(rawPlot)
		#t = np.linspace(0, n, num=n)
		spikeTimes = spikeDetect(rawPlot, thresh)

		# debug
		'''
		print('roiIdx:', roiIdx)
		print('  len(rawPlot):', len(rawPlot), rawPlot.shape)
		print('  len(spikeTimes):', len(spikeTimes), spikeTimes)
		'''

		if len(spikeTimes) > 0:
			if ax is None:
				plt.plot(spikeTimes, finalPlot[spikeTimes], 'ro', markersize=4)
			else:
				ax.plot(spikeTimes, finalPlot[spikeTimes], 'ro', markersize=4)

	#
	#plt.show()

def spikeDetect(v, thresh=0.15, refractoryPoints=10):
	"""
	v: the trace to detect on, for now this is caiman df/df_0
	thresh:
	"""

	mask = np.diff(1 * (v > thresh) != 0)
	spikeTimes = np.where(mask==True)[0] # todo: what happend when no spikes?

	# good spikes are on an upslope where (v[spikeTime-1] < v[spikeTime+1])
	goodSpikeTimes = [spikeTime for spikeTime in spikeTimes if (v[spikeTime-1] < v[spikeTime+1])]

	# todo: add in a refractory period to reject odulb espikes
	#refractoryPoints = 10 # 10 corresponds to about 0.5 seconds
	goodSpikeTimes2 = goodSpikeTimes
	if len(goodSpikeTimes) > 0:
		goodSpikeTimes2 = [goodSpikeTimes[0]] # first spike is always good

		goodSpikeTimes2 += [spikeTime for idx,spikeTime in enumerate(goodSpikeTimes[1:],1) if (goodSpikeTimes[idx] - goodSpikeTimes[idx-1] > refractoryPoints)]

		# this also works
		'''
		for idx, spikeTime in enumerate(goodSpikeTimes):
			if idx==0:
				continue
			timeFromLast = goodSpikeTimes[idx] - goodSpikeTimes[idx-1]
			if timeFromLast > refractoryPoints:
				goodSpikeTimes2 += [goodSpikeTimes[idx]] # append list to list
		'''

	return goodSpikeTimes2

if __name__ == '__main__':

	path = '/media/cudmore/data/20201014/inferior/2_nif_inferior_cropped_results.hdf5'
	path = '/media/cudmore/data/20201014/inferior/3_nif_inferior_cropped_results.hdf5'

	#import readCaiman
	from readCaiman import readCaiman

	caimanDict = readCaiman(path)

	# testing
	'''
	caimanImage = getImage(caimanDict, 0)
	(x,y) = getCentroid(caimanDict, 0)
	'''

	# this is taken from bimpy interface, after marking ROI within vasculature as good

	# 2_nif_inferior_cropped_results
	#plotTheseComponents = []

	# 3_nif_inferior_cropped_results
	plotTheseComponents = [2, 3, 6, 7, 12, 13, 14, 15, 21, 22, 23, 24, 25, 29, 30, 31, 32, 33, 34, 35, 41, 42, 43, 44, 45, 47, 57, 58, 59, 60, 67, 68, 69, 70, 71, 72, 75, 76, 77, 80, 81, 83, 84, 85, 87, 88, 92, 93, 94, 95, 96, 97, 100, 103, 104, 105, 106, 107, 108, 110, 111, 113, 114, 115, 118]

	# 4_nif_inferior_cropped_results
	#plotTheseComponents = []

	plotCaimanImage(caimanDict, plotTheseComponents=plotTheseComponents)
	plotCaimanTrace(caimanDict, plotTheseComponents=plotTheseComponents)
