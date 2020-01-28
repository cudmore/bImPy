#20200125

from PyQt5 import QtCore

class bEvent(QtCore.QObject):
	def __init__(self, eventType, nodeIdx=None, edgeIdx=None, slabIdx=None,
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

		self._snapz = snapz
		self._isShift = isShift

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
	def snapz(self):
		return self._snapz

	@property
	def isShift(self):
		return self._isShift
