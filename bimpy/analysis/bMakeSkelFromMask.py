import os, sys, time

import numpy as np

import bimpy


def bMakeSkelFromMask(path, channelToAnalyze, maskStartStop)
		# load the stack
		myStack = bimpy.bStack(path=path, loadImages=True, loadTracing=True)

		#
		# some options
		remakeSkelFromMask = True
		saveAtEnd = True

		# SLOW: load mask and make skel from mask
		if remakeSkelFromMask:
			myStack.slabList.loadDeepVess(vascChannel=channelToAnalyze, maskStartStop=maskStartStop)

		# remove edges based on criterion
		if 1:
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
		# this works, see bAnalyzeDiameters.py
		'''
		if 0:
			b_mpAnalyzeSlabs.runDiameterPool(myStack, channelToAnalyze)
		'''

		if 1:
			myStack.slabList._preComputeAllMasks()

		# save, next time we load, we do not need to (make skel, analyze diameter)
		if saveAtEnd:
			myStack.saveAnnotations()

if __name__ == '__main__':

	##
	##
	## GET OTHER FIRST/LAST from bAnalyzeDiameters.py
	##
	##
	path = '/media/cudmore/data/san-density/SAN3/SAN3_tail/aicsAnalysis/SAN3_tail_ch2.tif'
	channelToAnalyze = 2
	maskStartStop = (17, 41)

	bMakeSkelFromMask(path, channelToAnalyze, maskStartStop)
