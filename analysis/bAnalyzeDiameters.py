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

	radius = 12
	lineWidth = 5
	medianFilter = 5
	nEdges = gStackObject.slabList.numEdges()
	print('  nEdges:', nEdges)
	for edgeIdx in range(nEdges):
		args = [edgeIdx,
			radius,
			lineWidth,
			medianFilter]
		oneResult = pool.apply_async(my_mpWorker, args, callback=my_mpCallback)

	pool.close()
	pool.join()

	#stopTime = time.time()
	#elapsed = round(stopTime-startTime,2) #seconds
	#elapsedMinutes = round(elapsed/60, 2)
	#print(f'finished {nEdges} edges in {elapsed} seconds, {elapsedMinutes} minutes')
	print(myTimer.elapsed())

	# save gStackObject !!!
	print('saving gStackObject')
	gStackObject.saveAnnotations()

def my_mpCallback(result):
	""" apply_async() callback """
	oneEdgeIdx, oneSlabIdxList, oneDiamList = result #.get()
	#oneEdgeIdx, oneSlabIdxList, oneDiamList = result.get() # edgeIdx, slabIdxList, thisDiamList
	if oneEdgeIdx % 500 == 0:
		print('    my_mpCallback() oneEdgeIdx:', oneEdgeIdx, 'to', oneEdgeIdx+500)

	#print('  start my_mpCallback() oneEdgeIdx:', oneEdgeIdx)

	global gStackObject # we are mofifying this

	for oneResultIdx, oneSlabIdx in enumerate(oneSlabIdxList):
		gStackObject.slabList.d2[oneSlabIdx] = oneDiamList[oneResultIdx]
	if len(oneDiamList) > 0:
		if np.isnan(oneDiamList).all():
			# we have values but they are all nan
			thisDiamMean = np.nan
		else:
			# we have values, some could be nan
			thisDiamMean = np.nanmean(oneDiamList)
	else:
		thisDiamMean = np.nan
	edgeDict = gStackObject.slabList.getEdge(oneEdgeIdx)
	edgeDict['Diam2'] = thisDiamMean

	#print('  done my_mpCallback() oneEdgeIdx:', oneEdgeIdx)

def my_mpWorker(edgeIdx, radius, lineWidth, medianFilter):
	""" do the work """

	#print('my_mpWorker() edgeIdx:', edgeIdx)

	edgeDict = gStackObject.slabList.getEdge(edgeIdx)

	thisDiamList = []
	slabIdxList = []

	for slabIdx in edgeDict['slabList']:

		slabIdxList.append(slabIdx)

		lpDict = gLineProfile.getLine(slabIdx, radius=radius) # default is radius=30

		thisDiam = np.nan # without numpy import this fails but we never see an exception?
		if lpDict is not None:
			retDict = gLineProfile.getIntensity(lpDict, lineWidth=lineWidth, medianFilter=medianFilter)
			if retDict is not None:
				thisDiamList.append(retDict['diam']) # bImPy diameter
				#self.d2[slabIdx] = retDict['diam']
			else:
				thisDiamList.append(np.nan)
				#self.d2[slabIdx] = np.nan
		else:
			thisDiamList.append(np.nan)
			#self.d2[slabIdx] = np.nan

	#print('  done my_mpWorker() edgeIdx:', edgeIdx)
	return edgeIdx, slabIdxList, thisDiamList

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

	# load the stack
	myStack = bimpy.bStack(path=path, loadImages=True, loadTracing=True)

	# load mask and make skel from mask
	if 1:
		myStack.slabList.loadDeepVess(vascChannel=2, maskStartStop=maskStartStop)

	# remove zero edge nodes
	# not sure why we have these ??
	if 0:
		print('  1 bimpy.bVascularTracingAics.removeZeroEdgeNodes')
		bimpy.bVascularTracingAics.removeZeroEdgeNodes(myStack.slabList)

	# remove really short edges
	if 0:
		removeSmallerThan = 5
		onlyRemoveDisconnect = False
		bimpy.bVascularTracingAics.removeShortEdges(myStack.slabList,
					removeSmallerThan=removeSmallerThan,
					onlyRemoveDisconnect=onlyRemoveDisconnect)

	# remove zero edge nodes
	# not sure why we have these ??
	if 0:
		print('  2 bimpy.bVascularTracingAics.removeZeroEdgeNodes')
		bimpy.bVascularTracingAics.removeZeroEdgeNodes(myStack.slabList)

	if 1:
		myStack.slabList._preComputeAllMasks()

	# anlyze all slab diameter in a cpu pool
	if 0:
		runDiameterPool(myStack)

	# save, next time we load, we do not need to (make skel, analyze diameter)
	if 1:
		myStack.saveAnnotations()

	print('todo: write second analysis function() to load stack and')
	print('  plot histograms of edge (length, diam, etc)')
