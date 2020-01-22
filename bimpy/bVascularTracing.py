# 20200117

import os, sys
from collections import OrderedDict
import statistics # to get median value from a list of numbers

import numpy as np

class bVascularTracing:
	def __init__(self, path):
		"""
		path: path to file
		"""
		self.path = path

		self.nodeDictList = []
		self.edgeDictList = []
		self.editDictList = [] # backward compatibility with bSlabList ... remove

		self.x = np.empty((0,))
		self.y = np.empty((0,))
		self.z = np.empty((0,))
		self.d = np.empty(0)
		self.edgeIdx = np.empty(0, dtype=np.uint8) # will be nan for nodes
		self.nodeIdx = np.empty(0, dtype=np.uint8) # will be nan for slabs

	# todo: remove
	@property
	def id(self):
		# todo: get rid of this, backward compatibility with bSlabList ... remove
		return self.edgeIdx

	# getters
	def numSlabs(self):
		return len(self.x)

	def numNodes(self):
		return len(self.nodeDictList)

	def numEdges(self):
		return len(self.edgeDictList)

	def getNode(self, nodeIdx):
		theDict = self.nodeDictList[nodeIdx]
		theDict['idx'] = int(nodeIdx)
		theDict['nEdges'] = len(theDict['edgeList'])
		return theDict

	def getNode_zSlice(self, nodeIdx):
		"""
		Return z image slice of a node units are slices
		"""
		return int(round(self.nodeDictList[nodeIdx]['z'],2))

	def getNode_xyz(self, nodeIdx):
		x = self.nodeDictList[nodeIdx]['x']
		y = self.nodeDictList[nodeIdx]['y']
		z = self.nodeDictList[nodeIdx]['z']
		return (x, y, z)

	def getSlab_xyz(self, slabIdx):
		x = self.x[slabIdx]
		y = self.y[slabIdx]
		z = self.z[slabIdx]
		return (x, y, z)

	def getEdge(self, edgeIdx):
		theDict = self.edgeDictList[edgeIdx]
		theDict['idx'] = edgeIdx
		theDict['slabList'] = self.getEdgeSlabList(edgeIdx)
		theDict['nSlab'] = len(theDict['slabList'])
		return theDict

	def getEdgeSlabList(self, edgeIdx):
		"""
		return a list of slabs in an edge
		"""
		preNode = self.edgeDictList[edgeIdx]['preNode']
		postNode = self.edgeDictList[edgeIdx]['postNode']

		preSlab = self._getSlabFromNodeIdx(preNode)
		postSlab = self._getSlabFromNodeIdx(postNode)

		#slabList = self.edgeIdx[self.edgeIdx==edgeIdx]
		myTuple = np.where(self.edgeIdx == edgeIdx)
		myTuple = myTuple[0]
		slabList = myTuple

		#print('b) getEdgeSlabList() edgeIdx:', edgeIdx, 'slabList:', slabList)

		#build the list, [pre ... slabs ... post]
		theseIndices = [preSlab]
		for slab in slabList:
			theseIndices.append(slab)
		theseIndices.append(postSlab)
		#print('   theseIndices:', theseIndices)

		return theseIndices

	# edits
	def newNode(self, x, y, z):
		"""
		"""
		newNodeIdx = self.numNodes()
		newSlabIdx = self.numSlabs()

		nodeDict = self._defaultNodeDict(x=x, y=y, z=z, nodeIdx=newNodeIdx, slabIdx=newSlabIdx)
		self.nodeDictList.append(nodeDict)

		self._appendSlab(x=x, y=y, z=z, nodeIdx=newNodeIdx)

		print('= bVascularTracing.newNode()', newNodeIdx)
		self._printGraph()

		return newNodeIdx

	def newEdge(self, srcNode, dstNode):
		"""
		src/dst node are w.r.t self.nodeDictList
		"""
		newEdgeIdx = self.numEdges()

		edgeDict = self._defaultEdgeDict(edgeIdx=newEdgeIdx, srcNode=srcNode, dstNode=dstNode)

		# find the slabs corresponding to src/dst node
		srcSlab = np.where(self.nodeIdx==srcNode)[0]
		dstSlab = np.where(self.nodeIdx==dstNode)[0]

		srcSlab = srcSlab.ravel()[0]
		dstSlab = dstSlab.ravel()[0]

		# not needed
		#edgeDict['slabList'] = [srcSlab, dstSlab]

		# assign edge z to middle of src z, dst z
		x1,y1,z1 = self.getSlab_xyz(srcSlab)
		x2,y2,z2 = self.getSlab_xyz(srcSlab)
		z = (z1+z2)/2
		z = int(round(z))
		edgeDict['z'] = 0

		# append to edge list
		self.edgeDictList.append(edgeDict)

		# update src/dst node
		self.nodeDictList[srcNode]['edgeList'] += [newEdgeIdx]
		self.nodeDictList[dstNode]['edgeList'] += [newEdgeIdx]

		print('= bVascularTracing.newEdge()', newEdgeIdx, 'srcNode:', srcNode, 'dstNode:', dstNode)
		self._printGraph()

		return newEdgeIdx

	def updateEdge___(self, edgeIdx):
		"""
		when slabs change (add, subtract, move)
		update z (the median z of all slabs
		"""

		'''
		slabList = self.getEdgeSlabList(edgeIdx)
		z = round(statistics.median(newZList))
		'''

	def newSlab(self, edgeIdx, x, y, z, d=np.nan):
		"""
		append a new slab to edgeIDx

		"""
		#todo: check thar edgeIdx exists

		newSlabIdx = self.numSlabs()

		# append to x/y/z list
		self._appendSlab(x=x, y=y, z=z, d=d, edgeIdx=edgeIdx)

		# add slab to dict list, add slab before last slab which is postNode
		# not needed
		#self.edgeDictList[edgeIdx]['slabList'].insert(-1, newSlabIdx)

		print('= bVascularTracing.newSlab()', newSlabIdx)
		self._printGraph()

		return newSlabIdx

	def deleteNode(self, nodeIdx):
		# only delete if there are no edges

		# the node we will delete
		nodeDict = self.nodeDictList[nodeIdx]

		if self._getNumberOfEdgesInNode(nodeIdx)>0:
			print('   warning: can not delete a node connected to edges ...')
			return False

		nodeSlabIdx = self._getSlabFromNodeIdx(nodeIdx)

		# delete from all edges
		# not allowed to delete a node that is connected to an edge
		# do not need to check preNode/postNode
		for edgeIdx, edge in enumerate(self.edgeDictList): # EXPENSIVE
			preNode = edge['preNode']
			postNode = edge['postNode']
			if preNode is not None and (preNode > nodeIdx):
				#self.edgeDictList[edgeIdx]['preNode'] = preNode - 1
				edge['preNode'] -= 1
			if postNode is not None and (postNode > nodeIdx):
				#self.edgeDictList[edgeIdx]['postNode'] = postNode - 1
				edge['postNode'] -= 1

		# delete from dict
		self.nodeDictList.pop(nodeIdx)

		# delete from slabs
		self._deleteSlab(nodeSlabIdx)

		print('after) bVascularTracing.deleteNode()', nodeIdx)
		self._printGraph()

		return True

	def deleteEdge(self, edgeIdx):

		# the edge we will delete
		edge = self.edgeDictList[edgeIdx]
		# the slabs we will delete
		edgeSlabList = self.getEdgeSlabList(edgeIdx) #edge['slabList']

		#
		# delete from nodes
		preNode = edge['preNode']
		postNode = edge['postNode']
		if preNode is not None: # will always be true, edges always have pre/post node
			print('   preNode:', preNode, self.nodeDictList[preNode])
			try:
				edgeListIdx = self.nodeDictList[preNode]['edgeList'].index(edgeIdx)
				self.nodeDictList[preNode]['edgeList'].pop(edgeListIdx)
			except (ValueError) as e:
				print('   WARNING: exception:', str(e))
		if postNode is not None: # will always be true, edges always have pre/post node
			print('   postNode:', postNode, self.nodeDictList[postNode])
			try:
				edgeListIdx = self.nodeDictList[postNode]['edgeList'].index(edgeIdx)
				self.nodeDictList[postNode]['edgeList'].pop(edgeListIdx)
			except (ValueError) as e:
				print('   WARNING: exception:', str(e))

		# decrement remaining node['edgeList']
		for nodeIdx, node in enumerate(self.nodeDictList):
			for tmpEdgeIdx, nodeEdgeIdx in enumerate(node['edgeList']):
				if nodeEdgeIdx > edgeIdx:
					node['edgeList'][tmpEdgeIdx] -= 1

		#
		# delete from dict
		self.edgeDictList.pop(edgeIdx)

		#
		# delete from slabs
		# first/last slabs are nodes, do not delete !!!
		#edgeSlabList = self.getEdgeSlabList(edgeIdx) #edge['slabList']
		if len(edgeSlabList) == 2:
			# it is an edge with no slabs
			pass
		else:
			thisSlabList  = edgeSlabList[1:-1] # slabList without first/prenode and last/postnode
			self._deleteSlabList(thisSlabList)

		print('after) bVascularTracing.deleteEdge()', edgeIdx)
		self._printGraph()

	'''
	def updateNode(self, nodeIdx, x=None, y=None, z=None):
		"""
		update any parameter that is not None
		"""
		slabIdx = self.getSlabFromNodeIdx(nodeIdx) #self.nodeDictList[nodeIdx]['slabIdx']
		self.updateSlab(slabIdx, x=x, y=y, z=z)
	'''

	'''
	def updateSlab(self, slabIdx, x=None, y=None,z=None,d=None):
		if x is not None:
			self.x[slabIdx] = x
		if y is not None:
			self.y[slabIdx] = y
		if z is not None:
			self.z[slabIdx] = z
		if d is not None:
			self.d[slabIdx] = d
	'''

	def _getNumberOfEdgesInNode(self, nodeIdx):
		return len(self.nodeDictList[nodeIdx]['edgeList'])

	def _appendSlab(self, x, y, z, d=np.nan, edgeIdx=np.nan, nodeIdx=np.nan):
		newSlabIdx = self.numSlabs()
		self.x = np.append(self.x, x)
		self.y = np.append(self.y, y)
		self.z = np.append(self.z, z)
		self.d = np.append(self.d, d)
		self.edgeIdx = np.append(self.edgeIdx, edgeIdx)
		self.nodeIdx = np.append(self.nodeIdx, nodeIdx)
		return newSlabIdx

	def _deleteSlabList(self, slabList):
		"""
		special case to delete lots of slabs on deleting edge

		slabList: list of slab to delete
		"""
		print('!!! _deleteSlabList:', slabList)
		# this kinda works
		#self._deleteSlab(slabList)

		slabListCopy = np.array(slabList)

		for idx, slab in enumerate(slabList):
			thisSlab = slabListCopy[idx]
			self._deleteSlab(thisSlab)
			# decriment all items of slabList > slab
			slabListCopy = slabListCopy - 1 # this is assuming slabs are monotonically increasing

	def _deleteSlab(self, slabIdx):
		print('_deleteSlab() slabIdx:', slabIdx, 'shape:', self.x.shape)

		edgeIdx = self.edgeIdx[slabIdx]
		nodeIdx = self.nodeIdx[slabIdx]

		self.x = np.delete(self.x, slabIdx)
		self.y = np.delete(self.y, slabIdx)
		self.z = np.delete(self.z, slabIdx)
		self.d = np.delete(self.d, slabIdx)
		self.edgeIdx = np.delete(self.edgeIdx, slabIdx)
		self.nodeIdx = np.delete(self.nodeIdx, slabIdx)

		# remember, both self.edgeIdx and self.nodeIdx have nan!
		if edgeIdx is not None:
			#self.edgeIdx[self.edgeIdx>edgeIdx] -=1
			self.edgeIdx[(~np.isnan(self.edgeIdx)) & (self.edgeIdx>edgeIdx)] -=1
		if nodeIdx is not None:
			self.nodeIdx[self.nodeIdx>nodeIdx] -=1

	def _getSlabFromNodeIdx(self, nodeIdx):
		myTuple = np.where(self.nodeIdx==nodeIdx) # The result is a tuple with first all the row indices, then all the column indices.
		theRet = myTuple[0][0]
		return theRet

	def _defaultNodeDict(self, x=None, y=None, z=None, nodeIdx=None, slabIdx=None):
		nodeDict = {
			#'idx': nodeIdx, # index into self.nodeDictList
			#'slabIdx': slabIdx, # index into self.x/self.y etc
			#'idx': None,
			#'slabIdx': None,
			'x': round(x,2),
			'y': round(y,2),
			'z': round(z,2),
			#'zSlice': None, #todo remember this when I convert to um/pixel !!!
			'edgeList': [],
			#'nEdges': 0,
			'Bad': False,
			'Note': '',
		}
		return nodeDict

	def _defaultEdgeDict(self, edgeIdx, srcNode, dstNode):
		edgeDict = {
			#'idx': edgeIdx, # used by stack widget table
			'n': 0, # umber of slabs
			'Diam': None,
			'Len 3D': None,
			'Len 2D': None,
			'Tort': None,
			'z': None, # median from z of slab list
			'preNode': srcNode,
			'postNode': dstNode,
			'Bad': False,
			#'slabList': [], # list of slab indices on this edge
			'Note': '',
			}
		return edgeDict

	def _printGraph(self):
		self._printNodes()
		self._printEdges()
		self._printTracing()

	def _printTracing(self):
		print('   tracing:')
		print('    x,    y,    z,    d,  nodeIdx,  edgeIdx shape:', self.x.shape, type(self.x))
		for idx, x in enumerate(self.x):
			print('   ', x, self.y[idx], self.z[idx], self.d[idx], 'nodeIdx:', self.nodeIdx[idx], 'edgeIdx:', self.edgeIdx[idx])

	def _printNodes(self):
		print('   nodeDictList:')
		for node in self.nodeDictList:
			print('      ', node)

	def _printEdges(self):
		print('   edgeDictList:')
		for edgeIdx, edge in enumerate(self.edgeDictList):
			print('      ', edge, 'slabList:', self.getEdgeSlabList(edgeIdx))

	def save(self):
		"""
		save a dist of
		"""
		# nodeDictList
		# edgeDictList
		# maybe x/y/z/d or just extract on load?
		saveDict = OrderedDict()
		saveDict['nodeDictList'] = self.nodeDictList
		saveDict['edgeDictList'] = self.edgeDictList

		savePath = ''

		# save dict using json

	def load(self):
		"""
		Load from file
		"""
		filePath = ''

		# load json into self.nodeDictList and self.edgeDictList


if __name__ == '__main__':
	path = ''
	bvt = bVascularTracing(path)

	bvt.newNode(100, 200, 50)
	bvt.newNode(100, 200, 50)
	bvt.newEdge(0,1)
	edgeIdx = 0
	bvt.newSlab(edgeIdx, 100, 200, 50)
	bvt.deleteNode(1)

	print (bvt.x, bvt.y, bvt.z)
	print(bvt.x.shape, type(bvt.x))

	print(bvt.edgeDictList)
