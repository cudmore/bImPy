# Robert Cudmore
# 20200223

"""
General purpose table to display (nodes, edges, search results)

type: from (nodes, edges, search)
listOfDict: from nodeList, edgeList, searchList
"""

from qtpy import QtGui, QtCore, QtWidgets

import bimpy

class bTableWidget2(QtWidgets.QTableWidget):

	# signals
	selectRowSignal = QtCore.Signal(object) # object can be a dict

	def __init__(self, type, listOfDict, parent=None):
		"""
		type: ('nodes', 'edges', 'search')
		"""
		super(bTableWidget2, self).__init__(parent)

		if type not in {'nodes', 'edges', 'search'}:
			print('error: bTableWidget2 type is incorrect:', type)
			return

		self._type = type # from ('nodes', 'edges', 'search')

		self.stopSelectionPropogation = False

		self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

		# signals/slots
		#self.myNodeTableWidget.cellClicked.connect(self.on_clicked_row)
		self.itemSelectionChanged.connect(self.on_clicked_row)
		self.itemPressed.connect(self.on_clicked_row)

		header = self.horizontalHeader()
		header.sectionClicked.connect(self.on_click_header)

		self.populate(listOfDict)

	def populate(self, newDictList):

		print('bTableWidget2.populate()')

		self.clear() # need this otherwise populate() takes a SUPER long time

		self.headerLabels = []

		if len(newDictList) == 0:
			print('error: bTableWidget2.populate() type:', self._type, 'got 0 length dict list?')
			return

		# headers
		firstDict = newDictList[0]
		print('    firstDict:', firstDict)
		for k in firstDict.keys():
			self.headerLabels.append(k)
		#print('bTableWidget2.populate.headerLabels:', self.headerLabels)

		self.setColumnCount(len(self.headerLabels))
		self.setHorizontalHeaderLabels(self.headerLabels)

		#print('    self.headerLabels:', self.headerLabels)

		# rows
		numRows = len(newDictList)
		print('    bTableWidget2.populate() adding num rows:', numRows, self._type)
		self.setRowCount(numRows)
		for idx, editDict in enumerate(newDictList):
			for colIdx, header in enumerate(self.headerLabels):
				myString = str(editDict[header])
				item = QtWidgets.QTableWidgetItem()
				item.setData(QtCore.Qt.EditRole, editDict[header])
				#print('    idx:', idx, 'colIdx:', colIdx, 'editDict[header]:', editDict[header])
				'''
				if header == 'nEdges':
					print('nEdges', editDict[header], type(editDict[header]))
				'''
				self.setItem(idx, colIdx, item)

		#print('    2')

		# resize headers based on content
		header = self.horizontalHeader()
		for idx, label in enumerate(self.headerLabels):
			header.setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeToContents)

		#self.repaint()

		#print('bTableWidget2.populate() done')

	def mySelectRow(self, rowIdx=None, itemIdx=None):
		"""
		rowIdx: The row in the table
		itemIdx: value of 'idx' key from dict
		"""
		if rowIdx is None:
			rowIdx = self._findRow(theIdx=itemIdx)
		self.stopSelectionPropogation = True
		self.selectRow(rowIdx)
		self.repaint()

	def slot_select(self, myEvent):
		print('bTableWidget2.slot_select() myEvent:', myEvent)
		if myEvent.eventType == 'select node' and self._type == 'nodes':
			nodeIdx = myEvent.nodeIdx
			if nodeIdx is None:
				return # happens on user key 'esc'
			self.mySelectRow(itemIdx=nodeIdx)

		elif myEvent.eventType == 'select edge' and self._type == 'edges':
			edgeIdx = myEvent.edgeIdx
			if edgeIdx is None:
				return # happens on user key 'esc'
			self.mySelectRow(itemIdx=edgeIdx)

	def slot_updateTracing(self, myEvent):
		"""
		respond to edits
		"""
		print('bTableWidget2.slot_updateTracing() self._type:', self._type, 'myEvent.eventType:', myEvent.eventType)
		print('    myEvent.nodeDict:', myEvent.nodeDict)
		print('    myEvent.edgeDict:', myEvent.edgeDict)

		if myEvent.eventType == 'newNode' and self._type == 'nodes':
			newRowIdx = self.appendRow(myEvent.nodeDict)
			self.mySelectRow(rowIdx=newRowIdx)
			self.repaint()

		elif myEvent.eventType == 'newEdge' and self._type == 'nodes':
			srcNodeDict = myEvent.srcNodeDict
			self.setRow(srcNodeDict)
			dstNodeDict = myEvent.dstNodeDict
			self.setRow(dstNodeDict)
			self.repaint()

		elif myEvent.eventType == 'newEdge' and self._type == 'edges':
			newRowIdx = self.appendRow(myEvent.edgeDict)
			self.mySelectRow(rowIdx=newRowIdx)
			self.repaint()

		elif myEvent.eventType == 'deleteNode' and self._type == 'nodes':
			self.deleteRow(myEvent.nodeDict)
			self.repaint()

		elif myEvent.eventType == 'deleteEdge' and self._type == 'edges':
			self.deleteRow(myEvent.edgeDict)
			self.repaint()

	def appendRow(self, theDict):
		"""
		append
		"""
		print('bTableWidget2.addRow() theDict:', theDict)
		rowIdx = self.rowCount()
		self.insertRow(rowIdx)

		rowItems = self._itemFromDict(theDict)
		for colIdx, item in enumerate(rowItems):
			self.setItem(rowIdx, colIdx, item)

		return rowIdx

	def deleteRow(self, theDict):
		"""
		todo: need to decrement remaining 'idx'
		"""
		print('bTableWidget2.deleteRow() theDict:', theDict)
		self.stopSelectionPropogation = True
		rowIdx = self._findRow(theDict)
		if rowIdx is None:
			print('   !!! !!! THIS IS A BUG: bAnnotationTable.deleteRow() rowIdx', rowIdx)
			print(' ')
		else:
			self.removeRow(rowIdx)

	def setRow(self, rowDict):
		"""
		Assume: rowDict['Idx']
		"""
		theIdx = rowDict['idx']
		for row in range(self.rowCount()):
			idxItem = self.item(row, 0) # 0 is idx column
			myIdxStr = idxItem.text()
			if myIdxStr == str(theIdx):
				print('   setRow() theIdx:', theIdx, rowDict)
				rowItems = self._itemFromDict(rowDict)
				for colIdx, item in enumerate(rowItems):
					self.setItem(row, colIdx, item)

	def _findRow(self, theIdx=None, theDict=None):
		theRet = None
		if theIdx is None:
			theIdx = theDict['idx']
		for row in range(self.rowCount()):
			idxItem = self.item(row, 0) # 0 is idx column
			myIdxStr = idxItem.text()
			if myIdxStr == str(theIdx):
				theRet = row
				break
		return theRet

	def _itemFromDict(self, theDict):
		rowItems = []
		for colIdx, header in enumerate(self.headerLabels):
			item = QtWidgets.QTableWidgetItem()
			try:
				myString = str(theDict[header])
				item.setData(QtCore.Qt.EditRole, myString)
			except (KeyError) as e:
				pass
			rowItems.append(item)
		return rowItems

	def _getColumnIdx(self, colStr):
		colIdx = None
		try:
			colIdx = self.headerLabels.index(colStr)
		except (ValueError) as e:
			print('error: bTableWidget2._getColumnIdx() did not find col:', colStr, 'in self.headerLabels')
		return colIdx

	def keyPressEvent(self, event):
		super(bTableWidget2, self).keyPressEvent(event)
		key = event.key()
		print('=== on_keypress_node() key:', event.text())
		if key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			# reselect node
			self.on_clicked_row()
		else:
			event.setAccepted(False)

	def on_click_header(self, col):
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		print('on_click_header() col:', col, 'isShift:', isShift)
		if isShift:
			self.sortItems(col, order=QtCore.Qt.DescendingOrder)
		else:
			self.sortItems(col)

	def on_clicked_row(self):
		#print('on_clicked_node()')
		row = self.currentRow()
		myItem = self.item(row, 0) # 0 is idx column
		myIdx = myItem.text()
		if myIdx=='':
			return
		myIdx = int(myIdx)

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier

		# emit a signal
		if self.stopSelectionPropogation:
			self.stopSelectionPropogation = False
		else:
			print('=== bTableWidget2.on_clicked_row() row:', row, 'myIdx:', myIdx, isShift)
			if self._type == 'nodes':
				myEvent = bimpy.interface.bEvent('select node', nodeIdx=myIdx, snapz=True, isShift=isShift)
				colIdx = self._getColumnIdx('z')
				myItem = self.item(row, colIdx)
				myEvent._sliceIdx = int(float(myItem.text()))
				print('   emit myEvent:', myEvent)
				self.selectRowSignal.emit(myEvent)
			elif self._type == 'edges':
				myEvent = bimpy.interface.bEvent('select edge', edgeIdx=myIdx, snapz=True, isShift=isShift)
				colIdx = self._getColumnIdx('z')
				myItem = self.item(row, colIdx)
				myEvent._sliceIdx = int(float(myItem.text()))
				self.selectRowSignal.emit(myEvent)
			elif self._type == 'search':
				#
				colIdx = self._getColumnIdx('edge1')
				myItem = self.item(row, colIdx) # 0 is idx column
				edge1 = int(myItem.text())
				#
				colIdx = self._getColumnIdx('edge2')
				myItem = self.item(row, colIdx) # 0 is idx column
				edge2 = int(myItem.text())
				edgeList = [edge1, edge2]
				#
				myEvent = bimpy.interface.bEvent('select edge list', edgeList=edgeList, snapz=True, isShift=isShift)
				self.selectRowSignal.emit(myEvent)

if __name__ == '__main__':
	import sys
	app = QtWidgets.QApplication(sys.argv)

	dictList = []

	dict = {}
	dict['idx'] = 0
	dict['x'] = 10
	dict['y'] = 20
	dict['z'] = 1
	dictList.append(dict)

	dict = {}
	dict['idx'] = 1
	dict['x'] = 30
	dict['y'] = 40
	dict['z'] = 2
	dictList.append(dict)

	dict = {}
	dict['idx'] = 2
	dict['x'] = 50
	dict['y'] = 60
	dict['z'] = 3
	dictList.append(dict)

	type = 'search'
	btw2 = bTableWidget2(type, dictList)
	btw2.show()

	dict['idx'] = 1
	dict['x'] = 300
	dict['y'] = 400
	dict['z'] = 20
	btw2.setRow(dict)

	dict = {}
	dict['idx'] = 3
	dict['x'] = 70
	dict['y'] = 80
	dict['z'] = 4
	btw2.appendRow(dict)

	btw2.deleteRow(dictList[0])

	# load a stack and populate with editDictList
	from bimpy.interface import bStackBrowser
	path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/20191017/20191017__0001.tif'
	myBrowser = bStackBrowser()
	myBrowser.appendStack(path)
	myBrowser.showStackWindow(path)

	editDictList = myBrowser.myStackList[0].mySimpleStack.slabList.editDictList
	#print(editDictList)
	btw2.populate(editDictList)

	sys.exit(app.exec_())
