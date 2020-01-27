# 20200117

import os, sys
from collections import OrderedDict
import statistics # to get median value from a list of numbers
import math

from xml.dom import minidom # to load vesselucida xml file

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
		self.slabIdx = np.empty(0, dtype=np.uint8) # will be nan for slabs

		loadedVesselucida = self.loadVesselucida_xml()


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

	# edits
	def newNode(self, x, y, z):
		"""
		"""
		newNodeIdx = self.numNodes()
		newSlabIdx = self.numSlabs()

		nodeDict = self._defaultNodeDict(x=x, y=y, z=z, nodeIdx=newNodeIdx, slabIdx=newSlabIdx)
		self.nodeDictList.append(nodeDict)

		self._appendSlab(x=x, y=y, z=z, nodeIdx=newNodeIdx)

		print('   bVascularTracing.newNode()', newNodeIdx)
		#self._printGraph()

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
				edge['preNode'] -= 1
			if postNode is not None and (postNode > nodeIdx):
				#self.edgeDictList[edgeIdx]['postNode'] = postNode - 1
				edge['postNode'] -= 1

		# delete from dict
		self.nodeDictList.pop(nodeIdx)

		# delete from slabs
		self._deleteSlab(nodeSlabIdx)

		#print('after) bVascularTracing.deleteNode()', nodeIdx)
		#self._printGraph()

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
		self.slabIdx = np.append(self.slabIdx, newSlabIdx)
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
		self.slabIdx = np.delete(self.slabIdx, slabIdx)

		self.slabIdx[self.slabIdx>slabIdx] -= 1
		# remember, both self.edgeIdx and self.nodeIdx have nan!
		#if edgeIdx is not None:
		if not np.isnan(edgeIdx):
			#self.edgeIdx[self.edgeIdx>edgeIdx] -=1
			'''
			nonNanIndices = ~np.isnan(self.edgeIdx)
			print('nonNanIndices:', type(nonNanIndices))
			decrimentIndices = np.where(self.edgeIdx[nonNanIndices]>edgeIdx)[0]
			print('decrimentIndices:', type(decrimentIndices))
			'''
			#self.edgeIdx[self.edgeIdx>edgeIdx] -= 1
			#self.edgeIdx[decrimentIndices] -= 1

			# was this
			#self.edgeIdx[self.edgeIdx[decrimentIndices]>edgeIdx] -= 1
			#self.edgeIdx[(~np.isnan(self.edgeIdx)) & (self.edgeIdx>edgeIdx)] -= 1

			# x[np.less(x, -1000., where=~np.isnan(x))] = np.nan

			#print('\n\nsrewing everything up\n\n')
			#self.edgeIdx[np.greater(self.edgeIdx, edgeIdx, where=~np.isnan(self.edgeIdx))] -= 1

		#if nodeIdx is not None:
		if not np.isnan(nodeIdx):
			nonNanIndices = ~np.isnan(self.nodeIdx)
			decrimentIndices = np.where(self.nodeIdx[nonNanIndices]>nodeIdx)
			'''
			print('\n', 'slabIdx:', slabIdx, 'nodeIdx:', nodeIdx)
			print('nonNanIndices:', nonNanIndices)
			print('decrimentIndices:', decrimentIndices)
			print('self.nodeIdx[decrimentIndices]:', self.nodeIdx[decrimentIndices])
			'''
			#self.nodeIdx[decrimentIndices] -= 1

			# was this
			#self.nodeIdx[self.nodeIdx[decrimentIndices]>nodeIdx] -= 1

			#self.nodeIdx[(~np.isnan(self.nodeIdx)) & (self.nodeIdx>nodeIdx)] -= 1

	def _getSlabFromNodeIdx(self, nodeIdx):
		#print('debug _getSlabFromNodeIdx() nodeIdx:', nodeIdx)
		if nodeIdx is None:
			return None
		else:
			myTuple = np.where(self.nodeIdx==nodeIdx) # The result is a tuple with first all the row indices, then all the column indices.
			theRet = myTuple[0][0]
			return theRet

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
			'Note': '',
			})
		return edgeDict

	def _printStats(self):
		print('   x:', self.x.shape)
		print('   y:', self.y.shape)
		print('   z:', self.z.shape)
		print('   slabs:', self.numSlabs())
		print('   nodes:', self.numNodes())
		print('   edges:', self.numEdges())

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
		zUmPerSlice = 1 #0.5 #0.6 # Olympus .txt is telling us 0.4 ???

		# z can never be negative
		z = np.absolute(z)

		zOffset = 0

		if self.path.endswith('20191017__0001.tif'):
			#print('!!! scaling tiff file 20191017__0001.tif')
			# assuming xml file has point in um/pixel, this will roughly convert back to unitless voxel
			xUmPerPixel = 0.49718
			yUmPerPixel = 0.49718
			zUmPerPixel = 0.6
			zOffset = 25

		if self.path.endswith('tracing_20191217.tif'):
			xUmPerPixel = 0.3107
			yUmPerPixel = 0.3107
			zUmPerPixel = 0.5

		# flip y
		y = abs(y)
		# offset z
		z += zOffset
		# flip x/y
		if 1:
			tmp = y
			y = x
			x = tmp
		# convert um to pixel using um/pixel = 0.497 and 0.4 um/slice
		x = x / xUmPerPixel
		y = y / yUmPerPixel
		z = z / zUmPerSlice
		diam = diam / xUmPerPixel # assuming diamter is a sphere in x/y (not z?)

		x = round(x,2)
		y = round(y,2)
		z = round(z,2)
		diam = round(diam,2)

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
		mydoc = minidom.parse(xmlFilePath)

		vessels = mydoc.getElementsByTagName('vessel')
		#print('found', len(vessels), 'vessels')

		'''
		self.x = []
		self.y = []
		self.z = []
		self.d = []
		#self.id = []
		self.orig_x = []
		self.orig_y = []
		self.orig_z = []
		'''

		masterNodeIdx = 0
		masterEdgeIdx = 0
		masterSlabIdx = 0
		for i, vessel in enumerate(vessels):
			print('vessel i:', i, 'name:', vessel.attributes['name'].value)

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

						'''
						self.nodex.append(x)
						self.nodey.append(y)
						self.nodez.append(z)
						self.noded.append(diam)
						'''

						self._appendSlab(x, y, z, d=diam, edgeIdx=np.nan, nodeIdx=masterNodeIdx)
						'''
						self.x.append(x)
						self.y.append(y)
						self.z.append(z)
						self.d.append(diam)
						self.nodeIdx.append(masterNodeIdx)
						self.edgeIdx.append(np.nan)
						self.slabIdx.append(masterNodeIdx)
						'''

						# todo: somehow assign edge list
						# important so user can scroll through all nodes and
						# check they have >1 edge !!!
						nodeDict = self._defaultNodeDict(x=x, y=y, z=z, nodeIdx=masterNodeIdx)
						'''
						nodeDict = {
							'idx': masterNodeIdx, # used by stack widget table
							'x': x,
							'y': y,
							'z': z,
							'zSlice': int(z), #todo remember this when I convert to um/pixel !!!
							'edgeList':[],
							'nEdges':0,
						}
						'''
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

						'''
						self.orig_x.append(x)
						self.orig_y.append(y)
						self.orig_z.append(z)
						'''

						x,y,z,diam = self._massage_xyz(x,y,z,diam)

						numSlabs = self.numSlabs()

						self._appendSlab(x, y, z, d=diam, edgeIdx=masterEdgeIdx, nodeIdx=np.nan)
						'''
						self.x.append(x)
						self.y.append(y)
						self.z.append(z)
						self.d.append(diam)
						#self.id.append(masterEdgeIdx) ###
						self.nodeIdx.append(np.nan)
						self.edgeIdx.append(masterEdgeIdx)
						self.slabIdx.append(numSlabs)
						'''

						newZList.append(z)
						'''
						self.d.append(diam)
						self.edgeIdx.append(masterEdgeIdx)
						'''
						thisSlabList.append(masterSlabIdx)
						masterSlabIdx += 1

					# default
					# fill in srcNode/dstNode below
					edgeDict = self._defaultEdgeDict(edgeIdx=masterEdgeIdx, srcNode=None, dstNode=None)
					edgeDict['z'] = int(round(statistics.median(newZList)))
					'''
					edgeDict = {
						'type': 'edge',
						'idx': masterEdgeIdx, # used by stack widget table
						'edgeIdx': masterEdgeIdx,
						'n': len(newZList),
						'Diam': None,
						'Len 3D': None,
						'Len 2D': None,
						'Tort': None,
						'z': int(round(statistics.median(newZList))),
						'preNode': None,
						'postNode': None,
						'Bad': False,
						'slabList': thisSlabList, # list of slab indices on this edge
						'popList': [], # cases where we should be popped in joinEdges
						'editList': [], # cases where we should be edited in joinEdges
						'otherEdgeIdxList': [],
						'editPending': False,
						'popPending': False,
						}
					'''

					self.edgeDictList.append(edgeDict)

					# add nan
					"""
					self.x.append(np.nan)
					self.y.append(np.nan)
					self.z.append(np.nan)
					self.d.append(np.nan)
					self.id.append(np.nan)
					masterSlabIdx += 1
					'''
					self.d.append(np.nan)
					self.edgeIdx.append(np.nan)
					'''
					self.orig_x.append(np.nan)
					self.orig_y.append(np.nan)
					self.orig_z.append(np.nan)
					"""
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
		# convert to numpy array
		# nodes
		'''
		self.nodex = np.array(self.nodex, dtype='float32')
		self.nodey = np.array(self.nodey, dtype='float32')
		self.nodez = np.array(self.nodez, dtype='float32')
		'''

		# edges
		'''
		self.x = np.array(self.x, dtype='float32')
		self.y = np.array(self.y, dtype='float32')
		self.z = np.array(self.z, dtype='float32')
		self.d = np.array(self.d, dtype='float32')
		#self.id = np.array(self.id, dtype='float32')
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

		#self._printGraph()

		#
		self._analyze()

		# this sorta works
		#for i in range(1):
		#	self.joinEdges()

		# this sorta works
		#self.findCloseSlabs()

		# this works
		#self.makeVolumeMask()

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
