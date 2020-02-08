# copied here on 20200121

"""
Tables to display (nodes, edges, edits)
"""

#from PyQt5 import QtGui, QtCore, QtWidgets
from qtpy import QtGui, QtCore, QtWidgets

import bimpy

################################################################################
class bEditTableWidget(QtWidgets.QTableWidget):
	# signals/slots
	#selectEdgeSignal = QtCore.pyqtSignal(object) # object can be a dict
	selectEdgeSignal = QtCore.Signal(object) # object can be a dict

	#def __init__(self, mainWindow, editDictList, parent=None):
	def __init__(self, mainWindow, parent=None):
		super(bEditTableWidget, self).__init__(parent)
		self.mainWindow = mainWindow
		#self.editDictList = editDictList
		self.buildUI()

	def buildUI(self):
		self.headerLabels = ['idx', 'type', 'typeNum', 'edge1', 'pnt1', 'len1', 'edge2', 'pnt2', 'len2']
		#self.setRowCount(len(self.editDictList))

		self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		# signals/slots
		self.itemSelectionChanged.connect(self.on_clicked_item)
		self.itemPressed.connect(self.on_clicked_item)

		self.setColumnCount(len(self.headerLabels))
		self.setHorizontalHeaderLabels(self.headerLabels)
		header = self.horizontalHeader()

		header.sectionClicked.connect(self.on_click_header)

		for idx, label in enumerate(self.headerLabels):
			header.setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeToContents)


	def populate(self, editDictList):
		"""
		Call this on load ???
		"""
		#print('bEditTableWidget.populate() num edits:', len(editDictList))
		self.setRowCount(len(editDictList))

		for idx, editDict in enumerate(editDictList):
			for colIdx, header in enumerate(self.headerLabels):
				if header in ['x', 'y']:
					myString = str(round(editDict[header],2))
				else:
					myString = str(editDict[header])
				# so we can sort
				item = QtWidgets.QTableWidgetItem()
				if header in ['type']:
					item.setText(str(editDict[header]))
				else:
					item.setData(QtCore.Qt.EditRole, editDict[header])
				self.setItem(idx, colIdx, item)

	def on_click_header(self, col):
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		print('on_click_header() col:', col, 'isShift:', isShift)
		if isShift:
			self.sortItems(col, order=QtCore.Qt.DescendingOrder)
		else:
			self.sortItems(col)

	def keyPressEvent(self, event):
		super(bEditTableWidget, self).keyPressEvent(event)
		# handle left/right to select again
		key = event.key()
		if key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			# reselect node
			self.on_clicked_item()

	def on_clicked_item(self):
		row = self.currentRow()
		edge1Col = self.headerLabels.index('edge1')
		myItem = self.item(row, edge1Col) # 0 is idx column
		edge1 = myItem.text()
		edge1 = int(edge1)

		edge2Col = self.headerLabels.index('edge2')
		myItem = self.item(row, edge2Col) # 0 is idx column
		edge2 = myItem.text()
		edge2 = int(edge2)

		edgeList = [edge1, edge2]

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier

		#print('bEditTableWidget.on_clicked_item() row:', row, 'edge1:', edge1)
		#self.mainWindow.signal('selectEdgeListFromTable', value=edgeList, fromTable=True)

		#if self.stopSelectionPropogation:
		#	self.stopSelectionPropogation = False
		#else:
		if 1:
			print('\bEditTableWidget.on_clicked_item() row:', row, 'edgeList:', edgeList)
			#self.mainWindow.signal('selectEdgeFromTable', myIdx, fromTable=True)
			myEvent = bimpy.interface.bEvent('select edge list', edgeList=edgeList, snapz=True, isShift=isShift)
			self.selectEdgeSignal.emit(myEvent)

class bTableWidget(QtWidgets.QTableWidget):
	def __init__(self, keyPressEventCallback, parent=None):
		super(bTableWidget, self).__init__(parent)
		self.keyPressEventCallback = keyPressEventCallback

	def keyPressEvent(self, event):
		super(bTableWidget, self).keyPressEvent(event)
		'''
		if key in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
			#
			event.setAccepted(True)
			self.myNodeTableWidget.super().keyPressEvent(event)
		'''
		key = event.key()
		if key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			self.keyPressEventCallback(event)
		else:
			event.setAccepted(False)

class bAnnotationTable(QtWidgets.QWidget):

	# signals/emit
	#selectNodeSignal = QtCore.pyqtSignal(object) # object can be a dict
	#selectEdgeSignal = QtCore.pyqtSignal(object)
	selectNodeSignal = QtCore.Signal(object) # object can be a dict
	selectEdgeSignal = QtCore.Signal(object)

	#def __init__(self, mainWindow=None, parent=None, slabList=None):
	def __init__(self, mainWindow=None, parent=None):
		super(bAnnotationTable, self).__init__(parent)

		'''
		self.setObjectName('bAnnotationTable')
		self.setStyleSheet("""
			#bAnnotationTable {
				background-color: #222;
			}
			.QTableWidget {
				background-color: #222;
			}
		""")
		'''

		# use self.mainWindow.mySimpleStack.slabList
		self.mainWindow = mainWindow
		#self.slabList = slabList

		self.stopSelectionPropogation = False

		self.myQVBoxLayout = QtWidgets.QVBoxLayout(self)

		#
		# buttons
		buttonsHBoxLayout = QtWidgets.QHBoxLayout(self)

		mySaveButton = QtWidgets.QPushButton('Save h5f')
		mySaveButton.clicked.connect(self.saveButton_Callback)
		buttonsHBoxLayout.addWidget(mySaveButton)

		myLoadButton = QtWidgets.QPushButton('Load h5f')
		myLoadButton.clicked.connect(self.loadButton_Callback)
		buttonsHBoxLayout.addWidget(myLoadButton)

		myLoadButton = QtWidgets.QPushButton('Load xml')
		myLoadButton.clicked.connect(self.loadButton_xml_Callback)
		buttonsHBoxLayout.addWidget(myLoadButton)

		# check boxes
		checkBoxNames = ['Nodes', 'Edges', 'Edits']
		for checkboxName in checkBoxNames:
			thisCheckBox = QtWidgets.QCheckBox(checkboxName)
			thisCheckBox.setChecked(True)
			thisCheckBox.clicked.connect(self.onCheckbox_Callback)
			buttonsHBoxLayout.addWidget(thisCheckBox)

		self.myQVBoxLayout.addLayout(buttonsHBoxLayout)

		#
		# tables
		self.myQHBoxLayout = QtWidgets.QHBoxLayout(self) # to hold nodes and edges
		self.myQVBoxLayout.addLayout(self.myQHBoxLayout)

		#
		# table of node annotation
		self.myNodeTableWidget = bTableWidget(self.on_keypress_node)
		#self.myNodeTableWidget = QtWidgets.QTableWidget()
		'''
		if self.slabList is None:
			numNodes = 0
		else:
			numNodes = self.slabList.numNodes()
		self.myNodeTableWidget.setRowCount(numNodes)
		'''
		self.myNodeTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.myNodeTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.myNodeTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

		# signals/slots
		#self.myNodeTableWidget.cellClicked.connect(self.on_clicked_node)
		self.myNodeTableWidget.itemSelectionChanged.connect(self.on_clicked_node)
		self.myNodeTableWidget.itemPressed.connect(self.on_clicked_node)

		self.nodeHeaderLabels = ['idx', 'x', 'y', 'z', 'nEdges', 'edgeList']
		self.myNodeTableWidget.setColumnCount(len(self.nodeHeaderLabels))
		self.myNodeTableWidget.setHorizontalHeaderLabels(self.nodeHeaderLabels)
		header = self.myNodeTableWidget.horizontalHeader()

		header.sectionClicked.connect(self.on_click_node_header)

		for idx, label in enumerate(self.nodeHeaderLabels):
			header.setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeToContents)

		#
		# table of edge annotations
		self.myEdgeTableWidget = bTableWidget(self.on_keypress_edge)
		#self.myEdgeTableWidget = QtWidgets.QTableWidget()
		'''
		if self.slabList is None:
			numEdges = 0
		else:
			numEdges = self.slabList.numEdges()
		self.myEdgeTableWidget.setRowCount(numEdges)
		'''
		self.myEdgeTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

		# can't get multiple selections programatically (works with user clicks?)
		self.myEdgeTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.myEdgeTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		# QtGui.QAbstractItemView.MultiSelection
		# QtGui.QAbstractItemView.ExtendedSelection
		#self.myEdgeTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

		# signals/slots
		#self.myEdgeTableWidget.cellClicked.connect(self.on_clicked_edge)
		self.myEdgeTableWidget.itemSelectionChanged.connect(self.on_clicked_edge)
		self.myEdgeTableWidget.itemPressed.connect(self.on_clicked_edge)
		# todo: this work to select edge when arrow keys are used but casuses bug in interface
		# figure out how to get this to work
		#self.myEdgeTableWidget.currentCellChanged.connect(self.on_clicked)
		#headerLabels = ['type', 'n', 'Length 3D', 'Length 2D', 'z', 'preNode', 'postNode', 'Good']
		self.edgeHeaderLabels = ['idx', 'z', 'nSlab', 'Len 3D', 'Diam', 'preNode', 'postNode', 'Bad']
		self.myEdgeTableWidget.setColumnCount(len(self.edgeHeaderLabels))
		self.myEdgeTableWidget.setHorizontalHeaderLabels(self.edgeHeaderLabels)
		header = self.myEdgeTableWidget.horizontalHeader()
		header.sectionClicked.connect(self.on_click_edge_header)
		for idx, label in enumerate(self.edgeHeaderLabels):
			header.setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeToContents)

		# QHeaderView will automatically resize the section to fill the available space.
		# The size cannot be changed by the user or programmatically.
		#header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)


		#
		# populate node and edge list
		self.populate()
		#

		self.myQHBoxLayout.addWidget(self.myNodeTableWidget)
		#self.myQHBoxLayout.addWidget(self.myEdgeTableWidget, stretch=20)
		self.myQHBoxLayout.addWidget(self.myEdgeTableWidget)

		# todo: fix this
		# todo: put back in to use edit list for vesselucida
		self.myEditTableWidget = bEditTableWidget(mainWindow=mainWindow)
		self.myEditTableWidget.populate(self.mainWindow.mySimpleStack.slabList.editDictList)
		self.myQHBoxLayout.addWidget(self.myEditTableWidget)

	def onCheckbox_Callback(self):
		"""
		Check boxes to toggle show/hide of (nodes, edges, edits)
		"""
		sender = self.sender()
		title = sender.text()
		isChecked = sender.isChecked()
		print('bAnnotationTable.onCheckbox_Callback() sender title:', title, 'isChecked:', isChecked)
		if title=='Nodes':
			if isChecked:
				self.myNodeTableWidget.show()
			else:
				self.myNodeTableWidget.hide()
		if title=='Edges':
			if isChecked:
				self.myEdgeTableWidget.show()
			else:
				self.myEdgeTableWidget.hide()
		if title=='Edits':
			if isChecked:
				self.myEditTableWidget.show()
			else:
				self.myEditTableWidget.hide()

		self.repaint()

	def populate(self):
		"""
		populate with new list of nodes and edges
		"""
		if self.mainWindow.mySimpleStack.slabList is None:
			pass
		else:
			# nodes
			numNodes = self.mainWindow.mySimpleStack.slabList.numNodes()
			print('bAnnotationTable numNodes:', numNodes)
			self.myNodeTableWidget.setRowCount(numNodes)
			# edges
			numEdges = self.mainWindow.mySimpleStack.slabList.numEdges()
			print('bAnnotationTable numEdges:', numEdges)
			self.myEdgeTableWidget.setRowCount(numEdges)

			for idx, nodeDict in enumerate(self.mainWindow.mySimpleStack.slabList.nodeDictList):
				nodeDict = self.mainWindow.mySimpleStack.slabList.getNode(idx) # todo: fix this
				for colIdx, header in enumerate(self.nodeHeaderLabels):

					# debug
					#print('nodeDictList idx:', idx, 'header:', header, nodeDict[header], type(nodeDict[header]))

					if header in ['x', 'y']:
						myString = str(round(nodeDict[header],2))
					elif header == 'z':
						myString = str(int(round(nodeDict[header],0)))
						#print('header:', header, 'myString:', myString)
					else:
						myString = str(nodeDict[header])
					#assign
					# so we can sort
					item = QtWidgets.QTableWidgetItem()
					if header in ['edgeList']:
						item.setText(str(nodeDict[header]))
					elif header == 'nEdges':
						# special case
						nEdges = len(nodeDict['edgeList'])
						item.setData(QtCore.Qt.EditRole, nEdges)
					else:
						#item.setData(QtCore.Qt.EditRole, nodeDict[header])
						item.setData(QtCore.Qt.EditRole, myString)
					self.myNodeTableWidget.setItem(idx, colIdx, item)

			for idx, edgeDict in enumerate(self.mainWindow.mySimpleStack.slabList.edgeDictList):
				for colIdx, headerStr in enumerate(self.edgeHeaderLabels):
					myString = str(edgeDict[headerStr])
					# special cases
					if headerStr == 'Bad':
						myString = 'X' if myString=='True' else ''
					elif headerStr == 'preNode':
						myString = '' if myString=='None' else myString
					elif headerStr == 'postNode':
						myString = '' if myString=='None' else myString
					#assign
					item = QtWidgets.QTableWidgetItem()
					if headerStr in ['Bad']:
						item.setText(myString)
					else:
						item.setData(QtCore.Qt.EditRole, edgeDict[headerStr])
					self.myEdgeTableWidget.setItem(idx, colIdx, item)

					# debug
					#if headerStr == 'z':
					#	print('idx:', idx, 'z:', edgeDict[headerStr])

	def _getEdgeColumnIdx(self, colStr):
		colIdx = None
		try:
			colIdx = self.edgeHeaderLabels.index(colStr)
		except (ValueError) as e:
			print('error: bAnnotationTable._getEdgeColumnIdx() did not find col:', colStr, 'in self.edgeHeaderLabels')
		return colIdx

	def _getNodeColumnIdx(self, colStr):
		colIdx = None
		try:
			colIdx = self.nodeHeaderLabels.index(colStr)
		except (ValueError) as e:
			print('error: bAnnotationTable._getNodeColumnIdx() did not find col:', colStr, 'in self.nodeHeaderLabels')
		return colIdx

	def updateNode(self, nodeDict):
		# search for row in table (handles sorted order
		print('updateNode() nodeDict:', nodeDict)
		nodeIdx = nodeDict['idx']
		for row in range(self.myNodeTableWidget.rowCount()):
			idxItem = self.myNodeTableWidget.item(row, 0) # 0 is idx column
			#myIdx = idxItem.text()
			#CHECK TYPE !!!!!!!!
			#myIdx = int(idxItem.text())
			myIdxStr = idxItem.text()
			#if myIdx == nodeIdx:
			if myIdxStr == str(nodeIdx):
				print('   updateNode() nodeIdx:', nodeIdx, nodeDict)
				rowItems = self.nodeItemFromNodeDict(nodeIdx, nodeDict)
				for colIdx, item in enumerate(rowItems):
					self.myNodeTableWidget.setItem(row, colIdx, item)

	def updateEdge(self, edgeDict):
		print('updateEdge() edgeDict:', edgeDict)
		edgeIdx = edgeDict['idx']
		for row in range(self.myEdgeTableWidget.rowCount()):
			idxItem = self.myEdgeTableWidget.item(row, 0) # 0 is idx column
			myIdxStr = idxItem.text()
			if myIdxStr == str(edgeIdx):
				print('   updateEdge() edgeIdx:', edgeIdx, edgeDict)
				rowItems = self.edgeItemFromEdgeDict(edgeDict)
				for colIdx, item in enumerate(rowItems):
					self.myEdgeTableWidget.setItem(row, colIdx, item)

	def nodeItemFromNodeDict(self, nodeIdx, nodeDict):
		rowItems = []
		for colIdx, header in enumerate(self.nodeHeaderLabels):
			#if header in ['x', 'y']:
			#	myString = str(round(nodeDict[header],2))
			if header == 'idx':
				myString = str(nodeIdx)
			elif header == 'Bad':
				myString = 'X' if myString=='True' else ''
			elif header in ['x', 'y']:
				myString = str(round(nodeDict[header],2))
			elif header == 'z':
				myString = str(round(nodeDict[header],0))
			else:
				myString = str(nodeDict[header])
			#assign
			#item = QtWidgets.QTableWidgetItem(myString)
			# so we can sort
			item = QtWidgets.QTableWidgetItem()
			#item.setData(QtCore.Qt.EditRole, QtCore.QVariant(myString))
			if header in ['edgeList']:
				item.setText(str(nodeDict[header]))
			#elif header == 'nEdges':
			#	# special case
			#	nEdges = len(nodeDict['edgeList'])
			#	item.setData(QtCore.Qt.EditRole, nEdges)
			elif header == 'idx':
				item.setData(QtCore.Qt.EditRole, nodeIdx)
			else:
				#item.setData(QtCore.Qt.EditRole, nodeDict[header])
				item.setData(QtCore.Qt.EditRole, myString)
			rowItems.append(item)
		return rowItems

	def edgeItemFromEdgeDict(self, edgeDict):
		rowItems = []
		for colIdx, header in enumerate(self.edgeHeaderLabels):
			'''
			print('edgeItemFromEdgeDict()')
			print('   header:', header, edgeDict[header], type(edgeDict[header]))
			'''
			if header == 'idx':
				myString = str(edgeDict['idx'])
			else:
				myString = str(edgeDict[header])
			# special cases
			if header == 'Bad':
				myString = 'X' if myString=='True' else ''
			#assign
			# so we can sort
			item = QtWidgets.QTableWidgetItem()
			if header == 'idx':
				item.setData(QtCore.Qt.EditRole, edgeDict['idx'])
			else:
				item.setData(QtCore.Qt.EditRole, edgeDict[header])
			rowItems.append(item)
		return rowItems

	def addEdge(self, edgeIdx, edgeDict):
		rowIdx = self.myEdgeTableWidget.rowCount()
		self.myEdgeTableWidget.insertRow(rowIdx)
		rowItems = self.edgeItemFromEdgeDict(edgeDict)
		for colIdx, item in enumerate(rowItems):
			self.myEdgeTableWidget.setItem(rowIdx, colIdx, item)

	def addNode(self, nodeIdx, nodeDict):
		rowIdx = self.myNodeTableWidget.rowCount()
		self.myNodeTableWidget.insertRow(rowIdx)

		rowItems = self.nodeItemFromNodeDict(nodeIdx, nodeDict)
		for colIdx, item in enumerate(rowItems):
			self.myNodeTableWidget.setItem(rowIdx, colIdx, item)

	def deleteNode(self, nodeDict):
		print('bAnnotationTable.deleteNode() nodeDict:', nodeDict)
		self.stopSelectionPropogation = True
		nodeRowIdx = self.findNodeRow(nodeDict)
		if nodeRowIdx is None:
			print('   !!! !!! THIS IS A BUG: bAnnotationTable.deleteNode() nodeRowIdx', nodeRowIdx)
			print(' ')
		else:
			self.myNodeTableWidget.removeRow(nodeRowIdx)

	def deleteEdge(self, edgeDict):
		# remove edge from table
		print('bAnnotationTable.deleteEdge() edgeDict:', edgeDict)
		#rowItems = self.edgeItemFromEdgeDict(edgeDict)
		self.stopSelectionPropogation = True

		edgeRowIdx = self.findEdgeRow(edgeDict)
		if edgeRowIdx is None:
			print('   !!! !!! THIS IS A BUG: bAnnotationTable.deleteEdge() edgeRowIdx', edgeRowIdx)
			print(' ')
		else:
			self.myEdgeTableWidget.removeRow(edgeRowIdx)
		#
		# update pre/post nodes (they have different edge list)
		#preNodeRowIdx = self.findNodeRow(edgeDict)

	def on_keypress_node(self, event):
		key = event.key()
		print('=== on_keypress_node() key:', event.text())
		if key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			# reselect node
			self.on_clicked_node()

	def on_keypress_edge(self, event):
		print('=== on_keypress_edge()')
		key = event.key()
		if key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			# reselect edge
			self.on_clicked_edge()

	'''
	def keyPressEvent(self, event):
		print('keyPressEvent()')
	'''

	def mycurrentItemChanged(self, prev, current):
		print('mycurrentItemChanged()')

	# todo: this is broken
	def saveButton_Callback(self):
		"""
		Save the current annotation list
		"""
		print('bAnnotationTable.saveButton_Callback()')
		self.mainWindow.signal('save')

	def loadButton_Callback(self):
		"""
		Load the current annotation list
		"""
		print('bAnnotationTable.loadButton_Callback()')
		self.mainWindow.signal('load')

	def loadButton_xml_Callback(self):
		"""
		Load the current annotation list from raw Vesselucida xml
		"""
		print('bAnnotationTable.loadButton_xml_Callback()')
		self.mainWindow.signal('load_xml')

	'''
	def _refreshRow(self, idx):
		"""
		todo: this can't use numbers for column index, we need to look into our header labels
		"""
		stat = self.slabList.edgeDictList[idx]

		myString = str(stat['type'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myEdgeTableWidget.setItem(idx, 0, item)

		myString = str(stat['n'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myEdgeTableWidget.setItem(idx, 1, item)

		myString = str(stat['Length 3D'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myEdgeTableWidget.setItem(idx, 2, item)

		myString = str(stat['Length 2D'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myEdgeTableWidget.setItem(idx, 3, item)

		myString = str(stat['z'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myEdgeTableWidget.setItem(idx, 4, item)

		if stat['Good']:
			myString = ''
		else:
			myString = 'False'
		#myString = str(stat['Good'])
		item = QtWidgets.QTableWidgetItem(myString)
		self.myEdgeTableWidget.setItem(idx, 5, item)
	'''

	def findNodeRow(self, nodeDict):
		theRet = None
		nodeIdx = nodeDict['idx']
		for row in range(self.myNodeTableWidget.rowCount()):
			idxItem = self.myNodeTableWidget.item(row, 0) # 0 is idx column
			myIdxStr = idxItem.text()
			if myIdxStr == str(nodeIdx):
				theRet = row
				break
		return theRet

	def findEdgeRow(self, edgeDict):
		theRet = None
		edgeIdx = edgeDict['idx']
		for row in range(self.myEdgeTableWidget.rowCount()):
			idxItem = self.myEdgeTableWidget.item(row, 0) # 0 is idx column
			myIdxStr = idxItem.text()
			if myIdxStr == str(edgeIdx):
				theRet = row
				break
		return theRet

	# todo: need to search for edgeIdx in case we are sorted
	def slot_selectEdge(self, myEvent):
		print('bAnnotationTable.slot_selectEdge() myEvent:', myEvent)
		edgeList = myEvent.edgeList
		if len(edgeList)>0:
			# select a list of edges
			for edge in edgeList:
				print('   selecting edge:', edge)
				self.stopSelectionPropogation = True
				self.myEdgeTableWidget.selectRow(edge)
		else:
			# select a single edge
			edgeIdx = myEvent.edgeIdx
			#print('bAnnotationTable.slot_selectEdge() edgeIdx:', edgeIdx)
			self.stopSelectionPropogation = True
			self.myEdgeTableWidget.selectRow(edgeIdx)
			#self.repaint()

		#self.myEdgeTableWidget.update()
		self.myEdgeTableWidget.repaint()

	# todo: need to search for nodeIdx in case we are sorted
	def slot_selectNode(self, myEvent):
		nodeIdx = myEvent.nodeIdx
		print('bAnnotationTable.slot_selectNode() nodeIdx:', nodeIdx)
		self.stopSelectionPropogation = True
		self.myNodeTableWidget.selectRow(nodeIdx)

		self.myNodeTableWidget.repaint()

	def slot_updateTracing(self, myEvent):
		#print('bAnnotationTable.slot_updateTracing() eventType:', myEvent.eventType)

		updateNodes = False
		updateEdges = False
		if myEvent.eventType == 'newNode':
			#print('   myEvent.nodeDict:', myEvent.nodeDict)
			self.addNode(myEvent.nodeIdx, myEvent.nodeDict)
			updateNodes = True

		elif myEvent.eventType == 'newEdge':
			#print('   myEvent.edgeDict:', myEvent.edgeDict)
			self.addEdge(myEvent.edgeIdx, myEvent.edgeDict)
			# nodes
			srcNodeDict = myEvent.srcNodeDict
			#print('   srcNodeDict:', srcNodeDict)
			self.updateNode(srcNodeDict)
			dstNodeDict = myEvent.dstNodeDict
			#print('   dstNodeDict:', dstNodeDict)
			self.updateNode(dstNodeDict)
			updateEdges = True

		elif myEvent.eventType == 'deleteNode':
			self.deleteNode(myEvent.nodeDict)
			updateNodes = True

		elif myEvent.eventType == 'deleteEdge':
			self.deleteEdge(myEvent.edgeDict)
			updateEdges = True

		#self.repaint()
		if updateNodes:
			self.myNodeTableWidget.repaint()
		if updateEdges:
			self.myEdgeTableWidget.repaint()

	#@QtCore.pyqtSlot()
	def on_clicked_node(self):
		#print('on_clicked_node()')
		row = self.myNodeTableWidget.currentRow()
		myItem = self.myNodeTableWidget.item(row, 0) # 0 is idx column
		myIdx = myItem.text()
		#print('   myIdx:', myIdx)
		if myIdx=='':
			return
		myIdx = int(myIdx)

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier

		if self.stopSelectionPropogation:
			self.stopSelectionPropogation = False
		else:
			print('\nbAnnotationTable.on_clicked_node() row:', row, 'myIdx:', myIdx, isShift)
			myEvent = bimpy.interface.bEvent('select node', nodeIdx=myIdx, snapz=True, isShift=isShift)
			colIdx = self._getNodeColumnIdx('z')
			myItem = self.myNodeTableWidget.item(row, colIdx)
			myEvent._sliceIdx = int(float(myItem.text()))
			self.selectNodeSignal.emit(myEvent)

	# this decorator was causing runtime error, click was not calling function with parameter 'col'
	#@QtCore.pyqtSlot()
	def on_click_node_header(self, col):
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		print('on_click_node_header() col:', col, 'isShift:', isShift)
		if isShift:
			self.myNodeTableWidget.sortItems(col, order=QtCore.Qt.DescendingOrder)
		else:
			self.myNodeTableWidget.sortItems(col)

	def on_click_edge_header(self, col):
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		print('on_click_edge_header() col:', col, 'isShift:', isShift)
		if isShift:
			self.myEdgeTableWidget.sortItems(col, order=QtCore.Qt.DescendingOrder)
		else:
			self.myEdgeTableWidget.sortItems(col)

	#@QtCore.pyqtSlot()
	def on_clicked_edge(self):
		#print('bAnnotationTable.on_clicked_edge()')
		row = self.myEdgeTableWidget.currentRow()
		if row == -1 or row is None:
			return
		#yStat = self.myEdgeTableWidget.item(row,0).text() #
		myItem = self.myEdgeTableWidget.item(row, 0) # 0 is idx column
		myIdx = myItem.text()
		if myIdx == '':
			return
		myIdx = int(myIdx)

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier

		if self.stopSelectionPropogation:
			self.stopSelectionPropogation = False
			print('\n=== DEFFERED bAnnotationTable.on_clicked_edge() row:', row, 'myIdx:', myIdx, isShift)
		else:
			print('\n=== bAnnotationTable.on_clicked_edge() row:', row, 'myIdx:', myIdx, isShift)
			#self.mainWindow.signal('selectEdgeFromTable', myIdx, fromTable=True)
			myEvent = bimpy.interface.bEvent('select edge', edgeIdx=myIdx, snapz=True, isShift=isShift)
			colIdx = self._getEdgeColumnIdx('z')
			myItem = self.myEdgeTableWidget.item(row, colIdx)
			myEvent._sliceIdx = int(myItem.text())
			self.selectEdgeSignal.emit(myEvent)
