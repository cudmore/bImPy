# 20200117

import os, sys, time, warnings, json
from collections import OrderedDict
import statistics # to get median value from a list of numbers
import math
import traceback

from xml.dom import minidom # to load vesselucida xml file
#from skimage.external import tifffile as tif

from skimage import morphology
from scipy.sparse import csgraph # to get dijoint segments

# abb 20210104, removed
#import skan

# skan is used to make a skeleton from a mask. Like skeletonize in Fiji
# it is super problematic fpr boring things like imports
# reserve its use to just scripts, do NOT include it in the
# main bImPy interface !!!!
#from skan import draw # for plotting

import tifffile

import numpy as np
import h5py
import ast # to convert dict to string to save in h5py

import networkx as nx # see makeGraph

# to plot networkx with matplotlib, see self.plotGraph()
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

# to plot networkx with plotly, see self.plotGraph2()
import chart_studio.plotly as py
import plotly.graph_objs as go
import plotly.io as pio

import bimpy

# abb aics
#from sanode import bVascularTracingAics
#import sanode
from bimpy import bVascularTracingAics

class NpEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, np.integer):
			return int(obj)
		elif isinstance(obj, np.floating):
			return float(obj)
		elif isinstance(obj, np.ndarray):
			return obj.tolist()
		else:
			return super(NpEncoder, self).default(obj)

class bVascularTracing:
	def __init__(self, parentStack, path, loadTracing=True):
		"""
		path: path to file
		"""
		#print('bVascularTracing.__init__() loadTracing:', loadTracing, 'path:', path)
		self.parentStack = parentStack
		self.path = path

		#self._dvMask = None # created in loadDeepVess
		self._initTracing()

		if loadTracing:
			self.hasFile = {'h5f':False, 'vesselucida':False, 'deepvess':False}
			loaded_h5f = self.load()
			if loaded_h5f:
				self.hasFile['h5f'] = True
			else:
				donotloadForNow = False
				if not donotloadForNow:
					# load is probably broken
					#loadedVesselucida = self.loadVesselucida_xml()
					loadedVesselucida = False
					if loadedVesselucida:
						self.hasFile['vesselucida'] = True
					else:
						# this actually loads mask and then makes trcing from it
						# only do this explicitly in a script
						pass
						'''
						loadedDeepVess = self.loadDeepVess()
						if loadedDeepVess:
							self.hasFile['deepvess'] = True
						'''
					#
					# todo: combine the next two into one function
					self.analyzeEdgeDeadEnds() # mark edges coming from Vesseluica that has pre/post None
					self.fixMissingNodes() # fill in missing pre/post nodes coming from vesselucia
					self._analyze()
					self.colorize()
		#
		# remove short edges
		'''
		removeSmallerThan = 6
		print('  calling bVascularTracingAics.removeShortEdges() removeSmallerThan:', removeSmallerThan)
		bVascularTracingAics.removeShortEdges(self, removeSmallerThan=removeSmallerThan)
		'''
		#
		self.makeGraph() # always make the graph

	def _initTracing(self):
		self.nodeDictList = []
		self.edgeDictList = []
		self.editDictList = [] # created in self.joinEdge() for vesselucida

		self.x = np.empty((0,))
		self.y = np.empty((0,))
		self.z = np.empty((0,))
		self.d = np.empty(0)
		self.d2 = np.empty(0)
		self.int = np.empty(0)
		self.edgeIdx = np.empty(0, dtype=np.float) # will be nan for nodes
		self.nodeIdx = np.empty(0, dtype=np.float) # will be nan for slabs
		#self.slabIdx = np.empty(0, dtype=np.uint8) # will be nan for slabs
		# abb oct2020
		self.isBad = np.empty(0, dtype=np.float) # will be nan for nodes
		self.lpMin = np.empty(0, dtype=np.float) # will be nan for nodes
		self.lpMax = np.empty(0, dtype=np.float) # will be nan for nodes
		self.lpSNR = np.empty(0, dtype=np.float) # will be nan for nodes

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
		#print('getNode()', nodeIdx, theDict)
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

	def getNode_xyz_scaled(self, nodeIdx):
		x = self.nodeDictList[nodeIdx]['x'] * self.parentStack.xVoxel
		y = self.nodeDictList[nodeIdx]['y'] * self.parentStack.yVoxel
		z = self.nodeDictList[nodeIdx]['z'] * self.parentStack.zVoxel
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

		if slabIdx is None or np.isnan(slabIdx):
			return None
		slabIdx = int(slabIdx)
		edgeIdx = self.edgeIdx[slabIdx]
		if np.isnan(edgeIdx):
			return None
		else:
			return int(round(self.edgeIdx[slabIdx]))


	# abb aics
	# todo: put this out of class scope
	def myBoundCheck_Decorator(func):
		"""
		Use safe_run as a decorator
		Executes func() and return None on exception
		"""
		def func_wrapper(*args, **kwargs):
			try:
				return func(*args, **kwargs)
			except Exception as e:
				print('EXCEPTION in bVascularTracing.myBoundCheck_Decorator() e:', e)
				return None
		return func_wrapper

	def myBoundCheck_Node(self, nodeIdx):
		if nodeIdx is None:
			return True
		else:
			numNodes = len(self.nodeDictList)
			theRet = nodeIdx>=0 and nodeIdx < numNodes
			if not theRet:
				print('\n====================================')
				print('  ERROR: bVascularTracing.myBoundCheck_Node() got bad nodeIdx:', nodeIdx, 'with numNodes:', numNodes)
				traceback.print_stack()
				print('n')
			return theRet

	def myBoundCheck_Edge(self, edgeIdx):
		if edgeIdx is None:
			return True
		else:
			numEdges = len(self.edgeDictList)
			theRet =  edgeIdx>=0 and edgeIdx < numEdges # true/false
			if not theRet:
				print('\n====================================')
				print('  ERROR: bVascularTracing.myBoundCheck_Edge() got bad edgeIdx:', edgeIdx, 'with numEdges:', numEdges)
				traceback.print_stack()
				print('n')
			return theRet

	def myBoundCheck_Slab(self, slabIdx):
		if slabIdx is None:
			return True
		else:
			numSlabs = len(self.x)
			theRet = slabIdx>=0 and slabIdx < numSlabs
			if not theRet:
				print('\n====================================')
				print('  ERROR: bVascularTracing.myBoundCheck_Slab() got bad slabIdx:', slabIdx, 'with numSlabs:', numSlabs)
				traceback.print_stack()
				print('n')
			return theRet

	#@myBoundCheck_Decorator
	def getEdge(self, edgeIdx):

		# check edgeIdx is in bounds
		#if edgeIdx is None or edgeIdx<0 or edgeIdx > self.numEdges()-1:
		#	# error
		#	return None

		if not self.myBoundCheck_Edge(edgeIdx):
			return

		edgeDict = self.edgeDictList[edgeIdx]
		edgeDict['idx'] = edgeIdx
		#
		slabList = self.getEdgeSlabList(edgeIdx)
		edgeDict['nSlab'] = len(slabList)
		edgeDict['slabList'] = slabList

		return edgeDict

	# abb aics
	def getEdgeMinMax_Z(self, edgeIdx):
		slabIdxList = self.getEdgeSlabList(edgeIdx)
		zMin = np.min(self.z[slabIdxList])
		zMax = np.max(self.z[slabIdxList])

		zMin = int(zMin)
		zMax = int(zMax)

		return zMin, zMax

	def getEdgeSlabList(self, edgeIdx):
		"""
		return a list of slabs in an edge
		"""
		# abb aics, fixing out of bound error with emit() signal coming from table selection
		# when table is out of date
		try:
			preNode = self.edgeDictList[edgeIdx]['preNode']
			postNode = self.edgeDictList[edgeIdx]['postNode']
		except (IndexError) as e:
			print('ERROR: getEdgeSlabList() bad edgeIdx:', edgeIdx, e)
			return None

		preSlab = self._getSlabFromNodeIdx(preNode)
		postSlab = self._getSlabFromNodeIdx(postNode)

		#slabList = self.edgeIdx[self.edgeIdx==edgeIdx]
		myTuple = np.where(self.edgeIdx == edgeIdx)
		myTuple = myTuple[0]
		slabList = myTuple

		#print('b) getEdgeSlabList() edgeIdx:', edgeIdx, 'slabList:', slabList)

		#build the list, [pre ... slabs ... post]
		theseIndices = []
		# preNode slab
		if preSlab is not None:
			theseIndices.append(preSlab)
		# main list
		for slab in slabList:
			theseIndices.append(slab)
		# post node slab
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

	def analyzeEdgeDeadEnds(self):
		"""
		mark edges coming from Vesseluica that has pre/post None
		"""

		for edgeIdx, edge in enumerate(self.edgeIter()):
			foundDeadEnd = False
			preNode = edge['preNode']
			if preNode is not None:
				preNodeNumEdges = self.nodeDictList[preNode]['nEdges']
				if preNodeNumEdges == 1:
					foundDeadEnd = True
			else:
				foundDeadEnd = True
			postNode = edge['postNode']
			if postNode is not None:
				postNodeNumEdges = self.nodeDictList[postNode]['nEdges']
				if postNodeNumEdges == 1:
					foundDeadEnd = True
			else:
				foundDeadEnd = True
			edge['deadEnd'] = foundDeadEnd

	# edits
	def newNode(self, x, y, z):
		"""
		"""
		newNodeIdx = self.numNodes()
		newSlabIdx = self.numSlabs()

		nodeDict = self._defaultNodeDict(x=x, y=y, z=z, nodeIdx=newNodeIdx, slabIdx=newSlabIdx)
		self.nodeDictList.append(nodeDict)

		self._appendSlab(x=x, y=y, z=z, nodeIdx=newNodeIdx)

		#print('   bVascularTracing.newNode() newNodeIdx:', newNodeIdx, 'newSlabIdx:', newSlabIdx)

		return newNodeIdx

	def newEdge(self, srcNode, dstNode, verbose=False):
		"""
		src/dst node are w.r.t self.nodeDictList
		"""
		#print('bVascularTracing.newEdge() srcNode:', srcNode, type(srcNode), 'dstNode:', dstNode, type(dstNode))

		newEdgeIdx = self.numEdges()

		edgeDict = self.bimp(edgeIdx=newEdgeIdx, srcNode=srcNode, dstNode=dstNode)

		print('newEdge() edgeDict:', edgeDict)

		# find the slabs corresponding to src/dst node
		srcSlab = np.where(self.nodeIdx==srcNode)[0]
		dstSlab = np.where(self.nodeIdx==dstNode)[0]

		srcSlab = srcSlab.ravel()[0]
		dstSlab = dstSlab.ravel()[0]

		# not needed
		#edgeDict['slabList'] = [srcSlab, dstSlab]

		# assign edge z to middle of src z, dst z
		x1,y1,z1 = self.getSlab_xyz(srcSlab)
		x2,y2,z2 = self.getSlab_xyz(dstSlab)
		z = (z1+z2)/2
		z = int(round(z))
		edgeDict['z'] = z

		# append to edge list
		self.edgeDictList.append(edgeDict)

		# update src/dst node
		self.nodeDictList[srcNode]['edgeList'] += [newEdgeIdx]
		self.nodeDictList[dstNode]['edgeList'] += [newEdgeIdx]

		if verbose: print('bVascularTracing.newEdge()', newEdgeIdx, 'srcNode:', srcNode, 'dstNode:', dstNode)
		#self._printGraph()

		return newEdgeIdx

	def newSlab(self, edgeIdx, x, y, z, d=np.nan, d2=np.nan, verbose=False):
		"""
		append a new slab to edgeIdx

		"""
		#todo: check thar edgeIdx exists

		newSlabIdx = self.numSlabs()

		# append to x/y/z list
		self._appendSlab(x=x, y=y, z=z, d=d, d2=d2, edgeIdx=edgeIdx)

		# add slab to dict list, add slab before last slab which is postNode
		# not needed
		#self.edgeDictList[edgeIdx]['slabList'].insert(-1, newSlabIdx)

		# abb oct2020
		#self.addNewSlabToEdge(edgeIdx, slabIdx)

		if verbose: print('bVascularTracing.newSlab()', newSlabIdx)
		#self._printGraph()

		return newSlabIdx

	'''
	def addNewSlabToEdge(self, edgeIdx, slabIdx):
		pass
	'''

	def old_updateEdge___(self, edgeIdx):
		"""
		when slabs change (add, subtract, move)
		update z (the median z of all slabs
		"""

		pass
		'''
		slabList = self.getEdgeSlabList(edgeIdx)
		z = round(statistics.median(newZList))
		'''

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
				#print('ERROR: deleteNode() should not be here ... preNode')
				edge['preNode'] -= 1
			if postNode is not None and (postNode > nodeIdx):
				#self.edgeDictList[edgeIdx]['postNode'] = postNode - 1
				#print('ERROR: deleteNode() should not be here ... postNode')
				edge['postNode'] -= 1

		# delete from dict
		self.nodeDictList.pop(nodeIdx)

		# delete from slabs
		self.deleteSlab(nodeSlabIdx)

		#
		# decriment remaining self.nodeIdx
		# x[np.less(x, -1000., where=~np.isnan(x))] = np.nan
		self.nodeIdx[np.greater(self.nodeIdx, nodeIdx, where=~np.isnan(self.nodeIdx))] -= 1

		return True

	def deleteEdge(self, edgeIdx, verbose=False):

		if verbose: print('bVascularTracing.deleteEdge() edgeIdx:', edgeIdx)

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
			if verbose: print('   preNode:', preNode, self.nodeDictList[preNode])
			try:
				edgeListIdx = self.nodeDictList[preNode]['edgeList'].index(edgeIdx)
				self.nodeDictList[preNode]['edgeList'].pop(edgeListIdx)
				self.nodeDictList[preNode]['nEdges'] -= 1 # abb aics
				if verbose: print('      bVascularTracing.deleteEdge() popped edgeIdx from preNode:', preNode, 'edgeIdx:', edgeIdx, 'edgeListIdx:', edgeListIdx)
			except (ValueError) as e:
				print('   !!! WARNING: exception in bVascularTracing.deleteEdge():', str(e))
		if postNode is not None: # will always be true, edges always have pre/post node
			if verbose: print('   postNode:', postNode, self.nodeDictList[postNode])
			try:
				edgeListIdx = self.nodeDictList[postNode]['edgeList'].index(edgeIdx)
				self.nodeDictList[postNode]['edgeList'].pop(edgeListIdx)
				self.nodeDictList[postNode]['nEdges'] -= 1 # abb aics
				if verbose: print('      bVascularTracing.deleteEdge() popped edgeIdx from postNode:', postNode, 'edgeIdx:', edgeIdx, 'edgeListIdx:', edgeListIdx)
			except (ValueError) as e:
				print('   !!! WARNING: exception in bVascularTracing.deleteEdge():', str(e))

		# debug, edgeIdx should no longer be in node['edgeList']

		# decrement remaining node['edgeList']
		for nodeIdx, node in enumerate(self.nodeDictList):
			# debug
			# delete edge 70, causes interface error and is not caught here???
			try:
				edgeListIdx = node['edgeList'].index(edgeIdx)
				print('!!! !!! ERROR: in decriment bVascularTracing.deleteEdge() nodeIdx:', nodeIdx, 'still has edgeIdx:', edgeIdx, 'in ["edgeList"]:', node['edgeList'])
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

		# abb aics, was this
		'''
		if len(edgeSlabList) == 2:
			# it is an edge with no slabs
			pass
		else:
			# don't do this because some vessellucia don't have both pre/post node !!!
			# assuming we used getEdgeSlabList2() above
			#thisSlabList  = edgeSlabList[1:-1] # slabList without first/prenode and last/postnode
			thisSlabList = edgeSlabList # slabList without first/prenode and last/postnode
			self._deleteSlabList(thisSlabList, verbose=verbose)
		'''
		# abb aics, now this
		thisSlabList = edgeSlabList # slabList without first/prenode and last/postnode
		self._deleteSlabList(thisSlabList, verbose=verbose)

		# debug
		# look for remaining slabs with edge Idx
		# was this
		'''
		for tmpIdx, tmpEdgeIdx in enumerate(self.edgeIdx):
			if tmpEdgeIdx == edgeIdx:
				print('\n   !!! !!! ERROR: in debug bVascularTracing.deleteEdge() edgeIdx at slab idx:', tmpIdx, 'STILL has edgeIdx==', edgeIdx, '\n')
		'''
		stillThere = np.where(self.edgeIdx == edgeIdx)[0]
		if len(stillThere) > 0:
			print('\n   !!! !!! ERROR: in debug bVascularTracing.deleteEdge() edgeIdx at slab idx:', stillThere, 'STILL has edgeIdx==', edgeIdx)
			for stillThreIdx in range(len(stillThere)):
				self.printSlabInfo(stillThere[stillThreIdx])

		#
		# decriment remaining self.edgeIdx
		# x[np.less(x, -1000., where=~np.isnan(x))] = np.nan
		# abb aics removed, added to resetEdgeIdx()
		self.edgeIdx[np.greater(self.edgeIdx, edgeIdx, where=~np.isnan(self.edgeIdx))] -= 1

		# abb aics
		# decrement 'idx' or edges in self.edgeDictList[]
		self.resetEdgeIdx()

		#print('after) bVascularTracing.deleteEdge()', edgeIdx)
		#self._printGraph()

	def deleteSlab(self, slabIdx):
		'''
		print('bVascularTracing.deleteSlab() slabIdx:', slabIdx, 'shape:', self.x.shape)
		self._printSlab(slabIdx)
		'''

		if not self.myBoundCheck_Slab(slabIdx):
			print('ERROR: bVascularTracing.deleteSlab() got bad slab index:', slabIdx, 'total num slabs is:', len(self.x))
			return

		edgeIdx = self.edgeIdx[slabIdx]
		nodeIdx = self.nodeIdx[slabIdx]

		self.x = np.delete(self.x, slabIdx)
		self.y = np.delete(self.y, slabIdx)
		self.z = np.delete(self.z, slabIdx)
		self.d = np.delete(self.d, slabIdx)
		self.d2 = np.delete(self.d2, slabIdx)
		self.int = np.delete(self.int, slabIdx)
		self.edgeIdx = np.delete(self.edgeIdx, slabIdx)
		self.nodeIdx = np.delete(self.nodeIdx, slabIdx)
		#self.slabIdx = np.delete(self.slabIdx, slabIdx)

		# abb oct2020
		self.isBad = np.delete(self.isBad, slabIdx)
		self.lpMin = np.delete(self.lpMin, slabIdx)
		self.lpMax = np.delete(self.lpMax, slabIdx)
		self.lpSNR = np.delete(self.lpSNR, slabIdx)

		# abb oct2020, delete slab to edge
		#self.deleteSlabFromEdge(edgeIdx, slabIdx)

		#decriment remaining slabIdx
		#self.slabIdx[self.slabIdx>slabIdx] -= 1

		# remember, both self.edgeIdx and self.nodeIdx have nan!
		#if edgeIdx is not None:

	'''
	def deleteSlabFromEdge(self, edgeIdx, slabIdx)
		pass
	'''

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

	def _appendSlab(self, x, y, z, d=np.nan, d2=np.nan, edgeIdx=np.nan, nodeIdx=np.nan):
		newSlabIdx = self.numSlabs()
		self.x = np.append(self.x, x)
		self.y = np.append(self.y, y)
		self.z = np.append(self.z, z)
		self.d = np.append(self.d, d)
		self.d2 = np.append(self.d2, d2) # will be filled in by bLineIntensity profile
		self.int = np.append(self.int, np.nan) # oct2020, not used???
		self.edgeIdx = np.append(self.edgeIdx, edgeIdx)
		self.nodeIdx = np.append(self.nodeIdx, nodeIdx)
		#self.slabIdx = np.append(self.slabIdx, newSlabIdx)

		# abb oct2020, add slab to edge edgeIdx
		# slabs are NOT bad, edges are bad
		# this should allow us to NOT display bad edges
		self.isBad = np.append(self.isBad, np.nan)
		# line intensity profile
		self.lpMin = np.append(self.lpMin, np.nan)
		self.lpMax = np.append(self.lpMax, np.nan)
		self.lpSNR = np.append(self.lpSNR, np.nan) # lpMax/lpMin

		return newSlabIdx

	def _deleteSlabList(self, slabList, verbose=False):
		"""
		special case to delete lots of slabs on deleting edge

		slabList: list of slab to delete
		"""
		if verbose: print('bVascularTracing._deleteSlabList() slabList:', slabList)

		slabListCopy = np.array(slabList)

		for idx, slab in enumerate(slabList):
			thisSlab = slabListCopy[idx]
			self.deleteSlab(thisSlab)
			# decriment all items of slabList > slab
			slabListCopy = slabListCopy - 1 # this is assuming slabs are monotonically increasing

	def _getSlabFromNodeIdx(self, nodeIdx):
		# todo: not sure if this works
		#print('!!! NOT SURE IF THIS WORKS debug _getSlabFromNodeIdx() nodeIdx:', nodeIdx)
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
			'nEdges': 0,
			'type': '',
			'isBad': False,
			'note': '',
			'x': round(x,2),
			'y': round(y,2),
			'z': round(z,2),
			#'zSlice': None, #todo remember this when I convert to um/pixel !!!
			'skelID': None, # used by deepves
			'slabIdx': slabIdx,
			'edgeList': [],
		})
		return nodeDict

	def _defaultEdgeDict(self, edgeIdx, srcNode, dstNode):
		edgeDict = OrderedDict({
			'idx': edgeIdx, # used by stack widget table
			'type': '',
			'preNode': srcNode,
			'postNode': dstNode,
			'Diam': None, # mean
			'Diam2': None, # mean, my line intensity analysis
			'nSlab': 0, # umber of slabs
			'Len 3D': None,
			'Len 2D': None,
			'Tort': None,
			'isBad': False,
			'note': '',
			'z': None, # median from z of slab list
			'deadEnd': None,
			'skelID': None, # used by deepves
			'color': 'cyan',
			'nCon': None, # 0/1/2 for no other, one, or 2 other edges
			'slabList': [], # list of slab indices on this edge
			# abb oct2020
			'mSlabSNR': None,

			})
		return edgeDict

	def setNodeType(self, nodeIdx, newType):
		self.nodeDictList[nodeIdx]['type'] = newType

	def setEdgeType(self, edgeIdx, newType):
		self.edgeDictList[edgeIdx]['type'] = newType

	def setNodeIsBad(self, nodeIdx, isBad):
		self.nodeDictList[nodeIdx]['isBad'] = isBad

	def setEdgeIsBad(self, edgeIdx, isBad):
		self.edgeDictList[edgeIdx]['isBad'] = isBad

	# abb aics
	def _printStats(self):
		self._printInfo()

	def _printInfo2(self):
		print('    slabs:', self.numSlabs(),
			'nodes:', self.numNodes(),
			'edges:', self.numEdges())

	def _printInfo(self):
		'''
		print('file:', self.parentStack)
		print('   x:', self.x.shape)
		print('   y:', self.y.shape)
		print('   z:', self.z.shape)
		'''
		print(os.path.basename(self.parentStack.path),
			'slabs:', self.numSlabs(),
			'nodes:', self.numNodes(),
			'edges:', self.numEdges())

		print('len(x)', len(self.x))
		print('len(y)', len(self.y))
		print('len(z)', len(self.z))
		print('len(d)', len(self.d))
		print('len(d2)', len(self.d2))
		print('len(int)', len(self.int))
		print('len(edgeIdx)', len(self.edgeIdx))
		print('len(nodeIdx)', len(self.nodeIdx))

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
		print('   x:', self.x[idx], 'y:', self.y[idx], 'z:', self.z[idx], 'd:', self.d[idx], 'd2:', self.d2[idx], 'nodeIdx:', self.nodeIdx[idx], 'edgeIdx:', self.edgeIdx[idx])

	def _printNodes(self):
		print('   nodeDictList:')
		for node in self.nodeDictList:
			print('      ', node)

	def _printEdges(self):
		print('   edgeDictList:')
		for edgeIdx, edge in enumerate(self.edgeDictList):
			edge = self.getEdge(edgeIdx)
			print('      ', edge, 'slabList:', self.getEdgeSlabList(edgeIdx))

	def printNodeInfo(self, nodeIdx):
		node = self.getNode(nodeIdx)
		#print('    printNodeInfo() nodeIdx:', nodeIdx, 'idx:', node['idx'], 'nEdges:', node['nEdges'], 'edgeList:', node['edgeList'])
		print(json.dumps(node, indent=4))

	def printEdgeInfo(self, edgeIdx, withNodes=True):
		#print('printEdgeInfo() edgeIdx:', edgeIdx)

		edge = self.getEdge(edgeIdx)
		#print('    printEdgeInfo() edgeIdx:', edgeIdx, 'idx:', edge['idx'], 'nSlab:', edge['nSlab'])
		for k,v in edge.items():
			if k == 'slabList':
				continue
			print(f'    {k} : {v}')
		#print(json.dumps(edge, indent=4, cls=NpEncoder))

		if withNodes:
			preNodeIdx = edge['preNode']
			postNodeIdx= edge['postNode']

			self.printNodeInfo(preNodeIdx)
			self.printNodeInfo(postNodeIdx)

	def printSlabInfo(self, slabIdx):
		print('  slabIdx:', slabIdx, 'x:', self.x[slabIdx], 'y:', self.y[slabIdx], 'z:', self.z[slabIdx], 'edgeIdx:', self.edgeIdx[slabIdx], 'nodeIdx:', self.nodeIdx[slabIdx])

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

		elif self.path.endswith('20191017__0001.tif') or self.path.endswith('20191017__0001_z.tif') or self.path.endswith('20191017__0001_8b_z.tif'):
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

		elif self.path.endswith('20200127_gel_0011_z.tif'):
			xUmPerPixel = 0.3977476
			yUmPerPixel = 0.3977476
			zUmPerPixel = 0.51

		xUmPerPixel = self.parentStack.xVoxel
		yUmPerPixel = self.parentStack.yVoxel
		zUmPerPixel = self.parentStack.zVoxel

		'''
		if self.path.endswith('20191017_0001.tif'):
			xUmPerPixel = 0.4971802
			yUmPerPixel = 0.4971802
			zUmPerPixel = 0.4
		'''

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
			return False

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
						nodeDict['skelID'] = i
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
					edgeDict['skelID'] = i
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

		print('   loaded', masterNodeIdx, 'nodes,', masterEdgeIdx, 'edges, and approximately', masterSlabIdx, 'points')

		# defer this until we fix missing pre/post nodes
		#self._analyze()

		# this sorta works
		'''
		for i in range(1):
			self.joinEdges()
		'''

		# this sorta works
		#self.findCloseSlabs()

		# this works
		#self.makeVolumeMask()

		# defer this until we fix missing pre/post nodes
		#self.colorize()

		return True

	def loadDeepVess(self, vascChannel=2, maskStartStop=None):
		"""
		maskStartStop: inclusive (start slice, stop slice)
			mask out (set to 0) slices beyond this range
			use this to only analyze a subset of the mask

		todo: rename this makeSkelFromMask()
		"""
		print('bVascularTracing.loadDeepVess() maskStartStop:', maskStartStop)
		print('  todo: rename this to makeSkelFromMask()')
		dvMaskPath, ext = os.path.splitext(self.path)

		#print(' !!!!! 20200819 switching loadDeepVess to load vasc aics analysis')

		## abb aics analysis
		"""
		todo: use master cell db and add column to tell us which label index to use
		debugging with: /Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch2.tif
		"""
		doAics = True
		if doAics:
			# load _labeled, 16-bit
			'''
			labeledPath = dvMaskPath + '_labeled.tif'
			labeledData = tifffile.imread(labeledPath)
			'''
			# make mask from one label

			'''
			thisOneLabel = 1
			#self._dvMask = np.zeros(labeledData.shape, dtype=np.uint8)
			self._dvMask = np.where(labeledData==thisOneLabel, 1, 0)
			print(' !!!!! aics self._dvMask after including label', thisOneLabel, self._dvMask.shape, self._dvMask.dtype)
			'''

			#self._dvMask = labeledData > 0

			# erode _mask by 1 (before skel) as skel was getting mized up with z-collisions
			#self._dvMask = bimpy.util.morphology.binary_erosion(self._dvMask, iterations=2)

			dvMask = self.parentStack.getStack('mask', 2)
			if dvMask is not None:
				dvMask = dvMask.copy() # we might blank some slices

				##
				##
				print('  loadDeepVess() aics dvMask', dvMask.shape, dvMask.dtype)
				'''
				tmpPath = '/home/cudmore/data/nathan/20200814_SAN3_BOTTOM_tail/aicsAnalysis/20200814_SAN3_BOTTOM_tail_ch2.tif'
				if self.path == tmpPath:
					print('\n\n    need to remove top/bottom slices')
					print('    blanking slices 0..16')
					dvMask[0:16,:,:] = 0
				'''
				if maskStartStop is not None:
					#print('todo: blank out start/top of mask maskStartStop:', maskStartStop)
					startSlice = maskStartStop[0]
					stopSlice = maskStartStop[1]
					if startSlice is not None:
						print('   using startSlice:', startSlice, 'to mask [0..startSlice,:,:]')
						dvMask[0:startSlice,:,:] = 0
					if stopSlice is not None:
						print('   uisng stopSlice:', stopSlice, 'to mask [stopSlice+1:,:,:]')
						dvMask[stopSlice+1:,:,:] = 0
				##
				##
			else:
				print('bVasularTracing.loadDeepVess() got None dvMask')
				return False
		else:
			dvMaskPath += '_dvMask.tif'
			dvMaskPath += '_mask.tif'
			if not os.path.isfile(dvMaskPath):
				print('    error: did not find _dvMask file:', dvMaskPath)
				return False

		self._initTracing()

		## abb aics analysis
		if doAics:
			tmpBasePath, tmpExt = os.path.splitext(self.path)
			tmpBasePath, tmpBaseName = os.path.split(tmpBasePath)
			tmpBaseName = tmpBaseName.replace('_ch1', '')
			tmpBaseName = tmpBaseName.replace('_ch2', '')
			uFirstSlice = None
			uLastSlice = None
			try:
				#print('tmpBaseName:', tmpBaseName)
				trimDict = bVascularTracingAics.stackDatabase[tmpBaseName]
				uFirstSlice = trimDict['uFirstSlice']
				uLastSlice = trimDict['uLastSlice']
			except (KeyError) as e:
				# todo: get rid of this and use maskStartStop instead
				#print('did not find stack tmpBaseName:', tmpBaseName, 'in bVascularTracingAics.stackDatabase ---->>>> NO PRUNING/BLANKING')
				pass
			if uFirstSlice is not None and uLastSlice is not None:
				print('    loadDeepVess() aics pruning/blanking slices:', uFirstSlice, uLastSlice)
				dvMask[0:uFirstSlice-1,:,:] = 0
				dvMask[uLastSlice:,:,:] = 0

			'''
			uFirstSlice = 44 # /Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch2.tif
			uFirstSlice = 1 + uFirstSlice * 3 # for z-expanded file 'a'
			uLastSlice = 64
			uLastSlice = 1 + uLastSlice * 3 # for z-expanded file 'a'
			#uFirstSlice = 56 # /Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0015_ch2.tif
			#uLastSlice = 61
			if uFirstSlice is not None and uLastSlice is not None:
				print('    loadDeepVess() aics pruning slices:', uFirstSlice, uLastSlice)
				self._dvMask[0:uFirstSlice-1,:,:] = 0
				self._dvMask[uLastSlice:-1,:,:] = 0
			'''
		else:
			print('    loading _dvMask file:', dvMaskPath)
			self._dvMask = tifffile.imread(dvMaskPath)


		# 20200901 laptop
		#parentStack = self.parentStack.getStack('ch1')
		#print('critical todo: get rid of hard coded vascChannel = 2')
		#vascChannel = 2
		parentStack = self.parentStack.getStack('raw', vascChannel) # vasc channel
		print('  parentStack:', parentStack.shape)
		#
		# convert the deepvess mask to a skeleton (same as deepves postprocess)
		print('  making 1-pixel skeleton from binary stack dvMask ...')
		startSeconds = time.time()
		# todo: fix this, older version need to use max_pool3d
		#skeleton0 = morphology.skeletonize(dvMask)
		dvSkelPath, ext = os.path.splitext(self.path)
		dvSkelPath += '_dvSkel.tif'
		tryWith_dvSkel = False
		if tryWith_dvSkel and os.path.isfile(dvMaskPath):
			print('    - loading dv skel from file:', dvSkelPath)
			skeleton0 = tifffile.imread(dvSkelPath)
		else:
			print('    generating 1-pixel skeleton from dvMask using morphology.skeletonize_3d ... might be too slow')
			skeleton0 = morphology.skeletonize_3d(dvMask)
		print('    skeleton0:', type(skeleton0), skeleton0.dtype, skeleton0.shape, np.min(skeleton0), np.max(skeleton0))
		print('        took:', round(time.time()-startSeconds,2), 'seconds')

		'''
		# try and get mean intensity of each branch/edge
		pixel_graph, coordinates, degrees = skan.skeleton_to_csgraph(skeleton0)
		myStats = skan.csr.branch_statistics(pixel_graph, pixel_values=parentStack)
		for stat in myStats:
			print('    branch_statistics stat:', stat)
		'''

		#
		# convert raw skeleton into a proper graph with nodes/edges
		print('    generating skan (package) skeleton with skan.Skeleton(skeleton0)')
		startSeconds = time.time()
		skanSkel = skan.Skeleton(skeleton0, source_image=parentStack.astype('float'))
		print('        took:', round(time.time()-startSeconds,2), 'seconds')

		# not needed but just to remember
		branch_data = skan.summarize(skanSkel) # branch_data is a pandas dataframe
		print('    skan skanSkel branch_data.shape:', branch_data.shape)
		print(branch_data.head())

		# make a list of coordinate[i] that are segment endpoints_src
		nCoordinates = skanSkel.coordinates.shape[0]
		slabs = skanSkel.coordinates.copy() #np.full((nCoordinates,3), np.nan)
		nodes = np.full((nCoordinates), np.nan)
		nodeEdgeList = [[] for tmp in range(nCoordinates)]
		edges = np.full((nCoordinates), np.nan)

		_, skeleton_ids = csgraph.connected_components(skanSkel.graph, directed=False)

		path_lengths = skanSkel.path_lengths()
		path_means = skanSkel.path_means() # does not return intensity of image, always 1 (e.g. the mask?)

		masterNodeIdx = 0
		masterEdgeIdx = 0
		nPath = len(skanSkel.paths_list())
		print('    parsing skanSkel.paths_list() nPath:', nPath, '...')
		for edgeIdx, path in enumerate(skanSkel.paths_list()):
			# edgeIdx: int

			# skip paths made of just two nodes
			if len(path)<=2:
				#print('skipping edgeIdx:', edgeIdx)
				continue

			# remember to remove
			#if int(float(skeleton_ids[edgeIdx])) == 2:
			#	continue

			srcPnt = path[0]
			dstPnt = path[-1]

			z = float(skanSkel.coordinates[srcPnt,0]) # deepvess uses (slice, x, y)
			x = float(skanSkel.coordinates[srcPnt,1])
			y = float(skanSkel.coordinates[srcPnt,2])
			diam = 5 # todo: add this to _analysis

			if nodes[srcPnt] >= 0:
				srcNodeIdx = int(float(nodes[srcPnt]))
				self.nodeDictList[srcNodeIdx]['edgeList'].append(masterEdgeIdx)
				self.nodeDictList[srcNodeIdx]['nEdges'] = len(self.nodeDictList[srcNodeIdx]['edgeList'])
				'''
				print('=== srcPnt appended to node', srcNodeIdx, 'edge list:',masterEdgeIdx)
				print('    ', self.nodeDictList[srcNodeIdx])
				'''
			else:
				# new node
				srcNodeIdx = masterNodeIdx
				masterNodeIdx += 1
				#
				nodes[srcPnt] = srcNodeIdx
				#
				nodeDict = self._defaultNodeDict(x=x, y=y, z=z, nodeIdx=srcNodeIdx)
				nodeDict['idx'] = srcNodeIdx
				nodeDict['edgeList'].append(masterEdgeIdx)
				nodeDict['nEdges'] = 1
				nodeDict['skelID'] = int(float(skeleton_ids[edgeIdx]))
				self.nodeDictList.append(nodeDict)
				# always append slab
				self._appendSlab(x, y, z, d=diam, edgeIdx=np.nan, nodeIdx=srcNodeIdx)

			z = float(skanSkel.coordinates[dstPnt,0]) # deepvess uses (slice, x, y)
			x = float(skanSkel.coordinates[dstPnt,1])
			y = float(skanSkel.coordinates[dstPnt,2])
			diam = 5 # todo: add this to _analysis
			if nodes[dstPnt] >= 0:
				dstNodeIdx = int(float(nodes[dstPnt]))
				self.nodeDictList[dstNodeIdx]['edgeList'].append(masterEdgeIdx)
				self.nodeDictList[dstNodeIdx]['nEdges'] = len(self.nodeDictList[dstNodeIdx]['edgeList'])
				'''
				print('=== dstPnt appended to node', dstNodeIdx, 'edge list:',masterEdgeIdx)
				print('    ', self.nodeDictList[dstNodeIdx])
				'''
			else:
				# new node
				dstNodeIdx = masterNodeIdx
				masterNodeIdx += 1
				#
				nodes[dstPnt] = dstNodeIdx
				#
				nodeDict = self._defaultNodeDict(x=x, y=y, z=z, nodeIdx=dstNodeIdx)
				nodeDict['idx'] = dstNodeIdx
				nodeDict['edgeList'].append(masterEdgeIdx)
				nodeDict['nEdges'] = 1
				nodeDict['skelID'] = int(float(skeleton_ids[edgeIdx]))
				self.nodeDictList.append(nodeDict)
				# always append slab
				self._appendSlab(x, y, z, d=diam, edgeIdx=np.nan, nodeIdx=dstNodeIdx)

			#print('path_lengths[] edgeIdx:', edgeIdx, path_lengths[edgeIdx], 'skeleton_ids:', skeleton_ids[edgeIdx], 'len(path):', len(path), 'path_means:', path_means[edgeIdx])
			newZList = []
			#if len(path)>2:
			if 1:
				for idx2 in path[1:-2]:
					#edges[idx2] = idx
					zEdge = float(skanSkel.coordinates[idx2,0]) # deepvess uses (slice, x, y)
					xEdge = float(skanSkel.coordinates[idx2,1])
					yEdge = float(skanSkel.coordinates[idx2,2])
					newZList.append(zEdge)
					diam = 3
					newSlabIdx = self._appendSlab(xEdge, yEdge, zEdge, d=diam, edgeIdx=masterEdgeIdx, nodeIdx=np.nan)

				# always append an edge
				edgeDict = self._defaultEdgeDict(edgeIdx=masterEdgeIdx, srcNode=srcNodeIdx, dstNode=dstNodeIdx)
				masterEdgeIdx += 1
				if len(newZList) > 0:
					edgeDict['z'] = int(round(statistics.median(newZList)))
				self.edgeDictList.append(edgeDict)

			else:
				pass # this happens a lot ???
				#print('    warning: got len(path)<=2 at edgeIdx:',edgeIdx)

		print('    .done parsing skanSkel.paths_list() nPath:', nPath, '...')

		self._analyze()

		# abb aics, this just prints stats
		#bimpy.bVascularTracingAics.detectEdgesAndNodesToRemove(self)

		print('    .done bVascularTracing.loadDeepVess()')
		return True

	def makeVolumeMask(self):
		"""
		todo: could use my diameter ['d2']
		"""
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
				# todo: could use self.d2

				diamInt = int(round(diam))

				x = self.x[slab].astype('float')
				y = self.y[slab].astype('float')
				z = self.z[slab].astype('float')
				diam = self.d[slab].astype('float')
				diamInt = int(diam)

				# 20200303 THIS IS NOT WORKING ... FUCK THIS
				#diamInt *= 2 # expand by a factor !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

				#myShape = (diamInt+1,diamInt+1,diamInt+1)
				myShape = (diamInt,diamInt,diamInt)
				# 20200303 THIS IS NOT WORKING ... FUCK THIS
				#myRadius = int(round(diam/2)+1) * 4 # expand by a factor !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
				myRadius = float(diam/2)
				myPosition = (myRadius, myRadius, myRadius)

				# debug
				#print('   edge:', i, 'slab:', slab, 'myShape:', myShape, 'myRadius:', myRadius, 'myPosition:', myPosition, 'x:', x, 'y:', y, 'z:', z)

				print('myShape:', myShape, type(myShape[0]), 'myRadius:', myRadius, type(myRadius), 'myPosition:', myPosition, type(myPosition[0]))
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
		print('joinEdges() Number of edits (1,2,3,4):', numEdits1, numEdits2, numEdits3, numEdits4)
		print('   !!! NOT EDITING ANYTHING FOR NOW ... return')

		##
		##
		return
		##
		##

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

		colors = set(['r', 'g', 'b', 'orange', 'm'])

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

	def _analyze(self, thisEdgeIdx=None):
		"""
		Fill in derived values in self.edgeDictList
		"""

		'''
		todo: bSlabList.analyze() needs to step through each edge, not slabs !!!
		'''

		if thisEdgeIdx is None:
			# all
			thisEdgeDictList = self.edgeDictList
		else:
			thisEdgeDictList = [self.edgeDictList[thisEdgeIdx]]

		print('  bVascularTracing._analyze() thisEdgeIdx:', thisEdgeIdx, 'len(thisEdgeDictList):', len(thisEdgeDictList))

		for edgeIdx, edge in enumerate(thisEdgeDictList):
			#print('    edge:', edge)
			if thisEdgeIdx is not None:
				edge = self.getEdge(thisEdgeIdx) # todo: fix this, redundant self.getEdge() does calculations !
			else:
				edge = self.getEdge(edgeIdx) # todo: fix this, redundant self.getEdge() does calculations !
			len2d = 0
			len3d = 0
			#len3d_nathan = 0

			# get straighl line (euclidean distance) between nodes
			preNode = edge['preNode']
			postNode = edge['postNode']
			if preNode is not None and postNode is not None:
				#print('edgeIdx:', edgeIdx, 'preNode:', preNode, 'postNode:', postNode)
				x1,y1,z1 = self.getNode_xyz(preNode)
				x2,y2,z2 = self.getNode_xyz(postNode)
				euclideanDist = self.euclideanDistance(x1,y1,z1,x2,y2,z2)

				z = (z1+z2)/2
				z = int(round(z))
				edge['z'] = z
			else:
				euclideanDist = np.nan

			slabList = edge['slabList']
			for j, slabIdx in enumerate(slabList):

				x1, y1, z1 = self.getSlab_xyz(slabIdx)

				if j>0:
					len3d = len3d + self.euclideanDistance(prev_x1, prev_y1, prev_z1, x1, y1, z1)
					len2d = len2d + self.euclideanDistance(prev_x1, prev_y1, None, x1, y1, None)
					#len3d_nathan = len3d_nathan + self.euclideanDistance(prev_orig_x1, prev_orig_y1, prev_orig_z1, orig_x, orig_y, orig_z)

				# increment
				prev_x1 = x1
				prev_y1 = y1
				prev_z1 = z1

			edge['Len 2D'] = round(len2d,2)
			edge['Len 3D'] = round(len3d,2)
			#edge['Len 3D Nathan'] = round(len3d_nathan,2)

			if euclideanDist == 0:
				# todo: writ emore real-time code to find these (just sort the edge list!!!)
				#print('WARNING: bVascularTracing._analyze() euclideanDist==0 for edgeIdx:', edgeIdx)
				tort = np.nan
			else:
				tort = round(len3d / euclideanDist,2)
			edge['Tort'] = tort

			# diameter, pyqt does not like to display np.float, cast to float()
			# vesselucida
			meanDiameter = round(float(np.nanmean(self.d[edge['slabList']])),2)
			edge['Diam'] = meanDiameter
			# bob
			# self.d2 might all be nan
			warnings.filterwarnings('ignore')
			possibleNaN = np.nanmean(self.d2[edge['slabList']])
			if np.isnan(possibleNaN):
				meanDiameter = np.nan
			else:
				meanDiameter = round(float(possibleNaN),2)
			edge['Diam2'] = meanDiameter
			warnings.resetwarnings()
			#print(edgeIdx, meanDiameter)

			# number of other edges connected to, will be 0/1/2
			edge['nCon'] = self.getEdgeConnectivity(edgeIdx)

	def euclideanDistance2(self, src, dst):
		# src and dst are 3 element tuples (x,y,z)
		return self.euclideanDistance(src[0], src[1], src[2], dst[0], dst[1], dst[2])

	def euclideanDistance(self, x1, y1, z1, x2, y2, z2):
		if z1 is None and z2 is None:
			return math.sqrt((x2-x1)**2 + (y2-y1)**2)
		else:
			return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)

	def analyzeSlabIntensity(self, slabIdx=None, edgeIdx=None, allEdges=None):
		"""
		todo: add login to analyze one slab (slabIdx) or an edge (edgeIdx)
		todo: make edgeIdx a list of edge idx
		"""

		radius = 20
		lineWidth=5
		medianFilter = 3

		lp = bimpy.bLineProfile(self.parentStack)

		startTime = bimpy.util.bTimer()
		nEdges = self.numEdges()
		print('analyzeSlabIntensity() analyzing intensity of all slabs across', nEdges, 'edges ...')
		print("  will set each edge['Diam2'] to PIXELS")
		meanDiamList = [] # mean diam per segment based on Vesselucida
		meanDiamList2 = [] # my intensity calculation
		lengthList = []
		tortList = []
		numAnalyzed = 0
		for edgeIdx in range(nEdges):
			if edgeIdx % 20 == 0:
				print('    edgeIdx:', edgeIdx, 'of', nEdges, 'edges')

			edgeDict = self.getEdge(edgeIdx)

			thisDiamList = []

			for slabIdx in edgeDict['slabList']:
				lpDict = lp.getLine(slabIdx, radius=radius) # default is radius=30

				if lpDict is not None:
					retDict = lp.getIntensity(lpDict, lineWidth=lineWidth, medianFilter=medianFilter)
					if retDict is not None:
						thisDiamList.append(retDict['diam']) # bImPy diameter
						self.d2[slabIdx] = retDict['diam']
						numAnalyzed += 1
					else:
						self.d2[slabIdx] = np.nan
				else:
					self.d2[slabIdx] = np.nan

				if np.isnan(self.d2[slabIdx]):
					nodeIdx = self.nodeIdx[slabIdx]
					if np.isnan(nodeIdx):
						#print('    got nan width for edge', edgeIdx, 'slab', slabIdx, 'nodeIdx:', nodeIdx)
						pass

			if len(thisDiamList) > 0:
				thisDiamMean = np.nanmean(thisDiamList)
			else:
				thisDiamMean = np.nan
			meanDiamList2.append(thisDiamMean)
			meanDiamList.append(edgeDict['Diam']) # vessellucida
			lengthList.append(edgeDict['Len 3D'])
			tortList.append(edgeDict['Tort'])

			# abb aics
			edgeDict['Diam2'] = thisDiamMean

		print('   number of slabs analyzed:', numAnalyzed, startTime.elapsed())

	# my first generator :) I am almost back to my C++ savvyness
	def nodeIter(self):
		n = len(self.nodeDictList)
		i = 0
		while i<n:
			yield self.getNode(i)
			i += 1

	def edgeIter(self):
		n = len(self.edgeDictList)
		i = 0
		while i<n:
			yield self.getEdge(i)
			i += 1

	def search(self, type=None):
		"""
		search for close nodes

		very slow for large number of nodes
		"""
		print('search()')
		#
		thresholdDist = 10
		#
		timer = bimpy.util.bTimer(name='search')
		theDictList = []
		numRows = 0
		nNodes = len(self.nodeDictList)
		distanceMatrix = np.ndarray((nNodes,nNodes))
		distanceMatrix[:] = np.nan
		for i, iDict in enumerate(self.nodeDictList):
			iDict = self.getNode(i)
			x1 = iDict['x']
			y1 = iDict['y']
			z1 = iDict['z']
			for j, jDict in enumerate(self.nodeDictList):
				jDict = self.getNode(j)
				if i==j: continue
				if not np.isnan(distanceMatrix[j,i]): continue
				x2 = jDict['x']
				y2 = jDict['y']
				z2 = jDict['z']
				dist = self.euclideanDistance(x1,y1,z1,x2,y2,z2)
				if dist<thresholdDist:
					distanceMatrix[i,j] = dist
					theDict = OrderedDict()
					theDict['Idx'] = numRows
					theDict['z'] = z1
					theDict['node1'] = i
					theDict['nEdges1'] = iDict['nEdges']
					if iDict['nEdges'] == 1:
						theDict['edgeList'] = iDict['edgeList']
						edgeDict = self.getEdge(iDict['edgeList'][0])
						theDict['preNode'] = edgeDict['preNode']
						theDict['postNode'] = edgeDict['postNode']
						theDict['Len 2D'] = edgeDict['Len 2D']
					else:
						theDict['edgeList'] = ''
						theDict['preNode'] = ''
						theDict['postNode'] = ''
						theDict['Len 2D'] = ''
					theDict['node2'] = j
					theDict['nEdges2'] = jDict['nEdges']
					theDict['dist'] = round(dist,2)
					#print('    nodes close:', theDict)
					theDictList.append(theDict)
					numRows += 1
		self.editDictList = theDictList
		print('    found:', numRows, timer.elapsed())
		return theDictList

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
		h5FilePath = self._getSavePath() + '.h5f'
		print('=== bVascularTracing.save() h5FilePath:', h5FilePath)

		saveDict = OrderedDict()
		saveDict['nodeDictList'] = self.nodeDictList
		saveDict['edgeDictList'] = self.edgeDictList

		# todo: should use try:except ValueError and delete file if we get an error
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
				# debug mostly to check for numpy types that are not able to be converted to json
				'''
				if idx==0:
					for k,v in edge.items():
						print(k, v, type(v))
				'''

				# convert numpy int64 to int
				tmpSLabList = [int(tmpSlab) for tmpSlab in edge['slabList']]
				edge['slabList'] = tmpSLabList # careful, we are changing backend data !!!

				# each edge will have a group
				edgeGroup = f.create_group('edge' + str(idx))
				# each edge group will have a  dict with all parameters
				edgeDict_json = json.dumps(edge)
				edgeGroup.attrs['edgeDict'] = edgeDict_json

			# slabs are in a dataset
			slabData = np.column_stack((self.x, self.y, self.z,
							self.d, self.d2, self.int,
							self.edgeIdx, self.nodeIdx,
							self.isBad,
							self.lpMin, self.lpMax, self.lpSNR,))
			#print('slabData:', slabData.shape)
			f.create_dataset('slabs', data=slabData)

			#
			# maskedEdgesDict
			# oct 2020, we are loading this but we are always calling _preComputeAllMasks !!!!
			for k,v in self.maskedEdgesDict.items():
				f.create_dataset(k, data=v)

		return h5FilePath

	def load(self):
		"""
		Load from file
		This works but all entries are out of order. For example (edge,node)
		Need to order them correctly
		"""
		startSeconds = time.time()

		h5FilePath = self._getSavePath() + '.h5f'

		print('=== bVascularTracing.load()', h5FilePath)

		if not os.path.isfile(h5FilePath):
			#print('   file not found:', h5FilePath)
			return None

		maxNodeIdx = -1
		maxEdgeIdx = -1

		# needed because (nodes, slabs) come in in the wrong order,
		# we file them away using 'idx' after loaded
		tmpNodeDictList = []
		tmpEdgeDictList = []

		#
		# created in _preComputeAllMasks()
		self.maskedEdgesDict = {}

		with h5py.File(h5FilePath, "r") as f:
			for name in f:
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
					self.d2 = b[:,4]
					self.int = b[:,5]
					self.edgeIdx = b[:,6]
					self.nodeIdx = b[:,7]
					# oct2020
					try:
						self.isBad = b[:,8]
						self.lpMin = b[:,9]
						self.lpMax = b[:,10]
						self.lpSNR = b[:,11]
					except (IndexError) as e:
						print('=== bVascularTracing.load() new file format for (isBad, lpMin, lpMax, lpSNR)')
						loadedShape = self.x.shape
						print('  loadedShape:', loadedShape)
						self.isBad = np.zeros(loadedShape) * np.nan
						self.lpMin = np.zeros(loadedShape) * np.nan
						self.lpMax = np.zeros(loadedShape) * np.nan
						self.lpSNR = np.zeros(loadedShape) * np.nan
				elif name.startswith('aics'):
					self.maskedEdgesDict[name] = f[name][:]

				else:
					print('bVascularTracing.load() did not understand name:', name, 'in file:', h5FilePath)
				# all maskedEdgesDict start with aics

				'''
				elif name == 'masks':
					c = f['masks']
					print('debug c:', c)
					maskDictList = ast.literal_eval(c)
				'''
		#
		# go through what we loaded and sort them into the correct position based on ['idx']
		self.nodeDictList = [None] * (maxNodeIdx+1) # make an empy list with correct length
		for node in tmpNodeDictList:
			self.nodeDictList[node['idx']] = node
		self.edgeDictList = [None] * (maxEdgeIdx+1) # make an empy list with correct length
		for edge in tmpEdgeDictList:
			self.edgeDictList[edge['idx']] = edge

		stopSeconds = time.time()
		elapsedSeconds = round(stopSeconds-startSeconds,2)
		print(f'    loaded nodes: {maxNodeIdx} edges: {maxEdgeIdx} slabs: {len(self.x)} in {elapsedSeconds} seconds')

		#return maskDictList
		return h5FilePath

	def fixMissingNodes(self):
		"""
		Fill in missing pre/post nodes from Vesselucia
		"""
		print('bVascularTracing.fixMissingNodes() numNodes:', self.numNodes())
		for edgeIdx, edge in enumerate(self.edgeIter()):
			preNode = edge['preNode']
			if preNode is None:
				slabIdx = edge['slabList'][0]
				x = self.x[slabIdx]
				y = self.y[slabIdx]
				z = self.z[slabIdx]
				x = float(x)
				y = float(y)
				z = float(z)
				newNodeIdx = self.newNode(x,y,z)
				self.nodeDictList[newNodeIdx]['edgeList'] = [edgeIdx]
				self.nodeDictList[newNodeIdx]['nEdges'] = 1
				#
				edge['preNode'] = newNodeIdx
				#print('edge:', edgeIdx, 'after adding preNode', newNodeIdx, 'edge:', self.edgeDictList[edgeIdx])

			postNode = edge['postNode']
			if postNode is None:
				slabIdx = edge['slabList'][-1]
				x = self.x[slabIdx]
				y = self.y[slabIdx]
				z = self.z[slabIdx]
				x = float(x)
				y = float(y)
				z = float(z)
				newNodeIdx = self.newNode(x,y,z)
				self.nodeDictList[newNodeIdx]['edgeList'] = [edgeIdx]
				self.nodeDictList[newNodeIdx]['nEdges'] = 1
				#
				edge['postNode'] = newNodeIdx

		print('    done fixMissingNodes() numNodes:', self.numNodes())

	def makeGraph(self, verbose=False):
		"""
		Make a networkx graph

		see for adding position (pos): https://stackoverflow.com/questions/11804730/networkx-add-node-with-specific-position
		"""

		numNodes = 0
		numEdges = 0
		self.G = nx.Graph()
		for idx, edgeDict in enumerate(self.edgeDictList):
			edgeDict = self.getEdge(idx) # todo: fix this
			diam = edgeDict['Diam']
			len3d = edgeDict['Len 3D']
			preNode = edgeDict['preNode']
			postNode = edgeDict['postNode']

			if preNode is not None and postNode is not None:
				preNode = int(preNode)
				postNode = int(postNode)

				xPre,yPre,zPre = self.getNode_xyz(preNode)
				xPost,yPost,zPost = self.getNode_xyz(postNode)

				# add adge
				#print('    adding edge:', numEdges, preNode, postNode, diam, len3d)
				self.G.add_node(preNode, myIdx=preNode, pos=(xPre,yPre,zPre))
				self.G.add_node(postNode, myIdx=postNode, pos=(xPost,yPost,zPost))
				self.G.add_edge(preNode, postNode, edgeIdx=idx, diam=diam, len3d=len3d) # this adds a 'diam' key to the edge attributes
				numEdges += 1
			else:
				# error, why do my edges not have pre/post nodes?
				# this is a bigger problem
				print('makeGraph() skipping edge:', idx, 'pre/post:', preNode, postNode)

				#print('        error: edge idx:', idx, 'preNode:', preNode, 'postNode:', postNode)
		if verbose:
			print('  bVascularTracing.makeGraph() created self.G with:')
			print('    nodeDictList:', len(self.nodeDictList), 'edgeDictList:', len(self.edgeDictList))
			print('    number_of_nodes:', self.G.number_of_nodes())
			print('    number_of_edges:', self.G.number_of_edges())
			cc = list(nx.connected_components(self.G))
			print('    connected_components:', len(cc))
			'''
			allSimplePaths = nx.all_simple_paths(self.G, source=None, target=None)
			print('    number of simple paths:', len(list(allSimplePaths)))
			'''

	def plotGraph2(self):
		"""
		plot a 3d graph with plotly

		see: https://plot.ly/python/v3/3d-network-graph/
		"""

		pos = nx.get_node_attributes(self.G, 'pos')
		n = self.G.number_of_nodes()

		print('bVascularTracing.plotGraph2() n:', n)

		myColor = [None] * n
		for idx,cc in enumerate(nx.connected_components(self.G)):
			# cc is a set
			for nodeIdx in cc:
				myColor[nodeIdx] = idx

		# nodes
		Xn=[pos[k][0] for k in range(n)] # x-coordinates of nodes
		Yn=[pos[k][1] for k in range(n)]
		Zn=[pos[k][2] for k in range(n)]

		# node labels
		labels = []
		for k in range(n):
			labelStr = 'node:' + str(k) + ' cc:' + str(myColor[k])
			labels.append(labelStr)

		# edges
		Xe = []
		Ye = []
		Ze = []
		#for src,dst,myDict in self.G.edges_iter(data=True):
		for src,dst,myDict in self.G.edges(data=True):
			Xe+=[pos[src][0],pos[dst][0], None]# x-coordinates of edge ends
			Ye+=[pos[src][1],pos[dst][1], None]# x-coordinates of edge ends
			Ze+=[pos[src][2],pos[dst][2], None]# x-coordinates of edge ends

		# shortest path
		srcNode = 114
		dstNode = 57
		# networkx.exception.NetworkXNoPath
		try:
			oneShortestPath = nx.shortest_path(self.G, source=srcNode, target=dstNode)
			xshortestn = [pos[k][0] for k in oneShortestPath]
			yshortestn = [pos[k][1] for k in oneShortestPath]
			zshortestn = [pos[k][2] for k in oneShortestPath]
		except (nx.exception.NetworkXNoPath) as e:
			print('my exception e:', e)

		# edges
		trace1=go.Scatter3d(x=Xe,
			y=Ye,
			z=Ze,
			mode='lines',
			line=dict(color='rgb(125,125,125)', width=1),
			hoverinfo='none'
			)

		# nodes
		trace2=go.Scatter3d(x=Xn,
			y=Yn,
			z=Zn,
			mode='markers',
			name='actors',
			marker=dict(symbol='circle',
				size=6,
				color=myColor, #group,
				colorscale='Viridis',
				line=dict(color='rgb(50,50,50)', width=0.5)
				),
			text=labels,
			hoverinfo='text'
			)

		axis=dict(showbackground=False,
			showline=False,
			zeroline=False,
			showgrid=False,
			showticklabels=False,
			title=''
			)

		layout = go.Layout(
			title="my layout title",
			width=1000,
			height=1000,
			showlegend=False,
			scene=dict(
				xaxis=dict(axis),
				yaxis=dict(axis),
				zaxis=dict(axis),
			),
			margin=dict(t=100),
			hovermode='closest',
			annotations=[
				dict(
					showarrow=False,
					text="Image file: " + self.parentStack.path,
					xref='paper',
					yref='paper',
					x=0,
					y=0.1,
					xanchor='left',
					yanchor='bottom',
					font=dict(size=14)
					)
				],    )

		data = [trace1, trace2]
		fig = go.Figure(data=data, layout=layout)

		#py.iplot(fig, filename='Les-Miserables xxx')
		#py.plot(fig, filename='Les-Miserables xxx', auto_open=True)
		#pio.write_html(fig, file='hello_world.html', auto_open=True)

		return fig

	def plotGraph(self):
		"""
		Plot a graph with matplotlib
		In general, VERY SLOW ... use plotly instead

		see: https://www.idtools.com.au/3d-network-graphs-python-mplot3d-toolkit/
		"""
		pos = nx.get_node_attributes(self.G, 'pos')
		n = self.G.number_of_nodes()

		# debug
		print('=== plotGraph()')
		print('    len(pos):', len(pos))
		print('    number_of_nodes n:', n)
		# debug
		'''
		for i in range(n):
			if self.G.has_node(i):
				print('    ', i, type(i), 'degree:', self.G.degree(i))
			else:
				print('missing node:', i)
		'''

		edge_max = max([self.G.degree(i) for i in range(n)])
		colors = [plt.cm.plasma(self.G.degree(i)/edge_max) for i in range(n)]

		with plt.style.context(('ggplot')):
			fig = plt.figure(figsize=(10,7))
			ax = Axes3D(fig)

			# Loop on the pos dictionary to extract the x,y,z coordinates of each node
			for key, value in pos.items():
				xi = value[0]
				yi = value[1]
				zi = value[2]
				# Scatter plot
				#ax.scatter(xi, yi, zi, c=colors[key], s=20+20*self.G.degree(key), edgecolors='k', alpha=0.7)
				ax.scatter(xi, yi, zi, c='r', s=20+20*self.G.degree(key), edgecolors='k', alpha=0.7)

			# Loop on the list of edges to get the x,y,z, coordinates of the connected nodes
			# Those two points are the extrema of the line to be plotted
			for i,j in enumerate(self.G.edges()):
				#print('i/j:', i, j)
				x = np.array((pos[j[0]][0], pos[j[1]][0]))
				y = np.array((pos[j[0]][1], pos[j[1]][1]))
				z = np.array((pos[j[0]][2], pos[j[1]][2]))

				# Plot the connecting lines
				ax.plot(x, y, z, c='black', alpha=0.5)

		# Set the initial view
		angle = 0
		ax.view_init(30, angle)

		# Hide the axes
		ax.set_axis_off()

		plt.show()

	# abb aics
	def isDanglingEdge(self, edgeIdx):
		"""
		a 'dangling' edges is an edge where where pre/post nodes are only connected to one edge
		"""
		edge = self.getEdge(edgeIdx)
		preNodeIdx = edge['preNode']
		postNodeIdx = edge['postNode']

		preNode = self.getNode(preNodeIdx)
		postNode = self.getNode(postNodeIdx)

		preNumEdges = preNode['nEdges']
		postNumEdges = postNode['nEdges']

		theRet = False
		if preNumEdges==1 and postNumEdges==1:
			theRet = True

		return theRet

	# abb aics
	def getEdgeConnectivity(self, edgeIdx):
		"""
		Return 0, 1, or 2 where
			0: edge is dangling
			1: edge is connected to other edge on one end
			2: edge is connected to other edges on both ends
		"""
		connectedNumber = 0

		edge = self.getEdge(edgeIdx)

		preNodeIdx = edge['preNode']
		postNodeIdx = edge['postNode']

		preNode = self.getNode(preNodeIdx)
		postNode = self.getNode(postNodeIdx)

		preNumEdges = preNode['nEdges']
		postNumEdges = postNode['nEdges']

		if preNumEdges > 1:
			connectedNumber += 1
		if postNumEdges > 1:
			connectedNumber += 1

		return connectedNumber

	# abb aics
	def checkSanity(self):

		print('bVascularTracing.checkSanity()')
		numEdges = self.numEdges()
		print('  numEdges:', numEdges)
		for idx, edgeDict in enumerate(self.edgeDictList):
			print('  idx:', idx, 'edgeDict', edgeDict)

	# abb aics
	def resetEdgeIdx(self):
		for idx, edgeDict in enumerate(self.edgeDictList):
			#print('  idx:', idx, 'edgeDict', edgeDict)
			edgeDict['idx'] = idx
			# do not do here !!!!
			#self.edgeIdx[idx] = idx

	def _preComputeAllMasks(self, verbose=False):
		print('  bVascularTracing._preComputeAllMasks()')

		timeIt = bimpy.util.bTimer('  _preComputeAllMasks')

		aicsSlabList = []
		aicsSlabList_x = np.empty((0), np.float16) #[]
		aicsSlabList_y = np.empty((0), np.float16) #[]
		aicsSlabList_z = np.empty((0), np.float16) #[]
		aicsSlabList_edgeIdx = np.empty((0), np.uint16) #[]
		aicsSlabList_slabIdx = np.empty((0), np.uint16) #[]
		#aicsSlabList_isBad = np.empty((0), np.uint16) #[]

		for edgeIdx, edge in enumerate(self.edgeDictList):
			tmpSlabList = self.getEdgeSlabList(edgeIdx) # includes nodes
			aicsSlabList += tmpSlabList + [np.nan] # abb aics

			# x
			aicsSlabList_x = np.append(aicsSlabList_x, self.x[tmpSlabList])
			aicsSlabList_x = np.append(aicsSlabList_x, np.nan) # abb aics

			# y
			aicsSlabList_y = np.append(aicsSlabList_y, self.y[tmpSlabList])
			aicsSlabList_y = np.append(aicsSlabList_y, np.nan) # abb aics
			# z
			aicsSlabList_z = np.append(aicsSlabList_z, self.z[tmpSlabList])
			aicsSlabList_z = np.append(aicsSlabList_z, np.nan) # abb aics

			# edgeIdx (needs to be float)
			aicsSlabList_edgeIdx = np.append(aicsSlabList_edgeIdx, self.edgeIdx[tmpSlabList])
			aicsSlabList_edgeIdx = np.append(aicsSlabList_edgeIdx, np.nan) # abb aics

			# slabIdx (needs to be float)
			aicsSlabList_slabIdx = np.append(aicsSlabList_slabIdx, tmpSlabList)
			aicsSlabList_slabIdx = np.append(aicsSlabList_slabIdx, np.nan) # abb aics

			# isBad
			'''
			aicsSlabList_isBad = np.append(aicsSlabList_isBad, self.isBad[tmpSlabList])
			aicsSlabList_isBad = np.append(aicsSlabList_isBad, np.nan) # abb aics
			'''
		#
		# nodes
		nodeIdxMask = np.ma.masked_greater_equal(self.nodeIdx, 0)
		nodeIdxMask = nodeIdxMask.mask

		aicsNodeList_x = self.x[nodeIdxMask]
		aicsNodeList_y = self.y[nodeIdxMask]
		aicsNodeList_z = self.z[nodeIdxMask]
		aicsNodeList_nodeIdx = self.nodeIdx[nodeIdxMask].astype(np.uint16)

		self.maskedEdgesDict = {
			# edges
			'aicsSlabList': aicsSlabList,
			'aicsSlabList_x': aicsSlabList_x,
			'aicsSlabList_y': aicsSlabList_y,
			'aicsSlabList_z': aicsSlabList_z,
			'aicsSlabList_slabIdx': aicsSlabList_slabIdx,
			'aicsSlabList_edgeIdx': aicsSlabList_edgeIdx,
			# nodes
			'aicsNodeList_x': aicsNodeList_x,
			'aicsNodeList_y': aicsNodeList_y,
			'aicsNodeList_z': aicsNodeList_z,
			'aicsNodeList_nodeIdx': aicsNodeList_nodeIdx,

		}

		print('  ', timeIt.elapsed())

		return self.maskedEdgesDict

if __name__ == '__main__':
	path = '/home/cudmore/data/nathan/20200814_SAN3_BOTTOM_tail/aicsAnalysis/20200814_SAN3_BOTTOM_tail_ch2.tif'

	global myStack
	stack = bimpy.bStack(path=path)
	stack.slabList.fixMissingNodes()

	# do this once then save
	'''
	removeSmallerThan = 3
	bimpy.bVascularTracingAics.removeShortEdges(stack.slabList, removeSmallerThan=removeSmallerThan)

	stack.saveAnnotations()
	'''

	type = 'Analyze All Diameters'
	paramDict = {
		'radius': 12,
		'lineWidth': 5,
		'medianFilter': 5,
	}
	bimpy.bVascularTracingAics.myWorkThread(stack.slabList, type, paramDict)

	# after this we should have diam of all slabs
	#stack.saveAnnotations()

	stack.saveAnnotations()

	if 0:
		nodeIdx1 = 34
		nodeIdx2 = 116
		okJoin = bimpy.bVascularTracingAics.joinNodes(vascTracing, nodeIdx1, nodeIdx2, verbose=True)

	#
	# test join 2 edges
	if 0:
		edgeIdx1 = 209 #82
		edgeIdx2 = 210 #41

		# before join
		edge1 = stack.slabList.getEdge(edgeIdx1)
		edge2 = stack.slabList.getEdge(edgeIdx2)

		print('* before:')
		print('  stack.slabList.numNodes()', stack.slabList.numNodes())
		print('  stack.slabList.numEdges()', stack.slabList.numEdges())
		print('  edgeIdx1:', edgeIdx1, edge1)
		print('  edgeIdx2:', edgeIdx2, edge2)

		print('=== calling bimpy.bVascularTracingAics.joinEdges() edgeIdx1:', edgeIdx1, 'edgeIdx2:', edgeIdx2)
		newEdgeIdx, newSrcNodeIdx, newDstNodeIdx = bimpy.bVascularTracingAics.joinEdges(vascTracing, edgeIdx1, edgeIdx2, verbose=True)

		# after join, edge 1/2 still exist but should have been changed (the order in the list is changed because of removeEdge 1/2
		print('* after:')
		'''
		edge1 = stack.slabList.getEdge(edgeIdx1)
		edge2 = stack.slabList.getEdge(edgeIdx2)
		print('  edgeIdx1:', edgeIdx1, edge1)
		print('  edgeIdx2:', edgeIdx2, edge2)
		'''

		print('  newEdgeIdx:', newEdgeIdx)
		print('  newSrcNodeIdx:', newSrcNodeIdx)
		print('  newDstNodeIdx:', newDstNodeIdx)

		print('  stack.slabList.numNodes()', stack.slabList.numNodes())
		print('  stack.slabList.numEdges()', stack.slabList.numEdges())

		# new edge
		newEdge = stack.slabList.getEdge(newEdgeIdx)
		print('  newEdgeIdx:', newEdgeIdx, newEdge)

		# src/dst node of new edge
		preNode = stack.slabList.getNode(newSrcNodeIdx)
		postNode = stack.slabList.getNode(newDstNodeIdx)
		print('  newSrcNodeIdx:', newSrcNodeIdx, preNode)
		print('  newDstNodeIdx:', newDstNodeIdx, postNode)

		stack.slabList.resetEdgeIdx()

		stack.slabList.checkSanity()

	#
	# older debug
	#

	# this was a plotly plot
	# get it working again
	#stack.slabList.plotGraph2()

	# not implemented for undirected type
	'''
	simpleCycles = nx.simple_cycles(stack.slabList.G)
	print('simpleCycles:', simpleCycles)
	'''

	# this was working
	'''
	import matplotlib.pyplot as plt
	options = {
		'node_color': 'black',
		'node_size': 50, # 100
		'width': 3,
	}
	plt.subplot(111)
	#nx.draw(stack.slabList.G, with_labels=True) #, font_weight='bold')
	nx.draw(stack.slabList.G, **options) #, font_weight='bold')
	plt.show()
	'''

	#bvt = bVascularTracing(stack, '')

	'''
	stack.slabList.analyzeSlabIntensity()
	stack.slabList._analyze()
	stack.saveAnnotations()
	'''

	'''
	meanDiamList = []
	meanDiamList2 = []
	nEdges = stack.slabList.numEdges()
	for edgeIdx in range(nEdges):
		edgeDict = stack.slabList.getEdge(edgeIdx)
		meanDiamList.append(edgeDict['Diam']) # vessellucida
		meanDiamList2.append(edgeDict['Diam2']) # vessellucida
	print(meanDiamList2)
	'''

	'''
	bvt.newNode(100, 200, 50)
	bvt.newNode(100, 200, 50)
	bvt.newEdge(0,1)
	edgeIdx = 0
	bvt.newSlab(edgeIdx, 100, 200, 50)
	bvt.deleteNode(1)

	print (bvt.x, bvt.y, bvt.z)
	print(bvt.x.shape, type(bvt.x))

	print(bvt.edgeDictList)
	'''
