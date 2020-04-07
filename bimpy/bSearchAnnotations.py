# 20200313
# Robert Cudmore

"""
A class to search annotations
"""

import time
from collections import OrderedDict

import numpy as np

import networkx as nx # see makeGraph

import bimpy

# see: https://gist.github.com/joe-jordan/6548029
def find_all_cycles(G, source=None, cycle_length_limit=None):
    """forked from networkx dfs_edges function. Assumes nodes are integers, or at least
    types which work with min() and > ."""
    if source is None:
        # produce edges for all components
        nodes=[i[0] for i in nx.connected_components(G)]
    else:
        # produce edges for components with source
        nodes=[source]
    # extra variables for cycle detection:
    cycle_stack = []
    output_cycles = set()

    def get_hashable_cycle(cycle):
        """cycle as a tuple in a deterministic order."""
        m = min(cycle)
        mi = cycle.index(m)
        mi_plus_1 = mi + 1 if mi < len(cycle) - 1 else 0
        if cycle[mi-1] > cycle[mi_plus_1]:
            result = cycle[mi:] + cycle[:mi]
        else:
            result = list(reversed(cycle[:mi_plus_1])) + list(reversed(cycle[mi_plus_1:]))
        return tuple(result)

    for start in nodes:
        if start in cycle_stack:
            continue
        cycle_stack.append(start)

        stack = [(start,iter(G[start]))]
        while stack:
            parent,children = stack[-1]
            try:
                child = next(children)

                if child not in cycle_stack:
                    cycle_stack.append(child)
                    stack.append((child,iter(G[child])))
                else:
                    i = cycle_stack.index(child)
                    if i < len(cycle_stack) - 2:
                      output_cycles.add(get_hashable_cycle(cycle_stack[i:]))

            except StopIteration:
                stack.pop()
                cycle_stack.pop()

    return [list(i) for i in output_cycles]

class bSearchAnnotations:
	def __init__(self, slabList):
		self.slabList = slabList
		# parent stack is in self.slabList.parentStack
		self.initSearch()

	def initSearch(self, name=''):
		"""
		Initialize a search
		"""
		self.name = name
		self.nFound = 0
		self.nSearched = 0
		self.startTime = time.time()
		self.hitDictList = []

	def addFound(self, hitDict):
		"""
		Add a found object
		"""
		self.nFound += 1
		hitDict['Idx'] = self.nFound # modify the dict
		self.hitDictList.append(hitDict)

	def addSearched(self):
		"""
		Add to the number of searched objects/items
		"""
		self.nSearched += 1

	def finishSearch(self, verbose=False):
		"""
		Finish the search
		"""
		if verbose:
			for idx, hitDict in enumerate(self.hitDictList):
				print('    ', idx, hitDict)
		self.stopTime = time.time()
		self.elapsed = round(self.stopTime-self.startTime,2)
		print('bSearchAnnotations "' + self.name + '" finished in', self.elapsed, 'seconds, searched', self.nSearched, 'items -->> found', self.nFound)


	def _defaultSearchDict(self):
		"""
		Get a default search itme
		"""
		theRet = OrderedDict()
		theRet['Idx'] = None
		theRet['dist'] = None
		#
		theRet['node1'] = None
		theRet['edge1'] = None
		theRet['slab1'] = None
		#
		theRet['node2'] = None
		theRet['edge2'] = None
		theRet['slab2'] = None

		theRet['preNode'] = None
		theRet['postNode'] = None

		return theRet

	def _defaultSearchDict2(self):
		"""
		Get a default search itme
		"""
		theRet = OrderedDict()
		theRet['Idx'] = None

		return theRet

	def allLoops(self, srcNode):
		"""
		see: https://stackoverflow.com/questions/54283289/how-to-extract-all-paths-starting-from-and-ending-at-same-node
		"""
		print('=== allLoops() from node:', srcNode, type(srcNode), 'Please wait ...')

		# check if srcNode/dstNode is valid
		if srcNode>self.slabList.numNodes()-1:
			return None

		self.initSearch('allLoops')

		G = self.slabList.G

		nNodes = len(G.nodes())

		# see: https://stackoverflow.com/questions/54283289/how-to-extract-all-paths-starting-from-and-ending-at-same-node
		node_to_cycles = {}
		tmpIdx = 0
		#for source in G.nodes():
		for source in [srcNode]:
			if tmpIdx % 10 == 0:
				print('    ... node', tmpIdx, 'of', nNodes, 'source:', source)
			paths = []
			for target in G.neighbors(source):
				paths += [l + [source] for l in list(nx.all_simple_paths(G, source=source, target=target)) if len(l) > 2]
			node_to_cycles[source] = paths
			tmpIdx += 1
		print('    len(node_to_cycles):', len(node_to_cycles), len(node_to_cycles[srcNode]))
		#print(node_to_cycles[10])
		#for i in range(10):
		addedCyclesLength = []
		for cycleIdx, cycle in enumerate(node_to_cycles[srcNode]):
			# cycle is a list of nodes that make a loop/cycle
			cycleLen = len(cycle)
			if cycleLen in addedCyclesLength:
				#print('    cycleLen:', cycleLen, 'already in list. cycle:', cycle)
				continue
			#print('adding cycleIdx:', cycleIdx, 'cycleLen:', cycleLen, cycle)
			len3d = 0
			edgeList = []
			for tmpIdx2,(u,v) in enumerate(nx.utils.pairwise(cycle)):
				len3d += G[u][v]['len3d']
				edgeIdx = G[u][v]['edgeIdx']
				edgeList.append(edgeIdx)
			#
			hitDict = self._defaultSearchDict2()
			hitDict['cycleLen3d'] = len3d
			hitDict['cycleLen'] = cycleLen
			hitDict['edgeList'] = edgeList
			hitDict['nodeList'] = cycle
			self.addFound(hitDict)
			addedCyclesLength.append(cycleLen)

		self.finishSearch(verbose=False)
		return self.hitDictList

	"""
	def shortestLoop(self, srcNode):
		'''
		not implemented
		'''
		print('shortestLoop() from node:', srcNode, 'GET RID OF THIS !!!!!!!!!!!!')

		return None

		# check if srcNode/dstNode is valid
		if srcNode>self.slabList.numNodes()-1:
			return None

		self.initSearch('shortestLoop')

		G = self.slabList.G

		cycles = nx.find_cycle(G, srcNode)
		print('    cycles:', cycles)

		# does not work, shortest path is always 1, src==dst
		'''
		shortestPath = nx.shortest_path(G, source=srcNode, target=srcNode)
		print('    shortest loop (nodes):', shortestPath)
		'''

		pathLen = len(cycles)
		edgeList = []
		len3d = 0
		for u,v in nx.utils.pairwise(cycles):
			#print('    edgeIdx:', G[u][v]['edgeIdx'], 'srcNode:', u, 'dstNode:', v, 'diam:', G[u][v]['diam'], 'len3d:', G[u][v]['len3d'])
			len3d += G[u][v]['len3d']
			edgeIdx = G[u][v]['edgeIdx']
			edgeList.append(edgeIdx)
		#
		hitDict = self._defaultSearchDict2()
		hitDict['len3d'] = len3d
		hitDict['pathLen'] = pathLen
		hitDict['edgeList'] = edgeList
		self.addFound(hitDict)

		self.finishSearch(verbose=False)
		return self.hitDictList
	"""

	def allSubgraphs(self):
		"""
		Returns a list of subgraphs

		This was tricky as nx.connected_components returns an unordered set of nodes.
		We can not use them as a sequence with nx.utils.pairwis
		We need to use the G.adj[node] for each node and build up a list of edges
		"""

		print('bSearchAnnotations.allSubgraphs()')
		self.initSearch('allSubgraphs')

		G = self.slabList.G

		for idx, ccNodes in enumerate(nx.connected_components(G)):
			ccNodes = list(ccNodes)
			print('component:', idx, type(ccNodes), ccNodes)

			nNodes = len(ccNodes)

			# nodes are an UNORDERED SET !!!
			edgeList = [] # make sure we do not add edges twice !!!
			len3d = 0
			for node in ccNodes:
				print('    node:', node, 'adj:', G.adj[node])
				for k, v in G.adj[node].items():
					edgeIdx = v['edgeIdx']
					if edgeIdx in edgeList:
						continue
					print('        is adjacent to key:', k, 'value:', v)
					len3d += v['len3d']
					edgeList.append(edgeIdx)

			#
			hitDict = self._defaultSearchDict2()
			hitDict['len3d'] = len3d
			hitDict['nNodes'] = nNodes
			hitDict['edgeList'] = edgeList
			hitDict['nodeList'] = ccNodes
			self.addFound(hitDict)

		self.finishSearch(verbose=False)
		return self.hitDictList

		'''
		for idx,cc in enumerate(nx.connected_components(G)):
			# cc is a {set} of nodes
			ccList = list(cc)
			print('    ', type(cc), 'cc:', cc)

			nNodes = len(ccList)
			edgeList = []
			len3d = 0
			for u,v in nx.utils.pairwise(ccList):
				len3d += G[u][v]['len3d']
				edgeIdx = G[u][v]['edgeIdx']
				edgeList.append(edgeIdx)
			#
			hitDict = self._defaultSearchDict2()
			hitDict['len3d'] = len3d
			hitDict['nNodes'] = nNodes
			hitDict['edgeList'] = edgeList
			hitDict['nodeList'] = ccList
			self.addFound(hitDict)

		self.finishSearch(verbose=False)
		return self.hitDictList
		'''

	def allPaths(self, nodes):
		print('searching all paths between two nodes')
		srcNode = nodes[0]
		dstNode = nodes[1]
		print('bSearchAnnotations.allPaths() srcNode:', srcNode, 'dstNode:', dstNode)

		# check if srcNode/dstNode is valid
		if srcNode>self.slabList.numNodes()-1 or dstNode>self.slabList.numNodes()-1:
			return None

		self.initSearch('allPaths')

		G = self.slabList.G

		allSimplePaths = nx.all_simple_paths(G, source=srcNode, target=dstNode)
		#print('numPath:', len(list(allSimplePaths)))

		for path in allSimplePaths:
			# path is a list of nodes
			pathLen = len(path)
			edgeList = []
			len3d = 0
			for u,v in nx.utils.pairwise(path):
				#print('    edgeIdx:', G[u][v]['edgeIdx'], 'srcNode:', u, 'dstNode:', v, 'diam:', G[u][v]['diam'], 'len3d:', G[u][v]['len3d'])
				len3d += G[u][v]['len3d']
				edgeIdx = G[u][v]['edgeIdx']
				edgeList.append(edgeIdx)
			#
			hitDict = self._defaultSearchDict2()
			hitDict['len3d'] = len3d
			hitDict['pathLen'] = pathLen
			hitDict['edgeList'] = edgeList
			hitDict['nodeList'] = path
			self.addFound(hitDict)

		self.finishSearch(verbose=False)
		return self.hitDictList

	def shortestPath(self, nodes):
		srcNode = nodes[0]
		dstNode = nodes[1]
		print('bSearchAnnotations.shortestPath() searching shortest path between nodes srcNode:', srcNode, 'dstNode:', dstNode)

		# check if srcNode/dstNode is valid
		if srcNode>self.slabList.numNodes()-1 or dstNode>self.slabList.numNodes()-1:
			return None

		self.initSearch('shortestPath')

		G = self.slabList.G

		'''
		allSimplePaths = nx.all_simple_paths(G, source=srcNode, target=dstNode)
		print('number of simple paths:', len(list(allSimplePaths)))
		'''

		shortestPath = nx.shortest_path(G, source=srcNode, target=dstNode)
		print('    shortest path (nodes):', shortestPath)
		edgeList = []
		len3d = 0
		for u,v in nx.utils.pairwise(shortestPath):
			print('    edgeIdx:', G[u][v]['edgeIdx'], 'srcNode:', u, 'dstNode:', v, 'diam:', G[u][v]['diam'], 'len3d:', G[u][v]['len3d'])
			len3d += G[u][v]['len3d']
			edgeIdx = G[u][v]['edgeIdx']
			edgeList.append(edgeIdx)
		hitDict = self._defaultSearchDict2()
		hitDict['pathLen3d'] = len3d
		hitDict['pathLen'] = len(edgeList)
		hitDict['edgeList'] = edgeList
		self.addFound(hitDict)

		self.finishSearch(verbose=False)
		return self.hitDictList

	def allDeadEnds(self):
		"""
		"""
		print('searching for dead end edges')
		self.initSearch('allDeadEnds')

		for edgeIdx, edgeDict in enumerate(self.slabList.edgeIter()):
			#
			preNode = edgeDict['preNode']
			nEdgesPre = self.slabList.getNode(preNode)['nEdges']
			#
			postNode = edgeDict['postNode']
			nEdgesPost = self.slabList.getNode(postNode)['nEdges']

			if nEdgesPre==1 or nEdgesPost==1:
				hitDict = self._defaultSearchDict()
				hitDict['edge1'] = int(edgeIdx)
				self.addFound(hitDict)

		self.finishSearch(verbose=False)
		return self.hitDictList

	def searchCloseSlabs(self, thresholdDist=10, limitHits=100):
		def getJoiningSlabs(edgeDict):
			edgeIdx = edgeDict['idx']
			slabList = edgeDict['slabList']
			edgeList = [edgeIdx] # edges to not consider
			# pre
			preNode = edgeDict['preNode']
			for edgeIdx2 in self.slabList.getNode(preNode)['edgeList']:
				if edgeIdx2 in edgeList:
					continue
				innerSlabList = self.slabList.getEdgeSlabList(edgeIdx2)
				slabList.extend(innerSlabList)
				edgeList.append(edgeIdx2)
			# post
			postNode = edgeDict['postNode']
			for edgeIdx2 in self.slabList.getNode(postNode)['edgeList']:
				if edgeIdx2 in edgeList:
					continue
				innerSlabList = self.slabList.getEdgeSlabList(edgeIdx2)
				slabList.extend(innerSlabList)
				edgeList.append(edgeIdx2)
			return slabList

		try:
			numHits = 0
			pairedSLabs = [None] * self.slabList.numSlabs() #
			for edgeIdx1, edgeDict1 in enumerate(self.slabList.edgeIter()):
				if numHits > limitHits:
					continue
				joiningSlabList = getJoiningSlabs(edgeDict1)
				#print('edgeIdx1:', edgeIdx1, 'joiningSlabList:', joiningSlabList)
				slabList1 = self.slabList.getEdgeSlabList(edgeIdx1)
				for slab1 in slabList1:
					if numHits > limitHits:
						continue
					if pairedSLabs[slab1] is not None: continue
					x1,y1,z1 = self.slabList.getSlab_xyz(slab1)
					for edgeIdx2, edgeDict2 in enumerate(self.slabList.edgeIter()):
						if numHits > limitHits:
							continue
						if edgeIdx1 == edgeIdx2:
							continue
						slabList2 = self.slabList.getEdgeSlabList(edgeIdx2)
						for slab2 in slabList2:
							if slab2 in joiningSlabList:
								continue
							if pairedSLabs[slab2] is not None: continue
							x2,y2,z2 = self.slabList.getSlab_xyz(slab2)
							dist = bimpy.util.euclideanDistance(x1,y1,z1, x2,y2,z2)
							if dist < thresholdDist:
								print('numHits:', numHits, 'dist:', dist, 'edgeIdx1:', edgeIdx1, 'slab1:', slab1, 'edgeIdx2:', edgeIdx2, 'slab2:', slab2)
								numHits += 1
								pairedSLabs[slab1] = slab2
								pairedSLabs[slab2] = slab1
								hitDict = self._defaultSearchDict2()
								hitDict['dist'] = round(dist,2)
								hitDict['edge1'] = int(edgeIdx1)
								hitDict['slab1'] = int(slab1)
								hitDict['edge2'] = int(edgeIdx2)
								hitDict['slab2'] = int(slab2)
								self.addFound(hitDict)
								#
								continue # once we find a single slab on edgeIdx2, stop searching
						#
			#
		except (KeyboardInterrupt) as e:
			pass

		self.finishSearch(verbose=False)
		return self.hitDictList

	def searchCloseNodes(self, thresholdDist=10):

		self.initSearch('searchCloseNodes')

		pairedNodes = [None] * self.slabList.numNodes() #

		for nodeIdx1, nodeDict1 in enumerate(self.slabList.nodeIter()):
			if pairedNodes[nodeIdx1] is not None:
				continue

			x1,y1,z1 = self.slabList.getNode_xyz(nodeIdx1)
			for nodeIdx2, nodeDict2 in enumerate(self.slabList.nodeIter()):
				if nodeIdx1 == nodeIdx2:
					continue
				x2,y2,z2 = self.slabList.getNode_xyz(nodeIdx2)
				dist = bimpy.util.euclideanDistance(x1,y1,z1, x2,y2,z2)
				if dist < thresholdDist:
					pairedNodes[nodeIdx2] = nodeIdx1
					#
					hitDict = self._defaultSearchDict2()
					hitDict['dist'] = round(dist,2)
					hitDict['node1'] = int(nodeIdx1)
					hitDict['nEdges1'] = int(nodeDict1['nEdges'])
					hitDict['node2'] = int(nodeIdx2)
					hitDict['nEdges2'] = int(nodeDict2['nEdges'])
					self.addFound(hitDict)
		self.finishSearch(verbose=False)
		return self.hitDictList

	def searchBigGaps(self, thresholdDist=10):
		""" search edges for sequential slabs that are far apart.
		Edges that have gaps
		"""

		self.initSearch('searchBigGaps')

		for edgeIdx, edge in enumerate(self.slabList.edgeIter()):
			slabList = edge['slabList']
			nSLab = len(slabList)
			for edgeSlabIdx,slabIdx in enumerate(slabList):
				if edgeSlabIdx > 0:
					x, y, z = self.slabList.getSlab_xyz(slabIdx)
					dist = bimpy.util.euclideanDistance(xLast,yLast,zLast, x,y,z)
					if dist > thresholdDist:
						hitDict = self._defaultSearchDict2()
						hitDict['dist'] = round(dist,2)
						hitDict['edge1'] = int(edgeIdx)
						hitDict['slab1'] = int(slabIdx)
						hitDict['nslab'] = nSLab
						hitDict['len3d'] = edge['Len 3D']
						hitDict['tort'] = edge['Tort']
						self.addFound(hitDict)
				xLast, yLast, zLast = self.slabList.getSlab_xyz(slabIdx)

		self.finishSearch(verbose=False)
		return self.hitDictList

	def searchDeadEnd2(self, thresholdDist=10):
		"""
		Search edges that have a dead end near another node
		"""
		self.initSearch('searchDeadEnd2')

		print('thresholdDist:', thresholdDist)

		pairedNodes = [None] * self.slabList.numNodes() #

		for edgeIdx, edgeDict in enumerate(self.slabList.edgeIter()):
			preNode = edgeDict['preNode']
			postNode = edgeDict['postNode']

			if preNode is None or postNode is None:
				print('error searchDeadEnd2() got none pre/post node at edge idx:', edgeIdx)
				continue

			# only consider source dead end nodes (nEdges == 1)
			#pre
			doPre = False
			if pairedNodes[preNode] is None:
				nEdgesPre = self.slabList.getNode(preNode)['nEdges']
				doPre = nEdgesPre == 1
				xPre, yPre, zPre = self.slabList.getNode_xyz(preNode)

			# post
			doPost = False
			if pairedNodes[postNode] is None:
				nEdgesPost = self.slabList.getNode(postNode)['nEdges']
				doPost = nEdgesPost == 1
				xPost, yPost, zPost = self.slabList.getNode_xyz(postNode)

			for nodeIdx, nodeDict in enumerate(self.slabList.nodeIter()):
				# consider all target nodes
				x2, y2, z2 = self.slabList.getNode_xyz(nodeIdx)

				# pre
				if doPre and nodeIdx != preNode:
					dist = bimpy.util.euclideanDistance(xPre,yPre,zPre,x2,y2,z2)
					if dist < thresholdDist:
						# hit
						#pairedNodes[preNode] = nodeIdx
						pairedNodes[nodeIdx] = preNode
						hitDict = self._defaultSearchDict2()
						hitDict['dist'] = round(dist,2)
						hitDict['node1'] = preNode
						hitDict['nEdges1'] = nEdgesPre # will always be 1
						hitDict['node2'] = nodeIdx
						hitDict['nEdges2'] = self.slabList.getNode(preNode)['nEdges']
						self.addFound(hitDict)
				# post
				if doPost and nodeIdx != postNode:
					dist = bimpy.util.euclideanDistance(xPost,yPost,zPost,x2,y2,z2)
					if dist < thresholdDist:
						# hit
						#pairedNodes[postNode] = nodeIdx
						pairedNodes[nodeIdx] = postNode
						hitDict = self._defaultSearchDict2()
						hitDict['dist'] = round(dist,2)
						hitDict['node1'] = postNode
						hitDict['nEdges1'] = nEdgesPost # will always be 1
						hitDict['node2'] = nodeIdx
						hitDict['nEdges2'] = self.slabList.getNode(postNode)['nEdges']
						self.addFound(hitDict)

		self.finishSearch(verbose=False)
		return self.hitDictList

	def searchDeadEnd(self, thresholdDist=10):
		"""
		Search edges that have a dead end near another point in the tracing
		- A dead end of an edge is when preNode or postNode is None
		- exclude the edge we are searching
		- edge dead end are end of edge without a preNOde/dstNode

		This is inneficient
		"""

		print('searching for dead end edges near other slabs')

		self.initSearch('searchDeadEnd')

		print('thresholdDist:', thresholdDist)

		nSlabs = self.slabList.numSlabs()

		foundEdgeList = []
		for edgeIdx, edgeDict in enumerate(self.slabList.edgeIter()):
			preNode = edgeDict['preNode']
			postNode = edgeDict['postNode']

			if preNode is None or postNode is None:
				print('error searchDeadEnd() got none pre/post node at edge idx:', edgeIdx)
				continue

			firstSlab = edgeDict['slabList'][0]
			nEdgesPre = self.slabList.getNode(preNode)['nEdges']
			xPre, yPre, zPre = self.slabList.getNode_xyz(preNode)

			lastSlab = edgeDict['slabList'][-1]
			nEdgesPost = self.slabList.getNode(postNode)['nEdges']
			xPost, yPost, zPost = self.slabList.getNode_xyz(postNode)

			for j in range(nSlabs):
				if self.slabList.edgeIdx[j] == edgeIdx:
					continue # skip

				x2 = self.slabList.x[j]
				y2 = self.slabList.y[j]
				z2 = self.slabList.z[j]

				postEdgeIdx = self.slabList.edgeIdx[j]
				if np.isnan(postEdgeIdx) or postEdgeIdx in foundEdgeList:
					continue

				#if preNode is None:
				if nEdgesPre == 1:
					self.addSearched()
					dist = bimpy.util.euclideanDistance(xPre,yPre,zPre,x2,y2,z2)
					if dist < thresholdDist:
						# hit !!!
						#print('preNode slab', firstSlab, 'of edge', edgeIdx, 'is close to slab', j)
						foundEdgeList.append(postEdgeIdx)
						hitDict = self._defaultSearchDict()
						hitDict['dist'] = round(dist,2)
						hitDict['node1'] = int(preNode)
						hitDict['edge1'] = int(edgeIdx)
						hitDict['slab1'] = int(firstSlab)
						if np.isnan(postEdgeIdx):
							hitDict['edge2'] = 'None'
						else:
							hitDict['edge2'] = int(postEdgeIdx)
						hitDict['slab2'] = j
						self.addFound(hitDict)

				#if postNode is None:
				if nEdgesPost == 1:
					self.addSearched()
					dist = bimpy.util.euclideanDistance(xPost,yPost,zPost,x2,y2,z2)
					if dist < thresholdDist:
						# hit !!!
						#print('postNode slab', lastSlab, 'of edge', edgeIdx, 'is close to slab', j)
						foundEdgeList.append(postEdgeIdx)
						hitDict = self._defaultSearchDict()
						hitDict['dist'] = round(dist,2)
						hitDict['node1'] = int(postNode)
						hitDict['edge1'] = int(edgeIdx)
						hitDict['slab1'] = int(lastSlab)
						if np.isnan(postEdgeIdx):
							hitDict['edge2'] = 'None'
						else:
							hitDict['edge2'] = int(postEdgeIdx)
						hitDict['slab2'] = j
						self.addFound(hitDict)

		self.finishSearch(verbose=False)
		return self.hitDictList

if __name__ == '__main__':
	path = '/Users/cudmore/box/Sites/DeepVess/data/20191017/blur/20191017__0001_z.tif'
	stack = bimpy.bStack(path, loadImages=False)

	mySearch = bSearchAnnotations(stack.slabList)
	mySearch.searchDeadEnd()
