# 20200117

import os, sys
from collections import OrderedDict
import statistics # to get median value from a list of numbers
import math

from xml.dom import minidom # to load vesselucida xml file
from skimage.external import tifffile as tif

import json

import numpy as np

import h5py

class bVascularTracing:
	def __init__(self, parentStack, path):
		"""
		path: path to file
		"""
		self.parentStack = parentStack
		self.path = path

		self._initTracing()

		'''
		self.nodeDictList = []
		self.edgeDictList = []
		self.editDictList = [] # created in self.joinEdge() for vesselucida

		self.x = np.empty((0,))
		self.y = np.empty((0,))
		self.z = np.empty((0,))
		self.d = np.empty(0)
		self.edgeIdx = np.empty(0, dtype=np.float) # will be nan for nodes
		self.nodeIdx = np.empty(0, dtype=np.float) # will be nan for slabs
		#self.slabIdx = np.empty(0, dtype=np.uint8) # will be nan for slabs

		self._volumeMask = None
		'''

		loaded_h5f = self.load()
		if not loaded_h5f:
			loadedVesselucida = self.loadVesselucida_xml()


	def _initTracing(self):
		self.nodeDictList = []
		self.edgeDictList = []
		self.editDictList = [] # created in self.joinEdge() for vesselucida

		self.x = np.empty((0,))
		self.y = np.empty((0,))
		self.z = np.empty((0,))
		self.d = np.empty(0)
		self.edgeIdx = np.empty(0, dtype=np.float) # will be nan for nodes
		self.nodeIdx = np.empty(0, dtype=np.float) # will be nan for slabs
		#self.slabIdx = np.empty(0, dtype=np.uint8) # will be nan for slabs

		self._volumeMask = None

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

	def numEdits(self):
		return len(self.editDictList)

	def getNode(self, nodeIdx):
		if nodeIdx is None or np.isnan(nodeIdx) or nodeIdx > len(self.nodeDictList)-1:
			print('ERROR: getNode() nodeIdx:', nodeIdx, 'len(self.nodeDictList):', len(self.nodeDictList))
			return None
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

	def getSlabEdgeIdx(self, slabIdx):
		"""
		Can be nan !
		"""
		#print('!!! getSlabEdgeIdx() slabIdx:', slabIdx)
		#print('   self.edgeIdx[slabIdx]:', self.edgeIdx[slabIdx])
		edgeIdx = self.edgeIdx[slabIdx]
		if np.isnan(edgeIdx):
			return None
		else:
			return int(round(self.edgeIdx[slabIdx]))

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
		theseIndices = []
		if preSlab is not None:
			theseIndices.append(preSlab)
		for slab in slabList:
			theseIndices.append(slab)
		if postSlab is not None:
			theseIndices.append(postSlab)
		#print('   theseIndices:', theseIndices)

		return theseIndices

	def getEdgeSlabList2(self, edgeIdx):
		"""
		20200127 error because vesselucida has edges that do not have both pre/post nodes !!!!
		return a list of slabs in an edge
		"""
		myTuple = np.where(self.edgeIdx == edgeIdx)
		myTuple = myTuple[0]
		slabList = myTuple

		theseIndices = []

		for slab in slabList:
			theseIndices.append(slab)

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

		print('   bVascularTracing.newNode() newNodeIdx:', newNodeIdx, 'newSlabIdx:', newSlabIdx)

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
		#self._printGraph()

		return newEdgeIdx

	def updateEdge___(self, edgeIdx):
		"""
		when slabs change (add, subtract, move)
		update z (the median z of all slabs
		"""

		pass
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
		#self._printGraph()

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
				print('ERROR: deleteNode() should not be here ... preNode')
				edge['preNode'] -= 1
			if postNode is not None and (postNode > nodeIdx):
				#self.edgeDictList[edgeIdx]['postNode'] = postNode - 1
				print('ERROR: deleteNode() should not be here ... postNode')
				edge['postNode'] -= 1

		# delete from dict
		self.nodeDictList.pop(nodeIdx)

		# delete from slabs
		self._deleteSlab(nodeSlabIdx)

		#
		# decriment remaining self.nodeIdx
		# x[np.less(x, -1000., where=~np.isnan(x))] = np.nan
		self.nodeIdx[np.greater(self.nodeIdx, nodeIdx, where=~np.isnan(self.nodeIdx))] -= 1

		return True

	def deleteEdge(self, edgeIdx):

		print('bVascularTracing.deleteEdge() edgeIdx:', edgeIdx)

		# the edge we will delete
		edge = self.edgeDictList[edgeIdx]

		# the slabs we will delete
		# using 2() because vessel lucida has edges with missing pre/post nodes
		edgeSlabList = self.getEdgeSlabList2(edgeIdx) #edge['slabList']

		#
		# delete from nodes node['edgeList']
		preNode = edge['preNode']
		postNode = edge['postNode']
		if preNode is not None: # will always be true, edges always have pre/post node
			print('   preNode:', preNode, self.nodeDictList[preNode])
			try:
				edgeListIdx = self.nodeDictList[preNode]['edgeList'].index(edgeIdx)
				self.nodeDictList[preNode]['edgeList'].pop(edgeListIdx)
				print('      deleteEdge() popped preNode:', preNode, 'edgeIdx:', 'edgeListIdx:', edgeListIdx)
			except (ValueError) as e:
				print('   !!! WARNING: exception:', str(e))
		if postNode is not None: # will always be true, edges always have pre/post node
			print('   postNode:', postNode, self.nodeDictList[postNode])
			try:
				edgeListIdx = self.nodeDictList[postNode]['edgeList'].index(edgeIdx)
				self.nodeDictList[postNode]['edgeList'].pop(edgeListIdx)
				print('      deleteEdge() popped postNode:', postNode, 'edgeIdx:', edgeIdx, 'edgeListIdx:', edgeListIdx)
			except (ValueError) as e:
				print('   !!! WARNING: exception:', str(e))

		# debug, edgeIDx should no longer be in node['edgeList']

		# decrement remaining node['edgeList']
		for nodeIdx, node in enumerate(self.nodeDictList):
			# debug
			# delete edge 70, causes interface error and is not caught here???
			try:
				edgeListIdx = node['edgeList'].index(edgeIdx)
				print('!!! !!! ERROR: nodeIdx:', nodeIdx, 'still has edgeIdx:', edgeIdx, 'in ["edgeList"]:', node['edgeList'])
			except (ValueError) as e:
				pass
			#
			for tmpEdgeIdx, nodeEdgeIdx in enumerate(node['edgeList']):
				if nodeEdgeIdx > edgeIdx:
					node['edgeList'][tmpEdgeIdx] -= 1

		#
		# delete edge from dict
		self.edgeDictList.pop(edgeIdx)


		#
		# delete from slabs
		# first/last slabs are nodes, do not delete !!!
		#edgeSlabList = self.getEdgeSlabList(edgeIdx) #edge['slabList']
		if len(edgeSlabList) == 2:
			# it is an edge with no slabs
			pass
		else:
			# don't do this because some vessellucia don't have both pre/post node !!!
			# assuming we used getEdgeSlabList2() above
			#thisSlabList  = edgeSlabList[1:-1] # slabList without first/prenode and last/postnode
			thisSlabList  = edgeSlabList # slabList without first/prenode and last/postnode
			self._deleteSlabList(thisSlabList)

		# debug
		# look for remaining slabs with edge Idx
		for tmpIdx, tmpEdgeIdx in enumerate(self.edgeIdx):
			if tmpEdgeIdx == edgeIdx:
				print('\n   !!! !!! ERROR: self.edgeIdx at slab idx:', tmpIdx, 'STILL has edgeIdx==', edgeIdx, '\n')
		#
		# decriment remaining self.edgeIdx
		# x[np.less(x, -1000., where=~np.isnan(x))] = np.nan
		self.edgeIdx[np.greater(self.edgeIdx, edgeIdx, where=~np.isnan(self.edgeIdx))] -= 1

		#print('after) bVascularTracing.deleteEdge()', edgeIdx)
		#self._printGraph()

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
		#self.slabIdx = np.append(self.slabIdx, newSlabIdx)
		return newSlabIdx

	def _deleteSlabList(self, slabList):
		"""
		special case to delete lots of slabs on deleting edge

		slabList: list of slab to delete
		"""
		print('bVascularTracing._deleteSlabList() slabList:', slabList)

		slabListCopy = np.array(slabList)

		for idx, slab in enumerate(slabList):
			thisSlab = slabListCopy[idx]
			self._deleteSlab(thisSlab)
			# decriment all items of slabList > slab
			slabListCopy = slabListCopy - 1 # this is assuming slabs are monotonically increasing

	def _deleteSlab(self, slabIdx):
		'''
		print('_deleteSlab() slabIdx:', slabIdx, 'shape:', self.x.shape)
		self._printSlab(slabIdx)
		'''

		edgeIdx = self.edgeIdx[slabIdx]
		nodeIdx = self.nodeIdx[slabIdx]

		self.x = np.delete(self.x, slabIdx)
		self.y = np.delete(self.y, slabIdx)
		self.z = np.delete(self.z, slabIdx)
		self.d = np.delete(self.d, slabIdx)
		self.edgeIdx = np.delete(self.edgeIdx, slabIdx)
		self.nodeIdx = np.delete(self.nodeIdx, slabIdx)
		#self.slabIdx = np.delete(self.slabIdx, slabIdx)

		#decriment remaining slabIdx
		#self.slabIdx[self.slabIdx>slabIdx] -= 1

		# remember, both self.edgeIdx and self.nodeIdx have nan!
		#if edgeIdx is not None:

	def _getSlabFromNodeIdx(self, nodeIdx):
		#print('debug _getSlabFromNodeIdx() nodeIdx:', nodeIdx)
		if nodeIdx is None:
			return None
		else:
			try:
				myTuple = np.where(self.nodeIdx==nodeIdx) # The result is a tuple with first all the row indices, then all the column indices.
				# list of rows myTuple[0]
				# first element in list of rows myTuple[0][0]
				# debug
				rowHits = myTuple[0]
				if len(myTuple[0])==0:
					print('ERROR: bVascularTracing._getSlabFromNodeIdx() did not find any nodeIdx:', nodeIdx)
				elif len(myTuple[0]) == 1:
					pass
				else:
					print('ERROR: bVascularTracing._getSlabFromNodeIdx() too many nodeIdx:', nodeIdx, myTuple[0])
				#
				theRet = myTuple[0][0]
				return theRet
			except (IndexError) as e:
				print('_getSlabFromNodeIdx() error finding nodeIdx:', nodeIdx, 'myTuple:', myTuple)
				raise

	def _defaultNodeDict(self, x=None, y=None, z=None, nodeIdx=None, slabIdx=None):
		nodeDict = OrderedDict({
			#'idx': nodeIdx, # index into self.nodeDictList
			#'slabIdx': slabIdx, # index into self.x/self.y etc
			'idx': None,
			'slabIdx': None,
			'x': round(x,2),
			'y': round(y,2),
			'z': round(z,2),
			#'zSlice': None, #todo remember this when I convert to um/pixel !!!
			'edgeList': [],
			'nEdges': 0,
			'Bad': False,
			'Note': '',
		})
		return nodeDict

	def _defaultEdgeDict(self, edgeIdx, srcNode, dstNode):
		edgeDict = OrderedDict({
			'idx': None, # used by stack widget table
			'n': 0, # umber of slabs
			'Diam': None,
			'Len 3D': None,
			'Len 2D': None,
			'Tort': None,
			'z': None, # median from z of slab list
			'preNode': srcNode,
			'postNode': dstNode,
			'Bad': False,
			'slabList': [], # list of slab indices on this edge
			'color': None,
			'Note': '',
			})
		return edgeDict

	def _printStats(self):
		print('file:', self.parentStack)
		print('   x:', self.x.shape)
		print('   y:', self.y.shape)
		print('   z:', self.z.shape)
		print('   slabs:', self.numSlabs())
		print('   nodes:', self.numNodes())
		print('   edges:', self.numEdges())
		print('   edits:', self.numEdits())

	def _printGraph(self):
		self._printNodes()
		self._printEdges()
		self._printTracing()

	def _printTracing(self):
		print('   tracing:')
		print('    x,    y,    z,    d,  nodeIdx,  edgeIdx shape:', self.x.shape, type(self.x))
		for idx, x in enumerate(self.x):
			self._printSlab(idx)

	def _printSlab(self, idx):
		print('   x:', self.x[idx], 'y:', self.y[idx], 'z:', self.z[idx], 'd:', self.d[idx], 'nodeIdx:', self.nodeIdx[idx], 'edgeIdx:', self.edgeIdx[idx])

	def _printNodes(self):
		print('   nodeDictList:')
		for node in self.nodeDictList:
			print('      ', node)

	def _printEdges(self):
		print('   edgeDictList:')
		for edgeIdx, edge in enumerate(self.edgeDictList):
			edge = self.getEdge(edgeIdx)
			print('      ', edge, 'slabList:', self.getEdgeSlabList(edgeIdx))

	def _analyze(self):
		"""
		Fill in derived values in self.edgeDictList
		"""

		'''
		todo: bSlabList.analyze() needs to step through each edge, not slabs !!!
		'''

		for edgeIdx, edge in enumerate(self.edgeDictList):
			edge = self.getEdge(edgeIdx) # todo: fix this, redundant self.getEdge() does calculations !
			len2d = 0
			len3d = 0
			#len3d_nathan = 0

			slabList = edge['slabList']
			for j, slabIdx in enumerate(slabList):

				x1, y1, z1 = self.getSlab_xyz(slabIdx)
				'''
				x1 = self.x[slabIdx]
				y1 = self.y[slabIdx]
				z1 = self.z[slabIdx]
				'''

				#print('pointIdx:', pointIdx)
				'''
				orig_x = self.orig_x[slabIdx]
				orig_y = self.orig_y[slabIdx]
				orig_z = self.orig_z[slabIdx]
				'''

				if j>0:
					len3d = len3d + self.euclideanDistance(prev_x1, prev_y1, prev_z1, x1, y1, z1)
					len2d = len2d + self.euclideanDistance(prev_x1, prev_y1, None, x1, y1, None)
					#len3d_nathan = len3d_nathan + self.euclideanDistance(prev_orig_x1, prev_orig_y1, prev_orig_z1, orig_x, orig_y, orig_z)

				# increment
				prev_x1 = x1
				prev_y1 = y1
				prev_z1 = z1

				'''
				prev_orig_x1 = orig_x
				prev_orig_y1 = orig_y
				prev_orig_z1 = orig_z
				'''

			edge['Len 2D'] = round(len2d,2)
			edge['Len 3D'] = round(len3d,2)
			#edge['Len 3D Nathan'] = round(len3d_nathan,2)

			# diameter, pyqt does not like to display np.float, cast to float()
			meanDiameter = round(float(np.nanmean(self.d[edge['slabList']])),2)
			edge['Diam'] = meanDiameter

	def euclideanDistance2(self, src, dst):
		# src and dst are 3 element tuples (x,y,z)
		return self.euclideanDistance(src[0], src[1], src[2], dst[0], dst[1], dst[2])

	def euclideanDistance(self, x1, y1, z1, x2, y2, z2):
		if z1 is None and z2 is None:
			return math.sqrt((x2-x1)**2 + (y2-y1)**2)
		else:
			return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)

	def _massage_xyz(self, x, y, z, diam):
		"""
		used by vesselucida
		"""
		# todo: read this from header and triple check if valid, if not valid then us 1/1/1
		xUmPerPixel = 1 # 0.31074033574250315 #0.49718
		yUmPerPixel = 1 # 0.31074033574250315 #0.49718
		zUmPerPixel = 1 #0.5 #0.6 # Olympus .txt is telling us 0.4 ???

		# z can never be negative
		#don't use this because np.abs return np.float64 which is not compatible with pyqt (tables in particular)
		#z = np.absolute(z)
		z = abs(z)

		zOffset = 0

		if self.path.endswith('20200127__A01_G001_0011_cropped.tif') or self.path.endswith('20200127__A01_G001_0011_cropped_slidingz.tif'):
			xUmPerPixel = 0.3977476 #0.49718 #0.4971845
			yUmPerPixel = 0.3977476 #0.49718
			zUmPerPixel = 0.5

		elif self.path.endswith('20191017__0001-new_z.tif'):
			xUmPerPixel = 0.4971845
			yUmPerPixel = 0.4971845
			zUmPerPixel = 0.4

		elif self.path.endswith('20191017__0001.tif') or self.path.endswith('20191017__0001_8b_z.tif'):
			#print('!!! scaling tiff file 20191017__0001.tif')
			# assuming xml file has point in um/pixel, this will roughly convert back to unitless voxel
			xUmPerPixel = 0.4971847 #elif
			yUmPerPixel = 0.4971845 #0.0138889 #0.49718
			zUmPerPixel = 0.4 #0.4 # 0.6

		elif self.path.endswith('20200127__A01_G001_0011_croped.tif'):
			#print('!!! scaling tiff file 20200127__A01_G001_0011_croped.tif')
			# assuming xml file has point in um/pixel, this will roughly convert back to unitless voxel
			xUmPerPixel = 0.3977476
			yUmPerPixel = 0.3977476
			zUmPerPixel = 0.51

		elif self.path.endswith('tracing_20191217.tif'):
			xUmPerPixel = 0.3107
			yUmPerPixel = 0.3107
			zUmPerPixel = 0.5

		elif self.path.endswith('cylinder-scaled.tif'):
			xUmPerPixel = 0.15
			yUmPerPixel = 0.15
			zUmPerPixel = 0.4

		elif self.path.endswith('PV_Crop_Reslice.tif'):
			xUmPerPixel = 0.15
			yUmPerPixel = 0.15
			zUmPerPixel = 0.5

		y = abs(y)
		z += zOffset
		#z += 1 # does vesselucida indices start at 0 or 1???

		# flip x/y
		if 1:
			tmp = y
			y = x
			x = tmp
		# convert um to pixel using um/pixel = 0.497 and 0.4 um/slice
		x = x / xUmPerPixel
		y = y / yUmPerPixel
		z = z / zUmPerPixel
		diam = diam / xUmPerPixel # assuming diamter is a sphere in x/y (not z?)

		x = round(x,3)
		y = round(y,3)
		z = round(z,3)
		diam = round(diam,3)

		return x,y,z, diam

	def loadVesselucida_xml(self):
		"""
		Load a vesselucida xml file with nodes, edges, and edge connectivity
		"""

		xmlFilePath, ext = os.path.splitext(self.path)
		xmlFilePath += '.xml'
		if not os.path.isfile(xmlFilePath):
			#print('bSlabList.loadVesselucida_xml() warning, did not find', xmlFilePath)
			return

		print('loadVesselucida_xml() file', xmlFilePath)

		self._initTracing()

		mydoc = minidom.parse(xmlFilePath)

		vessels = mydoc.getElementsByTagName('vessel')
		#print('found', len(vessels), 'vessels')

		masterNodeIdx = 0
		masterEdgeIdx = 0
		masterSlabIdx = 0
		for i, vessel in enumerate(vessels):
			#print('vessel i:', i, 'name:', vessel.attributes['name'].value)

			#
			# nodes
			startNodeIdx = masterNodeIdx
			nodes = vessel.getElementsByTagName('nodes')
			#print('   has', len(nodes), 'nodes')
			for j, node in enumerate(nodes):
				nodeList = vessel.getElementsByTagName('node')
				for k in range(len(nodeList)):
					node_id = nodeList[k].attributes['id'].value
					point = nodeList[k].getElementsByTagName('point') # node is only one 3d point
					for point0 in point:
						x = float(point0.attributes['x'].value)
						y = float(point0.attributes['y'].value)
						z = float(point0.attributes['z'].value)
						diam = float(point0.attributes['d'].value)

						x,y,z,diam = self._massage_xyz(x,y,z,diam)

						numSlabs = self.numSlabs()

						self._appendSlab(x, y, z, d=diam, edgeIdx=np.nan, nodeIdx=masterNodeIdx)

						# todo: somehow assign edge list
						# important so user can scroll through all nodes and
						# check they have >1 edge !!!
						nodeDict = self._defaultNodeDict(x=x, y=y, z=z, nodeIdx=masterNodeIdx)
						self.nodeDictList.append(nodeDict)

					masterNodeIdx += 1

			#
			# edges
			startEdgeIdx = masterEdgeIdx
			edges = vessel.getElementsByTagName('edges')
			#print('   found', len(edges), 'edges')
			for j, edge in enumerate(edges):
				edgeList = vessel.getElementsByTagName('edge')
				#print('	  found', len(edgeList), 'edges')
				# one edge (vessel segment between 2 branch points)
				for k in range(len(edgeList)):
					edge_id = edgeList[k].attributes['id'].value
					points = edgeList[k].getElementsByTagName('point') # edge is a list of 3d points
					# this is my 'edge' list, the tubes between branch points ???
					#print('		 for edge id', edge_id, 'found', len(points), 'points')
					# list of points for one edge
					thisSlabList = []
					newZList = []
					for point in points:
						x = float(point.attributes['x'].value)
						y = float(point.attributes['y'].value)
						z = float(point.attributes['z'].value)
						diam = float(point.attributes['d'].value)

						x,y,z,diam = self._massage_xyz(x,y,z,diam)

						numSlabs = self.numSlabs()

						self._appendSlab(x, y, z, d=diam, edgeIdx=masterEdgeIdx, nodeIdx=np.nan)

						newZList.append(z)
						thisSlabList.append(masterSlabIdx)
						masterSlabIdx += 1

					# default
					# fill in srcNode/dstNode below
					edgeDict = self._defaultEdgeDict(edgeIdx=masterEdgeIdx, srcNode=None, dstNode=None)
					edgeDict['z'] = int(round(statistics.median(newZList)))

					self.edgeDictList.append(edgeDict)

					# important, leave here
					masterEdgeIdx += 1

			#
			# edgelists
			edgeListList = vessel.getElementsByTagName('edgelist')
			#print('   found', len(edgeListList), 'edgelists')
			for j, edgeList in enumerate(edgeListList):
				# src/dst node are 0 based for given vessel
				# todo: save original indices from xml in my data structures !
				id = edgeList.attributes['id'].value # gives us the edge list index in self.x
				srcNode = int(edgeList.attributes['sourcenode'].value)
				dstNode = int(edgeList.attributes['targetnode'].value)
				#print('   srcNode:', srcNode, 'dstNode:', dstNode)

				if srcNode != -1:
					self.edgeDictList[startEdgeIdx+j]['preNode'] = startNodeIdx+srcNode
				if dstNode != -1:
					self.edgeDictList[startEdgeIdx+j]['postNode'] = startNodeIdx+dstNode

				# need to properly calculate z, this is lame
				'''
				if srcNode != -1 and dstNode != -1:
					src_z = self.edgeDictList[startEdgeIdx+j]['z'] = self.nodeDictList[startNodeIdx+srcNode]['z']
					dst_z = self.edgeDictList[startEdgeIdx+j]['z'] = self.nodeDictList[startNodeIdx+srcNode]['z']
					tmp_z = int(round((src_z+dst_z) / 2))
					self.edgeDictList[startEdgeIdx+j]['z'] = tmp_z
				elif srcNode != -1:
					self.edgeDictList[startEdgeIdx+j]['z'] = int(round(self.nodeDictList[startNodeIdx+srcNode]['z']))
				elif dstNode != -1:
					self.edgeDictList[startEdgeIdx+j]['z'] = int(round(self.nodeDictList[startNodeIdx+dstNode]['z']))
				'''

				# using startNodeIdx is wrong !!!
				if srcNode != -1:
					self.nodeDictList[startNodeIdx+srcNode]['edgeList'].append(startEdgeIdx+j)
					#self.nodeDictList[startNodeIdx+srcNode]['nEdges'] = len(self.nodeDictList[startNodeIdx+srcNode]['edgeList'])
				if dstNode != -1:
					self.nodeDictList[startNodeIdx+dstNode]['edgeList'].append(startEdgeIdx+j)
					#self.nodeDictList[startNodeIdx+dstNode]['nEdges'] = len(self.nodeDictList[startNodeIdx+dstNode]['edgeList'])

			# debug
			'''
			for idx, edge in enumerate(self.edgeDictList):
				print('edge:', idx, 'preNode:', edge['preNode'], 'postNode:', edge['postNode'])
				print('   edge["slabList"]:', edge["slabList"])
				if edge['preNode'] is not None:
					print('   node self.nodeDictList[preNode]:', self.nodeDictList[edge['preNode']])
				if edge['postNode'] is not None:
					print('   self.nodeDictList[postNode]:', self.nodeDictList[edge['postNode']])
			'''
		#
		# end vessels
		# for i, vessel in enumerate(vessels):
		#

		'''
		nPoints = len(self.x)
		self.id = np.full(nPoints, 0) #Return a new array of given shape and type, filled with fill_value.
		'''

		#
		# create dead ends
		'''
		self.deadEndx = []
		self.deadEndy = []
		self.deadEndz = []
		for edgeIdx, edgeDict in enumerate(self.edgeDictList):
			edgeDict = self.getEdge(edgeIdx)
			if edgeDict['preNode'] is None:
				firstSlabIdx = edgeDict['slabList'][0]
				tmpx = self.x[firstSlabIdx]
				tmpy = self.y[firstSlabIdx]
				tmpz = self.z[firstSlabIdx]
				self.deadEndx.append(tmpx)
				self.deadEndy.append(tmpy)
				self.deadEndz.append(tmpz)
			if edgeDict['postNode'] is None:
				lastSlabIdx = edgeDict['slabList'][-1]
				tmpx = self.x[lastSlabIdx]
				tmpy = self.y[lastSlabIdx]
				tmpz = self.z[lastSlabIdx]
				self.deadEndx.append(tmpx)
				self.deadEndy.append(tmpy)
				self.deadEndz.append(tmpz)

		# convert list of dead ends to nump array
		self.deadEndx = np.array(self.deadEndx, dtype='float32')
		self.deadEndy = np.array(self.deadEndy, dtype='float32')
		self.deadEndz = np.array(self.deadEndz, dtype='float32')
		'''

		# debug min/max of x/y/z
		if 0:
			print('   x min/max', np.nanmin(self.x), np.nanmax(self.x))
			print('   y min/max', np.nanmin(self.y), np.nanmax(self.y))
			print('   z min/max', np.nanmin(self.z), np.nanmax(self.z))

			print('taking abs value of z')
			self.z = np.absolute(self.z)
			self.deadEndz = np.absolute(self.deadEndz)
			self.nodez = np.absolute(self.nodez)

		print('   loaded', masterNodeIdx, 'nodes,', masterEdgeIdx, 'edges, and approximately', masterSlabIdx, 'points')

		#
		self._analyze()

		# this sorta works
		for i in range(1):
			self.joinEdges()

		# this sorta works
		#self.findCloseSlabs()

		# this works
		#self.makeVolumeMask()

		self.colorize()

	def makeVolumeMask(self):
		# to embed a small volume in a bigger volume, see:
		# https://stackoverflow.com/questions/7115437/how-to-embed-a-small-numpy-array-into-a-predefined-block-of-a-large-numpy-arra
		# for sphere, see:
		# https://stackoverflow.com/questions/46626267/how-to-generate-a-sphere-in-3d-numpy-array/46626448
		def sphere(shape, radius, position):
			# assume shape and position are both a 3-tuple of int or float
			# the units are pixels / voxels (px for short)
			# radius is a int or float in px
			semisizes = (radius,) * 3

			# genereate the grid for the support points
			# centered at the position indicated by position
			grid = [slice(-x0, dim - x0) for x0, dim in zip(position, shape)]
			position = np.ogrid[grid]
			# calculate the distance of all points from `position` center
			# scaled by the radius
			arr = np.zeros(shape, dtype=float)
			for x_i, semisize in zip(position, semisizes):
				arr += (np.abs(x_i / semisize) ** 2)
			# the inner part of the sphere will have distance below 1
			return arr <= 1.0

		def paste_slices(tup):
			pos, w, max_w = tup
			wall_min = max(pos, 0)
			wall_max = min(pos+w, max_w)
			block_min = -min(pos, 0)
			block_max = max_w-max(pos+w, max_w)
			block_max = block_max if block_max != 0 else None
			return slice(wall_min, wall_max), slice(block_min, block_max)

		def paste(wall, block, loc):
			loc_zip = zip(loc, block.shape, wall.shape)
			wall_slices, block_slices = zip(*map(paste_slices, loc_zip))
			# was '=', use '+=' assuming we are using binary
			#print('   wall_slices:', wall_slices)
			#print('   block_slices:', block_slices)

			try:
				wall[wall_slices] += block[block_slices]
			except (ValueError) as e:
				print('paste() error in wall[wall_slices] ... fix this later')

		print('bSlabList.makeVolumeMask() ... please wait')
		parentSlices = self.parentStack.numSlices
		pixelsPerLine = self.parentStack.pixelsPerLine
		linesPerFrame = self.parentStack.linesPerFrame
		finalVolume = np.zeros([parentSlices, pixelsPerLine, linesPerFrame])
		print('   finalVolume.shape:', finalVolume.shape)

		for i in range(len(self.edgeDictList)):
			slabList = self.edgeDictList[i]['slabList']
			# debug
			#print('edge:', i)
			for slab in slabList:
				#print('x:', self.x[slab], 'y:', self.y[slab], 'z:', self.z[slab], 'd:', self.d[slab])
				x = int(round(self.x[slab]))
				y = int(round(self.y[slab]))
				z = int(round(self.z[slab]))
				diam = self.d[slab]
				#diam = int(round(self.d[slab]))
				diamInt = int(round(diam))
				myShape = (diamInt+1,diamInt+1,diamInt+1)
				myRadius = int(round(diam/2)+1)
				myPosition = (myRadius, myRadius, myRadius)

				# debug
				#print('   edge:', i, 'slab:', slab, 'myShape:', myShape, 'myRadius:', myRadius, 'myPosition:', myPosition, 'x:', x, 'y:', y, 'z:', z)

				arr = sphere(myShape, myRadius, myPosition)

				paste(finalVolume, arr, (z,x,y))
				#paste(finalVolume, arr, (z,y,x))

		finalVolume = finalVolume > 0

		finalVolume = finalVolume.astype('int8')

		self._volumeMask = finalVolume
		#
		# save results
		maskTiffPath = self._getSavePath() + '_mask.tif'
		print('   saving:', maskTiffPath)
		print('   finalVolume.shape:', finalVolume.shape, type(finalVolume), finalVolume.dtype)
		tif.imsave(maskTiffPath, finalVolume, bigtiff=True)

	def joinEdges(self, distThreshold=20):
		"""
		Try and join edges that have src/dst near another src dst

		Parameters:
			distThreshold
		Algorithm:
			Four cases
				1) dist_src_src2
				2) dist_src_dst2
				3) dist_dst_src2
				4) dist_dst_dst2
		"""
		def addEdit(type, typeNum, edge1, pnt1, edge2, pnt2):
			idx = len(self.editDictList)
			if edge1 is not None:
				len1 = self.edgeDictList[edge1]['Len 3D']
			else:
				len1 = None
			if edge2 is not None:
				len2 = self.edgeDictList[edge2]['Len 3D']
			else:
				len2 = None

			editDict = OrderedDict({
				'idx': idx,
				'type': type,
				'typeNum': typeNum,
				'edge1': edge1,
				'pnt1': pnt1,
				'len1': len1,
				'edge2': edge2,
				'pnt2': pnt2,
				'len2': len2,
				})
			self.editDictList.append(editDict)

		distThreshold = 5

		# reset edit
		for idx, edge in enumerate(self.edgeDictList):
			edge['popList'] = []
			edge['editList'] = []
			edge['editPending'] = False
			edge['popPending'] = False
			edge['otherEdgeIdxList'] = []

		numEdits1 = 0
		numEdits2 = 0
		numEdits3 = 0
		numEdits4 = 0
		for idx, edge in enumerate(self.edgeDictList):
			preNode = edge['preNode'] # can be None
			postNode = edge['postNode']
			if edge['editPending']:
				continue
			if edge['popPending']:
				continue
			slabList = edge['slabList']
			numSlab = len(slabList)
			#print('joinEdges() idx:', idx, 'numSlab', numSlab)
			if numSlab<2:
				continue

			firstSlab = slabList[0]
			lastSlab = slabList[-1]

			src = (self.x[firstSlab], self.y[firstSlab], self.z[firstSlab])
			dst = (self.x[lastSlab], self.y[lastSlab], self.z[lastSlab])

			editDict = OrderedDict({
				'type': '',
				'typeNum': None,
				'edge1': None,
				'pnt1': None,
				'edge2': None,
				'pnt2': None
				})

			for idx2, edge2 in enumerate(self.edgeDictList):
				preNode2 = edge2['preNode'] # can be None
				postNode2 = edge2['postNode']
				if idx2 == idx:
					continue
				if edge2['editPending']:
					continue
				if edge2['popPending']:
					continue
				slabList2 = edge2['slabList']
				numSlab2 = len(slabList2)
				if numSlab2<2:
					continue
				firstSlab2 = slabList2[0]
				lastSlab2 = slabList2[-1]

				# self.x/y/z have nan between edges
				src2 = (self.x[firstSlab2], self.y[firstSlab2], self.z[firstSlab2])
				dst2 = (self.x[lastSlab2], self.y[lastSlab2], self.z[lastSlab2])

				# make 4x comparisons
				dist_src_src2 = self.euclideanDistance2(src, src2)
				dist_src_dst2 = self.euclideanDistance2(src, dst2)
				dist_dst_src2 = self.euclideanDistance2(dst, src2)
				dist_dst_dst2 = self.euclideanDistance2(dst, dst2)
				# 1)
				if dist_src_src2 < distThreshold:
					# reverse idx, put idx2 after idx, pop idx2
					dist = dist_src_src2
					node1 = preNode
					node2 = preNode2
					if (node1 is not None) and (node1 == node2):
						# already connected
						#print('   1.0) already connected by node')
						continue
					elif node1 is None and node2 is None:
						# potential join
						'''
						print('   1.1) potential join')
						'''
						addEdit('join', 1.1, idx, node1, idx2, node2)
					elif node1 is not None and node2 is not None and (node1 != node2):
						'''
						print('   1.2) both preNode and preNode2 have node but they are different ... nodes should be merged ???')
						print('      self.nodeDictList[node1]:', self.nodeDictList[node1])
						print('      self.nodeDictList[node2]:', self.nodeDictList[node2])
						'''
						addEdit('merge', 1.2, idx, node1, idx2, node2)
					elif node1 is not None and node2 is None:
						'''
						print('   1.3) easy ... connect preNode2 to node at preNode')
						print('      MAKING EDIT ... edge:', idx, 'edge2["preNode"] is now preNode:', preNode)
						'''
						numEdits1 += 1
						edge2['preNode'] = preNode
						preNode2 = preNode
						addEdit('connect1', 1.3, idx, node1, idx2, preNode2)
					elif node1 is None and node2 is not None:
						'''
						print('   1.4) easy ... connect preNode to node at preNode2')
						print('      MAKING EDIT ... edge:', idx, 'edge["preNode"] is now preNode2:', preNode2)
						'''
						numEdits1 += 1
						edge['preNode'] = preNode2
						preNode = preNode2
						addEdit('connect2', 1.4, idx, preNode, idx2, node2)
					'''
					print('      dist_src_src2:', dist, 'idx:', idx, 'node1:', node1, 'idx2:', idx2, 'node2:', node2)
					'''
					'''
					numEdits1 += 1
					edge['editList'].append(1) # reverse
					edge['otherEdgeIdxList'].append(idx2)
					edge['editPending'] = True
					edge2['popList'].append(1)
					edge2['popPending'] = True
					#edge2['editPending'] = True
					#print('   (1) idx2:', idx2, 'numSlab2:', numSlab2, 'dist_src_src2:', dist_src_src2)
					print('   1) dist_src_src2:', dist_src_src2, 'idx:', idx, 'preNode:', preNode, 'idx2:', idx2, 'preNode2:', preNode2)
					print('         firstSlab:', firstSlab, 'src:', src)
					print('         firstSlab2:', firstSlab2, 'src2:', src2)
					print('         self.nodeDictList[preNode]:', self.nodeDictList[preNode])
					print('         self.nodeDictList[preNode2]:', self.nodeDictList[preNode2])
					'''
					#continue
				# 2)
				if dist_src_dst2 < distThreshold:
					# put idx after idx2, pop idx
					dist = dist_src_dst2
					node1 = preNode
					node2 = postNode2
					if (node1 is not None) and (node1 == node2):
						# already connected
						#print('   1.0) already connected by node')
						continue
					elif node1 is None and node2 is None:
						# potential join
						'''
						print('   2.1) potential join')
						'''
						addEdit('join', 2.1, idx, node1, idx2, node2)
					elif node1 is not None and node2 is not None and (node1 != node2):
						'''
						print('   2.2) both preNode and postNode2 have node but they are different?')
						print('      self.nodeDictList[node1]:', self.nodeDictList[node1])
						print('      self.nodeDictList[node2]:', self.nodeDictList[node2])
						'''
						addEdit('merge', 2.2, idx, node1, idx2, node2)
					elif node1 is not None and node2 is None:
						'''
						print('   2.3) xxx easy ... connect postNode2 to node at preNode')
						print('      MAKING EDIT ... edge:', idx, 'edge2["postNode"] is now preNode:', preNode)
						'''
						numEdits2 += 1
						edge2['postNode'] = preNode
						postNode2 = preNode
						addEdit('connect1', 2.3, idx, node1, idx2, postNode2)
					elif node1 is None and node2 is not None:
						'''
						print('   2.4) xxx easy ... connect preNode to node at postNode2')
						print('      MAKING EDIT ... edge:', idx, 'edge2["preNode"] is now preNode:', postNode2)
						'''
						numEdits2 += 1
						edge['preNode'] = postNode2
						preNode = postNode2
						addEdit('connect2', 2.4, idx, preNode, idx2, node2)
					'''
					print('      dist_src_dst2:', dist, 'idx:', idx, 'node1:', node1, 'idx2:', idx2, 'node2:', node2)
					'''

					'''
					if (preNode is not None) and (preNode == postNode2):
						# already connected
						continue
					numEdits2 += 1
					edge['popList'].append(2)
					edge['popPending'] = True
					#edge['editPending'] = True
					edge2['editList'].append(2)
					edge2['otherEdgeIdxList'].append(idx)
					edge2['editPending'] = True
					#print('   (2) idx2:', idx2, 'numSlab2:', numSlab2, 'dist_src_dst2:', dist_src_dst2)
					print('   2) dist_src_dst2:', dist_src_dst2, 'idx:', idx, 'preNode:', preNode, 'idx2:', idx2, 'postNode2:', postNode2)
					#print('         edgeDictList[idx]:', self.edgeDictList[idx])
					#print('         edgeDictList[idx2]:', self.edgeDictList[idx2])
					print('         firstSlab:', firstSlab, 'src:', src)
					print('         lastSlab2:', lastSlab2, 'dst2:', dst2)
					if preNode is None:
						print('         preNode=None')
					else:
						print('         self.nodeDictList[preNode]:', self.nodeDictList[preNode])
					if postNode2 is None:
						print('         postNode2=None')
					else:
						print('         self.nodeDictList[postNode2]:', self.nodeDictList[postNode2])
					'''
					#continue
				# 3)
				if dist_dst_src2 < distThreshold:
					# no change, put idx2 after idx, pop idx2
					dist = dist_dst_src2
					node1 = postNode
					node2 = preNode2
					if (node1 is not None) and (node1 == node2):
						# already connected
						#print('   1.0) already connected by node')
						continue
					elif node1 is None and node2 is None:
						# potential join
						'''
						print('   3.1) potential join')
						'''
						addEdit('join', 3.1, idx, node1, idx2, node2)
					elif node1 is not None and node2 is not None and (node1 != node2):
						'''
						print('   3.2) both postNode and preNode2 have node but they are different?')
						print('      self.nodeDictList[node1]:', self.nodeDictList[node1])
						print('      self.nodeDictList[node2]:', self.nodeDictList[node2])
						'''
						addEdit('merge', 3.2, idx, node1, idx2, node2)
					elif node1 is not None and node2 is None:
						'''
						print('   3.3) xxx easy ... connect postNode2 to node at preNode')
						print('      MAKING EDIT ... ')
						'''
						numEdits3 += 1
						edge2['preNode'] = postNode
						preNode2 = postNode
						addEdit('connect1', 3.3, idx, node1, idx2, preNode2)
					elif node1 is None and node2 is not None:
						'''
						print('   3.4) xxx easy ... connect preNode to node at postNode2')
						print('      MAKING EDIT ... ')
						'''
						numEdits3 += 1
						edge['postNode'] = preNode2
						postNode = preNode2
						addEdit('connect2', 3.4, idx, node1, idx2, postNode)
					'''
					print('      dist_dst_src2:', dist, 'idx:', idx, 'node1:', node1, 'idx2:', idx2, 'node2:', node2)
					'''

					'''
					numEdits3 += 1
					edge['editList'].append(3)
					edge['otherEdgeIdxList'].append(idx2)
					edge['editPending'] = True
					edge2['popList'].append(3)
					edge2['popPending'] = True
					#edge2['editPending'] = True
					#print('   (3) idx2:', idx2, 'numSlab2:', numSlab2, 'dist_dst_src2:', dist_dst_src2)
					if postNode is not None or preNode2 is not None:
						print('   3) idx:', idx, 'postNode:', postNode, 'idx2:', idx2, 'preNode2:', preNode2)
						print('      dist_dst_src2:', dist_dst_src2)
						if postNode == preNode2:
							# already members of the same node
							print('      match')
						# 4 more cases ?
						if postNode is None and preNode2 is not None:
							# never happens
							pass
							#print('      case 3.1) idx1 dst joins src at idx2')
						elif postNode is not None and preNode2 is None:
							# never happen
							pass
							#print('      case 3.2) idx2 src joins dst at idx 1')
						elif postNode is not None and preNode2 is not None:
							print('      case 3.3) match')
							# debug, position of postNode and preNode2
							# this is not correct
							print('         self.nodeDictList[postNode]:', self.nodeDictList[postNode])
							print('         self.nodeDictList[preNode2]:', self.nodeDictList[preNode2])
							#
							# YES, bingo, my slab indices do not match my preNode/postNode
							print('         lastSlab  :', self.x[lastSlab], self.y[lastSlab], self.z[lastSlab])
							print('         firstSlab2:', self.x[firstSlab2], self.y[firstSlab2], self.z[firstSlab2])
					else:
						# never happens
						pass
						#print('   3.0) both assigned')
					'''
					#continue
				# 4)
				if dist_dst_dst2 < distThreshold:
					# reverse idx2, put idx2 after idx, pop idx2
					dist = dist_dst_dst2
					node1 = postNode
					node2 = postNode2
					if (node1 is not None) and (node1 == node2):
						# already connected
						#print('   1.0) already connected by node')
						continue
					elif node1 is None and node2 is None:
						# potential join
						'''
						print('   4.1) potential join')
						'''
						addEdit('join', 4.1, idx, node1, idx2, node2)
					elif node1 is not None and node2 is not None and (node1 != node2):
						'''
						print('   4.2) xxx both postNode and postNode2 have node but they are different?')
						print('      self.nodeDictList[node1]:', self.nodeDictList[node1])
						print('      self.nodeDictList[node2]:', self.nodeDictList[node2])
						'''
						addEdit('merge', 4.2, idx, node1, idx2, node2)
					elif node1 is not None and node2 is None:
						'''
						print('   4.3) xxx easy ... connect postNode2 to node at preNode')
						print('      MAKING EDIT ... ')
						'''
						numEdits4 += 1
						edge2['postNode'] = postNode
						postNode2 = postNode
						addEdit('connect1', 3.3, idx, node1, idx2, postNode2)
					elif node1 is None and node2 is not None:
						'''
						print('   4.4) xxx easy ... connect preNode to node at postNode2')
						print('      MAKING EDIT ... ')
						'''
						numEdits4 += 1
						edge['postNode'] = postNode2
						postNode = postNode2
						addEdit('connect2', 3.4, idx, postNode, idx2, node2)
					'''
					print('      dist_dst_dst2:', dist, 'idx:', idx, 'node1:', node1, 'idx2:', idx2, 'node2:', node2)
					'''

					'''
					if (postNode is not None) and (postNode == postNode2):
						# already connected
						continue
					numEdits4 += 1
					edge['editList'].append(4)
					edge['otherEdgeIdxList'].append(idx2)
					edge['editPending'] = True
					edge2['editList'].append(4) # reverse
					edge2['popList'].append(4)
					edge2['editPending'] = True
					edge2['popPending'] = True
					#print('   (4) idx2:', idx2, 'numSlab2:', numSlab2, 'dist_dst_dst2:', dist_dst_dst2)
					print('   4) dist_dst_dst2:', dist_dst_dst2, 'idx:', idx, 'postNode:', postNode, 'idx2:', idx2, 'postNode2:', postNode2)
					if postNode is None:
						print('         postNode is None')
					else:
						print('         self.nodeDictList[postNode]:', self.nodeDictList[postNode])
					if postNode2 is None:
						print('         postNode2 is None')
					else:
						print('         self.nodeDictList[postNode2]:', self.nodeDictList[postNode2])
					'''

					#continue

		#
		# done
		print('Number of edits:', numEdits1, numEdits2, numEdits3, numEdits4)
		print('   !!! NOT EDITING ANYTHING FOR NOW ... return')
		return

		print('*** EDITS joinEdges')
		print('before joinEdges() numEdges:', len(self.edgeDictList), '1:', numEdits1, '2:', numEdits2, '3:', numEdits3, '4:', numEdits4)
		totalNumEdits = 0
		newEdgeIdx = 0 # we will make a new edgeDictList
		self.edgeDictList2 = []
		for idx, edge in enumerate(self.edgeDictList):
			if edge['popPending']:
				# do nothing, will eventually be removed/merged
				continue
			#print('   idx:', idx, 'editList:', edge['editList'], 'otherEdgeIdxList:', edge['otherEdgeIdxList'])
			totalNumEdits += 1

			currNumEdits = len(edge['editList'])
			newEdgeDict = copy.deepcopy(edge)
			if currNumEdits==0:
				# no edit, just append
				newEdgeDict['edgeIdx'] = newEdgeIdx
				newEdgeDict = self.updateEdge(newEdgeDict)
				self.edgeDictList2.append(newEdgeDict)
				newEdgeIdx += 1
			else:
				firstEdit = edge['editList'][0]
				firstOtherIdx = edge['otherEdgeIdxList'][0]
				if firstEdit == 1:
					# reverse idx, put idx2 after idx, pop idx2
					newEdgeDict['slabList'].reverse() # reverse() is on place?
					newEdgeDict['slabList'] += self.edgeDictList[firstOtherIdx]['slabList']
					newEdgeDict['edgeIdx'] = newEdgeIdx
					newEdgeDict = self.updateEdge(newEdgeDict)
					self.edgeDictList2.append(newEdgeDict)
					newEdgeIdx += 1
				elif firstEdit == 2:
					# put idx after idx2, pop idx
					newEdgeDict2 = copy.deepcopy(self.edgeDictList[firstOtherIdx])
					newEdgeDict2['slabList'] += newEdgeDict['slabList']
					newEdgeDict2['edgeIdx'] = newEdgeIdx
					newEdgeDict2 = self.updateEdge(newEdgeDict2)
					self.edgeDictList2.append(newEdgeDict2)
					newEdgeIdx += 1
				elif firstEdit == 3:
					# no change, put idx2 after idx, pop idx2
					newEdgeDict['slabList'] += self.edgeDictList[firstOtherIdx]['slabList']
					newEdgeDict['edgeIdx'] = newEdgeIdx
					newEdgeDict = self.updateEdge(newEdgeDict)
					self.edgeDictList2.append(newEdgeDict)
					newEdgeIdx += 1
				elif firstEdit == 4:
					# reverse idx2, put idx2 after idx, pop idx2
					otherSlabList = self.edgeDictList[firstOtherIdx]['slabList']
					otherSlabList.reverse()
					newEdgeDict['slabList'] += otherSlabList
					newEdgeDict['edgeIdx'] = newEdgeIdx
					newEdgeDict = self.updateEdge(newEdgeDict)
					self.edgeDictList2.append(newEdgeDict)
					newEdgeIdx += 1

		# done
		self.edgeDictList = copy.deepcopy(self.edgeDictList2)

		##
		##
		# FIX THIS
		##
		##

		#
		# need to update each point with its edge idx
		# todo: get rid of .id point throuout (including bStackWidget)
		for idx, edge in enumerate(self.edgeDictList):
			slabList = edge['slabList']
			self.id[slabList] = idx

		print('after joinEdges() numEdges:', len(self.edgeDictList), 'totalNumEdits:', totalNumEdits, '1:', numEdits1, '2:', numEdits2, '3:', numEdits3, '4:', numEdits4)

	def colorize(self):
		"""
		color each edge with color different from other ajoining edges
		Will not work well for edges that do not have both pre/post node
		"""

		colors = set(['r', 'g', 'b', 'c', 'm'])

		# clear all color
		for idx, edge in enumerate(self.edgeDictList):
			edge['color'] = None

		for edgeIdx, edge in enumerate(self.edgeDictList):
			preNode = edge['preNode']
			postNode = edge['postNode']

			potentialColors = set(colors) # use set() to make a copy

			if preNode is not None:
				preNodeDict = self.getNode(preNode)
				preEdgeList = preNodeDict['edgeList']
				for preEdgeIdx in preEdgeList:
					preEdgeColor = self.edgeDictList[preEdgeIdx]['color'] # can be None
					if preEdgeColor is not None:
						# remove from possible colors
						potentialColors -= set([preEdgeColor])
			if postNode is not None:
				postNodeDict = self.getNode(postNode)
				postEdgeList = postNodeDict['edgeList']
				for postEdgeIdx in postEdgeList:
					postEdgeColor = self.edgeDictList[postEdgeIdx]['color'] # can be None
					if postEdgeColor is not None:
						# remove from possible colors
						potentialColors -= set([postEdgeColor])

			# debug
			#print('edgeIdx:', edgeIdx, 'potentialColors:', potentialColors)
			numPotentialColors = len(potentialColors)
			if numPotentialColors==0:
				print('   error: ran out out colors')
			else:
				edge['color'] = list(potentialColors)[0] # first available color

	def _getSavePath(self):
		"""
		return full path to filename without extension
		"""
		path, filename = os.path.split(self.path)
		savePath = os.path.join(path, os.path.splitext(filename)[0])
		return savePath

	def save(self):
		"""
		save a h5f file
		"""
		print('=== save()')
		h5FilePath = self._getSavePath() + '.h5f'
		print('   h5FilePath:', h5FilePath)

		saveDict = OrderedDict()
		saveDict['nodeDictList'] = self.nodeDictList
		saveDict['edgeDictList'] = self.edgeDictList

		with h5py.File(h5FilePath, "w") as f:
			for idx, node in enumerate(self.nodeDictList):
				node = self.getNode(idx)
				#print('   idx:', idx, 'shape:', shape)
				# each node will have a group
				nodeGroup = f.create_group('node' + str(idx))
				# each node group will have a node dict with all parameters
				nodeDict_json = json.dumps(node)
				nodeGroup.attrs['nodeDict'] = nodeDict_json

			for idx, edge in enumerate(self.edgeDictList):
				edge = self.getEdge(idx)
				#print('idx:', idx, 'edge:', edge)

				# convert numpy int64 to int
				tmpSLabList = [int(tmpSlab) for tmpSlab in edge['slabList']]
				edge['slabList'] = tmpSLabList # careful, we are changing backend data !!!

				# each edge will have a group
				edgeGroup = f.create_group('edge' + str(idx))
				# each edge group will have a  dict with all parameters
				edgeDict_json = json.dumps(edge)
				edgeGroup.attrs['edgeDict'] = edgeDict_json

			# slabs are in a dataset
			slabData = np.column_stack((self.x, self.y, self.z, self.d, self.edgeIdx, self.nodeIdx,))
			#print('slabData:', slabData.shape)
			f.create_dataset('slabs', data=slabData)

		# save dict using json

	def load(self):
		"""
		Load from file
		This works but all entries are out of order. For example (edge,node)
		Need to order them correctly
		"""
		h5FilePath = self._getSavePath() + '.h5f'

		print('=== bVascularTracing.load()', h5FilePath)

		if not os.path.isfile(h5FilePath):
			print('   file not found:', h5FilePath)
			return False

		maxNodeIdx = -1
		maxEdgeIdx = -1

		# needed because (nodes, slabs) come in in the wrong order,
		# we file them away using 'idx' after loaded
		tmpNodeDictList = []
		tmpEdgeDictList = []

		with h5py.File(h5FilePath, "r") as f:
			for name in f:
				#print('   loading name:', name)
				# The order of groups in h5f file is not same as saved?
				# I guess this is ok, it is structured so we need to check what we are loading?
				# both (nodes,edges) are coming in in a string sort ordr, we can't simply append()
				if name.startswith('node'):
					json_str = f[name].attrs['nodeDict']
					json_dict = json.loads(json_str) # convert from string to dict
					#print('json_dict:', json_dict)
					if json_dict['idx'] > maxNodeIdx:
						maxNodeIdx = json_dict['idx']
					tmpNodeDictList.append(json_dict)
				elif name.startswith('edge'):
					#print('loading:', name)
					json_str = f[name].attrs['edgeDict']
					json_dict = json.loads(json_str) # convert from string to dict
					#print('json_dict:', json_dict)
					if json_dict['idx'] > maxEdgeIdx:
						maxEdgeIdx = json_dict['idx']
					tmpEdgeDictList.append(json_dict)
				elif name == 'slabs':
					b = f['slabs'][:]
					#print('b:', type(b), b.shape)
					self.x = b[:,0]
					self.y = b[:,1]
					self.z = b[:,2]
					self.d = b[:,3]
					self.edgeIdx = b[:,4]
					self.nodeIdx = b[:,5]

		#
		# go through what we loaded and sort them into the correct position based on ['idx']
		self.nodeDictList = [None] * (maxNodeIdx+1) # make an empy list with correct length
		for node in tmpNodeDictList:
			self.nodeDictList[node['idx']] = node
		self.edgeDictList = [None] * (maxEdgeIdx+1) # make an empy list with correct length
		for edge in tmpEdgeDictList:
			self.edgeDictList[edge['idx']] = edge

		print('    loaded nodes:', maxNodeIdx, 'edges:', maxEdgeIdx)

		return True

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
