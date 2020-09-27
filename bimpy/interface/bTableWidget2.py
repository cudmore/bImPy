# Robert Cudmore
# 20200223

"""
General purpose table to display (nodes, edges, search results)

type: from (nodes, edges, search)
listOfDict: from nodeList, edgeList, searchList
"""

import json

import numpy as np

from qtpy import QtGui, QtCore, QtWidgets

import bimpy

######################################################
class bTableWidget2(QtWidgets.QTableWidget):

	# signals
	selectRowSignal = QtCore.Signal(object) # object can be a dict

	def __init__(self, type, listOfDict, parent=None):
		"""
		type: ('nodes', 'edges', 'node search', 'edge search')
		"""
		super(bTableWidget2, self).__init__(parent)

		self.mainWindow = parent

		# todo: remove this, I am now explicitly deriving. For example, see bAnnotationTableWidget
		if type not in {'nodes', 'edges', 'node search', 'edge search', 'annotations'}:
			print('error: bTableWidget2 type is incorrect:', type)
			return

		self._type = type # from ('nodes', 'edges', 'search')

		# set font size of table (default seems to be 13 point)
		fnt = self.font()
		#print('  original table font size:', fnt.pointSize())
		fnt.setPointSize(12)
		self.setFont(fnt)

		self._rowHeight = 12
		#self.setRowHeight(12)

		# getting error: AttributeError: 'PyQt5.QtCore.pyqtSignal' object has no attribute 'connect'
		'''
		if type == 'node search':
			print('bTableWidget2() connecting to bSearchAnnotations.searchFinishedSignal')
			bimpy.bSearchAnnotations.searchFinishedSignal.connect(self.slot_SearchFinished)
		'''

		# I want a visual iterator to traverse a path/loop of edges
		# this will require a second search in bStackView and bNapari
		self.edgeIterIndex = None

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
		header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		header.customContextMenuRequested.connect(self.contextMenuEvent_Header)

		#self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		#self.customContextMenuRequested.connect(self.handleItemContextMenu)

		self.populate(listOfDict)

	def hideColumns(self, columnList):
		"""
		hide a list of columns

		see: https://stackoverflow.com/questions/25366830/qtableview-column-control-to-facilitate-show-hide-columns
		"""
		nColHeader = self.horizontalHeader().count()
		for colIdx in range(nColHeader):
			headerItem = self.horizontalHeaderItem(colIdx)
			headerItemText = headerItem.text()
			if headerItemText in columnList:
				#print('    hideColumns() hiding type:', self._type, 'colIdx:', colIdx, headerItemText)
				self.horizontalHeader().hideSection(colIdx)
			else:
				self.horizontalHeader().showSection(colIdx)

	def populate(self, newDictList):

		#print('bTableWidget2.populate() type:', self._type)

		self.clear() # need this otherwise populate() takes a SUPER long time

		self.headerLabels = []

		numRows = len(newDictList)

		if numRows == 0:
			#print('    warning: bTableWidget2.populate() type:', self._type, 'adding num rows:', numRows, self._type)
			return

		# headers
		firstDict = newDictList[0]
		for k in firstDict.keys():
			#print('populate() headerLabels.append k:', k)
			self.headerLabels.append(k)

		#print('setColumnCount to len(self.headerLabels)', len(self.headerLabels))
		self.setColumnCount(len(self.headerLabels))
		self.setHorizontalHeaderLabels(self.headerLabels)

		# show/hide
		#self.setHorizontalHeaderLabels.hideSection(sectionIdx)

		# rows
		print('    bTableWidget2.populate() adding type:', self._type, 'num rows:', numRows)
		self.setRowCount(numRows)
		for rowIdx, editDict in enumerate(newDictList):
			rowItems = self._itemFromDict(editDict)
			for colIdx, item in enumerate(rowItems):
				self.setRowHeight(rowIdx, self._rowHeight)
				self.setItem(rowIdx, colIdx, item)

		# resize headers based on content
		header = self.horizontalHeader()
		for idx, label in enumerate(self.headerLabels):
			header.setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeToContents)

		self.repaint()

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
		# search does not auto select
		myEvent.printSlot('bTableWidget2.slot_select()')

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

		else:
			myEvent.printSlot('bTableWidget.slot_select() did not respond')
			#print('    slot_select() did not respond to myEvent.eventType:', myEvent.eventType)

	def slot_updateTracing(self, myEvent):
		"""
		respond to edits
		"""

		myEvent.printSlot('bTableWidget2.slot_updateTracing()')

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

		elif myEvent.eventType == 'newSlab' and self._type == 'edges':
			self.setRow(myEvent.edgeDict)
			self.repaint()

		elif myEvent.eventType == 'deleteNode' and self._type == 'nodes':
			#self.deleteRow(myEvent.nodeDict)
			self.deleteRowByIndex(myEvent.nodeIdx)
			self.repaint()

		elif myEvent.eventType == 'deleteEdge' and self._type == 'edges':
			#self.deleteRow(myEvent.edgeDict)
			self.deleteRowByIndex(myEvent.edgeIdx)
			self.repaint()

		elif myEvent.eventType == 'updateNode' and self._type == 'nodes':
			self.setRow(myEvent.nodeDict)

		elif myEvent.eventType == 'updateEdge' and self._type == 'edges':
			self.setRow(myEvent.edgeDict)

		else:
			myEvent.printSlot('bTableWidget2.slot_updateTracing() case not taken')

	def slot_newSearchHit(self, searchType, newHitDict):
		print('bTableWidget2.slot_newSearchHit()')
		print('  searchType:', searchType)
		print('  newHitDict:', newHitDict)

	def slot_SearchFinished(self, searchType, hitDictList):
		print('bTableWidget2.slot_SearchFinished()')
		print('  searchType:', searchType)
		print('  len(hitDictList):', len(hitDictList))
		'''
		self.editTable.populate(self.hitDictList)
		self.editTable._type = 'edge search'
		'''
		self._type = searchType
		self.populate(hitDictList)

	def appendRow(self, theDict):
		"""
		append
		"""
		rowIdx = self.rowCount()
		print('bTableWidget2.appendRow()', self._type, 'rowIdx:', rowIdx, 'theDict:', theDict)
		if rowIdx == 0:
			self.populate([theDict])
		else:
			self.insertRow(rowIdx)

			rowItems = self._itemFromDict(theDict)
			for colIdx, item in enumerate(rowItems):
				self.setRowHeight(rowIdx, self._rowHeight)
				self.setItem(rowIdx, colIdx, item)

			self.repaint()

		return rowIdx

	def deleteRowByIndex(self, deleteRowIdx):
		"""
		this is super freaking sloppy
		"""
		print('bTableWidget2.deleteRowByIndex()', self._type, 'deleteRowIdx:', deleteRowIdx)

		self.stopSelectionPropogation = True

		rowIdx = self._findRow(theIdx=deleteRowIdx, theDict=None)
		if rowIdx is None:
			print('   \n\n\n                    !!! !!! THIS IS A BUG: bTableWidget2.deleteRowByIndex() rowIdx', rowIdx, 'theDict:', theDict)
			print('\n\n\n')
		else:
			self.removeRow(rowIdx)
			# decriment remaining ['idx']
			for row in range(self.rowCount()):
				idx = self.getCellValue_int('idx', row)
				if idx > deleteRowIdx:
					# decriment 'idx' of remaining
					idx -= 1
					item = QtWidgets.QTableWidgetItem()
					myString = str(idx)
					item.setData(QtCore.Qt.EditRole, myString)
					self.setItem(row, 0, item) # assuming col 0 is 'idx' !!!!!!!!!
		#
		self.repaint()

	'''
	def deleteRow(self, theDict):
		"""
		this is super freaking sloppy
		"""
		if theDict is None:
			print('warning: bTableWidget2.deleteRow()', self._type, 'got None dict')
			return
		else:
			print('bTableWidget2.deleteRow()', self._type, 'theDict["idx"]:', theDict['idx'])

		self.stopSelectionPropogation = True
		deletingRowIdx = theDict['idx']
		rowIdx = self._findRow(theDict=theDict)
		if rowIdx is None:
			print('   \n\n\n                    !!! !!! THIS IS A BUG: bTableWidget2.deleteRow() rowIdx', rowIdx, 'theDict:', theDict)
			print('\n\n\n')
		else:
			self.removeRow(rowIdx)
			# todo: decriment remaining ['idx']
			for row in range(self.rowCount()):
				#print('    row:',row)
				idx = self.getCellValue_int('idx', row)
				if idx > deletingRowIdx:
					# decriment 'idx' of remaining
					idx -= 1
					item = QtWidgets.QTableWidgetItem()
					myString = str(idx)
					item.setData(QtCore.Qt.EditRole, myString)
					self.setItem(row, 0, item) # assuming col 0 is 'idx' !!!!!!!!!
	'''

	def setRow(self, rowDict):
		"""
		Assume: rowDict['Idx']
		"""
		theIdx = rowDict['idx']
		for row in range(self.rowCount()):
			idxItem = self.item(row, 0) # 0 is idx column
			myIdxStr = idxItem.text()
			if myIdxStr == str(theIdx):
				#print('    bTableWidget2.setRow()', self._type, 'theIdx:', theIdx, rowDict)
				rowItems = self._itemFromDict(rowDict)
				for colIdx, item in enumerate(rowItems):
					#print('  row:', row, 'col:', colIdx, rowItems)
					self.setItem(row, colIdx, item)
				self.repaint()
				break

	def _findRow(self, theIdx=None, theDict=None):
		#print('_findRow() theIdx:', theIdx, type(theIdx), 'theDict:', theDict, type(theDict))
		theRet = None
		if theIdx is None:
			theIdx = theDict['idx']
		#print('_findRow() looking for theIdx:', type(theIdx))
		nRow = self.rowCount()
		for row in range(nRow):
			#print('    row:', row)
			idxItem = self.item(row, 0) # 0 is idx column
			myIdxStr = idxItem.text()
			myIdxInt = int(myIdxStr)
			#print('    myIdxInt:', myIdxInt, type(myIdxInt))
			#if myIdxStr == str(theIdx):
			if myIdxInt == theIdx:
				theRet = row
				break
		return theRet

	def _itemFromDict(self, theDict):
		myItemRole = QtCore.Qt.DisplayRole #options are (DisplayRole,EditRole)
		rowItems = []
		for colIdx, header in enumerate(self.headerLabels):
			item = QtWidgets.QTableWidgetItem()
			try:
				if isinstance(theDict[header], list):
					item.setData(myItemRole, str(theDict[header]))
				elif isinstance(theDict[header], np.int64):
					item.setData(myItemRole, int(theDict[header]))
				elif isinstance(theDict[header], np.float64):
					item.setData(myItemRole, float(theDict[header]))
				elif isinstance(theDict[header], str):
					item.setData(myItemRole, str(theDict[header]))
				else:
					if theDict[header] is None:
						item.setData(myItemRole, '')
					elif str(theDict[header]) == 'nan':
						item.setData(myItemRole, '')
					else:
						#item.setData(myItemRole, theDict[header])
						item.setData(myItemRole, theDict[header]) # DON'T PUT STR() HERE !!! abb 20200831
				#myString = str(theDict[header])
				#item.setData(QtCore.Qt.EditRole, myString)
			except (KeyError) as e:
				pass
			rowItems.append(item)
		return rowItems

	def _getColumnIdx(self, colStr):
		colIdx = None
		try:
			colIdx = self.headerLabels.index(colStr)
		except (ValueError) as e:
			print('error: bTableWidget2._getColumnIdx() did not find col:', colStr, 'in self.headerLabels:', self.headerLabels)
		return colIdx

	def keyPressEvent(self, event):
		super(bTableWidget2, self).keyPressEvent(event)
		key = event.key()
		print('=== bTableWidget2.keyPressEvent() in', self._type, 'key:', event.text())
		if key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			if self._type == 'edge search':
				if self.edgeIterIndex is None:
					self.edgeIterIndex = 0
				else:
					if key == QtCore.Qt.Key_Left:
						self.edgeIterIndex -= 1 #
						if self.edgeIterIndex < 0:
							self.edgeIterIndex = 0
					elif key == QtCore.Qt.Key_Right:
						self.edgeIterIndex += 1 # this will overflow
			# reselect node
			self.on_clicked_row()

		elif key in [QtCore.Qt.Key_D, QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
			if not self._type in ['nodes', 'edges']:
				return
			objectIdx = self.getCellValue_int('idx') #, row=None):
			if self._type == 'nodes':
				event = {'type':'deleteNode', 'objectType': self._type, 'objectIdx':objectIdx}
			if self._type == 'edges':
				event = {'type':'deleteEdge', 'objectType': self._type, 'objectIdx':objectIdx}
			if self._type == 'edge search':
				event = {'type':'deleteEdge', 'objectType': 'edge', 'objectIdx':objectIdx}
			self.mainWindow.getStackView().myEvent(event)

		elif key in [QtCore.Qt.Key_A]:
			# select all in list
			if self._type == 'edges':
				# analyze edge
				objectIdx = self.getCellValue_int('idx') #, row=None):
				event = {'type':'analyzeEdge', 'objectType': self._type, 'objectIdx':objectIdx}
				self.mainWindow.getStackView().myEvent(event)

			elif self._type == 'edge search':
				# emit a select edge list
				myEvent = bimpy.interface.bEvent('select edge', edgeIdx=None, snapz=True, isShift=False) # using myEvent._edgeList
				nRows = self.rowCount()
				print('    nRows:', nRows, 'myEvent._edgeList:', myEvent._edgeList)
				for row in range(nRows):
					edge1 = self.getCellValue_int('idx', row)
					myEvent._edgeList.append(edge1)
				print('    emit event:', myEvent)
				self.selectRowSignal.emit(myEvent)

		elif key in [QtCore.Qt.Key_Escape]:
			self.mainWindow.signal('cancelSelection')

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

		'''
		mouse_state = self.mainWindow.mainWindow.mouseButtons()
		print('mouse_state:', mouse_state)
		'''

		'''
		if event.button() == QtCore.Qt.RightButton:
			print('bTableWidget2.on_clicked_row() right click !!!')
			self.handleItemContextMenu(row)
			#point = QtCore.QPoint(100,100)
			#self.showRightClickMenu(event.pos())
			#self.mouseReleaseEvent(event)
		'''

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
			print('=== bTableWidget2.on_clicked_row() type:', self._type, 'row:', row, 'myIdx:', myIdx, 'isShift:', isShift)
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

			elif self._type == 'node search':
				#
				node1 = self.getCellValue_int('node1')
				myEvent = bimpy.interface.bEvent('select node', nodeIdx=node1, snapz=True, isShift=isShift)
				print('   emit myEvent:', myEvent)
				self.selectRowSignal.emit(myEvent)

			elif self._type == 'edge search':
				#self.edgeIterIndex = None
				nodeIdx = None
				slabIdx = None
				colorList = []
				edgeList = self.getCellValue('edgeList')
				if edgeList is not None:
					edgeList = json.loads(edgeList)
					if self.edgeIterIndex is not None:
						edgeIdx = edgeList[self.edgeIterIndex]
				else:
					edgeList = []

					# todo: make all edge/node search use idx for object (edge/node) index
					idx = self.getCellValue_int('idx')
					edge1 = self.getCellValue_int('edge1')
					if edge1 is not None:
						edgeList.append(edge1)
						colorList.append('y')
					elif idx is not None:
						edgeList.append(idx)
						colorList.append('y')
					#
					slab = self.getCellValue_int('slab1')
					if slab is not None:
						slabIdx = slab
					#
					node1 = self.getCellValue_int('node1')
					if node1 is not None:
						nodeIdx = node1
					#
					edge2 = self.getCellValue_int('edge2')
					if edge2 is not None:
						edgeList.append(edge2)
						colorList.append('r')
					#
					slab2 = self.getCellValue_int('slab2')
					if slab2 is not None:
						slabIdx2 = slab2
					print('    edge search idx:', idx, 'edge2:', edge2)

				# todo: convert bEvent nodeList to None rather than empty list []
				nodeList = self.getCellValue('nodeList')
				if nodeList is not None:
					nodeList = json.loads(nodeList)
				else:
					nodeList = []
				#
				if len(edgeList) == 1:
					edgeIdx = edgeList[0]
					myEvent = bimpy.interface.bEvent('select edge', edgeIdx=edgeIdx, nodeIdx=None, snapz=True, isShift=isShift)
					print('   emit myEvent:', myEvent)
					self.selectRowSignal.emit(myEvent)
				else:
					myEvent = bimpy.interface.bEvent('select edge list', nodeIdx=nodeIdx, slabIdx=slabIdx, edgeList=edgeList, snapz=True, isShift=isShift)
					myEvent._nodeList = nodeList
					if len(colorList) > 0:
						myEvent._colorList = colorList
					self.selectRowSignal.emit(myEvent)

	def contextMenuEvent_Header(self, pos):
		"""
		Right-click to show and hide columns

		Checked items are being shown

		see: https://stackoverflow.com/questions/11909139/pyqt-table-header-context-menu
		"""
		column = self.horizontalHeader().logicalIndexAt(pos.x())
		print('bTableWidget2.contextMenuEvent_Header() column:', column)

		menu = QtWidgets.QMenu()

		nColHeader = self.horizontalHeader().count()
		for colIdx in range(nColHeader):
			headerItem = self.horizontalHeaderItem(colIdx)
			headerItemText = headerItem.text()
			isHidden = not self.horizontalHeader().isSectionHidden(colIdx) # check those not hidden
			currentAction = QtWidgets.QAction(headerItemText, self, checkable=True, checked=isHidden)
			currentAction.triggered.connect(self.menuActionHandler_header)
			menuAction = menu.addAction(currentAction)

		userAction = menu.exec_(self.mapToGlobal(pos))

	def contextMenuEvent(self, event):
		"""

		for a more advanced example, see
		https://stackoverflow.com/questions/20930764/how-to-add-a-right-click-menu-to-each-cell-of-qtableview-in-pyqt
		"""

		# only allow right-click menu for nodes/edges
		if self._type in ['nodes', 'edges']:
			# ok
			pass
		else:
			return

		row = self.currentRow()
		pos = event.pos()
		print('bTableWidget2.contextMenuEvent() row:', row, pos)

		myType = self.getCellValue('type', row=row)
		if myType is None:
			myType = ''
		#print('    myType:', myType, type(myType))

		# make a popup allowing 'type' to be set
		menu = QtWidgets.QMenu()
		nodeTypes = ['Empty', 'Type 1', 'Type 2', 'Type 3', 'Type 4']
		for nodeType in nodeTypes:
			# make an action
			isChecked = nodeType == myType
			currentAction = QtWidgets.QAction(nodeType, self, checkable=True, checked=isChecked)
			currentAction.setProperty('bobID0', self._type)
			currentAction.setProperty('bobID', 'setType')
			currentAction.triggered.connect(self.menuActionHandler)
			# add to menu
			menuAction = menu.addAction(currentAction)

		menu.addSeparator()

		myIsBad = self.getCellValue('isBad', row=row) # this is a string
		#print('myIsBad:', myIsBad, type(myIsBad))
		if myIsBad == 'True':
			myIsBad = True
		elif myIsBad == 'False':
			myIsBad = False
		else:
			myIsBad = False
		badAction = QtWidgets.QAction('Bad', self, checkable=True, checked=myIsBad)
		badAction.setProperty('bobID0', self._type)
		badAction.setProperty('bobID', 'setIsBad')
		badAction.triggered.connect(self.menuActionHandler)
		menuAction = menu.addAction(badAction)

		userAction = menu.exec_(self.mapToGlobal(pos))
		#print('userAction:', userAction)

	def menuActionHandler_header(self):
		"""
		show/hide columns

		as a lot of this ... this is messy !!!!!!!!!!!!!
		"""
		print('  menuActionHandler_header()', self._type)
		sender = self.sender()
		title = sender.text()
		isChecked = sender.isChecked()
		print('    title:', title, 'isChecked:', isChecked, type(sender))

		# self.horizontalHeader().isSectionHidden(colIdx)

		# build a list of columns to hide
		hideColumnList = []
		nColHeader = self.horizontalHeader().count()
		for colIdx in range(nColHeader):
			headerItem = self.horizontalHeaderItem(colIdx)
			headerItemText = headerItem.text()
			if headerItemText == title: # logic here is a bit backwards
				# checked means show
				#print('menuActionHandler_header() is changing headerItemText:', headerItemText, 'to:', isChecked)
				if isChecked:
					# checked means show
					pass
				else:
					# not checked means hide
					hideColumnList.append(headerItemText)
			elif self.horizontalHeader().isSectionHidden(colIdx):
				# not checked means hide
				hideColumnList.append(headerItemText)

		self.hideColumns(hideColumnList)

		# repaint
		self.repaint()

	def menuActionHandler(self):
		"""
		receives event when user selects a right-click menu
		"""
		print('menuActionHandler')
		row = self.currentRow() # this is dangerous but seems to stay in sync, I owuld rather have the row in the event?
		sender = self.sender()
		title = sender.text()
		isChecked = sender.isChecked()
		bobID0 = sender.property('bobID0') # object type node/index/search
		bobID = sender.property('bobID') # set type or isBad
		print('    title:', title, 'row:', row, 'isChecked:', isChecked, 'bobID:', bobID)

		#
		objectIndex = self.getCellValue('idx', row=row)
		myEvent = {'type': bobID, 'bobID0': bobID0, 'newType': title, 'objectIdx':int(objectIndex), 'isChecked':isChecked}
		self.mainWindow.getStackView().myEvent(myEvent)

	def getCellValue_int(self, colName, row=None):
		"""
		row: pass none to use current selected row with self.currentRow()
		"""
		theRet = None
		if row is None:
			row = self.currentRow()
		colIdx = self._getColumnIdx(colName)
		if colIdx is not None:
			myItem = self.item(row, colIdx) # 0 is idx column
			if myItem.text() == '':
				pass
			else:
				theRet = int(myItem.text())
		return theRet

	def getCellValue(self, colName, row=None):
		"""
		return as string, caller is responsible for castine
		e.g. list()
		"""
		theRet = None
		if row is None:
			row = self.currentRow()
		colIdx = self._getColumnIdx(colName)
		if colIdx is not None:
			myItem = self.item(row, colIdx) # 0 is idx column
			if myItem.text() == '':
				pass
			else:
				theRet = myItem.text()
		return theRet

######################################################
class bAnnotationTableWidget(bTableWidget2):
	def __init__(self, listOfDict, parent=None):
		type = 'annotations'
		super(bAnnotationTableWidget, self).__init__(type, listOfDict, parent)

	def on_clicked_row(self):
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
			print('=== bAnnotationTableWidget.on_clicked_row() type:', self._type, 'row:', row, 'myIdx:', myIdx, 'isShift:', isShift)
			myEvent = bimpy.interface.bEvent('select annotation', nodeIdx=myIdx, snapz=True, isShift=isShift)
			colIdx = self._getColumnIdx('z')
			myItem = self.item(row, colIdx)
			myEvent._sliceIdx = int(float(myItem.text()))
			print('   emit myEvent:', myEvent)
			self.selectRowSignal.emit(myEvent)

	def keyPressEvent(self, event):
		key = event.key()
		print('=== bAnnotationTableWidget.keyPressEvent() in', self._type, 'key:', event.text())

		if key in [QtCore.Qt.Key_D, QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
			print('bAnnotationTableWidget delete not implemented ... please delete from the image')
			'''
			selectedObjectIdx = self.getCellValue_int('idx') #, row=None):
			event = {'type':'deleteAnnotation', 'objectType': 'annotation', 'objectIdx':selectedObjectIdx}
			self.mainWindow.getStackView().myEvent(event)
			'''
		else:
			super(bAnnotationTableWidget, self).keyPressEvent(event)

	def slot_select(self, myEvent):
		myEvent.printSlot('bAnnotationTableWidget.slot_select()')

		if myEvent.eventType == 'select annotation':
			annotationIdx = myEvent.nodeIdx
			if annotationIdx is None:
				return # happens on user key 'esc'
			self.mySelectRow(itemIdx=annotationIdx)

	def slot_updateTracing(self, myEvent):
		"""
		respond to edits
		"""

		myEvent.printSlot('bAnnotationTableWidget.slot_updateTracing()')

		if myEvent.eventType == 'newAnnotation':
			newRowIdx = self.appendRow(myEvent.nodeDict)
			self.mySelectRow(rowIdx=newRowIdx)
			self.repaint()

		elif myEvent.eventType == 'deleteAnnotation':
			self.deleteRowByIndex(myEvent.nodeIdx)
			self.repaint()

		elif myEvent.eventType == 'updateAnnotation':
			self.setRow(myEvent.nodeDict)

def main():
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

if __name__ == '__main__':
	main()
