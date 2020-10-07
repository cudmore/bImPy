import os, sys, time

import multiprocessing as mp

import numpy as np

import b_mpAnalyzeSlabs

import bimpy


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
	channelToAnalyze = 2
	maskStartStop = (9,46)

	# load the stack
	myStack = bimpy.bStack(path=path, loadImages=True, loadTracing=True)

	#
	# some options
	remakeSkelFromMask = False
	saveAtEnd = True

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

	# anlyze all slab diameter in a cpu pool
	if 1:
		b_mpAnalyzeSlabs.runDiameterPool(myStack, channelToAnalyze)

	if 1:
		myStack.slabList._preComputeAllMasks()

	# save, next time we load, we do not need to (make skel, analyze diameter)
	if saveAtEnd:
		myStack.saveAnnotations()

	#print('todo: write second analysis function() to load stack and')
	#print('  plot histograms of edge (length, diam, etc)')
