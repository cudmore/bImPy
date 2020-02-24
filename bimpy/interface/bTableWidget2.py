# Robert Cudmore
# 20200223

"""
General purpose table to display (nodes, edges, search results)

type: from (nodes, edges, search)
listOfDict: from nodeList, edgeList, searchList
"""

from qtpy import QtGui, QtCore, QtWidgets

class bTableWidget2(QtWidgets.QTableWidget):
	def __init__(self, type, listOfDict, parent=None):
		super(bTableWidget2, self).__init__(parent)

		self._type = type # from ('nodes', 'edges', 'search')
		self._listOfDict = listOfDict # list of dict to populate
		
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
		self.buildUI()
		
	def buildUI(self):
		pass
	
	def populate(self, newDictList):
		self.headerLabels = []
		
		print('_listOfDict:', self._listOfDict)
		
		# headers
		firstDict = self._listOfDict[0]
		for k in firstDict.keys():
			self.headerLabels.append(k)
		print('self.headerLabels:', self.headerLabels)

		self.setColumnCount(len(self.headerLabels))
		self.setHorizontalHeaderLabels(self.headerLabels)
				
		# rows
		numRows = len(self._listOfDict)
		self.setRowCount(numRows)
		for idx, editDict in enumerate(self._listOfDict):
			for colIdx, header in enumerate(self.headerLabels):
				myString = str(editDict[header])
				item = QtWidgets.QTableWidgetItem()
				item.setData(QtCore.Qt.EditRole, editDict[header])
				print('    idx:', idx, 'colIdx:', colIdx, 'editDict[header]:', editDict[header])
				self.setItem(idx, colIdx, item)

		# resize headers based on content
		header = self.horizontalHeader()
		for idx, label in enumerate(self.headerLabels):
			header.setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeToContents)
				
	def keyPressEvent(self, event):
		super(bTableWidget, self).keyPressEvent(event)
		key = event.key()
		print('=== on_keypress_node() key:', event.text())
		if key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			# reselect node
			self.on_clicked_row()

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

if __name__ == '__main__':
	import sys
	app = QtWidgets.QApplication(sys.argv)

	dictList = []

	dict = {}
	dict['Idx'] = 0
	dict['x'] = 10
	dict['y'] = 20
	dict['z'] = 1
	dictList.append(dict)
	
	dict = {}
	dict['Idx'] = 1
	dict['x'] = 30
	dict['y'] = 40
	dict['z'] = 2
	dictList.append(dict)

	dict = {}
	dict['Idx'] = 1
	dict['x'] = 50
	dict['y'] = 60
	dict['z'] = 3
	dictList.append(dict)

	type = 'test'
	btw2 = bTableWidget2(type, dictList)
	btw2.show()
	
	sys.exit(app.exec_())