import os, math, copy
from collections import OrderedDict
import numpy as np
import pandas as pd
import statistics # to get median value from a list of numbers
from xml.dom import minidom # to load vesselucida xml file

class bSlabList:
	"""
	Full list of all points in a vascular tracing

	This should work for both Vesselucida and output of DeepVess
	"""
	def __init__(self, tifPath):
		"""
		tifPath : full file path to Tiff file
		"""

		self.tifPath = tifPath

		# nodes, used by bStackView
		self.nodex = []
		self.nodey = []
		self.nodez = []
		self.noded = []

		self.nodeDictList = []
		self.edgeDictList = [] # this should be .annotationList
		self.editDictList = []

		# slab/edges
		self.id = None # to count edges
		self.x = []
		self.y = []
		self.z = []

		# for nathan convex hull
		self.orig_x = []
		self.orig_y = []
		self.orig_z = []

		# todo: change this to _slabs.txt
		'''
		slabFilePath, ext = os.path.splitext(tifPath)
		slabFilePath += '_slabs.txt'

		if not os.path.isfile(slabFilePath):
			#print('bSlabList warning, did not find slabFilePath:', slabFilePath)
			#return
			pass
		else:
			df = pd.read_csv(slabFilePath)

			nSlabs = len(df.index)
			#self.id = np.full(nSlabs, np.nan) #df.iloc[:,0].values # each point/slab will have an edge id
			self.id = np.full(nSlabs, 0) #Return a new array of given shape and type, filled with fill_value.

			self.x = df.iloc[:,0].values
			self.y = df.iloc[:,1].values
			self.z = df.iloc[:,2].values

			self.orig_x = self.x
			self.orig_y = self.y
			self.orig_z = self.z

			print('file:', slabFilePath)
			print('   len(self.x)', len(self.x))
			print('   tracing z max:', np.nanmax(self.z))
		'''

		self.loadDeepVess()
		self.loadVesselucida_xml()

		#self.analyze()

	#@property
	def numNodes(self):
		return len(self.nodeDictList)

	#@property
	def numSlabs(self):
		return len(self.x)

	#@property
	def numEdges(self):
		return len(self.edgeDictList)

	def _massage_xyz(self, x, y, z, diam):
		# todo: read this from header and triple check if valid, if not valid then us 1/1/1
		xUmPerPixel = 1 # 0.31074033574250315 #0.49718
		yUmPerPixel = 1 # 0.31074033574250315 #0.49718
		zUmPerSlice = 1 #0.5 #0.6 # Olympus .txt is telling us 0.4 ???

		# z can never be negative
		z = np.absolute(z)

		zOffset = 0

		if self.tifPath.endswith('20191017__0001.tif'):
			#print('!!! scaling tiff file 20191017__0001.tif')
			# assuming xml file has point in um/pixel, this will roughly convert back to unitless voxel
			xUmPerPixel = 0.49718
			yUmPerPixel = 0.49718
			zUmPerPixel = 0.6
			zOffset = 25

		if self.tifPath.endswith('tracing_20191217.tif'):
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

		return x,y,z, diam

	def loadDeepVess(self):
		# todo: change this to _slabs.txt
		slabFilePath, ext = os.path.splitext(self.tifPath)
		slabFilePath += '_slabs.txt'

		if not os.path.isfile(slabFilePath):
			#print('bSlabList warning, did not find DeepVess slabFilePath:', slabFilePath)
			pass
		else:
			df = pd.read_csv(slabFilePath)

			nSlabs = len(df.index)
			#self.id = np.full(nSlabs, np.nan) #df.iloc[:,0].values # each point/slab will have an edge id
			self.id = np.full(nSlabs, 0) #Return a new array of given shape and type, filled with fill_value.

			self.x = df.iloc[:,0].values
			self.y = df.iloc[:,1].values
			self.z = df.iloc[:,2].values

			self.orig_x = self.x
			self.orig_y = self.y
			self.orig_z = self.z

			print('bSlabList.loadDeepVess() slabFilePath:', slabFilePath)
			print('   len(self.x)', len(self.x))
			print('   tracing z max:', np.nanmax(self.z))

			# parse the points/slabs and create a list of self.edgeDictList
			newZList = []
			thisSlabList = []
			for idx, pnt in enumerate(self.x):
				#print('idx:', idx, 'pnt:', pnt, type(pnt))
				#newZList = []
				#thisSlabList = []

				masterEdgeIdx = 0

				if np.isnan(pnt):
					# we just reached the end of an edge/vessel
					#print('   point', idx, 'is nan')

					edgeDict = {
						'type': 'edge',
						'edgeIdx': masterEdgeIdx,
						'n': len(newZList),
						'Len 3D': None,
						'Len 2D': None,
						'Tort': None,
						'z': round(statistics.median(newZList)),
						'preNode': -1,
						'postNode': -1,
						'Bad': False,
						'slabList': thisSlabList, # list of slab indices on this edge
						}

					self.edgeDictList.append(edgeDict)
					masterEdgeIdx += 1
					newZList = []
				else:
					newZList.append(self.z[idx])
					thisSlabList.append(idx)

	def loadVesselucida_xml(self):
		"""
		Load a vesselucida xml file with nodes, edges, and edge connectivity
		"""

		xmlFilePath, ext = os.path.splitext(self.tifPath)
		xmlFilePath += '.xml'
		if not os.path.isfile(xmlFilePath):
			#print('bSlabList.loadVesselucida_xml() warning, did not find', xmlFilePath)
			return False

		print('loadVesselucida_xml() file', xmlFilePath)
		mydoc = minidom.parse(xmlFilePath)

		vessels = mydoc.getElementsByTagName('vessel')
		#print('found', len(vessels), 'vessels')

		self.x = []
		self.y = []
		self.z = []
		self.d = []
		self.id = []
		self.orig_x = []
		self.orig_y = []
		self.orig_z = []

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

						self.nodex.append(x)
						self.nodey.append(y)
						self.nodez.append(z)
						self.noded.append(diam)

						# todo: somehow assign edge list
						# important so user can scroll through all nodes and
						# check they have >1 edge !!!
						nodeDict = {
							'idx': masterNodeIdx, # used by stack widget table
							'x': x,
							'y': y,
							'z': z,
							'zSlice': int(z), #todo remember this when I convert to um/pixel !!!
							'edgeList':[],
							'nEdges':0,
						}
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

						self.orig_x.append(x)
						self.orig_y.append(y)
						self.orig_z.append(z)

						x,y,z,diam = self._massage_xyz(x,y,z,diam)

						self.x.append(x)
						self.y.append(y)
						self.z.append(z)
						self.d.append(diam)
						self.id.append(masterEdgeIdx)

						newZList.append(z)
						'''
						self.d.append(diam)
						self.edgeIdx.append(masterEdgeIdx)
						'''
						thisSlabList.append(masterSlabIdx)
						masterSlabIdx += 1

					# default
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

					self.edgeDictList.append(edgeDict)

					# add nan
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

				# using startNodeIdx is wrong !!!
				if srcNode != -1:
					self.nodeDictList[startNodeIdx+srcNode]['edgeList'].append(startEdgeIdx+j)
					self.nodeDictList[startNodeIdx+srcNode]['nEdges'] = len(self.nodeDictList[startNodeIdx+srcNode]['edgeList'])
				if dstNode != -1:
					self.nodeDictList[startNodeIdx+dstNode]['edgeList'].append(startEdgeIdx+j)
					self.nodeDictList[startNodeIdx+dstNode]['nEdges'] = len(self.nodeDictList[startNodeIdx+dstNode]['edgeList'])

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
		self.nodex = np.array(self.nodex, dtype='float32')
		self.nodey = np.array(self.nodey, dtype='float32')
		self.nodez = np.array(self.nodez, dtype='float32')

		# edges
		self.x = np.array(self.x, dtype='float32')
		self.y = np.array(self.y, dtype='float32')
		self.z = np.array(self.z, dtype='float32')
		self.d = np.array(self.d, dtype='float32')
		self.id = np.array(self.id, dtype='float32')

		#
		# create dead ends
		self.deadEndx = []
		self.deadEndy = []
		self.deadEndz = []
		for edgeDict in self.edgeDictList:
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

		# debug min/max of x/y/z
		if 1:
			print('   x min/max', np.nanmin(self.x), np.nanmax(self.x))
			print('   y min/max', np.nanmin(self.y), np.nanmax(self.y))
			print('   z min/max', np.nanmin(self.z), np.nanmax(self.z))

			print('taking abs value of z')
			self.z = np.absolute(self.z)
			self.deadEndz = np.absolute(self.deadEndz)
			self.nodez = np.absolute(self.nodez)

		print('   loaded', masterNodeIdx, 'nodes,', masterEdgeIdx, 'edges, and approximately', masterSlabIdx, 'points')

		#
		self.__analyze()

		for i in range(1):
			self.joinEdges()
		self.findCloseSlabs()

		# this works
		#self.makeVolumeMask()

		return True
		
	def findCloseSlabs(self):
		for idx, edge in enumerate(self.edgeDictList):
			slabList = edge['slabList']
			for slab in slabList:

				# get xyz

				# super expensive
				for idx2, edge2 in enumerate(self.edgeDictList):
					if idx2 == idx:
						# don't compare to self
						continue
					for slab in slabList:

						# get x2, y2,z2

						#self.euclideanDistance2
						pass

	#202001
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
						print('   1.1) potential join')
						addEdit('join', 1.1, idx, node1, idx2, node2)
					elif node1 is not None and node2 is not None and (node1 != node2):
						print('   1.2) both preNode and preNode2 have node but they are different ... nodes should be merged ???')
						print('      self.nodeDictList[node1]:', self.nodeDictList[node1])
						print('      self.nodeDictList[node2]:', self.nodeDictList[node2])
						addEdit('merge', 1.2, idx, node1, idx2, node2)
					elif node1 is not None and node2 is None:
						print('   1.3) easy ... connect preNode2 to node at preNode')
						print('      MAKING EDIT ... edge:', idx, 'edge2["preNode"] is now preNode:', preNode)
						numEdits1 += 1
						edge2['preNode'] = preNode
						preNode2 = preNode
						addEdit('connect1', 1.3, idx, node1, idx2, preNode2)
					elif node1 is None and node2 is not None:
						print('   1.4) easy ... connect preNode to node at preNode2')
						print('      MAKING EDIT ... edge:', idx, 'edge["preNode"] is now preNode2:', preNode2)
						numEdits1 += 1
						edge['preNode'] = preNode2
						preNode = preNode2
						addEdit('connect2', 1.4, idx, preNode, idx2, node2)
					print('      dist_src_src2:', dist, 'idx:', idx, 'node1:', node1, 'idx2:', idx2, 'node2:', node2)
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
						print('   2.1) potential join')
						addEdit('join', 2.1, idx, node1, idx2, node2)
					elif node1 is not None and node2 is not None and (node1 != node2):
						print('   2.2) both preNode and postNode2 have node but they are different?')
						print('      self.nodeDictList[node1]:', self.nodeDictList[node1])
						print('      self.nodeDictList[node2]:', self.nodeDictList[node2])
						addEdit('merge', 2.2, idx, node1, idx2, node2)
					elif node1 is not None and node2 is None:
						print('   2.3) xxx easy ... connect postNode2 to node at preNode')
						print('      MAKING EDIT ... edge:', idx, 'edge2["postNode"] is now preNode:', preNode)
						numEdits2 += 1
						edge2['postNode'] = preNode
						postNode2 = preNode
						addEdit('connect1', 2.3, idx, node1, idx2, postNode2)
					elif node1 is None and node2 is not None:
						print('   2.4) xxx easy ... connect preNode to node at postNode2')
						print('      MAKING EDIT ... edge:', idx, 'edge2["preNode"] is now preNode:', postNode2)
						numEdits2 += 1
						edge['preNode'] = postNode2
						preNode = postNode2
						addEdit('connect2', 2.4, idx, preNode, idx2, node2)
					print('      dist_src_dst2:', dist, 'idx:', idx, 'node1:', node1, 'idx2:', idx2, 'node2:', node2)

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
						print('   3.1) potential join')
						addEdit('join', 3.1, idx, node1, idx2, node2)
					elif node1 is not None and node2 is not None and (node1 != node2):
						print('   3.2) both postNode and preNode2 have node but they are different?')
						print('      self.nodeDictList[node1]:', self.nodeDictList[node1])
						print('      self.nodeDictList[node2]:', self.nodeDictList[node2])
						addEdit('merge', 3.2, idx, node1, idx2, node2)
					elif node1 is not None and node2 is None:
						print('   3.3) xxx easy ... connect postNode2 to node at preNode')
						print('      MAKING EDIT ... ')
						numEdits3 += 1
						edge2['preNode'] = postNode
						preNode2 = postNode
						addEdit('connect1', 3.3, idx, node1, idx2, preNode2)
					elif node1 is None and node2 is not None:
						print('   3.4) xxx easy ... connect preNode to node at postNode2')
						print('      MAKING EDIT ... ')
						numEdits3 += 1
						edge['postNode'] = preNode2
						postNode = preNode2
						addEdit('connect2', 3.4, idx, node1, idx2, postNode)
					print('      dist_dst_src2:', dist, 'idx:', idx, 'node1:', node1, 'idx2:', idx2, 'node2:', node2)

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
						print('   4.1) potential join')
						addEdit('join', 4.1, idx, node1, idx2, node2)
					elif node1 is not None and node2 is not None and (node1 != node2):
						print('   4.2) xxx both postNode and postNode2 have node but they are different?')
						print('      self.nodeDictList[node1]:', self.nodeDictList[node1])
						print('      self.nodeDictList[node2]:', self.nodeDictList[node2])
						addEdit('merge', 4.2, idx, node1, idx2, node2)
					elif node1 is not None and node2 is None:
						print('   4.3) xxx easy ... connect postNode2 to node at preNode')
						print('      MAKING EDIT ... ')
						numEdits4 += 1
						edge2['postNode'] = postNode
						postNode2 = postNode
						addEdit('connect1', 3.3, idx, node1, idx2, postNode2)
					elif node1 is None and node2 is not None:
						print('   4.4) xxx easy ... connect preNode to node at postNode2')
						print('      MAKING EDIT ... ')
						numEdits4 += 1
						edge['postNode'] = postNode2
						postNode = postNode2
						addEdit('connect2', 3.4, idx, postNode, idx2, node2)
					print('      dist_dst_dst2:', dist, 'idx:', idx, 'node1:', node1, 'idx2:', idx2, 'node2:', node2)

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
		print('NOT EDITING ANYTHING FOR NOW')
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

	def updateEdge(self, edgeDict):
		"""
		When slabs change, update edge
		"""
		n = len(edgeDict['slabList'])
		edgeDict['n'] = n

		len2d = 0
		len3d = 0
		zList = []
		prevPoint2d = None
		prevPoint3d = None
		for slab in edgeDict['slabList']:
			zList.append(self.z[slab])

			currPnt2d = (self.x[slab], self.y[slab], None)
			currPnt3d = (self.x[slab], self.y[slab], self.z[slab])
			if prevPoint3d is not None:
				len2d += self.euclideanDistance2(prevPoint2d, currPnt2d)
				len3d += self.euclideanDistance2(prevPoint3d, currPnt3d)

			prevPoint2d = (self.x[slab], self.y[slab], None)
			prevPoint3d = (self.x[slab], self.y[slab], self.z[slab])

		edgeDict['Len 2D'] = round(len2d,1)
		edgeDict['Len 3D'] = round(len3d,1)

		z = round(statistics.median(zList),0)
		edgeDict['z'] = z

		#print('z:', z, type(z))

		return edgeDict

	def ____defaultEdgeDict(self):
		edgeDict = {
			'type': 'edge',
			'edgeIdx': None, #masterEdgeIdx,
			'n': None, #len(newZList),
			'Len 3D': None,
			'Len 2D': None,
			'Tort': None,
			'z': None, #round(statistics.median(newZList)),
			'preNode': -1,
			'postNode': -1,
			'Bad': False,
			'slabList': [], #thisSlabList, # list of slab indices on this edge
			'popList': [], # cases where we should be popped in joinEdges
			'editList': [], # cases where we should be edited in joinEdges
			'otherEdgeIdxList': [],
			'editPending': False,
			'popPending': False,
			}
		return edgeDict

	#202001
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
			wall[wall_slices] += block[block_slices]

		#slice:134, width:1981, height:5783
		#finalVolume = np.zeros([134, 1981, 5783])
		finalVolume = np.zeros([134, 5783, 1981])
		# finalVolume = np.zeros([145, 640, 640]) #20191017__0001

		print('bSlabList.makeVolumeMask() ... please wait')
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
				#print('   slab:', slab, 'myShape:', myShape, 'myRadius:', myRadius, 'myPosition:', myPosition, 'x:', x, 'y:', y, 'z:', z)

				arr = sphere(myShape, myRadius, myPosition)

				paste(finalVolume, arr, (z,x,y))
				#paste(finalVolume, arr, (z,y,x))

		finalVolume = finalVolume > 0

		# save results
		from skimage.external import tifffile as tif
		finalVolume = finalVolume.astype('int8')
		print('finalVolume.shape:', finalVolume.shape, type(finalVolume), finalVolume.dtype)
		tif.imsave('a.tif', finalVolume, bigtiff=True)

	def save(self):
		"""
		Save _ann.txt file from self.annotationList
		"""
		print('bSlabList.save() not implemented')

		# headers are keys of xxxx

		# each element in xxx is a comma seperated row

	def load(self):
		"""
		Load _ann.txt file
		Store in self.annotationList
		"""
		print('bSlabList.load()')

	def toggleBadEdge(self, edgeIdx):
		print('bSlabList.toggleBadEdge() edgeIdx:', edgeIdx)
		self.edgeDictList[edgeIdx]['Good'] = not self.edgeDictList[edgeIdx]['Good']
		print('   edge', edgeIdx, 'is now', self.edgeDictList[edgeIdx]['Good'])

	def getNode_zSlice(self, nodeIdx):
		"""
		Return z image slice of a node units are slices
		"""
		return self.nodeDictList[nodeIdx]['zSlice']

	def getNode_xyz(self, nodeIdx):
		"""
		Return (x,y,z) of a node units are um/pixel
		"""
		x = self.nodeDictList[nodeIdx]['x']
		y = self.nodeDictList[nodeIdx]['y']
		z = self.nodeDictList[nodeIdx]['z']
		return (x,y,z)

	def getEdgeSlabList(self, edgeIdx):
		"""
		return a list of slabs in an edge
		"""
		# 202001 was this
		#theseIndices = np.argwhere(self.id == edgeIdx)
		# now this
		theseIndices = self.edgeDictList[edgeIdx]['slabList']
		return theseIndices

	def euclideanDistance2(self, src, dst):
		# src and dst are 3 element tuples (x,y,z)
		return self.euclideanDistance(src[0], src[1], src[2], dst[0], dst[1], dst[2])

	def euclideanDistance(self, x1, y1, z1, x2, y2, z2):
		if z1 is None and z2 is None:
			return math.sqrt((x2-x1)**2 + (y2-y1)**2)
		else:
			return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)

	def __analyze(self):
		"""
		Fill in derived values in self.edgeDictList
		"""

		'''
		todo: bSlabList.analyze() needs to step through each edge, not slabs !!!
		'''

		for edgeIdx, edge in enumerate(self.edgeDictList):
			len2d = 0
			len3d = 0
			len3d_nathan = 0

			slabList = edge['slabList']
			for j, slabIdx in enumerate(slabList):

				x1 = self.x[slabIdx]
				y1 = self.y[slabIdx]
				z1 = self.z[slabIdx]

				#print('pointIdx:', pointIdx)
				orig_x = self.orig_x[slabIdx]
				orig_y = self.orig_y[slabIdx]
				orig_z = self.orig_z[slabIdx]

				if j>0:
					len3d = len3d + self.euclideanDistance(prev_x1, prev_y1, prev_z1, x1, y1, z1)
					len2d = len2d + self.euclideanDistance(prev_x1, prev_y1, None, x1, y1, None)
					len3d_nathan = len3d_nathan + self.euclideanDistance(prev_orig_x1, prev_orig_y1, prev_orig_z1, orig_x, orig_y, orig_z)

				# increment
				prev_x1 = x1
				prev_y1 = y1
				prev_z1 = z1

				prev_orig_x1 = orig_x
				prev_orig_y1 = orig_y
				prev_orig_z1 = orig_z

			edge['Len 2D'] = round(len2d,2)
			edge['Len 3D'] = round(len3d,2)
			edge['Len 3D Nathan'] = round(len3d_nathan,2)

			# diameter, pyqt does not like to display np.float, cast to float()
			meanDiameter = round(float(np.nanmean(self.d[edge['slabList']])),2)
			edge['Diam'] = meanDiameter


if __name__ == '__main__':
	path = '/Users/cudmore/box/data/nathan/vesselucida/20191017__0001.tif'
	path = '/Users/cudmore/Sites/bImpy-Data/deepvess/mytest.tif'
	sl = bSlabList(path)
