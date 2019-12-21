import os, math
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

		# nodes
		self.nodex = []
		self.nodey = []
		self.nodez = []
		self.noded = []

		self.nodeDictList = []
		self.edgeDictList = [] # this should be .annotationList

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

		self.analyze()

	@property
	def numNodes(self):
		return len(self.nodeDictList)

	@property
	def numSlabs(self):
		return len(self.x)

	@property
	def numEdges(self):
		return len(self.edgeDictList)

	def _massage_xyz(self, x, y, z):
		# todo: read this from header and triple check if valid, if not valid then us 1/1/1
		xUmPerPixel = 1 # 0.31074033574250315 #0.49718
		yUmPerPixel = 1 # 0.31074033574250315 #0.49718
		zUmPerSlice = 1 #0.5 #0.6 # Olympus .txt is telling us 0.4 ???

		# z can never be negative
		z = np.absolute(z)

		zOffset = 0

		if self.tifPath.endswith('20191017__0001.tif'):
			print('!!! scaling tiff file 20191017__0001.tif')
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

		return x,y,z

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
			return

		print('loadVesselucida_xml() file', xmlFilePath)
		mydoc = minidom.parse(xmlFilePath)

		vessels = mydoc.getElementsByTagName('vessel')
		#print('found', len(vessels), 'vessels')

		self.x = []
		self.y = []
		self.z = []
		self.orig_x = []
		self.orig_y = []
		self.orig_z = []

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

						x,y,z = self._massage_xyz(x,y,z)

						self.nodex.append(x)
						self.nodey.append(y)
						self.nodez.append(z)
						self.noded.append(diam)

						# todo: somehow assign edge list
						# important so user can scroll through all nodes and
						# check they have >1 edge !!!
						nodeDict = {
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
				#print('      found', len(edgeList), 'edges')
				# one edge (vessel segment between 2 branch points)
				for k in range(len(edgeList)):
					edge_id = edgeList[k].attributes['id'].value
					points = edgeList[k].getElementsByTagName('point') # edge is a list of 3d points
					# this is my 'edge' list, the tubes between branch points ???
					#print('         for edge id', edge_id, 'found', len(points), 'points')
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

						x,y,z = self._massage_xyz(x,y,z)

						self.x.append(x)
						self.y.append(y)
						self.z.append(z)

						newZList.append(z)
						'''
						self.d.append(diam)
						self.edgeIdx.append(masterEdgeIdx)
						'''
						thisSlabList.append(masterSlabIdx)
						masterSlabIdx += 1

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

					# add nan
					self.x.append(np.nan)
					self.y.append(np.nan)
					self.z.append(np.nan)
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
				id = edgeList.attributes['id'].value # gives us the edge list index in self.x
				srcNode = int(edgeList.attributes['sourcenode'].value)
				dstNode = int(edgeList.attributes['targetnode'].value)
				#print('   srcNode:', srcNode, 'dstNode:', dstNode)
				self.edgeDictList[j]['preNode'] = srcNode
				self.edgeDictList[j]['postNode'] = dstNode
				if srcNode != -1:
					#print('adding srcNode startNodeIdx:', startNodeIdx, 'srcNode:', srcNode, 'startEdgeIdx:', startEdgeIdx)
					self.nodeDictList[startNodeIdx+srcNode]['edgeList'].append(startEdgeIdx+j)
					self.nodeDictList[startNodeIdx+srcNode]['nEdges'] = len(self.nodeDictList[startNodeIdx+srcNode]['edgeList'])
					#print('   edgeList:', self.nodeDictList[startNodeIdx+srcNode]['edgeList'])
					#print('   nEdges:', self.nodeDictList[startNodeIdx+srcNode]['nEdges'])
				if dstNode != -1:
					#print('adding dstNode startNodeIdx:', startNodeIdx, 'dstNode:', dstNode, 'startEdgeIdx:', startEdgeIdx)
					self.nodeDictList[startNodeIdx+dstNode]['edgeList'].append(startEdgeIdx+j)
					self.nodeDictList[startNodeIdx+dstNode]['nEdges'] = len(self.nodeDictList[startNodeIdx+dstNode]['edgeList'])
					#print('   edgeList:', self.nodeDictList[startNodeIdx+dstNode]['edgeList'])
					#print('   nEdges:', self.nodeDictList[startNodeIdx+dstNode]['nEdges'])
		# end
		# for i, vessel in enumerate(vessels):

		nPoints = len(self.x)
		self.id = np.full(nPoints, 0) #Return a new array of given shape and type, filled with fill_value.

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

		#
		# create dead ends
		self.deadEndx = []
		self.deadEndy = []
		self.deadEndz = []
		for edgeDict in self.edgeDictList:
			if edgeDict['preNode'] == -1:
				firstSlabIdx = edgeDict['slabList'][0]
				tmpx = self.x[firstSlabIdx]
				tmpy = self.y[firstSlabIdx]
				tmpz = self.z[firstSlabIdx]
				self.deadEndx.append(tmpx)
				self.deadEndy.append(tmpy)
				self.deadEndz.append(tmpz)
			if edgeDict['postNode'] == -1:
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

	def getEdge(self, edgeIdx):
		"""
		return a list of slabs in an edge
		"""
		theseIndices = np.argwhere(self.id == edgeIdx)
		return theseIndices

	def analyze(self):
		"""
		Fill in derived values in self.edgeDictList
		"""
		def euclideanDistance(x1, y1, z1, x2, y2, z2):
			if z1 is None and z2 is None:
				return math.sqrt((x2-x1)**2 + (y2-y1)**2)
			else:
				return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)

		edgeIdx = 0
		n = self.numSlabs
		len2d = 0
		len3d = 0
		len3d_nathan = 0
		for pointIdx in range(n):
			# todo get rid of this
			self.id[pointIdx] = edgeIdx

			x1 = self.x[pointIdx]
			y1 = self.y[pointIdx]
			z1 = self.z[pointIdx]

			#print('pointIdx:', pointIdx)
			orig_x = self.orig_x[pointIdx]
			orig_y = self.orig_y[pointIdx]
			orig_z = self.orig_z[pointIdx]

			if np.isnan(z1):
				# move on to a new edge/vessel
				self.edgeDictList[edgeIdx]['Len 2D'] = round(len2d,2)
				self.edgeDictList[edgeIdx]['Len 3D'] = round(len3d,2)
				self.edgeDictList[edgeIdx]['Len 3D Nathan'] = round(len3d_nathan,2)
				len2d = 0
				len3d = 0
				len3d_nathan = 0
				orig_x = 0
				edgeIdx += 1
				continue

			if pointIdx > 0:
				len3d = len3d + euclideanDistance(prev_x1, prev_y1, prev_z1, x1, y1, z1)
				len2d = len2d + euclideanDistance(prev_x1, prev_y1, None, x1, y1, None)
				len3d_nathan = len3d_nathan + euclideanDistance(prev_orig_x1, prev_orig_y1, prev_orig_z1, orig_x, orig_y, orig_z)
			prev_x1 = x1
			prev_y1 = y1
			prev_z1 = z1

			prev_orig_x1 = orig_x
			prev_orig_y1 = orig_y
			prev_orig_z1 = orig_z

if __name__ == '__main__':
	path = '/Users/cudmore/box/data/nathan/vesselucida/20191017__0001.tif'
	path = '/Users/cudmore/Sites/bImpy-Data/deepvess/mytest.tif'
	sl = bSlabList(path)
