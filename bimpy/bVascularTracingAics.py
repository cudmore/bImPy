"""
20200819
bVascularTracingAics
"""
import json

import numpy as np

from qtpy import QtGui, QtCore, QtWidgets

import bimpy

import multiprocessing as mp

#####################################################################
def aicsTest():
	print('bVascularTracingAics.py is working !!!')
	
#####################################################################
def joinEdges(vascTracing, edgeIdx1, edgeIdx2, verbose=False):
	"""
	join edges that are connected by a node
	
	triggered by bStackView.myEvent 'joinTwoEdges'
	
	4 cases:
		e1(pre) -- e2(pre)
		e1(pre) -- e2(post)
		e1(post) -- e2(pre)
		e1(post) -- e2(pre)
		
	vascTracing: bVascularTracing object
	
	"""
	
	def makeNewEdgeSlabs(edgeIdx1, edgeIdx2, flipEdge, joinOrder):
		"""
		Make the 'guts' of a new edge, mostly appending 2x slab lists in the proper order
		
		flipEdge: (None, 1, 2) to flip None, edge1, or edge2
		joinOrder:
			'forward': edgeIdx1 -- edgeIdx2
			'reverse': edgeIdx2 -- edgeIdx1
		
		uses global vascTracing
		"""
		slabList1 = vascTracing.getEdge(edgeIdx1)['slabList']
		slabList2 = vascTracing.getEdge(edgeIdx2)['slabList']
	
		# new src node is pre node of edge joinOrder[0]
		# new dst node is post node of edge joinOrder[1]

		# defaults (with no flipping)
		if joinOrder == 'forward':
			newSrcNodeIdx = preNodeIdx1
			newDstNodeIdx = postNodeIdx2
		elif joinOrder == 'reverse':
			newSrcNodeIdx = preNodeIdx2
			newDstNodeIdx = postNodeIdx1
		
		if flipEdge is not None:
			if flipEdge==1:
				slabList1 = list(reversed(slabList1))
				if joinOrder == 'forward':
					newSrcNodeIdx = postNodeIdx1
				elif joinOrder == 'reverse':
					newDstNodeIdx = preNodeIdx1
			elif flipEdge==2:
				slabList2 = list(reversed(slabList2))
				if joinOrder == 'forward':
					newDstNodeIdx = preNodeIdx2
				elif joinOrder == 'reverse':
					newSrcNodeIdx = postNodeIdx2

		if joinOrder == 'forward':
			newSlabList = slabList1 + slabList2
		elif joinOrder == 'reverse':
			newSlabList = slabList2 + slabList1

		newSlab_x = vascTracing.x[newSlabList]
		newSlab_y = vascTracing.y[newSlabList]
		newSlab_z = vascTracing.z[newSlabList]
		
		d = vascTracing.d[newSlabList]
		d2 = vascTracing.d2[newSlabList]

		return newSrcNodeIdx, newDstNodeIdx, newSlab_x, newSlab_y, newSlab_z, d, d2
		
	# main
	if verbose: print('\n')
	if verbose: print('=== bVascularTracingAics.joinEdges() edgeIdx1:', edgeIdx1, 'edgeIdx2:', edgeIdx2)
	
	# 1
	edge1 = vascTracing.getEdge(edgeIdx1)	
	preNodeIdx1 = edge1['preNode']
	postNodeIdx1 = edge1['postNode']
	
	# 2
	edge2 = vascTracing.getEdge(edgeIdx2)
	preNodeIdx2 = edge2['preNode']
	postNodeIdx2 = edge2['postNode']
	
	#
	# find common connection, reject if 1/2 connected on both ends
	connectedBy = []
	if preNodeIdx1 == preNodeIdx2:
		flipEdge = 1
		joinOrder = 'forward'
		connectedBy += ['pre', 'pre']
	elif preNodeIdx1 == postNodeIdx2:
		# do nothing and join 2--1
		flipEdge = None
		joinOrder = 'reverse'
		connectedBy += ['pre', 'post']
	elif postNodeIdx1 == preNodeIdx2:
		flipEdge = None
		joinOrder = 'forward'
		connectedBy += ['post', 'pre']
	elif postNodeIdx1 == postNodeIdx2:
		flipEdge = 2
		joinOrder = 'forward'
		connectedBy += ['post', 'post']
	else:
		print(f'  ERROR: joinEdges() edges {edgeIdx1} and {edgeIdx2} not connected?')
		return None, None, None
		
	if len(connectedBy) == 2:
		# ok, one connection
		pass
	else:
		print(f'  ERROR: joinEdges() found too many connections between edges {edgeIdx1} and {edgeIdx2}')
		return None, None, None
		
	if verbose: print('  flipEdge:', flipEdge, 'joinOrder:', joinOrder, 'connectedBy:', connectedBy)
	
	# each variable (x,y,z,d,d2) on lhs is a list of slabs (in order) along the new edge
	newSrcNodeIdx, newDstNodeIdx, x, y, z, d, d2 = makeNewEdgeSlabs(edgeIdx1, edgeIdx2, flipEdge, joinOrder)
	numNewSlabs = len(x)
	
	if verbose: print('  newSrcNodeIdx:', newSrcNodeIdx)
	if verbose: print('  newDstNodeIdx:', newDstNodeIdx)

	#
	# edit tracing
	#
	
	# todo: we need to edgeIdx2 -= 1, basically
	#
	# b) remove edgeIdx1 and edgeIdx2
	vascTracing.deleteEdge(edgeIdx1)

	# after delete, all edge index are decrimented
	if edgeIdx2>edgeIdx1:
		edgeIdx2 -=1
	vascTracing.deleteEdge(edgeIdx2)
	
	#
	# c) add new edge
	newEdgeIdx = vascTracing.newEdge(newSrcNodeIdx, newDstNodeIdx)
	
	newEdge = vascTracing.getEdge(newEdgeIdx)

	#
	# add slabs
	for slabIdx in range(numNewSlabs):
		newSlabIdx = vascTracing.newSlab(newEdgeIdx, x[slabIdx], y[slabIdx], z[slabIdx], d=d[slabIdx], d2=d2[slabIdx])

	newEdge = vascTracing.getEdge(newEdgeIdx)

	# todo
	# analyze edge for new diameter
	
	return newEdgeIdx, newSrcNodeIdx, newDstNodeIdx
	
#####################################################################
def detectEdgesAndNodesToRemove(vascTracing):
	"""
	remove edges that have src/dst nodes that do not connect to other
	e.g. src/dst node has nEdges==1
	"""
	
	print('=== detectEdgesAndNodesToRemove()')
	
	# vascTracing.deleteEdge(self, edgeIdx)
	
	# each edge is
	# OrderedDict([('idx', 0), ('type', ''), ('preNode', 0), ('postNode', 1), ('Diam', None), ('Diam2', None), ('nSlab', 0), ('Len 3D', None), ('Len 2D', None), ('Tort', None), ('isBad', False), ('note', ''), ('z', 43), ('deadEnd', None), ('skelID', None), ('color', 'cyan'), ('slabList', [])])
	
	# each node is
	# OrderedDict([('idx', 0), ('nEdges', 1), ('type', ''), ('isBad', False), ('note', ''), ('x', 0.0), ('y', 625.0), ('z', 43.0), ('skelID', 0), ('slabIdx', None), ('edgeList', [0])])

	#
	# this is similar to bVascularTracing.joinEdges
	# at end of that function, see '*** EDITS joinEdges'
	#
	
	#
	# dangling edge is edge with src/dst node with nEdge==1
	dangEdgelingList = []
	for edgeIdx, edge in enumerate(vascTracing.edgeIter()):
		if vascTracing.isDanglingEdge(edgeIdx):
			dangEdgelingList.append(edgeIdx)
		
	print('  ', len(dangEdgelingList), 'dangling edges', dangEdgelingList)
	
	#print('  ', 'removing dangling ...')
	#for edgeIdx in dangEdgelingList:
	
	#
	# nodes with just two edges should be j
	# 1) merge two edges
	# 2) remove node
	twoEdgeNodeList = []
	for nodeIdx, node in enumerate(vascTracing.nodeIter()):
		#node = vascTracing.getNode(nodeIdx)
		nEdges = node['nEdges']
		if nEdges == 2:
			twoEdgeNodeList.append(nodeIdx)
			
	print('  ', len(twoEdgeNodeList), 'node with 2 edges', twoEdgeNodeList)
	
	#
	# close nodes
	distThresh = 5
	distList = []
	closeNodeList = []
	closeNodeNumEdgesList = []
	for nodeIdx1, node1 in enumerate(vascTracing.nodeIter()):
		#node1 = vascTracing.getNode(nodeIdx1)
		nEdges1 = node1['nEdges']
		src1 = vascTracing.getNode_xyz_scaled(nodeIdx1) # um

		for nodeIdx2, node2 in enumerate(vascTracing.nodeIter()):
			if nodeIdx1 == nodeIdx2:
				continue
			if [nodeIdx2,nodeIdx1] in closeNodeList:
				#print('nodeIdx2:', nodeIdx2, 'nodeIdx1:', nodeIdx1, 'already in list')
				continue
			
			#node2 = vascTracing.getNode(nodeIdx2)
			nEdges2 = node2['nEdges']
			src2 = vascTracing.getNode_xyz_scaled(nodeIdx2)
		
			dist = vascTracing.euclideanDistance2(src1, src2)
			if dist < distThresh:
				distList.append(dist)
				closeNodeList.append([nodeIdx1, nodeIdx2])
				closeNodeNumEdgesList.append([nEdges1, nEdges2])
				
	print('  ', len(closeNodeList), 'close nodes') #, closeNodeList)
	#for idx in range(len(closeNodeList)):
	#	print('dist:', distList[idx], 'closeNodeList:', closeNodeList[idx], 'closeNodeNumEdgesList:', closeNodeNumEdgesList[idx])
		
#####################################################################
# see: https://stackoverflow.com/questions/29310824/how-to-implement-multicore-processing-in-python-3-and-pyqt5
#class myWorkThread(QtCore.QThread):
class myWorkThread(QtCore.QRunnable):
	"""
	General purpose thread to run python multiprocessing pool.
	This is required for mp to work within the main PyQt5 thread
	
	type: pass a unique string and we will call different worker function
	"""
	
	workerThreadFinishedSignal = QtCore.Signal(object)

	def __init__(self, slabList, type, paramDict):
		"""
		slabList: usually bStackWindget.mySimpleStack.slabList
		type: string description
		"""
		super(myWorkThread, self).__init__()
		
		self.slabList = slabList # self.mySimpleStack.slabList
		self.type = type
		self.paramDict = paramDict

	'''
	def __del__(self):
		self.wait()
	'''
	
	'''
	def ____worker_getOneEdgeRadius(self, lp, edgeIdx, radius, lineWidth, medianFilter):
		"""
		return list of slabIdx with diam of each (can be nan)
		"""
		edgeDict = self.slabList.getEdge(edgeIdx)
	
		thisDiamList = []
		slabIdxList = []
	
		#print('worker_getOneEdgeRadius edgeIdx:', edgeIdx, len(edgeDict['slabList']))
		for slabIdx in edgeDict['slabList']:
	
			slabIdxList.append(slabIdxList)
		
			lpDict = lp.getLine(slabIdx, radius=radius) # default is radius=30
		
			thisDiam = np.nan
			if lpDict is not None:
				retDict = lp.getIntensity(lpDict, lineWidth=lineWidth, medianFilter=medianFilter)
				if retDict is not None:
					thisDiamList.append(retDict['diam']) # bImPy diameter
					#self.d2[slabIdx] = retDict['diam']
				else:
					thisDiamList.append(np.nan)
					#self.d2[slabIdx] = np.nan
			else:
				thisDiamList.append(np.nan)
				#self.d2[slabIdx] = np.nan

		#print('  done worker_getOneEdgeRadius edgeIdx:', edgeIdx, len(edgeDict['slabList']))
		return edgeIdx, slabIdxList, thisDiamList
	'''
	
	def run(self):
		print('myWorkThread.run() type:', self.type)
		
		radius = self.paramDict['radius'] #20
		lineWidth = self.paramDict['lineWidth'] #5
		medianFilter = self.paramDict['medianFilter'] #3

		cpuCount = mp.cpu_count()
		cpuCount -= 1
		print('  run() cpuCount:', cpuCount)
		# The multiprocessing.pool.ThreadPool behaves the same as the multiprocessing.Pool with the only difference that uses threads instead of processes to run the workers logic
		pool = mp.Pool(processes=cpuCount)
		#pool = mp.pool.ThreadPool(processes=cpuCount)
		results = []

		lp = bimpy.bLineProfile(self.slabList.parentStack)
		
		nEdges = self.slabList.numEdges()
		for edgeIdx in range(nEdges):
			if edgeIdx % 20 == 0:
				print('    putting edgeIdx:', edgeIdx, 'of', nEdges, 'edges')

			edgeDict = self.slabList.getEdge(edgeIdx)

			args = [self.slabList, lp, edgeIdx, radius, lineWidth, medianFilter]
			#pool.apply_async(worker_getOneEdgeRadius, args, callback=results.append)
			oneResult = pool.apply_async(worker_getOneEdgeRadius, args)
			results.append(oneResult)

		#pool.close()
		#pool.join()
		
		print('xxx done')
		
		numAnalyzed = 0
		nResult = len(results)
		print('  myWorkThread.run() fetching', nResult, 'results')
		for resultIdx, result in enumerate(results):
			if resultIdx % 10 == 0:
				print('    fetching resultIdx:', resultIdx+1, 'of', nResult)

			oneEdgeIdx, oneSlabIdxList, oneDiamList = result.get() # edgeIdx, slabIdxList, thisDiamList
			
			'''
			print('result')
			print('  oneEdgeIdx:', oneEdgeIdx)
			print('  oneSlabIdxList:', oneSlabIdxList)
			print('  oneDiamList:', oneDiamList)
			'''
			
			for oneResultIdx, oneSlabIdx in enumerate(oneSlabIdxList):
				self.slabList.d2[oneSlabIdx] = oneDiamList[oneResultIdx]
			if len(oneDiamList) > 0:
				thisDiamMean = np.nanmean(oneDiamList)
			else:
				thisDiamMean = np.nan
			edgeDict = self.slabList.getEdge(oneEdgeIdx)
			edgeDict['Diam2'] = thisDiamMean
			
			#
			numAnalyzed += len(oneSlabIdxList)
			
			#self.workerThreadFinishedSignal.emit(resultIdx)

		#
		print('  myWorkThread.run() done with', nResult, 'results and ', numAnalyzed, 'analyzed')
		
#####################################################################
def worker_getOneEdgeRadius(slabList, lp, edgeIdx, radius, lineWidth, medianFilter):
	"""
	return list of slabIdx with diam of each (can be nan)
	"""
	edgeDict = slabList.getEdge(edgeIdx)

	thisDiamList = []
	slabIdxList = []

	print('worker_getOneEdgeRadius edgeIdx:', edgeIdx, len(edgeDict['slabList']))
	for slabIdx in edgeDict['slabList']:

		slabIdxList.append(slabIdx)
	
		lpDict = lp.getLine(slabIdx, radius=radius) # default is radius=30
	
		thisDiam = np.nan
		if lpDict is not None:
			retDict = lp.getIntensity(lpDict, lineWidth=lineWidth, medianFilter=medianFilter)
			if retDict is not None:
				thisDiamList.append(retDict['diam']) # bImPy diameter
				#self.d2[slabIdx] = retDict['diam']
			else:
				thisDiamList.append(np.nan)
				#self.d2[slabIdx] = np.nan
		else:
			thisDiamList.append(np.nan)
			#self.d2[slabIdx] = np.nan

	#print('  done worker_getOneEdgeRadius edgeIdx:', edgeIdx, len(edgeDict['slabList']))
	return edgeIdx, slabIdxList, thisDiamList

#####################################################################
# multiprocessing does not work inside PyQt5, need to make a thread clas and spawn/run
# bimpy.bVascularTracingAics.analyzeSlabIntensity2(self.mySimpleStack.slabList)
def analyzeSlabIntensity2(self, slabIdx=None, edgeIdx=None, allEdges=None):
	"""
	self: bVascularTracing object
	
	pulled this to make it muliprocessing !!!!
	
	todo: add login to analyze one slab (slabIdx) or an edge (edgeIdx)
	todo: make edgeIdx a list of edge idx
	"""

	radius = 20
	lineWidth=5
	medianFilter = 3

	cpuCount = mp.cpu_count()
	cpuCount -= 2
	pool = mp.Pool(processes=cpuCount)
	results = []
	
	lp = bimpy.bLineProfile(self.parentStack)

	startTime = bimpy.util.bTimer()
	nEdges = self.numEdges()
	print('analyzeSlabIntensity2() analyzing intensity of all slabs across', nEdges, 'edges ...')
	print("  will set each edge['Diam2'] to PIXELS")

	for edgeIdx in range(nEdges):
		#if edgeIdx % 20 == 0:
		#	print('    edgeIdx:', edgeIdx, 'of', nEdges, 'edges')

		edgeDict = self.getEdge(edgeIdx)

		args = [self, lp, edgeIdx, radius, lineWidth, medianFilter]
		oneResult = pool.apply_async(worker_getOneEdgeRadius, args)
		results.append(oneResult)
		
	print('fetching results')
	numAnalyzed = 0
	nResult = len(results)
	for resultIdx, result in enumerate(results):
		print('resultIdx:', resultIdx)
		if resultIdx % 10 == 0:
			print('    resultIdx:', resultIdx+1, 'of', nResult)

		oneEdgeIdx, oneSlabIdxList, oneDiamList = result.get() # edgeIdx, slabIdxList, thisDiamList
		for oneResultIdx, oneSlabIdx in enumerate(oneSlabIdxList):
			self.d2[oneSlabIdx] = oneDiamList[oneResultIdx]
		if len(oneDiamList) > 0:
			thisDiamMean = np.nanmean(oneDiamList)
		else:
			thisDiamMean = np.nan
		edgeDict = self.getEdge(oneEdgeIdx)
		edgeDict['Diam2'] = thisDiamMean
		numAnalyzed += len(oneSlabIdxList)
		
	print('   number of slabs analyzed:', numAnalyzed, startTime.elapsed())

if __name__ == '__main__':
	pass
