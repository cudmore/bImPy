# 20190802

# goal: make a stack window and overlay tracing from deepvess

import os, time
from collections import OrderedDict
import math

import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends import backend_qt5agg

import bimpy

################################################################################
#class bStackWidget(QtWidgets.QMainWindow):
class bStackWidget(QtWidgets.QWidget):
	"""
	A widget to display a stack. This includes a bStackView and a bAnnotationTable.
	"""
	def __init__(self, mainWindow=None, parent=None, path=''):
		super(bStackWidget, self).__init__()

		#self.options_defaults()

		self.path = path

		basename = os.path.basename(self.path)
		self.setWindowTitle(basename)

		self.setObjectName('bStackWidget0')
		self.setStyleSheet("""
			#bStackWidget0 {
				background-color: #222;
			}
			.QLabel {
				color: #bbb;
			}
			.QCheckBox {
				color: #bbb;
			}
		""")

		self.napariViewer = None
		#
		#self.mySimpleStack = bSimpleStack(path) # backend stack
		self.mySimpleStack = bimpy.bStack(path) # backend stack
		#

		self.showLeftControlBar = True
		self.showContrastBar = True
		self.showFeebackBar = True
		self.showLineProfileBar = True

		self.myHBoxLayout = QtWidgets.QHBoxLayout(self)

		self.myVBoxLayout = QtWidgets.QVBoxLayout(self)

		self.myContrastWidget = bimpy.interface.bStackContrastWidget(mainWindow=self)

		self.bStackFeebackWidget = bimpy.interface.bStackFeebackWidget(mainWindow=self)
		#self.bStackFeebackWidget.setFeedback('num slices', self.mySimpleStack.numImages)

		self.myHBoxLayout2 = QtWidgets.QHBoxLayout(self)

		self.myStackView = bStackView(self.mySimpleStack, mainWindow=self) # a visual stack

		# a slider to set slice number
		self.mySliceSlider = myStackSlider(self.mySimpleStack.numImages)
		'''
		self.mySliceSlider = QtWidgets.QSlider(QtCore.Qt.Vertical)
		self.mySliceSlider.setMaximum(self.mySimpleStack.numImages)
		self.mySliceSlider.setInvertedAppearance(True) # so it goes from top:0 to bottom:numImages
		self.mySliceSlider.setMinimum(0)
		if self.mySimpleStack.numImages < 2:
			self.mySliceSlider.setDisabled(True)
		# use this
		#self.mySliceSlider.sliderReleased.connect
		#self.mySliceSlider.valueChanged.connect(self.sliceSliderValueChanged)
		'''

		self.myHBoxLayout2.addWidget(self.myStackView)
		self.myHBoxLayout2.addWidget(self.mySliceSlider)

		# add
		self.myVBoxLayout.addWidget(self.myContrastWidget) #, stretch=0.1)
		self.myVBoxLayout.addWidget(self.bStackFeebackWidget) #, stretch=0.1)
		#self.myVBoxLayout.addWidget(self.myStackView) #, stretch = 9)
		self.myVBoxLayout.addLayout(self.myHBoxLayout2) #, stretch = 9)

		self.lineProfileWidget = bimpy.interface.bLineProfileWidget(mainWindow=self)
		self.myVBoxLayout.addWidget(self.lineProfileWidget)

		self.statusToolbarWidget = myStatusToolbarWidget(parent=self)
		#self.addToolBar(QtCore.Qt.BottomToolBarArea, self.statusToolbarWidget)
		self.myVBoxLayout.addWidget(self.statusToolbarWidget) #, stretch = 9)

		# todo: Need to show/hide annotation table
		self.annotationTable = bAnnotationTable(mainWindow=self, parent=None, slabList=self.mySimpleStack.slabList)
		self.myHBoxLayout.addWidget(self.annotationTable, stretch=7) # stretch=10, not sure on the units???
		#self.myHBoxLayout.addWidget(self.annotationTable) # stretch=10, not sure on the units???
		#print('self.mySimpleStack.slabList:', self.mySimpleStack.slabList)
		if self.mySimpleStack.slabList is None:
			self.annotationTable.hide()
			self.showLeftControlBar = False
		else:
			pass
			#self.annotationTable.hide()

		# vertical layout for contrast/feedback/image
		self.myHBoxLayout.addLayout(self.myVBoxLayout, stretch=7) # stretch=10, not sure on the units???

		#
		# signals and slots

		# listen to self.bStackFeebackWidget
		self.bStackFeebackWidget.clickStateChange.connect(self.myStackView.slot_StateChange)
		# listen to self.myStackView
		self.myStackView.displayStateChange.connect(self.bStackFeebackWidget.slot_StateChange)
		self.myStackView.setSliceSignal.connect(self.mySliceSlider.slot_UpdateSlice)
		self.myStackView.setSliceSignal.connect(self.bStackFeebackWidget.slot_StateChange)
		self.myStackView.selectNodeSignal.connect(self.annotationTable.slot_selectNode)
		self.myStackView.selectEdgeSignal.connect(self.annotationTable.slot_selectEdge)
		self.myStackView.tracingEditSignal.connect(self.annotationTable.slot_updateTracing)
		# listen to self.mySliceSlider
		self.mySliceSlider.updateSliceSignal.connect(self.myStackView.slot_StateChange)
		self.mySliceSlider.updateSliceSignal.connect(self.bStackFeebackWidget.slot_StateChange)
		# listen to self.annotationTable
		self.annotationTable.selectNodeSignal.connect(self.myStackView.slot_selectNode) # change to slot_selectNode ???
		self.annotationTable.selectEdgeSignal.connect(self.myStackView.slot_selectEdge) # change to slot_selectNode ???


		self.updateDisplayedWidgets()

		self.move(1000,100)
		#self.resize(2000, 1000)
		self.resize(2000, 1000)

		self.myStackView.setSlice(0)

	# todo: remove
	def slot_StateChange_(self, signalName, signalValue):
		print('bStackWidget.slot_StateChange() signalName:', signalName, 'signalValue:', signalValue)
		#if signalName=='set slice':
		#	self.mySliceSlider.setValue(signalValue)

	def getFeedbackWidget(self):
		return self.bStackFeebackWidget

	def attachNapari(self, napariViewer):
		self.napariViewer = napariViewer

	def getStatusToolbar(self):
		return self.statusToolbarWidget

	def updateDisplayedWidgets(self):
		# left control bar
		if self.showLeftControlBar:
			# todo: fix this
			if self.annotationTable is not None:
				self.annotationTable.show()
		else:
			if self.annotationTable is not None:
				self.annotationTable.hide()
		# contrast bar
		if self.showContrastBar:
			self.myContrastWidget.show()
		else:
			self.myContrastWidget.hide()
		# feedback bar
		if self.showFeebackBar:
			self.bStackFeebackWidget.show()
		else:
			self.bStackFeebackWidget.hide()
		if self.showLineProfileBar:
			self.lineProfileWidget.show()
		else:
			self.lineProfileWidget.hide()

	# get rid of this
	def getStack(self):
		return self.mySimpleStack

	def signal(self, signal, value=None, fromTable=False, recursion=True):
		print('=== bStackWidget.signal()', 'signal:', signal, 'value:', value, 'fromTable:', fromTable)

		# used for my vesselucida edit list
		if signal == 'selectEdgeListFromTable':
			print('=== bStackWidget.signal() selectEdgeListFromTable value:', value)
			self.myStackView.selectEdgeList(value, snapz=True)
			#self.selectEdgeList(value, snapz=True)
			# would require multiple selection
			'''
			if not fromTable:
				self.annotationTable.selectEdgeRow(value)
			'''

		if signal == 'contrast change':
			minContrast = value['minContrast']
			maxContrast = value['maxContrast']
			self.myStackView.minContrast = minContrast
			self.myStackView.maxContrast = maxContrast
			self.myStackView.setSlice(index=None) # will just refresh current slice

		if signal == 'toggle sliding z':
			self.myStackView._toggleSlidingZ(recursion=recursion)

		if signal == 'update line profile':
			self.lineProfileWidget.update(value)

		if signal == 'save':
			self.mySimpleStack.saveAnnotations()

	def keyPressEvent(self, event):
		#print('=== bStackWidget.keyPressEvent() event.key():', event.key())
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		isControl = modifiers == QtCore.Qt.ControlModifier

		if isControl and event.key() in [QtCore.Qt.Key_L]:
			self.mySimpleStack.slabList.loadVesselucida_xml()

		if event.key() in [QtCore.Qt.Key_Escape]:
			self.myStackView.selectNode(None)
			self.myStackView.selectEdge(None)
			self.myStackView.selectSlab(None)
		#elif event.key() == QtCore.Qt.Key_BraceLeft: # '['
		elif event.text() == '[':
			self.showLeftControlBar = not self.showLeftControlBar
			self.updateDisplayedWidgets()
			'''
			isVisible = self.annotationTable.isVisible()
			if isVisible:
				self.annotationTable.hide()
				self.showLeftControlBar = False
			else:
				self.annotationTable.show()
				self.showLeftControlBar = True
			'''
		elif event.key() in [QtCore.Qt.Key_L]:
			self.showLineProfileBar = not self.showLineProfileBar
			self.updateDisplayedWidgets()
		elif event.key() in [QtCore.Qt.Key_C]:
			self.showContrastBar = not self.showContrastBar
			self.updateDisplayedWidgets()
		elif event.key() in [QtCore.Qt.Key_F]:
			self.showFeebackBar = not self.showFeebackBar
			self.updateDisplayedWidgets()
		elif event.key() in [QtCore.Qt.Key_H]:
			self.printHelp()
		elif event.key() in [QtCore.Qt.Key_B]:
			print('set selected edge to bad ... need to implement this')
			'''
			selectedEdge = self.myStackView.mySelectedEdge
			self.mySimpleStack.setAnnotation('toggle bad edge', selectedEdge)
			# force refresh of table, I need to use model/view/controller !!!!
			self.annotationTable._refreshRow(selectedEdge)
			'''
		elif event.text() == 'i':
			self.mySimpleStack.print()

		else:
			#print('bStackWidget.keyPressEvent() not handled', event.text())
			event.setAccepted(False)

	def printHelp(self):
		print('=============================================================')
		print('bStackWidget help')
		print('==============================================================')
		print(' Navigation')
		print('   mouse wheel: scroll through images')
		print('   command + mouse wheel: zoom in/out (follows mouse position)')
		print('   +/-: zoom in/out (follows mouse position)')
		print('   click + drag: pan')
		print(' Show/Hide interface')
		print('   t: show/hide tracing')
		print('   l: show/hide list of annotations')
		print('   c: show/hide contrast bar')
		print('   f: show/hide feedback bar')
		print('   esc: remove edge selection (cyan)')
		print(' Stacks To Display')
		print('   1: Channel 1 - Raw Data')
		print('   2: Channel 2 - Raw Data')
		print('   3: Channel 3 - Raw Data')
		print('   9: Segmentation mask - DeepVess')
		print('   0: Skeleton mask - DeepVess')
		print(' Sliding Z-Projection')
		print('   z: toggle sliding z-projection on/off, will apply to all "Stacks To Display"')
		print(' ' )

################################################################################
class myStackSlider(QtWidgets.QSlider):
	"""
	Assuming stack is not going to change slices
	"""

	# signal/emit
	updateSliceSignal = QtCore.pyqtSignal(str, object) # object can be a dict

	def __init__(self, numSlices):
		super(myStackSlider, self).__init__(QtCore.Qt.Vertical)
		self.setMaximum(numSlices-1)
		self.setInvertedAppearance(True) # so it goes from top:0 to bottom:numImages
		self.setMinimum(0)
		if numSlices < 2:
			self.setDisabled(True)

		self.sliderMoved.connect(self.updateSlice_Signal)
		#self.valueChanged.connect(self.sliceSliderValueChanged)

	def slot_UpdateSlice(self, signalName, signalValue):
		#print('myStackSlider.slot_UpdateSlice() signalName:', signalName, 'signalValue:', signalValue)
		self.setValue(signalValue)

	def updateSlice_Signal(self):
		self.updateSliceSignal.emit('set slice', self.value())

################################################################################
class bEditTableWidget(QtWidgets.QTableWidget):
	def __init__(self, mainWindow, editDictList, parent=None):
		super(bEditTableWidget, self).__init__(parent)
		self.mainWindow = mainWindow
		self.editDictList = editDictList
		self.buildUI()

	def buildUI(self):
		self.headerLabels = ['idx', 'type', 'typeNum', 'edge1', 'pnt1', 'len1', 'edge2', 'pnt2', 'len2']
		self.setRowCount(len(self.editDictList))

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

		print('bEditTableWidget num edits:', len(self.editDictList))

		for idx, editDict in enumerate(self.editDictList):
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

		print('bEditTableWidget.on_clicked_item() row:', row, 'edge1:', edge1)
		self.mainWindow.signal('selectEdgeListFromTable', value=edgeList, fromTable=True)

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
	selectNodeSignal = QtCore.pyqtSignal(object) # object can be a dict
	selectEdgeSignal = QtCore.pyqtSignal(object)

	def __init__(self, mainWindow=None, parent=None, slabList=None):
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

		self.mainWindow = mainWindow
		self.slabList = slabList

		self.stopSelectionPropogation = False

		self.myQVBoxLayout = QtWidgets.QVBoxLayout(self)

		#
		# buttons
		mySaveButton = QtWidgets.QPushButton('Save')
		mySaveButton.clicked.connect(self.saveButton_Callback)
		self.myQVBoxLayout.addWidget(mySaveButton)

		self.myQHBoxLayout = QtWidgets.QHBoxLayout(self) # to hold nodes and edges
		self.myQVBoxLayout.addLayout(self.myQHBoxLayout)

		#
		# table of node annotation
		self.myNodeTableWidget = bTableWidget(self.on_keypress_node)
		#self.myNodeTableWidget = QtWidgets.QTableWidget()
		if self.slabList is None:
			numNodes = 0
		else:
			numNodes = self.slabList.numNodes()
		self.myNodeTableWidget.setRowCount(numNodes)
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
		if self.slabList is None:
			pass
		else:
			print('bAnnotationTable num nodes:', len(self.slabList.nodeDictList))
			'''
			for tmpNode in self.slabList.nodeDictList:
				print('tmpNode:', tmpNode)
			'''
			for idx, nodeDict in enumerate(self.slabList.nodeDictList):
				nodeDict = self.slabList.getNode(idx) # todo: fix this
				for colIdx, header in enumerate(self.nodeHeaderLabels):
					if header in ['x', 'y']:
						myString = str(round(nodeDict[header],2))
					else:
						myString = str(nodeDict[header])
					'''
					# special cases
					if header == 'Bad':
						myString = 'X' if myString=='True' else ''
					'''
					#assign
					#item = QtWidgets.QTableWidgetItem(myString)
					# so we can sort
					item = QtWidgets.QTableWidgetItem()
					#item.setData(QtCore.Qt.EditRole, QtCore.QVariant(myString))
					if header in ['edgeList']:
						item.setText(str(nodeDict[header]))
					elif header == 'nEdges':
						# special case
						nEdges = len(nodeDict['edgeList'])
						item.setData(QtCore.Qt.EditRole, nEdges)
					else:
						item.setData(QtCore.Qt.EditRole, nodeDict[header])
					self.myNodeTableWidget.setItem(idx, colIdx, item)

		#
		# table of edge annotations
		self.myEdgeTableWidget = bTableWidget(self.on_keypress_edge)
		#self.myEdgeTableWidget = QtWidgets.QTableWidget()
		if self.slabList is None:
			numEdges = 0
		else:
			numEdges = self.slabList.numEdges()
		self.myEdgeTableWidget.setRowCount(numEdges)
		self.myEdgeTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.myEdgeTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.myEdgeTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		# signals/slots
		#self.myEdgeTableWidget.cellClicked.connect(self.on_clicked_edge)
		self.myEdgeTableWidget.itemSelectionChanged.connect(self.on_clicked_edge)
		self.myEdgeTableWidget.itemPressed.connect(self.on_clicked_edge)
		# todo: this work to select edge when arrow keys are used but casuses bug in interface
		# figure out how to get this to work
		#self.myEdgeTableWidget.currentCellChanged.connect(self.on_clicked)
		#headerLabels = ['type', 'n', 'Length 3D', 'Length 2D', 'z', 'preNode', 'postNode', 'Good']
		self.edgeHeaderLabels = ['idx', 'z', 'nSlab', 'Len 3D', 'Len 2D', 'Diam', 'preNode', 'postNode', 'Bad']
		self.myEdgeTableWidget.setColumnCount(len(self.edgeHeaderLabels))
		self.myEdgeTableWidget.setHorizontalHeaderLabels(self.edgeHeaderLabels)
		header = self.myEdgeTableWidget.horizontalHeader()
		header.sectionClicked.connect(self.on_click_edge_header)
		for idx, label in enumerate(self.edgeHeaderLabels):
			header.setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeToContents)
			'''
			if label == 'z':
				header.setSectionResizeMode(idx, QtWidgets.QHeaderView.Fixed)
				header.resizeSection(idx, 100)
			else:
				header.setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeToContents)
			'''
		# QHeaderView will automatically resize the section to fill the available space.
		# The size cannot be changed by the user or programmatically.
		#header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
		if self.slabList is None:
			pass
		else:
			for idx, edgeDict in enumerate(self.slabList.edgeDictList):
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

		self.myQHBoxLayout.addWidget(self.myNodeTableWidget)
		#self.myQHBoxLayout.addWidget(self.myEdgeTableWidget, stretch=20)
		self.myQHBoxLayout.addWidget(self.myEdgeTableWidget)

		# todo: put back in to use edit list for vesselucida
		'''
		editTableWidget = bEditTableWidget(mainWindow=mainWindow, editDictList=self.slabList.editDictList)
		self.myQHBoxLayout.addWidget(editTableWidget)
		'''

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
			else:
				myString = str(nodeDict[header])
			# special cases
			if header == 'Bad':
				myString = 'X' if myString=='True' else ''
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
				item.setData(QtCore.Qt.EditRole, nodeDict[header])
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
		print('on_keypress_node() key:', event.text())
		if key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			# reselect node
			self.on_clicked_node()

	def on_keypress_edge(self, event):
		print('on_keypress_edge()')
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
		edgeIdx = myEvent.edgeIdx
		print('bAnnotationTable.slot_selectEdge() edgeIdx:', edgeIdx)
		self.stopSelectionPropogation = True
		self.myEdgeTableWidget.selectRow(edgeIdx)
		self.repaint()

	# todo: need to search for nodeIdx in case we are sorted
	def slot_selectNode(self, myEvent):
		nodeIdx = myEvent.nodeIdx
		print('bAnnotationTable.slot_selectNode() nodeIdx:', nodeIdx)
		self.stopSelectionPropogation = True
		self.myNodeTableWidget.selectRow(nodeIdx)
		self.repaint()

	def slot_updateTracing(self, myEvent):
		print('bAnnotationTable.slot_updateTracing() eventType:', myEvent.eventType)
		if myEvent.eventType == 'newNode':
			print('   myEvent.nodeDict:', myEvent.nodeDict)
			self.addNode(myEvent.nodeIdx, myEvent.nodeDict)

		elif myEvent.eventType == 'newEdge':
			print('   myEvent.edgeDict:', myEvent.edgeDict)
			self.addEdge(myEvent.edgeIdx, myEvent.edgeDict)
			# nodes
			srcNodeDict = myEvent.srcNodeDict
			#print('   srcNodeDict:', srcNodeDict)
			self.updateNode(srcNodeDict)
			dstNodeDict = myEvent.dstNodeDict
			#print('   dstNodeDict:', dstNodeDict)
			self.updateNode(dstNodeDict)

		elif myEvent.eventType == 'deleteEdge':
			self.deleteEdge(myEvent.edgeDict)

		self.repaint()

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
			self.selectNodeSignal.emit(myEvent)
			#self.mainWindow.signal('selectNodeFromTable', myIdx, fromTable=True)

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
		#print('bAnnotationTable.on_clicked_edge')
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
		else:
			print('\nbAnnotationTable.on_clicked_edge() row:', row, 'myIdx:', myIdx, isShift)
			#self.mainWindow.signal('selectEdgeFromTable', myIdx, fromTable=True)
			myEvent = bimpy.interface.bEvent('select edge', edgeIdx=myIdx, snapz=True, isShift=isShift)
			self.selectEdgeSignal.emit(myEvent)

'''
class myRectItem(QtWidgets.QGraphicsRectItem):
	def paint(self, painter, option, widget=None):
		super(myRectItem, self).paint(painter, option, widget)
		painter.save()
		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		painter.setBrush(QtCore.Qt.red)
		painter.drawEllipse(option.rect)
		painter.restore()
'''

################################################################################
#class bStackView(QtWidgets.QWidget):
class bStackView(QtWidgets.QGraphicsView):

	displayStateChange = QtCore.pyqtSignal(str, object) # object can be a dict
	setSliceSignal = QtCore.pyqtSignal(str, object)
	selectNodeSignal = QtCore.pyqtSignal(object)
	selectEdgeSignal = QtCore.pyqtSignal(object)
	tracingEditSignal = QtCore.pyqtSignal(object) # on new/delete/edit of node, edge, slab

	def __init__(self, simpleStack, mainWindow=None, parent=None):
		super(bStackView, self).__init__(parent)

		self.setObjectName('bStackView')
		self.setStyleSheet("""
			#bStackView {
				background-color: #222;
			}
		""")

		#self.path = path
		self.options_defaults()

		self.onpick_alreadypicked = False
		self.onpick_madeNewEdge = False
		self.keyIsDown = None

		self.mySimpleStack = simpleStack #bSimpleStack(path)
		self.mainWindow = mainWindow

		self.mySelectedNode = None # node index of selected node
		self.mySelectedEdge = None # edge index of selected edge
		self.mySelectedSlab = None # slab index of selected slab

		self.displayThisStack = 'ch1'
		self.displaySlidingZ = False

		self.currentSlice = 0
		self.minContrast = 0
		#self.maxContrast = 2 ** self.mySimpleStack.getHeaderVal('bitDepth')
		print('   bStackView.__init__ got stack bit depth of:', self.mySimpleStack.bitDepth, 'type:', type(self.mySimpleStack.bitDepth))
		self.maxContrast = 2 ** self.mySimpleStack.bitDepth

		'''
		self.idMasked = None
		self.xMasked = None
		self.yMasked = None
		self.zMasked = None
		'''

		#self.showTracing = True
		self.showNodes = True
		self.showEdges = True
		self.showDeadEnds = True

		self.imgplot = None

		# for click and drag
		self.clickPos = None

		self.displayStateDict = {
			'displayThisStack': 'ch1',
			'displaySlidingZ': False,
			'showTracing': True,
			'showNodes': True,
			'showEdges': True,
			'showDeadEnds': True,
		}

		self._preComputeAllMasks()

		#
		scene = QtWidgets.QGraphicsScene(self)
		# this works
		#scene.setBackgroundBrush(QtCore.Qt.blue);

		# was this
		# visually turn off scroll bars
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

		#self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

		# was this
		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		# now this
		#self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
		#self.setResizeAnchor(QtGui.QGraphicsView.NoAnchor)

		# this does nothing???
		#self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))

		self.setFrameShape(QtWidgets.QFrame.NoFrame)

		#todo: add interface to turn axes.axis ('on', 'off')
		# image
		#self.figure = Figure(figsize=(width, height), dpi=dpi)
		self.figure = Figure(figsize=(5,5)) # need size otherwise square image gets squished in y?
		self.canvas = backend_qt5agg.FigureCanvas(self.figure)
		self.axes = self.figure.add_axes([0, 0, 1, 1], aspect=1) #remove white border
		#self.axes.set_aspect('equal')
		self.axes.axis('off') #turn off axis labels

		# OMG, this took many hours to find the right function, set the background of the figure !!!
		self.figure.set_facecolor("black")

		# slab/point list
		'''
		markersize = self.options['Tracing']['tracingPenSize'] #2**2
		markerColor = self.options['Tracing']['tracingColor'] #2**2
		self.mySlabPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, picker=True)
		'''

		# draw lines between slabs in each edge
		zorder = 1
		self.myEdgePlot, = self.axes.plot([], [],'.c-', zorder=zorder, picker=5) # Returns a tuple of line objects, thus the comma

		# nodes (put this after slab/point list to be on top, order matter)
		# this HAS TO BE declared first, so nodes receive onpick_mpl() first
		# also see self.onpick_alreadypicked to stop double selection (node then edge or edge then node)
		zorder = 2
		markersize = self.options['Tracing']['nodePenSize'] #2**2
		markerColor = self.options['Tracing']['nodeColor'] #2**2
		self.myNodePlot = self.axes.scatter([], [],
			marker='o', color=markerColor, s=markersize, edgecolor='none', zorder=zorder, picker=True)
		#self.myNodePlot.set_clim(3, 5)


		# tracing/slabs that are dead end
		'''
		markersize = self.options['Tracing']['deadEndPenSize'] #2**2
		markerColor = self.options['Tracing']['deadEndColor'] #2**2
		self.myDeadEndPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, picker=None)
		'''

		zorder = 3

		# node selection
		markersize = self.options['Tracing']['nodeSelectionPenSize'] #2**2
		markerColor = self.options['Tracing']['nodeSelectionColor'] #2**2
		self.myNodeSelectionPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, zorder=zorder, picker=None)

		# flash node selection
		zorder += 1
		markersize = self.options['Tracing']['nodeSelectionFlashPenSize'] #2**2
		markerColor = self.options['Tracing']['nodeSelectionFlashColor'] #2**2
		self.myNodeSelectionFlash = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, zorder=zorder, picker=None)

		# edge selection
		zorder += 1
		markersize = self.options['Tracing']['tracingSelectionPenSize'] #2**2
		markerColor = self.options['Tracing']['tracingSelectionColor'] #2**2
		self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, zorder=zorder, picker=None)

		# slab selection
		zorder += 1
		markersize = self.options['Tracing']['tracingSelectionPenSize'] #2**2
		markersize *= 2
		markerColor = self.options['Tracing']['tracingSelectionColor'] #2**2
		self.mySlabSelectionPlot = self.axes.scatter([], [], marker='x', color=markerColor, s=markersize, zorder=zorder, picker=None)

		# flash edge selection
		zorder += 1
		markersize = self.options['Tracing']['tracingSelectionFlashPenSize'] #2**2
		markerColor = self.options['Tracing']['tracingSelectionFlashColor'] #2**2
		self.myEdgeSelectionFlash = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, zorder=zorder, picker=None)

		# slab line (perpendicular to tracing to extract line intensity profile)
		zorder += 1
		self.mySlabLinePlot, = self.axes.plot([], [], 'og-', zorder=zorder, picker=None) # Returns a tuple of line objects, thus the comma

		#self.canvas.mpl_connect('key_press_event', self.onkey)
		#self.canvas.mpl_connect('button_press_event', self.onclick)
		#self.canvas.mpl_connect('scroll_event', self.onscroll)
		self.canvas.mpl_connect('pick_event', self.onpick_mpl)
		self.canvas.mpl_connect('button_press_event', self.onclick_mpl)
		self.canvas.mpl_connect('motion_notify_event', self.onmove_mpl)

		scene.addWidget(self.canvas)

		self.setScene(scene)

		self.displayStateChange.emit('num slices', self.mySimpleStack.numImages)

	def slot_StateChange(self, signalName, signalValue):
		print(' bStackView.slot_StateChange() signalName:', signalName, 'signalValue:', signalValue)
		if signalName == 'set slice':
			self.setSlice(signalValue)

	def slot_selectNode(self, myEvent):
		nodeIdx = myEvent.nodeIdx
		snapz = myEvent.snapz
		isShift = myEvent.isShift
		self.selectNode(nodeIdx, snapz=snapz, isShift=isShift)

	def slot_selectEdge(self, myEvent):
		edgeIdx = myEvent.edgeIdx
		snapz = myEvent.snapz
		isShift = myEvent.isShift
		self.selectEdge(edgeIdx, snapz=snapz, isShift=isShift)

	def myEvent(self, event):
		theRet = None
		doUpdate = False
		if event['type']=='newNode':
			x = event['x']
			y = event['y']
			z = event['z']
			print('=== bStackView.myEvent() ... new node x:', x, 'y:', y, 'z:', z)
			newNodeIdx = self.mySimpleStack.slabList.newNode(x,y,z)
			self._preComputeAllMasks(fromSlice=z)
			self.setSlice() #refresh
			theRet = newNodeIdx
			#
			nodeDict = self.mySimpleStack.slabList.getNode(newNodeIdx)
			myEvent = bimpy.interface.bEvent('newNode', nodeIdx=newNodeIdx, nodeDict=nodeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='newEdge':
			srcNode = event['srcNode']
			dstNode = event['dstNode']
			print('=== bStackView.myEvent() ... new edge srcNode:', srcNode, 'dstNode:', dstNode)
			newEdgeIdx = self.mySimpleStack.slabList.newEdge(srcNode,dstNode)
			self._preComputeAllMasks(fromCurrentSlice=True)
			self.setSlice() #refresh
			theRet = newEdgeIdx

			edgeDict = self.mySimpleStack.slabList.getEdge(newEdgeIdx)
			myEvent = bimpy.interface.bEvent('newEdge', edgeIdx=newEdgeIdx, edgeDict=edgeDict)
			myEvent._srcNodeDict = self.mySimpleStack.slabList.getNode(srcNode)
			myEvent._dstNodeDict = self.mySimpleStack.slabList.getNode(dstNode)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='newSlab':
			edgeIdx = event['edgeIdx']
			x = event['x']
			y = event['y']
			z = event['z']
			newSlabIdx = self.mySimpleStack.slabList.newSlab(edgeIdx, x, y, z)
			self._preComputeAllMasks(fromCurrentSlice=True)
			self.mySelectedSlab = newSlabIdx # self.setSlice() will draw new slab
			self.setSlice() #refresh
			theRet = newSlabIdx

		elif event['type']=='deleteSelection':
			if self.mySelectedNode is not None:
				#delete node, only if it does not have edges !!!
				node = self.mySimpleStack.slabList.getNode(self.mySelectedNode)
				print('\n=== bStackView.myEvent() ... delete node:', self.mySelectedNode, node)
				wasDeleted = self.mySimpleStack.slabList.deleteNode(self.mySelectedNode)
				if wasDeleted:
					self.selectNode(None)
				doUpdate = True
			elif self.mySelectedEdge is not None:
				deleteEdgeIdx = self.mySelectedEdge
				deleteEdgeDict = self.mySimpleStack.slabList.getEdge(self.mySelectedEdge)
				print('\n=== bStackView.myEvent() ... delete edge:', self.mySelectedEdge, deleteEdgeDict)
				self.mySimpleStack.slabList.deleteEdge(self.mySelectedEdge)
				self.selectEdge(None)
				self.selectSlab(None)
				doUpdate = True
				#
				myEvent = bimpy.interface.bEvent('deleteEdge', edgeIdx=deleteEdgeIdx, edgeDict=deleteEdgeDict)
				self.tracingEditSignal.emit(myEvent)
		else:
			print('bStackView.myEvent() not understood event:', event)
		# finalize
		if doUpdate:
			self._preComputeAllMasks(fromCurrentSlice=True)
			self.setSlice() #refresh
		return theRet

	def flashNode(self, nodeIdx, numberOfFlashes):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashEdge() edgeIdx:', edgeIdx, on)
		if nodeIdx is None:
			return
		if numberOfFlashes>0:
			if self.mySimpleStack.slabList is not None:
				x, y, z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)
				self.myNodeSelectionFlash.set_offsets(np.c_[y, x])
				#self.myNodeSelectionFlash.set_offsets(np.c_[x, y])
				#
				QtCore.QTimer.singleShot(20, lambda:self.flashNode(nodeIdx, numberOfFlashes-1))
		else:
			self.myNodeSelectionFlash.set_offsets(np.c_[[], []])
		#
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def flashEdgeList(self, edgeList, on):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashEdge() edgeIdx:', edgeIdx, on)
		if edgeList is None or len(edgeList)==0:
			return
		if on:
			if self.mySimpleStack.slabList is not None:
				theseIndices = []
				for edgeIdx in edgeList:
					theseIndices += self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
				xMasked = self.mySimpleStack.slabList.y[theseIndices]
				yMasked = self.mySimpleStack.slabList.x[theseIndices]
				self.myEdgeSelectionFlash.set_offsets(np.c_[xMasked, yMasked])
				#
				QtCore.QTimer.singleShot(20, lambda:self.flashEdgeList(edgeList, False))
		else:
			self.myEdgeSelectionFlash.set_offsets(np.c_[[], []])
		#
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def flashEdge(self, edgeIdx, on):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashEdge() edgeIdx:', edgeIdx, on)
		if edgeIdx is None:
			return
		if on:
			if self.mySimpleStack.slabList is not None:
				theseIndices = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
				xMasked = self.mySimpleStack.slabList.y[theseIndices]
				yMasked = self.mySimpleStack.slabList.x[theseIndices]
				self.myEdgeSelectionFlash.set_offsets(np.c_[xMasked, yMasked])
				#
				QtCore.QTimer.singleShot(20, lambda:self.flashEdge(edgeIdx, False))
		else:
			self.myEdgeSelectionFlash.set_offsets(np.c_[[], []])
		#
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def setSelection(nodeIdx=None, edgeIdx=None, slabIdx=None, clearAll=False):
		if nodeIdx is not None:
			self.mySelectedNode = nodeIdx
		if edgeIdx is not None:
			self.mySelectedEdge = edgeIdx
		if slabIdx is not None:
			self.mySelectedSlab = slabIdx
		if clearAll:
			self.mySelectedNode = None
			self.mySelectedEdge = None
			self.mySelectedSlab = None

	def selectNode(self, nodeIdx, snapz=False, isShift=False):
		print('bStackView.selectNode() nodeIdx:', nodeIdx, type(nodeIdx))
		if nodeIdx is None:
			print('bStackView.selectNode() nodeIdx:', nodeIdx)
			self.mySelectedNode = None
			self.myNodeSelectionPlot.set_offsets(np.c_[[], []])
		else:
			if self.mySimpleStack.slabList is not None:
				print('bStackView.selectNode() nodeIdx:', nodeIdx, self.mySimpleStack.slabList.getNode(nodeIdx))
				self.mySelectedNode = nodeIdx

				x,y,z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)

				if snapz:
					z = self.mySimpleStack.slabList.getNode_zSlice(nodeIdx)
					self.setSlice(z)

					#self.zoomToPoint(y, x)
					self.zoomToPoint(x, y)

				self.myNodeSelectionPlot.set_offsets(np.c_[y,x]) # flipped

				markerColor = self.options['Tracing']['tracingSelectionColor']
				self.myNodeSelectionPlot.set_color(markerColor)

				QtCore.QTimer.singleShot(10, lambda:self.flashNode(nodeIdx, 2))

		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

		if isShift:
			node = self.mySimpleStack.slabList.nodeDictList[nodeIdx]
			edgeList = node['edgeList']
			self.selectEdgeList(edgeList)
		'''
		if nodeIdx is not None:
			modifiers = QtWidgets.QApplication.keyboardModifiers()
			isShift = modifiers == QtCore.Qt.ShiftModifier
			if isShift:
				node = self.mySimpleStack.slabList.nodeDictList[nodeIdx]
				edgeList = node['edgeList']
				self.selectEdgeList(edgeList)
		'''

	def selectEdgeList(self, edgeList, thisColorList=None, snapz=False):
		if snapz:
			firstEdge = edgeList[0]
			z = self.mySimpleStack.slabList.edgeDictList[firstEdge]['z']
			z = int(z)
			self.setSlice(z)

		colors = ['r', 'g', 'b']
		slabList = []
		colorList = []
		colorIdx = 0
		for idx, edgeIdx in enumerate(edgeList):
			slabs = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
			slabList += slabs
			if thisColorList is not None:
				colorList += [thisColorList[idx] for slab in slabs]
			else:
				colorList += [colors[colorIdx] for slab in slabs]
			colorIdx += 1
			if colorIdx==len(colors)-1:
				colorIdx = 0
		#print('selectEdgeList() slabList:', slabList)
		xMasked = self.mySimpleStack.slabList.x[slabList] # flipped
		yMasked = self.mySimpleStack.slabList.y[slabList]
		self.myEdgeSelectionPlot.set_offsets(np.c_[yMasked, xMasked])
		self.myEdgeSelectionPlot.set_color(colorList)

		QtCore.QTimer.singleShot(10, lambda:self.flashEdgeList(edgeList, True))

		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!
		#QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, True))

	def selectEdge(self, edgeIdx, snapz=False, isShift=False):
		if edgeIdx is None:
			print('   bStackView.selectEdge() edgeIdx:', edgeIdx, 'snapz:', snapz)
			#markersize = 10
			#self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color='c', s=markersize, picker=True)
			self.mySelectedEdge = None
			#self.mySelectedSlab = None
			self.myEdgeSelectionPlot.set_offsets(np.c_[[], []])
		else:
			self.mySelectedEdge = edgeIdx

			if self.mySimpleStack.slabList is not None:
				theseIndices = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)

				print('   bStackView.selectEdge() edgeIdx:', edgeIdx, 'snapz:', snapz, self.mySimpleStack.slabList.getEdge(edgeIdx))
				#print('      theseIndices:', theseIndices)
				# todo: add option to snap to a z
				# removed this because it was confusing
				if snapz:
					'''
					z = self.mySimpleStack.slabList.z[theseIndices[0]][0] # not sure why i need trailing [0] ???
					z = int(z)
					'''
					z = self.mySimpleStack.slabList.edgeDictList[edgeIdx]['z']
					z = int(z)
					self.setSlice(z)

				xMasked = self.mySimpleStack.slabList.x[theseIndices] # flipped
				yMasked = self.mySimpleStack.slabList.y[theseIndices]
				self.myEdgeSelectionPlot.set_offsets(np.c_[yMasked, xMasked])

				markerColor = self.options['Tracing']['tracingSelectionColor']
				self.myEdgeSelectionPlot.set_color(markerColor)

				QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, True))

		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

		if edgeIdx is not None:
			if isShift:
				colors = ['r', 'g', 'r', 'g']
				edge = self.mySimpleStack.slabList.edgeDictList[edgeIdx]
				selectedEdgeList = [edgeIdx] # could be [edgeIdx]
				colorList = ['y']
				if edge['preNode'] is not None:
					print('   selectEdge() selecting edges on preNode:', edge['preNode'], 'of edgeIdx:', edgeIdx)
					edgeList = self.mySimpleStack.slabList.nodeDictList[edge['preNode']]['edgeList']
					edgeList = list(edgeList) # make a copy
					try:
						repeatIdx = edgeList.index(edgeIdx) # find the index of our original edgeIdx and remove it
						edgeList.pop(repeatIdx)
					except (ValueError) as e:
						print('WARNING: selectEdge() pre node:', edge['preNode'], 'edgeList:', edgeList, 'does not contain:', edgeIdx)
					selectedEdgeList += edgeList
					colorList += [colors[colorIdx] for colorIdx in range(len(edgeList))]
				if edge['postNode'] is not None:
					print('   selectEdge() selecting edges on postNode:', edge['postNode'], 'of edgeIdx:', edgeIdx)
					edgeList = self.mySimpleStack.slabList.nodeDictList[edge['postNode']]['edgeList']
					edgeList = list(edgeList) # make a copy
					try:
						repeatIdx = edgeList.index(edgeIdx) # find the index of our original edgeIdx and remove it
						edgeList.pop(repeatIdx)
					except (ValueError) as e:
						print('WARNING: selectEdge() post node:', edge['postNode'], 'edgeList:', edgeList, 'does not contain:', edgeIdx)
					selectedEdgeList += edgeList
					colorList += [colors[colorIdx] for colorIdx in range(len(edgeList))]
				#print('edgeList:', edgeList)
				self.selectEdgeList(selectedEdgeList, thisColorList=colorList)

	def selectSlab(self, slabIdx, snapz=False):
		if self.mySimpleStack.slabList is None:
			return
		print('selectSlab() slabIdx:', type(slabIdx), slabIdx)
		'''
		if np.isnan(slabIdx):
			print('warning: selectSlab() got slabIdx:', slabIdx)
			return
		'''

		if slabIdx is None or np.isnan(slabIdx):
			print('   bStackView.selectSlab() slabIdx:', slabIdx, 'snapz:', snapz)
			#markersize = 10
			#self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color='c', s=markersize, picker=True)
			self.mySelectedSlab = None
			self.mySlabSelectionPlot.set_offsets(np.c_[[], []])
			self.mySlabLinePlot.set_xdata([])
			self.mySlabLinePlot.set_ydata([])
		else:
			numSlabs = self.mySimpleStack.slabList.numSlabs()
			if slabIdx > numSlabs-1:
				print('warning: bStackView.selectSlab() got out of bound slabIdx:', slabIdx, 'there are only numSlabs:', numSlabs)
				return

			self.mySelectedSlab = slabIdx

			x,y,z = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)
			numSlabs = self.mySimpleStack.slabList.numSlabs()

			#print('   bStackView.selectSlab() slabIdx:', slabIdx, 'snapz:', snapz, 'x:', x, 'y:', y, 'z:', z)
			# todo: add option to snap to a z
			if snapz:
				'''
				z = self.mySimpleStack.slabList.z[theseIndices[0]][0] # not sure why i need trailing [0] ???
				z = int(z)
				'''
				z = int(z)
				self.setSlice(z)

			self.mySlabSelectionPlot.set_offsets(np.c_[y, x]) # flipped

			markerColor = self.options['Tracing']['tracingSelectionColor']
			self.mySlabSelectionPlot.set_color(markerColor)

			#QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, True))

			#
			# draw the line
			#if slabIdx == 0 or (slabIdx == numSlabs-1):
			if 0:
				pass
			else:
				radius = 30
				# todo: could pas edgeIdx as a parameter
				edgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(slabIdx)
				if edgeIdx is None:
					print('warning: bStackView.selectSlab() got bad edgeIdx:', edgeIdx)
					return
				edgeSlabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
				thisSlabIdx = edgeSlabList.index(slabIdx) # index within edgeSlabList
				#print('   edgeIdx:', edgeIdx, 'thisSlabIdx:', thisSlabIdx, 'len(edgeSlabList):', len(edgeSlabList))
				# todo: not sure but pretty sure this will not fail?
				if thisSlabIdx==0 or thisSlabIdx==len(edgeSlabList)-1:
					# we were at a slab that was also a node
					return
				prevSlab = edgeSlabList[thisSlabIdx - 1]
				nextSlab = edgeSlabList[thisSlabIdx + 1]
				this_x, this_y, this_z = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)
				prev_x, prev_y, prev_z = self.mySimpleStack.slabList.getSlab_xyz(prevSlab)
				next_x, next_y, next_z = self.mySimpleStack.slabList.getSlab_xyz(nextSlab)
				dy = next_y - prev_y
				dx = next_x - prev_x
				slope = dy/dx
				slope = dx/dy # flipped
				inverseSlope = -1/slope
				x_ = radius / math.sqrt(slope**2 + 1) #
				y_ = x_ * slope
				#y_ = radius / math.sqrt(slope**2 + 1) # flipped
				#x_ = y_ * slope
				xLine1 = this_x - x_ #
				xLine2 = this_x + x_
				yLine1 = this_y + y_
				yLine2 = this_y - y_
				xSlabPlot = [xLine1, xLine2]
				ySlabPlot = [yLine1, yLine2]
				'''
				print('selectSlab() slabIdx:', slabIdx, 'slope:', slope, 'inverseSlope:', inverseSlope)
				print('   slope:', slope, 'inverseSlope:', inverseSlope)
				print('   xSlabPlot:', xSlabPlot)
				print('   ySlabPlot:', ySlabPlot)
				'''
				self.mySlabLinePlot.set_xdata(ySlabPlot) # flipped
				self.mySlabLinePlot.set_ydata(xSlabPlot)

				profileDict = {
					'ySlabPlot': ySlabPlot,
					'xSlabPlot': xSlabPlot,
					'slice': self.currentSlice,
				}
				self.mainWindow.signal('update line profile', profileDict)
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	'''
	def setSliceContrast(self, sliceNumber):
		img = self.mySimpleStack._images[sliceNumber, :, :].copy()

		#print('setSliceContrast() BEFORE min:', img.min(), 'max:', img.max(), 'mean:', img.mean(), 'dtype:', img.dtype)

		maxInt = 2 ** self.mySimpleStack.bitDepth - 1

		lowContrast = self.minContrast
		highContrast = self.maxContrast

		#print('   setSliceContrast() sliceNumber:', sliceNumber, 'maxInt:', maxInt, 'lowContrast:', lowContrast, 'highContrast:', highContrast)

		#mult = maxInt / abs(highContrast - lowContrast)
		denominator = abs(highContrast - lowContrast)
		if denominator != 0:
			mult = maxInt / denominator
		else:
			mult = maxInt

		#img.astype(numpy.uint16)
		img[img < lowContrast] = lowContrast
		img[img > highContrast] = highContrast
		img -= lowContrast

		img = img * mult
		img = img.astype(np.uint8)

		#print('setSliceContrast() AFTER min:', img.min(), 'max:', img.max(), 'mean:', img.mean(), 'dtype:', img.dtype, 'int(mult):', int(mult))

		return img
	'''

	def _preComputeAllMasks(self, fromSlice=None, fromCurrentSlice=False):
		"""
		Precompute all masks once. When user scrolls through slices this is WAY faster
		On new/delete (node, edge), just compute slices within +/- show tracing

		Parameter:
			fromCurrentSlice trumps fromSlice
		"""
		startSeconds = time.time()

		if self.mySimpleStack.slabList is None:
			return

		recomputeAll = False
		if fromSlice is None and not fromCurrentSlice:
			#recreate all
			self.maskedNodes = []
			recomputeAll = True
		'''
		self.maskedEdges = []
		self.maskedDeadEnds = []
		'''

		showTracingAboveSlices = self.options['Tracing']['showTracingAboveSlices']
		showTracingBelowSlices = self.options['Tracing']['showTracingBelowSlices']

		sliceRange = range(self.mySimpleStack.numImages)
		if fromCurrentSlice:
			fromSlice = self.currentSlice
		if fromSlice is not None:
			sliceRange = range(fromSlice-showTracingAboveSlices, fromSlice+showTracingBelowSlices)
		#for i in range(self.mySimpleStack.numImages):
		print('_preComputeAllMasks() computing masks for slices:', sliceRange, 'recomputeAll:', recomputeAll)
		for i in sliceRange:
			# when using fromSlice
			if i<0 or i>self.mySimpleStack.numImages-1:
				continue

			upperz = i - self.options['Tracing']['showTracingAboveSlices']
			lowerz = i + self.options['Tracing']['showTracingBelowSlices']

			#if self.mySimpleStack.slabList is not None:
			#
			# nodes
			zNodeMasked = np.ma.masked_outside(self.mySimpleStack.slabList.z, upperz, lowerz)
			if len(zNodeMasked) > 0:
				xNodeMasked = self.mySimpleStack.slabList.y[~zNodeMasked.mask] # swapping
				yNodeMasked = self.mySimpleStack.slabList.x[~zNodeMasked.mask]
				dMasked = self.mySimpleStack.slabList.d[~zNodeMasked.mask]
				nodeIdxMasked = self.mySimpleStack.slabList.nodeIdx[~zNodeMasked.mask]
				edgeIdxMasked = self.mySimpleStack.slabList.edgeIdx[~zNodeMasked.mask]
				#slabIdxMasked = self.mySimpleStack.slabList.slabIdx[~zNodeMasked.mask]

				nodeMasked_x = xNodeMasked[~np.isnan(nodeIdxMasked)]
				nodeMasked_y = yNodeMasked[~np.isnan(nodeIdxMasked)]
				nodeMasked_nodeIdx = nodeIdxMasked[~np.isnan(nodeIdxMasked)]

				nodeMasked_x = nodeMasked_x.ravel()
				nodeMasked_y = nodeMasked_y.ravel()
				nodeMasked_nodeIdx = nodeMasked_nodeIdx.ravel().astype(int)

				#
				# to draw lines on edges, make a disjoint list (seperated by nan
				xEdgeLines = []
				yEdgeLines = []
				dEdgeLines = []
				edgeIdxLines = []
				slabIdxLines = []
				nodeIdxLines = [] # to intercept clicks on edge that are also node
				for edgeIdx, edge in enumerate(self.mySimpleStack.slabList.edgeDictList):
					# slabList will include srcNode/dstNode as slabs
					slabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
					# decide if the slabs are within (upperz, lowerz)
					for slab in slabList:
						zSlab = self.mySimpleStack.slabList.z[slab]
						if zSlab>upperz and zSlab<lowerz:
							# include
							xEdgeLines.append(self.mySimpleStack.slabList.y[slab]) # flipped
							yEdgeLines.append(self.mySimpleStack.slabList.x[slab])
							dEdgeLines.append(self.mySimpleStack.slabList.d[slab])
							edgeIdxLines.append(edgeIdx)
							slabIdxLines.append(slab)
							nodeIdxLines.append(self.mySimpleStack.slabList.nodeIdx[slab])
						else:
							# exclude
							xEdgeLines.append(np.nan)
							yEdgeLines.append(np.nan)
							dEdgeLines.append(np.nan)
							edgeIdxLines.append(np.nan)
							slabIdxLines.append(np.nan)
							nodeIdxLines.append(np.nan)
					xEdgeLines.append(np.nan)
					yEdgeLines.append(np.nan)
					dEdgeLines.append(np.nan)
					edgeIdxLines.append(np.nan)
					slabIdxLines.append(np.nan)
					nodeIdxLines.append(np.nan)

			else:
				# len(zNodeMasked)<1
				nodeMasked_x = []
				nodeMasked_y = []
				nodeMasked_nodeIdx = []

				xEdgeLines = []
				yEdgeLines = []
				dEdgeLines = []
				edgeIdxLines = []
				slabIdxLines = []
				nodeIdxLines = []

			maskedNodeDict = {
				'zNodeMasked': zNodeMasked,
				'nodeMasked_x': nodeMasked_x,
				'nodeMasked_y': nodeMasked_y,
				'nodeMasked_nodeIdx': nodeMasked_nodeIdx,

				'xEdgeLines': xEdgeLines,
				'yEdgeLines': yEdgeLines,
				'dEdgeLines': dEdgeLines,
				'edgeIdxLines': edgeIdxLines,
				'slabIdxLines': slabIdxLines,
				'nodeIdxLines': nodeIdxLines,
			}

			'''
			if i==70:
				print('i:', i, maskedNodeDict['xEdgeLines'])
			'''

			# update
			if fromSlice is not None:
				#print('   updating slide i:', i)
				self.maskedNodes[i] = maskedNodeDict
			else:
				#print('   appending i:', i)
				self.maskedNodes.append(maskedNodeDict)

			#
			# slabs/edges dead ends
			'''
			maskedDeadEndDict = {
				'zMasked': [],
				'xMasked': [],
				'yMasked': [],
			}
			for edgeDict in self.mySimpleStack.slabList.edgeDictList:
				if edgeDict['preNode'] is None:
					# include dead end
					# get the z of the first slab
					firstSlabIdx = edgeDict['slabList'][0]
					tmpz = self.mySimpleStack.slabList.z[firstSlabIdx]
					if tmpz > upperz and tmpz < lowerz:
						tmpx = self.mySimpleStack.slabList.x[firstSlabIdx]
						tmpy = self.mySimpleStack.slabList.y[firstSlabIdx]
						maskedDeadEndDict['yMasked'].append(tmpx) # swapping
						maskedDeadEndDict['xMasked'].append(tmpy)
						maskedDeadEndDict['zMasked'].append(tmpz)
				if edgeDict['postNode'] is None:
					# include dead end
					# get the z of the last slab
					lastSlabIdx = edgeDict['slabList'][-1]
					tmpz = self.mySimpleStack.slabList.z[lastSlabIdx]
					if tmpz > upperz and tmpz < lowerz:
						tmpx = self.mySimpleStack.slabList.x[lastSlabIdx]
						tmpy = self.mySimpleStack.slabList.y[lastSlabIdx]
						maskedDeadEndDict['yMasked'].append(tmpx) # swapping
						maskedDeadEndDict['xMasked'].append(tmpy)
						maskedDeadEndDict['zMasked'].append(tmpz)
			self.maskedDeadEnds.append(maskedDeadEndDict)
			'''

			#print('slice', i, '_preComputeAllMasks() len(x):', len(xMasked), 'len(y)', len(yMasked))
		stopSeconds= time.time()
		print('   took', round(stopSeconds-startSeconds,2), 'seconds')

	# todo: remove recursion
	def setSlice(self, index=None):
		#print('bStackView.setSlice()', index)

		if index is None:
			index = self.currentSlice

		if index < 0:
			index = 0
		if index > self.mySimpleStack.numImages-1:
			index = self.mySimpleStack.numImages -1

		showImage = True

		if showImage:
			if self.displaySlidingZ:
				upSlices = self.options['Stack']['upSlidingZSlices']
				downSlices = self.options['Stack']['downSlidingZSlices']
				image = self.mySimpleStack.getSlidingZ(index, self.displayThisStack, upSlices, downSlices, self.minContrast, self.maxContrast)
			else:
				# works
				image = self.mySimpleStack.setSliceContrast(index, thisStack=self.displayThisStack, minContrast=self.minContrast, maxContrast=self.maxContrast)

			if self.imgplot is None:
				cmap = self.options['Stack']['colorLut'] #2**2
				self.imgplot = self.axes.imshow(image, cmap=cmap)
			else:
				self.imgplot.set_data(image)
		else:
			pass

		#
		# update point annotations
		#if self.showTracing:
		if self.displayStateDict['showTracing']:
			if self.mySimpleStack.slabList is None:
				# no tracing
				pass
			else:
				# nodes
				# abb upgrade bSlabList

				# 202001 fix this !!!
				if self.showNodes:

					# lines between slabs of edge
					self.myEdgePlot.set_xdata(self.maskedNodes[index]['xEdgeLines'])
					self.myEdgePlot.set_ydata(self.maskedNodes[index]['yEdgeLines'])

					# xNodeMasked -->> all slabs
					# xNodeMasked2 -->> just nodes
					self.myNodePlot.set_offsets(np.c_[self.maskedNodes[index]['nodeMasked_x'], self.maskedNodes[index]['nodeMasked_y']])

					#print('setSlice() index:', index, 'color:', self.maskedNodes[index]['colorMasked'])
					#self.myNodePlot.set_array(self.maskedNodes[index]['colorMasked'])
					#self.myNodePlot.set_clim(3, 5)


				if self.mySelectedSlab is not None:
					self.selectSlab(self.mySelectedSlab)

				# slabs
				# 202001 fix this !!!
				'''
				if self.showEdges:
					self.mySlabPlot.set_offsets(np.c_[self.maskedEdges[index]['xMasked'], self.maskedEdges[index]['yMasked']])
				if self.showDeadEnds:
					self.myDeadEndPlot.set_offsets(np.c_[self.maskedDeadEnds[index]['xMasked'], self.maskedDeadEnds[index]['yMasked']])
				'''

		else:
			self.myEdgePlot.set_xdata([])
			self.myEdgePlot.set_ydata([])
			self.myNodePlot.set_offsets(np.c_[[], []])
			#self.mySlabPlot.set_offsets(np.c_[[], []])
			#self.myDeadEndPlot.set_offsets(np.c_[[], []])

		self.currentSlice = index # update slice

		self.canvas.draw_idle()

	def zoomToPoint(self, x, y):
		# todo convert this to use a % of the total image ?
		print('bStackView.zoomToPoint() x:', x, 'y:', y, 'THIS DOES NOT WORK WHEN ZOOMED !!!!')

		scenePnt = self.mapToScene(y, x) # swapping
		#scenePnt = self.mapFromScene(x, y)
		print('   scenePnt:', scenePnt)
		self.centerOn(scenePnt)
		#self.centerOn(x, y)

		self.canvas.draw_idle()
		'''
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!
		'''

	def keyReleaseEvent(self, event):
		self.keyIsDown = None

	def keyPressEvent(self, event):
		#print('=== bStackView.keyPressEvent() event.key():', event.key())

		self.keyIsDown = event.text()
		key = event.key()

		if event.key() == QtCore.Qt.Key_R:
			self._preComputeAllMasks()
			self.setSlice()

		elif event.key() in [QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal]:
			self.zoom('in')
		elif event.key() == QtCore.Qt.Key_Minus:
			self.zoom('out')
		elif event.key() == QtCore.Qt.Key_T:
			print('\ntodo: signal to app feedback bar there is a state change')
			print(' *this will then receive the change in the slot() we are subscribed to')
			self.displayStateDict['showTracing'] = not self.displayStateDict['showTracing']
			self.displayStateChange.emit('tracing', self.displayStateDict['showTracing'])
			#self.mainWindow.get
			# create a signal that goes to feedback widget !!!

			# and then do this
			#self.showTracing = not self.showTracing
			#self.setSlice() #refresh

		#elif event.key() == QtCore.Qt.Key_N:
		#	self.showNodes = not self.showNodes
		#	self.setSlice() #refresh
		elif event.key() == QtCore.Qt.Key_E:
			self.showEdges = not self.showEdges
			self.setSlice() #refresh

		elif event.key() in [QtCore.Qt.Key_D, QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
			#self.showDeadEnds = not self.showDeadEnds
			#self.setSlice() #refresh
			event = {'type':'deleteSelection'}
			self.myEvent(event)

		# move to next/prev slab
		elif key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			if self.mySelectedSlab is not None:
				tmpEdgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(self.mySelectedSlab)
				if tmpEdgeIdx is None:
					print('warning: move to next/prev slab got bad edge idx:', tmpEdgeIdx)
					return
				tmpSlabList = self.mySimpleStack.slabList.getEdgeSlabList(tmpEdgeIdx)
				slabIdxInList = tmpSlabList.index(self.mySelectedSlab)
				if slabIdxInList==0 or slabIdxInList==len(tmpSlabList)-1:
					return
				if key ==QtCore.Qt.Key_Left:
					slabIdxInList -= 1
				elif key == QtCore.Qt.Key_Right:
					slabIdxInList += 1
				newSlabIdx = tmpSlabList[slabIdxInList]
				self.selectSlab(newSlabIdx, snapz=True)

		# choose which stack to display
		elif event.key() == QtCore.Qt.Key_1:
			self.displayThisStack = 'ch1'
			self.setSlice(recursion=False) # just refresh
		elif event.key() == QtCore.Qt.Key_2:
			numChannels = self.mySimpleStack.numChannels
			if numChannels > 1:
				self.displayThisStack = 'ch2'
				self.setSlice(recursion=False) # just refresh
			else:
				print('warning: stack only has', numChannels, 'channel(s)')
		elif event.key() == QtCore.Qt.Key_3:
			numChannels = self.mySimpleStack.numChannels
			if numChannels > 2:
				self.displayThisStack = 'ch3'
				self.setSlice(recursion=False) # just refresh
			else:
				print('warning: stack only has', numChannels, 'channel(s)')
		elif event.key() == QtCore.Qt.Key_9:
			if self.mySimpleStack._imagesMask is not None:
				self.displayThisStack = 'mask'
				self.setSlice(recursion=False) # just refresh
		elif event.key() == QtCore.Qt.Key_0:
			if self.mySimpleStack._imagesSkel is not None:
				self.displayThisStack = 'skel'
				self.setSlice(recursion=False) # just refresh

		elif event.key() == QtCore.Qt.Key_Z:
			self._toggleSlidingZ()

		elif event.key() == QtCore.Qt.Key_P:
			self.mySimpleStack.slabList._printStats()

		else:
			#print('bStackView.keyPressEvent() not handled:', event.text())
			event.setAccepted(False)

	def _toggleSlidingZ(self, recursion=True):
		print('_toggleSlidingZ() recursion:', recursion, 'self.displaySlidingZ', self.displaySlidingZ)
		self.displaySlidingZ = not self.displaySlidingZ
		# todo: don't call this deep
		if recursion:
			self.mainWindow.bStackFeebackWidget.setFeedback('sliding z', self.displaySlidingZ)
		self.setSlice(recursion=False) # just refresh

	def zoom(self, zoom):
		#print('=== bStackView.zoom()', zoom)
		if zoom == 'in':
			scale = 1.2
		else:
			scale = 0.8
		self.scale(scale,scale)
		#self.zoomToPoint(100,100)

		'''
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!
		'''

	def wheelEvent(self, event):
		#if self.hasPhoto():

		#print('event.angleDelta().y():', event.angleDelta().y())

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		if modifiers == QtCore.Qt.ControlModifier:
			'''
			self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
			self.setResizeAnchor(QtGui.QGraphicsView.NoAnchor)
			'''

			oldPos = self.mapToScene(event.pos())
			if event.angleDelta().y() > 0:
				zoomFactor = 1.2
			else:
				zoomFactor = 0.8
			self.scale(zoomFactor,zoomFactor)
			newPos = self.mapToScene(event.pos())
			# Move scene to old position
			delta = newPos - oldPos

			self.translate(delta.y(), delta.x())

			#self.centerOn(newPos)

			#event.setAccepted(True)
			#super(bStackView,self).wheelEvent(event)
		else:
			if event.angleDelta().y() > 0:
				self.currentSlice -= 1
			else:
				self.currentSlice += 1
			self.setSlice(self.currentSlice)
			#self.displayStateChange.emit('set slice', self.currentSlice)
			self.setSliceSignal.emit('set slice', self.currentSlice)
			#event.setAccepted(True)

	def mousePressEvent(self, event):
		"""
		shift+click will create a new node
		n+click (assuming there is a node selected ... will create a new edge)
		"""
		#print('=== bStackView.mousePressEvent()', event.pos())
		self.clickPos = event.pos()
		super().mousePressEvent(event)

	def mouseMoveEvent(self, event):
		#print('=== bStackView.mouseMoveEvent()')
		if self.clickPos is not None:
			newPos = event.pos() - self.clickPos
			dx = self.clickPos.x() - newPos.x()
			dy = self.clickPos.y() - newPos.y()
			self.translate(dx, dy)

		super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		#print('=== bStackView.mouseReleaseEvent()')
		self.clickPos = None
		super().mouseReleaseEvent(event)
		event.setAccepted(True)

	def onmove_mpl(self, event):
		#print('onmove_mpl()', event.xdata, event.ydata)
		thePoint = QtCore.QPoint(event.ydata, event.xdata) # swapped
		self.mainWindow.getStatusToolbar().setMousePosition(thePoint)

	def onclick_mpl(self, event):
		"""
		onpick() get called first
		"""

		x = event.ydata # swapped
		y = event.xdata
		z = self.currentSlice
		x = round(x,2)
		y = round(y,2)
		newNodeEvent = {'type':'newNode','x':x,'y':y,'z':z}

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers & QtCore.Qt.ShiftModifier
		nKey = self.keyIsDown == 'n'

		if self.onpick_madeNewEdge:
			self.onpick_madeNewEdge = False
		elif nKey and self.mySelectedNode is not None:
			# make a new edge
			print('\n=== bStackWidget.onclick_mpl() new edge ...')
			newNodeIdx = self.myEvent(newNodeEvent)
			newEdgeEvent = {'type':'newEdge','srcNode':self.mySelectedNode, 'dstNode':newNodeIdx}
			newEdgeIdx = self.myEvent(newEdgeEvent)
			self.selectNode(None) # cancel self.mySelectedNode
			self.selectEdge(newEdgeIdx) # select the new edge

		elif isShift:
			if self.mySelectedEdge is not None:
				# make a new slab
				print('\n=== bStackWidget.onclick_mpl() new slab ...')
				newSlabEvent = {'type':'newSlab','edgeIdx':self.mySelectedEdge, 'x':x, 'y':y, 'z':z}
				self.myEvent(newSlabEvent)
			else:
				# make a new node
				print('\n=== bStackWidget.onclick_mpl() new node ...')
				self.myEvent(newNodeEvent)

	'''
	def onpick(event):
	    thisline = event.artist
	    xdata = thisline.get_xdata()
	    ydata = thisline.get_ydata()
	    ind = event.ind
	    print ('onpick points:', zip(xdata[ind], ydata[ind]))
	'''

	def onpick_mpl(self, event):
		"""
		Click to select (node, edge, slab)
		called before onclick_mpl()

		i want to be able to pick both (nodes, slabs) but need to know which one was clicked?
		"""
		# stop onpick being called twice for one mouse down
		if self.onpick_alreadypicked:
			self.onpick_alreadypicked = False
			return False
		else:
			self.onpick_alreadypicked = True

		selectionType = None
		thisLine = event.artist
		if thisLine == self.myNodePlot:
			selectionType = 'nodeSelection'
		elif thisLine == self.myEdgePlot:
			selectionType = 'edgeSelection'

		nKey = self.keyIsDown == 'n'
		print('\n=== bStackView.onpick() nKey:', nKey, 'selectionType:', selectionType)
		xdata = event.mouseevent.xdata
		ydata = event.mouseevent.ydata
		ind = event.ind

		# find the first ind in bSlabList.id
		firstInd = ind[0]

		if selectionType=='nodeSelection':
			nodeIdx = self.maskedNodes[self.currentSlice]['nodeMasked_nodeIdx'][firstInd]
			print('   nodeIdx:', nodeIdx)
		elif selectionType=='edgeSelection':
			edgeIdx = self.maskedNodes[self.currentSlice]['edgeIdxLines'][firstInd]
			slabIdx = self.maskedNodes[self.currentSlice]['slabIdxLines'][firstInd]
			nodeIdx = self.maskedNodes[self.currentSlice]['nodeIdxLines'][firstInd]
			print('   edgeIdx:', edgeIdx, 'slabIdx:', slabIdx, 'is also nodeIdx:', nodeIdx)
			if not np.isnan(nodeIdx):
				print('   converting to node selection')
				selectionType = 'nodeSelection'
				nodeIdx = int(round(nodeIdx)) # why is nodeIDx coming in as numpy.float64 ????
		# was this
		#slabIdx = self.maskedNodes[self.currentSlice]['slabIdxMasked'][firstInd]
		#nodeIdx = self.maskedNodes[self.currentSlice]['nodeIdxMasked'][firstInd]
		#edgeIdx = self.maskedNodes[self.currentSlice]['edgeIdxMasked'][firstInd]

		if self.mainWindow is not None:
			#if nodeIdx >= 0:
			if selectionType=='nodeSelection':
				if nKey and self.mySelectedNode is not None:
					print('   need to make a new edge to nodeIdx', nodeIdx)
					self.onpick_madeNewEdge = True
					print('\n=== bStackWidget.onpick() new edge ...')
					#newNodeIdx = self.myEvent(newNodeEvent)
					newEdgeEvent = {'type':'newEdge','srcNode':self.mySelectedNode, 'dstNode':nodeIdx}
					newEdgeIdx = self.myEvent(newEdgeEvent)
					self.selectNode(None) # cancel self.mySelectedNode
					self.selectEdge(newEdgeIdx) # select the new edge
				else:
					self.selectNode(nodeIdx)
					myEvent = bimpy.interface.bEvent('select node', nodeIdx=nodeIdx)
					self.selectNodeSignal.emit(myEvent)
			elif selectionType=='edgeSelection':
				self.selectEdge(edgeIdx)
				self.selectSlab(slabIdx)
				myEvent = bimpy.interface.bEvent('select edge', edgeIdx=edgeIdx, slabIdx=slabIdx)
				self.selectEdgeSignal.emit(myEvent)

	def options_defaults(self):
		print('options_defaults()')

		self.options = OrderedDict()

		"""
		Possible values are: Accent, Accent_r, Blues, Blues_r, BrBG, BrBG_r, BuGn, BuGn_r, BuPu, BuPu_r, CMRmap, CMRmap_r, Dark2, Dark2_r, GnBu, GnBu_r, Greens, Greens_r, Greys, Greys_r, OrRd, OrRd_r, Oranges, Oranges_r, PRGn, PRGn_r, Paired, Paired_r, Pastel1, Pastel1_r, Pastel2, Pastel2_r, PiYG, PiYG_r, PuBu, PuBuGn, PuBuGn_r, PuBu_r, PuOr, PuOr_r, PuRd, PuRd_r, Purples, Purples_r, RdBu, RdBu_r, RdGy, RdGy_r, RdPu, RdPu_r, RdYlBu, RdYlBu_r, RdYlGn, RdYlGn_r, Reds, Reds_r, Set1, Set1_r, Set2, Set2_r, Set3, Set3_r, Spectral, Spectral_r, Wistia, Wistia_r, YlGn, YlGnBu, YlGnBu_r, YlGn_r, YlOrBr, YlOrBr_r, YlOrRd, YlOrRd_r, afmhot, afmhot_r, autumn, autumn_r, binary, binary_r, bone, bone_r, brg, brg_r, bwr, bwr_r, cividis, cividis_r, cool, cool_r, coolwarm, coolwarm_r, copper, copper_r, cubehelix, cubehelix_r, flag, flag_r, gist_earth, gist_earth_r, gist_gray, gist_gray_r, gist_heat, gist_heat_r, gist_ncar, gist_ncar_r, gist_rainbow, gist_rainbow_r, gist_stern, gist_stern_r, gist_yarg, gist_yarg_r, gnuplot, gnuplot2, gnuplot2_r, gnuplot_r, gray, gray_r, hot, hot_r, hsv, hsv_r, inferno, inferno_r, jet, jet_r, magma, magma_r, nipy_spectral, nipy_spectral_r, ocean, ocean_r, pink, pink_r, plasma, plasma_r, prism, prism_r, rainbow, rainbow_r, seismic, seismic_r, spring, spring_r, summer, summer_r, tab10, tab10_r, tab20, tab20_r, tab20b, tab20b_r, tab20c, tab20c_r, terrain, terrain_r, twilight, twilight_r, twilight_shifted, twilight_shifted_r, viridis, viridis_r, winter, winter_r
		"""

		self.options['Stack'] = OrderedDict()
		self.options['Stack'] = OrderedDict({
			'colorLut': 'gray',
			'upSlidingZSlices': 5,
			'downSlidingZSlices': 5,
			})

		self.options['Tracing'] = OrderedDict()
		self.options['Tracing'] = OrderedDict({
			'nodePenSize': 10,
			'nodeColor': 'r',
			'nodeSelectionPenSize': 20,
			'nodeSelectionColor': 'y',
			'nodeSelectionFlashPenSize': 200,
			'nodeSelectionFlashColor': 'm',
			'showTracingAboveSlices': 5,
			'showTracingBelowSlices': 5,
			'tracingPenSize': 2,
			'tracingColor': 'c',
			'tracingSelectionPenSize': 4,
			'tracingSelectionColor': 'y',
			'tracingSelectionFlashPenSize': 80,
			'tracingSelectionFlashColor': 'm',
			'deadEndPenSize': 5,
			'deadEndColor': 'b',
			})

#class myStatusToolbarWidget(QtWidgets.QWidget):
class myStatusToolbarWidget(QtWidgets.QToolBar):
	def __init__(self, parent):
		print('myStatusToolbarWidget.__init__')
		#super(QtWidgets.QToolBar, self).__init__(parent)
		super(myStatusToolbarWidget, self).__init__(parent)
		self.myCanvasWidget = parent

		self.setMovable(False)

		myGroupBox = QtWidgets.QGroupBox()
		myGroupBox.setTitle('')

		hBoxLayout = QtWidgets.QHBoxLayout()

		self.lastActionLabel = QtWidgets.QLabel("Last Action: None")
		hBoxLayout.addWidget(self.lastActionLabel)

		xMousePosition_ = QtWidgets.QLabel("X (pixel)")
		self.xMousePosition = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(xMousePosition_)
		hBoxLayout.addWidget(self.xMousePosition)

		yMousePosition_ = QtWidgets.QLabel("Y (pixel)")
		self.yMousePosition = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(yMousePosition_)
		hBoxLayout.addWidget(self.yMousePosition)

		# finish
		myGroupBox.setLayout(hBoxLayout)
		self.addWidget(myGroupBox)

	def setMousePosition(self, point):
		self.xMousePosition.setText(str(round(point.x(),1)))
		self.xMousePosition.repaint()
		self.yMousePosition.setText(str(round(point.y(),1)))
		self.yMousePosition.repaint()

if __name__ == '__main__':
	import sys
	#from bimpy.interface import bStackWidget

	#path = '/Users/cudmore/box/DeepVess/data/invivo/20190613__0028.tif'
	if len(sys.argv) == 2:
		path = sys.argv[1]
	else:
		path = '/Users/cudmore/box/DeepVess/data/immuno-stack/mytest.tif'
		#path = '/Users/cudmore/box/DeepVess/data/invivo/20190613__0028.tif'

		# works well
		path = '/Users/cudmore/box/data/bImpy-Data/deepvess/mytest.tif'
		path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/20191017__0001.tif'

		# for this one, write code to revover tracing versus image scale
		# x/y=0.3107, z=0.5

		#path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/high_mag_top_of_node/tracing_20191217.tif'

	print('!!! bStackWidget __main__ is creating QApplication')
	app = QtWidgets.QApplication(sys.argv)

	sw = bStackWidget(mainWindow=app, parent=None, path=path)
	sw.show()
	sw.myStackView.setSlice(0)

	'''
	sw2 = bStackWidget(mainWindow=app, parent=None, path=path)
	sw2.show()
	sw2.setSlice(0)
	'''

	#print('app.topLevelWidgets():', app.topLevelWidgets())

	print('bStackWidget __main__ done')
	sys.exit(app.exec_())
