#20200125

#from PyQt5 import QtCore
from qtpy import QtCore

class bEvent(QtCore.QObject):

	#
	_verboseSlots = False # if true then have slots print when they get called

	def __init__(self, eventType, nodeIdx=None, edgeIdx=None, slabIdx=None,
			edgeList=None,
			nodeDict=None, edgeDict=None, snapz=False, isShift=False):
		super(bEvent, self).__init__()
		self._eventType = eventType
		self._nodeIdx = nodeIdx
		self._edgeIdx = edgeIdx
		self._slabIdx = slabIdx

		self._nodeDict = nodeDict
		self._edgeDict = edgeDict

		self._srcNodeDict = None
		self._dstNodeDict = None

		#self._objectPointer = None # abb caiman and roi

		# not sure what is happening here?
		# When I construct bEvent a second time, we get (edgeList not equal to None) ???
		# print('bEvent.__init__() with edgeList:', edgeList)
		if edgeList is None:
			self._edgeList = []
		else:
			self._edgeList = edgeList # list of int of edges
		self._nodeList = [] # abb 20200320
		self._colorList = []

		self.contrastDict = {}
		#self._minContrast = None
		#self._maxContrast = None

		self._sliceIdx = None

		self._snapz = snapz
		self._isShift = isShift

	def __str__(self):
		retStr = 'bEvent eventType:' + str(self.eventType) + \
			' nodeIdx:' + str(self.nodeIdx) + \
			' edgeIdx:' + str(self.edgeIdx) + \
			' slabIdx:' + str(self.slabIdx) + \
			' len(edgeList):' + str(len(self.edgeList)) + \
			' len(nodeList):' + str(len(self.nodeList))
		return retStr

	@property
	def eventType(self):
		return self._eventType

	@property
	def nodeIdx(self):
		return self._nodeIdx

	@property
	def edgeIdx(self):
		return self._edgeIdx

	@property
	def slabIdx(self):
		return self._slabIdx

	@property
	def nodeList(self):
		return self._nodeList

	@property
	def edgeList(self):
		return self._edgeList

	@property
	def colorList(self):
		return self._colorList

	@property
	def nodeDict(self):
		return self._nodeDict

	@property
	def edgeDict(self):
		return self._edgeDict

	@property
	def srcNodeDict(self):
		return self._srcNodeDict

	@property
	def dstNodeDict(self):
		return self._dstNodeDict

	@property
	def minContrast(self):
		return self._minContrast

	@property
	def maxContrast(self):
		return self._maxContrast

	@property
	def sliceIdx(self):
		return self._sliceIdx

	@property
	def snapz(self):
		return self._snapz

	@property
	def isShift(self):
		return self._isShift

	def printSlot(self, str):
		if self._verboseSlots:
			print('    ', str, self)
