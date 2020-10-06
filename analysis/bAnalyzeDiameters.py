import os, sys, time

import multiprocessing as mp

import numpy as np

import bimpy

def runDiameterPool(stackObject):
	print('runDiameterPool() stack:', stackObject.print())

	#myStack = bimpy.bStack(path=path)

	# making these global (bad form) because I can't call
	# Pool() init with bStack (i tis not iterable)
	global gStackObject
	gStackObject = stackObject

	# todo: the stack already has this -->> no need for global
	global gLineProfile
	gLineProfile = bimpy.bLineProfile(gStackObject)

	myTimer = bimpy.util.bTimer('runDiameterPool')
	#startTime = time.time()

	cpuCount = mp.cpu_count()
	print('  total cpuCount:', cpuCount)
	cpuCount -= 2
	print('  using cpuCount:', cpuCount)
	# The multiprocessing.pool.ThreadPool behaves the same as the multiprocessing.Pool
	#with the only difference that uses threads instead of processes
	#to run the workers logic
	'''
	initargs = stackObject.slabList
	pool = mp.Pool(processes=cpuCount,
		initializer=my_mpInit, initargs=initargs) #, maxtasksperchild=10)
	'''
	pool = mp.Pool(processes=cpuCount) #, maxtasksperchild=10)

	'''
	radius = 12
	lineWidth = 5
	medianFilter = 5
	'''
	detectionDict = gLineProfile.getDefaultDetectionParams()

	nEdges = gStackObject.slabList.numEdges()
	print('  nEdges:', nEdges)

	for edgeIdx in range(nEdges):
		args = [edgeIdx, detectionDict]
		oneResult = pool.apply_async(my_mpWorker, args, callback=my_mpCallback)

	pool.close()
	pool.join()

	#stopTime = time.time()
	#elapsed = round(stopTime-startTime,2) #seconds
	#elapsedMinutes = round(elapsed/60, 2)
	#print(f'finished {nEdges} edges in {elapsed} seconds, {elapsedMinutes} minutes')
	print(myTimer.elapsed())

	# save gStackObject !!!
	'''
	print('saving gStackObject')
	gStackObject.saveAnnotations()
	'''

def my_mpCallback(result):
	"""
	apply_async() callback
	"""
	def getMeanFromList(theList):
		if np.isnan(theList).all():
			return np.nan
		else:
			return np.nanmean(theList)

	# unzip result into local variables
	oneEdgeIdx, oneSlabIdxList, \
	oneDiamList, \
	one_lpMinList, one_lpMaxList, one_lpSNRList = result

	#oneEdgeIdx, oneSlabIdxList, oneDiamList = result.get() # edgeIdx, slabIdxList, thisDiamList
	if oneEdgeIdx % 500 == 0:
		print('    my_mpCallback() oneEdgeIdx:', oneEdgeIdx, 'to', oneEdgeIdx+500)

	#print('  start my_mpCallback() oneEdgeIdx:', oneEdgeIdx)

	global gStackObject # we are mofifying this

	# slabs have properties (diam, lpMin, lpMax, lpSNR)
	for oneResultIdx, oneSlabIdx in enumerate(oneSlabIdxList):
		gStackObject.slabList.d2[oneSlabIdx] = oneDiamList[oneResultIdx]
		gStackObject.slabList.lpMin[oneSlabIdx] = one_lpMinList[oneResultIdx]
		gStackObject.slabList.lpMax[oneSlabIdx] = one_lpMaxList[oneResultIdx]
		gStackObject.slabList.lpSNR[oneSlabIdx] = one_lpSNRList[oneResultIdx]

	thisDiamMean = np.nan
	this_SNR_Mean = np.nan
	if len(oneDiamList) > 0:
		thisDiamMean = getMeanFromList(oneDiamList)
		this_SNR_Mean = getMeanFromList(one_lpSNRList)

	# todo: don't use getEdge() here, expensive
	# just index directly
	edgeDict = gStackObject.slabList.getEdge(oneEdgeIdx)
	edgeDict['Diam2'] = thisDiamMean
	edgeDict['mSlabSNR'] = this_SNR_Mean

	#print('  done my_mpCallback() oneEdgeIdx:', oneEdgeIdx)

def my_mpWorker(edgeIdx, detectionDict):
	"""
	do the work for one edge
	return results for the list of slabs
	"""

	#print('my_mpWorker() edgeIdx:', edgeIdx)

	# slabList.getEdge() also returns nodes !!!
	edgeDict = gStackObject.slabList.getEdge(edgeIdx)

	mySlabList = edgeDict['slabList']

	# remove first/last slab, they are nodes
	#mySlabList

	#myNumSlabs = len(mySlabList)

	# abb oct2020 todo: make thesee lists up front, we know the # odf slabs
	slabIdxList = []
	thisDiamList = [np.nan for x in mySlabList]
	this_lpMinList = [np.nan for x in mySlabList]
	this_lpMaxList = [np.nan for x in mySlabList]
	this_lpSNRList = [np.nan for x in mySlabList]

	for idx, slabIdx in enumerate(mySlabList):

		slabIdxList.append(slabIdx)

		if idx==0 or idx==len(mySlabList)-1:
			# don't analyze pre/post nodes
			# we will return lists with these as np.nan
			continue

		'''
		abb oct2020
		we need a dict to specify all line detection params
			radius: passed to bLineProfile.getLine to make the actual line

		'''

		#lpDict = gLineProfile.getLine(slabIdx, radius=radius) # default is radius=30
		# this uses line radius internal to bLineProfile
		xSlabPlot, ySlabPlot = gLineProfile.getSlabLine2(slabIdx) #

		# without numpy import this fails but we never see an exception?
		#thisDiam = np.nan

		if lpDict is not None:
			#retDict = gLineProfile.getIntensity(lpDict, lineWidth=lineWidth, medianFilter=medianFilter)
			retDict = gLineProfile.getLineProfile2(lpDict, xSlabPlot, ySlabPlot)
			if retDict is not None:
				oneDiam = retDict['diam'] # can be np.nan
				one_lpMin = retDict['minVal']
				one_lpMax = retDict['maxVal']
				one_lpSNR = retDict['snrVal']
				# append
				thisDiamList[idx] = oneDiam
				this_lpMinList[idx] = one_lpMin
				this_lpMaxList[idx] = one_lpMax
				this_lpSNRList[idx] = one_lpSNR
				#self.d2[slabIdx] = retDict['diam']

	#print('  done my_mpWorker() edgeIdx:', edgeIdx)
	return edgeIdx, slabIdxList, thisDiamList, this_lpMinList, this_lpMaxList, this_lpSNRList

if __name__ == '__main__':
	# this is output of saNode.aicsVasc.py
	# folder contains (raw, labeled)
	#path = '/home/cudmore/data/nathan/20200814_SAN3_BOTTOM_tail/aicsAnalysis/20200814_SAN3_BOTTOM_tail_ch2.tif'

	maskStartStop = None

	#SAN4_head, keep 36:93
	path = '/home/cudmore/data/nathan/SAN4/aicsAnalysis/SAN4_head_ch2.tif'
	maskStartStop = (36,93)

	path = '/home/cudmore/data/nathan/SAN4/aicsAnalysis/SAN4_mid_ch2.tif'
	maskStartStop = (69,98)

	path = '/home/cudmore/data/nathan/SAN4/aicsAnalysis/SAN4_tail_ch2.tif'
	maskStartStop = (9,46)

	# TESTING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	path = '/home/cudmore/data/nathan/SAN4/aicsAnalysis/testing/SAN4_tail_ch2.tif'
	maskStartStop = (9,46)

	# load the stack
	myStack = bimpy.bStack(path=path, loadImages=True, loadTracing=True)

	#
	# some options
	remakeSkelFromMask = False
	saveAtEnd = False

	# SLOW: load mask and make skel from mask
	if remakeSkelFromMask:
		myStack.slabList.loadDeepVess(vascChannel=2, maskStartStop=maskStartStop)

	# remove edges based on criterion
	if 0:
		#
		# remove all nCon==0
		edgeListToRemove = bimpy.bVascularTracingAics._getListFromCriterion(
					myStack.slabList,
					'edges',
					'nCon', '==', 0,
					verbose=True)

		# delete the edges
		bimpy.bVascularTracingAics._deleteList(myStack.slabList,
					'edges',
					edgeListToRemove,
					verbose=True)


		#
		# remove (nCon==1 and nSlab<20)
		edgeListToRemove = bimpy.bVascularTracingAics._getListFromCriterion(
					myStack.slabList,
					'edges',
					'nCon', '==', 1,
					verbose=True)
		#
		edgeListToRemove = bimpy.bVascularTracingAics._getListFromCriterion(
					myStack.slabList,
					'edges',
					'nSlab', '<', 20,
					fromThisList=edgeListToRemove,
					verbose=True)
		# delete edges
		bimpy.bVascularTracingAics._deleteList(myStack.slabList,
					'edges',
					edgeListToRemove,
					verbose=True)

		#
		# now we have a bunch of nodes with nEdges==0
		print('  == after deleting edges')
		nodeListToRemove = bimpy.bVascularTracingAics._getListFromCriterion(
					myStack.slabList,
					'nodes',
					'nEdges', '==', 0,
					verbose=True)
		# delete edges
		bimpy.bVascularTracingAics._deleteList(myStack.slabList,
					'nodes',
					nodeListToRemove,
					verbose=True)

		print('  == after deleting nodes with nEdges==0')
		nodeListToRemove = bimpy.bVascularTracingAics._getListFromCriterion(
					myStack.slabList,
					'nodes',
					'nEdges', '==', 0,
					verbose=True)

	# remove zero edge nodes
	# not sure why we have these ??
	'''
	if 0:
		print('  2 bimpy.bVascularTracingAics.removeZeroEdgeNodes')
		bimpy.bVascularTracingAics.old_removeZeroEdgeNodes(myStack.slabList)
	'''

	# anlyze all slab diameter in a cpu pool
	if 1:
		runDiameterPool(myStack)

	if 1:
		myStack.slabList._preComputeAllMasks()

	# save, next time we load, we do not need to (make skel, analyze diameter)
	if saveAtEnd:
		myStack.saveAnnotations()

	#print('todo: write second analysis function() to load stack and')
	#print('  plot histograms of edge (length, diam, etc)')
