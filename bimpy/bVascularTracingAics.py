"""
20200819
bVascularTracingAics
"""
import time, json
import operator
from collections import OrderedDict

import numpy as np

#from qtpy import QtGui, QtCore, QtWidgets

import bimpy

import multiprocessing as mp

stackDatabase = OrderedDict()

tmpFile = '20200717__A01_G001_0014'
stackDatabase[tmpFile] = OrderedDict()
stackDatabase[tmpFile]['uFirstSlice'] = 44 # 1 + uFirstSlice * 3
stackDatabase[tmpFile]['uLastSlice'] = 64 # 1 + uLastSlice * 3

#####################################################################
def aicsTest():
	print('bVascularTracingAics.py is working !!!')

#####################################################################
def sharedEdges(vascTracing, nodeIdx1, nodeIdx2):
	"""
	return list of shared edges between two nodes

	# see: https://www.techbeamers.com/program-python-list-contains-elements/
	"""
	node1 = vascTracing.getNode(nodeIdx1)
	node2 = vascTracing.getNode(nodeIdx2)

	edgeList1 = node1['edgeList']
	edgeList2 = node2['edgeList']

	# as a boolean
	# nodeShareAnEdge =  any(item in edgeList1 for item in edgeList2)
	tmpShareEdgeList = []
	for item in edgeList2:
		if item in edgeList1:
			tmpShareEdgeList.append(item)
	return tmpShareEdgeList

def joinNodes(vascTracing, nodeIdx1, nodeIdx2, verbose=True):
	"""
	- make a new node with union of nod1/node2 edge list (no repeats)
	- for each edge in node1/node2, figure out if the node is either (pre, post) and update edges
	"""

	def getPrePost(nodeIdx, edgeIdx):
		""" return ('pre', 'post') """
		edgeDict = vascTracing.getEdge(edgeIdx)
		prePostKey = None
		if edgeDict['preNode'] == nodeIdx:
			prePostKey = 'preNode'
		elif edgeDict['postNode'] == nodeIdx:
			prePostKey = 'postNode'
		return prePostKey

	print('=== bVascularTracingAics.joinNodes() nodeIdx1:', nodeIdx1, 'nodeIdx2:', nodeIdx2)

	node1 = vascTracing.getNode(nodeIdx1)
	edgeList1 = node1['edgeList']
	prePostKeyList1= []
	for tmpEdgeIdx in edgeList1:
		tmpPrePostKey = getPrePost(nodeIdx1, tmpEdgeIdx)
		prePostKeyList1.append(tmpPrePostKey)

	node2 = vascTracing.getNode(nodeIdx2)
	edgeList2 = node2['edgeList']
	prePostKeyList2= []
	for tmpEdgeIdx in edgeList2:
		tmpPrePostKey = getPrePost(nodeIdx2, tmpEdgeIdx)
		prePostKeyList2.append(tmpPrePostKey)

	# if node1/node2 share any edges then bail
	tmpShareEdgeList = sharedEdges(vascTracing, nodeIdx1, nodeIdx2)
	if len(tmpShareEdgeList) > 0:
		print(f'    warning: nodes {nodeIdx1} and {nodeIdx2} share edges {tmpShareEdgeList}, edgeList1: {edgeList1}, edgeList2: {edgeList2}')
		return None

	print('    edgeList1:', edgeList1)
	print('    prePostKeyList1:', prePostKeyList1)

	print('    edgeList2:', edgeList2)
	print('    prePostKeyList2:', prePostKeyList2)


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

	return newEdgeIdx, newSrcNodeIdx, newDstNodeIdx
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
	commonNodeIdx = None
	if preNodeIdx1 == preNodeIdx2:
		flipEdge = 1
		joinOrder = 'forward'
		connectedBy += ['pre', 'pre']
		commonNodeIdx = preNodeIdx1 # could use preNodeIdx2
	elif preNodeIdx1 == postNodeIdx2:
		# do nothing and join 2--1
		flipEdge = None
		joinOrder = 'reverse'
		connectedBy += ['pre', 'post']
		commonNodeIdx = preNodeIdx1 # could use postNodeIdx2
	elif postNodeIdx1 == preNodeIdx2:
		flipEdge = None
		joinOrder = 'forward'
		connectedBy += ['post', 'pre']
		commonNodeIdx = postNodeIdx1 # could use preNodeIdx2
	elif postNodeIdx1 == postNodeIdx2:
		flipEdge = 2
		joinOrder = 'forward'
		connectedBy += ['post', 'post']
		commonNodeIdx = postNodeIdx1 # could use postNodeIdx2
	else:
		print(f'  ERROR: bVascularTracingAics.joinEdges() edges {edgeIdx1} and {edgeIdx2} not connected?')
		return None, None, None

	if len(connectedBy) == 2:
		# ok, one connection
		pass
	else:
		print(f'  ERROR: bVascularTracingAics.joinEdges() found too many connections between edges {edgeIdx1} and {edgeIdx2}')
		return None, None, None

	if verbose: print('  flipEdge:', flipEdge, 'joinOrder:', joinOrder, 'connectedBy:', connectedBy)

	# each variable (x,y,z,d,d2) on lhs is a list of slabs (in order) along the new edge
	newSrcNodeIdx, newDstNodeIdx, x, y, z, d, d2 = makeNewEdgeSlabs(edgeIdx1, edgeIdx2, flipEdge, joinOrder)
	numNewSlabs = len(x)

	#
	# edit tracing
	#

	#
	# b) remove edgeIdx1 and edgeIdx2
	# todo: we need to edgeIdx2 -= 1, basically
	vascTracing.deleteEdge(edgeIdx1)

	# after delete, all edge index are decrimented
	if edgeIdx2>edgeIdx1:
		edgeIdx2 -=1
	vascTracing.deleteEdge(edgeIdx2)

	#
	# c) add new edge
	newEdgeIdx = vascTracing.newEdge(newSrcNodeIdx, newDstNodeIdx)

	#newEdge = vascTracing.getEdge(newEdgeIdx)

	#
	# add slabs
	for slabIdx in range(numNewSlabs):
		newSlabIdx = vascTracing.newSlab(newEdgeIdx, x[slabIdx], y[slabIdx], z[slabIdx], d=d[slabIdx], d2=d2[slabIdx])

	#newEdge = vascTracing.getEdge(newEdgeIdx)

	'''
	if verbose: print('  newEdgeIdx:', newEdgeIdx)
	if verbose: print('  newSrcNodeIdx:', newSrcNodeIdx)
	if verbose: print('  newDstNodeIdx:', newDstNodeIdx)
	'''

	# todo: if node connecting 2x edges has no more edges then remove
	commonNodeNumEdges = vascTracing.nodeDictList[commonNodeIdx]['nEdges']
	if commonNodeNumEdges== 0:
		print('  need to remove commonNodeIdx:', commonNodeIdx, 'commonNodeNumEdges:', commonNodeNumEdges)
	else:
		print('  keep commonNodeIdx:', commonNodeIdx, 'commonNodeNumEdges:', commonNodeNumEdges)

	# remember: need to analyze new edge

	return newEdgeIdx, newSrcNodeIdx, newDstNodeIdx

#####################################################################
def old_removeZeroEdgeNodes(vascTracing):
	"""
	THIS DOES NOTHING????
	the error might be in the list display of nodes ???

	20200928, not sure why we are ending up with zero edge nodes???
	For now, just remove them
	"""
	return True

	deleteNodeList = []
	for nodeIdx, node in enumerate(vascTracing.nodeIter()):
		nEdges = node['nEdges']
		#print('removeZeroEdgeNodes() nodeIdx', nodeIdx, 'nEdges:', nEdges)
		if nEdges == 0:
			deleteNodeList.append(nodeIdx)

	nNodesToRemove= len(deleteNodeList)
	print(f'   removing {nNodesToRemove} zero edge nodes')
	print(f'   before remove we have {vascTracing.numNodes()} nodes ...')
	for idx in range(nNodesToRemove):
		nodeIdx = deleteNodeList[idx]
		#print(f'  removeShortEdges() deleting edgeIdx {edgeIdx}, total edges is {vascTracing.numEdges()}')
		try:
			vascTracing.nodeDictList[edgeIdx]
		except (IndexError) as e:
			print(f'    removeZeroEdgeNodes() nodeIdx does not exist {nodeIdx}, num nodes is {vascTracing.numNodes()}')
		else:
			# do te delete
			vascTracing.deleteNode(nodeIdx)
		deleteNodeList = [x-1 if x>nodeIdx else x for x in deleteNodeList]
	print(f'   after remove we have {vascTracing.numNodes()} nodes')

#####################################################################
'''
def deleteEdgeList(vascTracing, deleteEdgeList):
	"""
	delete a list of edges
	"""
	nEdgesToRemove = len(deleteEdgeList)
	print(f'  bVascularTracingAics.deleteEdgeList() removing {nEdgesToRemove} edges')
	print(f'    before remove we have {vascTracing.numEdges()} edges ...')
	for idx in range(nEdgesToRemove):
		edgeIdx = deleteEdgeList[idx]
		#print(f'  removeShortEdges() deleting edgeIdx {edgeIdx}, total edges is {vascTracing.numEdges()}')
		try:
			tmp = vascTracing.edgeDictList[edgeIdx]
		except (IndexError) as e:
			print(f'    EXCEPTION ERROR: deleteEdgeList() edgeIdx does not exist {edgeIdx}, num edges is {vascTracing.numEdges()}')
		else:
			# do the delete
			vascTracing.deleteEdge(edgeIdx)
		deleteEdgeList = [x-1 if x>edgeIdx else x for x in deleteEdgeList]
	#
	print(f'    after remove we have {vascTracing.numEdges()} edges')
'''

#####################################################################
def _deleteList(vascTracing, type, listToDelete, verbose=False):
	"""
	delete a list of objects, either (nodes, edges)

	parameters:
		type: (nodes, edges)
		listToDelete: list of either (nodes, edges) indices to delete
	"""
	nToRemove = len(listToDelete)

	if type == 'nodes':
		theDictList = vascTracing.nodeDictList
	elif type == 'edges':
		theDictList = vascTracing.edgeDictList

	nInDict = len(theDictList)

	if verbose:
		print(f'  bVascularTracingAics._deleteList() {type} deleting {nToRemove} {type} from {nInDict}')

	for idx in range(nToRemove):
		theIdx = listToDelete[idx]
		try:
			tmp = theDictList[idx]
		except (IndexError) as e:
			print(f'    EXCEPTION ERROR: _deleteList() idx does not exist {idx}, num is {nInDict}')
		else:
			# do the delete
			if type == 'edges':
				vascTracing.deleteEdge(theIdx)
			elif type == 'nodes':
				vascTracing.deleteNode(theIdx)

		# rebuild the list, decrimenting remaing that are > the one just deleted
		listToDelete = [x-1 if x>theIdx else x for x in listToDelete]
	#
	if verbose:
		print(f'    bVascularTracingAics._deleteList() {type} after delete we have {len(theDictList)} {type}')

#####################################################################
def old_getEdgeListFromCriterion(vascTracing,
							key, operatorStr, value,
							fromThisEdgeList=None,
							verbose=False):
	"""
	Return a list of edges indices matching a criterion
		like, edgeDict[key] < 5
	Parameters:
		key: key into vascTracing.edgeDictList[key]
		value: value to compare
		operatorStr: ('>', '<', '>=', '<=', '==')
	"""
	type = 'edges'
	edgeList = _getListFromCriterion(vascTracing, type,
						key, operatorStr, value,
						fromThisList=fromThisEdgeList,
						verbose=verbose)
	return edgeList

#####################################################################
def old_getNodeListFromCriterion(vascTracing,
							key, operatorStr, value,
							fromThisEdgeList=None,
							verbose=False):
	"""
	Return a list of edges indices matching a criterion
		like, edgeDict[key] < 5
	Parameters:
		key: key into vascTracing.edgeDictList[key]
		value: value to compare
		operatorStr: ('>', '<', '>=', '<=', '==')
	"""
	type = 'nodes'
	nodeList = _getListFromCriterion(vascTracing, type,
						key, operatorStr, value,
						fromThisList=fromThisEdgeList,
						verbose=verbose)
	return nodeList

#####################################################################
def _getListFromCriterion(vascTracing,
							type,
							key, operatorStr, value,
							fromThisList=None,
							verbose=False):
	"""
	Return a list of either (nodes, edges) that match a criterion

	Parameters:
		type: ('nodes', 'edges')
	"""

	ops = {'>': operator.gt,
		'<': operator.lt,
		'>=': operator.ge,
		'<=': operator.le,
		'==': operator.eq}

	if type == 'nodes':
		thisDictList = vascTracing.nodeDictList
	elif type == 'edges':
		thisDictList = vascTracing.edgeDictList

	if fromThisList is None:
		# do all
		fromThisList = range(len(thisDictList))

	returnList = []
	for idx, dictIdx in enumerate(fromThisList):
		oneDict = thisDictList[dictIdx]
		oneValue = oneDict[key]
		if ops[operatorStr](oneValue, value):
			returnList.append(dictIdx)

	if verbose:
		print(f'  bVascularTracingAics._getListFromCriterion() found {len(returnList)} {type} from {len(thisDictList)} with {key} {operatorStr} {value}')

	return returnList

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
#class myWorkThread(QtCore.QRunnable):
class old_myWorkThread:
	"""
	General purpose thread to run python multiprocessing pool.
	This is required for mp to work within the main PyQt5 thread

	type: pass a unique string and we will call different worker function
	"""

	#workerThreadFinishedSignal = QtCore.Signal(object)

	def __init__(self, slabList, type, paramDict=None):
		"""
		slabList: usually bStackWindget.mySimpleStack.slabList
		type: string description
		paramDict: 'radius;, 'lineWidth', 'medianFilter
		'"""

		#super(myWorkThread, self).__init__()

		self.slabList = slabList # self.mySimpleStack.slabList
		self.type = type

		if paramDict is None:
			paramDict = {
				'radius': 12,
				'lineWidth': 5,
				'medianFilter': 5,
			}
		self.paramDict = paramDict

		print('bVascularTracingAics.myWorkThread() init')
		print('  self.type:', type)
		print('  self.paramDict:', self.paramDict)

		self.run()

	def run(self):
		print('myWorkThread.run() type:', self.type, 'self.paramDict:', self.paramDict)

		startTime = time.time()

		#def applyCallback(oneEdgeIdx, oneSlabIdxList, oneDiamList):
		def applyCallback(result):
			#oneEdgeIdx, oneSlabIdxList, oneDiamList = result.get() # edgeIdx, slabIdxList, thisDiamList
			oneEdgeIdx, oneSlabIdxList, oneDiamList = result #.get()
			if oneEdgeIdx % 500 == 0:
				print('    applyCallback() oneEdgeIdx:', oneEdgeIdx, 'to', oneEdgeIdx+500)
			#print('    applyCallback() oneEdgeIdx:', oneEdgeIdx, 'to', oneEdgeIdx+500)

			#print('    got oneEdgeIdx:', oneEdgeIdx, 'oneSlabIdxList:', oneSlabIdxList, 'oneDiamList:', oneDiamList)

			# put this back in after debug(ing)
			for oneResultIdx, oneSlabIdx in enumerate(oneSlabIdxList):
				self.slabList.d2[oneSlabIdx] = oneDiamList[oneResultIdx]
			if len(oneDiamList) > 0:
				thisDiamMean = np.nanmean(oneDiamList)
			else:
				thisDiamMean = np.nan
			edgeDict = self.slabList.getEdge(oneEdgeIdx)
			edgeDict['Diam2'] = thisDiamMean

		radius = self.paramDict['radius'] #20
		lineWidth = self.paramDict['lineWidth'] #5
		medianFilter = self.paramDict['medianFilter'] #3

		cpuCount = mp.cpu_count()
		cpuCount -= 2
		print('  myWorkThread.run() cpuCount:', cpuCount)
		# The multiprocessing.pool.ThreadPool behaves the same as the multiprocessing.Pool with the only difference that uses threads instead of processes to run the workers logic
		pool = mp.Pool(processes=cpuCount) #, maxtasksperchild=10)
		#pool = mp.pool.ThreadPool(processes=cpuCount)
		results = []

		# this was working but trying to get it to run in parallel
		#lp = bimpy.bLineProfile(self.slabList.parentStack)

		self.oneLineProfile = bimpy.bLineProfile(self.slabList.parentStack)

		nEdges = self.slabList.numEdges()
		#nEdges = 100
		for edgeIdx in range(nEdges):
			if edgeIdx % 500 == 0:
				print('    putting edgeIdx:', edgeIdx, 'to', edgeIdx+500, 'of', nEdges, 'edges')

			#edgeDict = self.slabList.getEdge(edgeIdx)

			# debug
			'''
			args = [edgeIdx]
			oneResult = pool.apply_async(worker_debug, args)
			'''

			#args = [self.slabList, lp, edgeIdx, radius, lineWidth, medianFilter]
			args = [edgeIdx,
				radius,
				lineWidth,
				medianFilter]
			#pool.apply_async(worker_getOneEdgeRadius, args, callback=results.append)
			# real
			oneResult = pool.apply_async(self.worker_getOneEdgeRadius, args, callback=applyCallback)

			# used by pool.get() which I believe is blocking
			#results.append(oneResult)

		pool.close()
		pool.join()

		print(f'myWorkThread() done with {nEdges} edges to pool.apply_async')
		stopTime = time.time()
		elapsedSeconds = round(stopTime-startTime,2)
		print(f'  took {elapsedSeconds} seconds, {elapsedSeconds/60} minutes')
		'''
		numAnalyzed = 0
		nResult = len(results)
		print('  myWorkThread.run() fetching', nResult, 'results')
		for resultIdx, result in enumerate(results):
			if resultIdx % 10 == 0:
				print('    fetching resultIdx:', resultIdx+1, 'of', nResult)

			oneEdgeIdx, oneSlabIdxList, oneDiamList = result.get() # edgeIdx, slabIdxList, thisDiamList

			print('    got oneEdgeIdx:', oneEdgeIdx, 'oneSlabIdxList:', oneSlabIdxList, 'oneDiamList:', oneDiamList)

			# put this back in after debug(ing)
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
		'''
		#
		#print('  myWorkThread.run() done with', nResult, 'results and ', numAnalyzed, 'analyzed')

	#####################################################################
	def worker_getOneEdgeRadius(self, edgeIdx, radius, lineWidth, medianFilter):
		"""
		return list of slabIdx with diam of each (can be nan)

		parameters:
			slabList:
			lp: bimpy.bLineProfile(self.parentStack)
			edgeIDx:
			radius:
			lineWidth:
			medianFilter:
		"""
		edgeDict = self.slabList.getEdge(edgeIdx)

		thisDiamList = []
		slabIdxList = []

		#print('worker_getOneEdgeRadius edgeIdx:', edgeIdx, 'nSlabs:', len(edgeDict['slabList']), 'num edges:', slabList.numEdges())
		for slabIdx in edgeDict['slabList']:

			slabIdxList.append(slabIdx)

			lpDict = self.oneLineProfile.getLine(slabIdx, radius=radius) # default is radius=30

			thisDiam = np.nan
			if lpDict is not None:
				retDict = self.oneLineProfile.getIntensity(lpDict, lineWidth=lineWidth, medianFilter=medianFilter)
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
# trying to understand why this is not in parallel
def old_worker_debug(edgeIdx):
	time.sleep(2)
	#edgeIdx = edgeIdx
	slabIdxList = [-999]
	thisDiamList = [-999]
	return edgeIdx, slabIdxList, thisDiamList

#####################################################################
# multiprocessing does not work inside PyQt5, need to make a thread clas and spawn/run
# bimpy.bVascularTracingAics.analyzeSlabIntensity2(self.mySimpleStack.slabList)
def old_analyzeSlabIntensity2(self, slabIdx=None, edgeIdx=None, allEdges=None):
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
	print('bVascularTracingAics __main__')
