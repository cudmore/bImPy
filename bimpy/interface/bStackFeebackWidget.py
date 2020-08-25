# Robert Cudmore
# 20200218

"""
Using css style sheets !!!
"""

import os

from qtpy import QtGui, QtCore, QtWidgets

class bStackFeebackWidget(QtWidgets.QWidget):
	feedbackStateChange = QtCore.Signal(str, object)

	def __init__(self, mainWindow=None, parent=None):
		super(bStackFeebackWidget, self).__init__(parent)

		self.mainWindow = mainWindow

		self.buildUI()

	def slot_OptionsStateChange(self, key1, key2, value):
		print('    bStackFeedbackWidget.slot_OptionsStateChange()', key1, key2, value)
		doRepaint = False
		if key1 == 'Panels':
			checkbox = self.findBobID(key2)
			if checkbox is not None:
				checkbox.setChecked(value)
				self.repaint()

	def slot_selectNode(self, myEvent):
		#print('    bStackFeebackWidget.slot_SelectNode() myEvent:', myEvent)
		myEvent.printSlot('bStackFeebackWidget.slot_SelectNode()')
		if myEvent.eventType == 'select node':
			deleteNodeButton = self.findBobID('- Node')
			if myEvent.nodeIdx is not None:
				deleteNodeButton.setEnabled(True)
			else:
				deleteNodeButton.setEnabled(False)

	def slot_DisplayStateChange(self, signal, displayStateDict):
		print('    bStackFeedbackWidget.slot_DisplayStateChange() signal:', signal)
		#if signal == 'image':

	def slot_selectEdge(self, myEvent):
		myEvent.printSlot('bStackFeebackWidget.slot_selectEdge()')
		if myEvent.eventType == 'select edge':
			#
			deleteEdgeButton = self.findBobID('- Edge')
			if myEvent.edgeIdx is not None:
				deleteEdgeButton.setEnabled(True)
			else:
				deleteEdgeButton.setEnabled(False)
			#
			deleteSlabButton = self.findBobID('- Slab')
			if myEvent.slabIdx is not None:
				deleteSlabButton.setEnabled(True)
			else:
				deleteSlabButton.setEnabled(False)
			#
			slabToNodeButton = self.findBobID('To Node')
			if myEvent.slabIdx is not None:
				slabToNodeButton.setEnabled(True)
			else:
				slabToNodeButton.setEnabled(False)

	def button_callback(self):
		sender = self.sender()
		title = sender.text()
		bobID = sender.property('bobID')
		print('=== bStackFeebackWidget.button_callback() title:', title, 'bobID:', bobID)

		if title == 'Save Tracing':
			self.mainWindow.signal('save')
		elif title == 'Load Tracing':
			self.mainWindow.signal('load')
		elif title == 'Save Stack Copy':
			self.mainWindow.signal('save stack copy')

		# search
		#elif title == '1':
		elif title=='Dead end near other slab':
			distThreshold = self.minSpinBox.value()
			self.mainWindow.signal('search 1', value=distThreshold)
		elif title=='Dead end near other nodes':
			distThreshold = self.minSpinBox.value()
			self.mainWindow.signal('search 1_1', value=distThreshold)
		elif title=='Slab Gaps':
			distThreshold = self.minSpinBox.value()
			self.mainWindow.signal('search 1_2', value=distThreshold)
		#elif title == '2':
		elif title == 'All Dead Ends':
			self.mainWindow.signal('search 2')
		elif title=='Close Nodes':
			distThreshold = self.minSpinBox.value()
			self.mainWindow.signal('search 1_5', value=distThreshold)
		elif title=='Close Slabs':
			distThreshold = self.minSpinBox.value()
			self.mainWindow.signal('search 1_6', value=distThreshold)
		#elif title == '3':
		elif title == 'Shortest Path':
			# shortest path
			node1 = self.node1SpinBox.value()
			node2 = self.node2SpinBox.value()
			self.mainWindow.signal('search 3', value=(node1,node2))
		#elif title == '4':
		elif title == 'All Paths':
			# all paths
			node1 = self.node1SpinBox.value()
			node2 = self.node2SpinBox.value()
			self.mainWindow.signal('search 4', value=(node1,node2))

		#elif title == 'Shortest Loop':
		#	# all paths
		#	node1 = self.node1SpinBox.value()
		#	self.mainWindow.signal('search 5', value=node1)

		elif title == 'All Subgraphs':
			# all subgraphs
			self.mainWindow.signal('search 5')

		elif title == 'All Loops':
			# all paths
			node1 = self.node1SpinBox.value()
			self.mainWindow.signal('search 6', value=node1)

		elif title == 'Analyze All Diameters':
			self.mainWindow.signal('Analyze All Diameters') # calls slabList.analyseSlabIntensity()

		else:
			print('    bStackFeedbackWidget.button_callback() case not taken:', title)

	def checkbox_callback(self, isChecked):
		sender = self.sender()
		title = sender.text()
		bobID = sender.property('bobID')
		print('bStackFeedbackWidget.checkbox_callback() title:', title, 'isChecked:', isChecked, 'bobID:', bobID)
		self.mainWindow.options['Panels'][bobID] = not self.mainWindow.options['Panels'][bobID]
		self.mainWindow.updateDisplayedWidgets()
		"""
		if title == 'Nodes':
			self.mainWindow.options['Panels']['showNodeList'] = not self.mainWindow.options['Panels']['showNodeList']
			self.mainWindow.updateDisplayedWidgets()
		elif title == 'Edges':
			self.mainWindow.options['Panels']['showEdgeList'] = not self.mainWindow.options['Panels']['showEdgeList']
			self.mainWindow.updateDisplayedWidgets()
		elif title == 'Search':
			self.mainWindow.options['Panels']['showSearch'] = not self.mainWindow.options['Panels']['showSearch']
			self.mainWindow.updateDisplayedWidgets()
		elif title == 'Contrast':
			self.mainWindow.options['Panels']['showContrast'] = not self.mainWindow.options['Panels']['showContrast']
			self.mainWindow.updateDisplayedWidgets()
		elif title == 'Status':
			self.mainWindow.options['Panels']['showStatus'] = not self.mainWindow.options['Panels']['showStatus']
			self.mainWindow.updateDisplayedWidgets()
		elif title == 'Line Profile':
			self.mainWindow.options['Panels']['showLineProfile'] = not self.mainWindow.options['Panels']['showLineProfile']
			self.mainWindow.updateDisplayedWidgets()
		"""

	def findBobID(self, bobID):
		"""
		Can not use layout.findChild() or layout.children() ... bug in Qt or PyQt
		see: https://stackoverflow.com/questions/3077192/get-a-layouts-widgets-in-pyqt
		"""
		theRet = None
		for checkbox in self.myWidgetList:
			currentBobID = checkbox.property('bobID')
			if currentBobID == bobID:
				#print('bStackFeedbackWidget.findBobID() found bobID:', currentBobID)
				theRet = checkbox
				break
		return theRet

	def buildUI(self):

		self.myWidgetList = []

		mainLayout = QtWidgets.QVBoxLayout(self)
		#mainLayout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize) # fixed size

		myPath = os.path.dirname(os.path.abspath(__file__))
		mystylesheet_css = os.path.join(myPath, 'css', 'mystylesheet.css')

		#
		# file
		fileGridLayout = QtWidgets.QGridLayout()
		button1 = QtWidgets.QPushButton('Save Tracing')
		button2 = QtWidgets.QPushButton('Load Tracing')
		button3 = QtWidgets.QPushButton('Save Stack Copy')

		button1.clicked.connect(self.button_callback)
		button2.clicked.connect(self.button_callback)
		button3.clicked.connect(self.button_callback)

		row = 0
		fileGridLayout.addWidget(button1, row, 0)
		fileGridLayout.addWidget(button2, row, 1)
		fileGridLayout.addWidget(button3, row, 2)
		mainLayout.addLayout(fileGridLayout)

		#
		# view group
		# todo: put this back in
		"""
		viewGroupBox = QtWidgets.QGroupBox('View')
		#viewGroupBox.setStyleSheet('QGroupBox  {color: white;}')
		viewGroupBox.setStyleSheet(open(mystylesheet_css).read())
		viewGridLayout = QtWidgets.QGridLayout(self)

		row = 0

		#
		# image display
		radio1 = QtWidgets.QRadioButton("Ch 1")
		radio2 = QtWidgets.QRadioButton("Ch 2")
		radio3 = QtWidgets.QRadioButton("Ch 3")
		radio4 = QtWidgets.QRadioButton("RGB")
		radio1.setChecked(True)
		#
		viewGridLayout.addWidget(radio1, row, 0)
		viewGridLayout.addWidget(radio2, row, 1)
		row += 1
		viewGridLayout.addWidget(radio3, row, 0)
		viewGridLayout.addWidget(radio4, row, 1)

		# image visuals, show/hide (image, sliding z, nodes, edges)
		row += 1
		check1 = QtWidgets.QCheckBox("Image")
		check2 = QtWidgets.QCheckBox("Sliding Z")
		check3 = QtWidgets.QCheckBox("Nodes")
		check4 = QtWidgets.QCheckBox("Edges")
		#
		viewGridLayout.addWidget(check1, row, 0)
		viewGridLayout.addWidget(check2, row, 1)
		row += 1
		viewGridLayout.addWidget(check3, row, 0)
		viewGridLayout.addWidget(check4, row, 1)

		# finalize
		for rowIdx in range(row):
			#print('rowIdx:', rowIdx)
			viewGridLayout.setRowMinimumHeight(rowIdx, 20)
			viewGridLayout.setRowStretch(rowIdx,1)

		viewGroupBox.setLayout(viewGridLayout)
		mainLayout.addWidget(viewGroupBox)

		# todo: put this back in
		"""

		with open(mystylesheet_css) as f:
			myStyleSheet = f.read()

		#
		# search group
		searchGroupBox = QtWidgets.QGroupBox('Search')
		#searchGroupBox.setStyleSheet(open(mystylesheet_css).read())
		searchGroupBox.setStyleSheet(myStyleSheet)
		searchGridLayout = QtWidgets.QGridLayout()

		row = 0

		spinBoxWidth = 64

		minLabel = QtWidgets.QLabel("Distance Threshold (um)")
		self.minSpinBox = QtWidgets.QSpinBox()
		self.minSpinBox.setMaximumWidth(spinBoxWidth)
		self.minSpinBox.setMinimum(0)
		self.minSpinBox.setMaximum(1e6)
		self.minSpinBox.setValue(10)

		nodeLabel = QtWidgets.QLabel("Nodes")
		self.node1SpinBox = QtWidgets.QSpinBox()
		self.node1SpinBox.setMaximumWidth(spinBoxWidth)
		self.node1SpinBox.setMinimum(0)
		self.node1SpinBox.setMaximum(1e6)
		self.node1SpinBox.setValue(10)
		#
		self.node2SpinBox = QtWidgets.QSpinBox()
		self.node2SpinBox.setMaximumWidth(spinBoxWidth)
		self.node2SpinBox.setMinimum(0)
		self.node2SpinBox.setMaximum(1e6)
		self.node2SpinBox.setValue(20)

		searchGridLayout.addWidget(minLabel, row, 0)
		searchGridLayout.addWidget(self.minSpinBox, row, 1)
		#
		row += 1
		searchGridLayout.addWidget(nodeLabel, row, 0)
		searchGridLayout.addWidget(self.node1SpinBox, row, 1)
		searchGridLayout.addWidget(self.node2SpinBox, row, 2)

		row += 1

		button7 = QtWidgets.QPushButton("Dead end near other slab")
		button7.setToolTip('search for dead end nodes near a slab')
		button8 = QtWidgets.QPushButton("All Dead Ends")
		button8.setToolTip('search for all dead end edges')
		#
		button7_1 = QtWidgets.QPushButton("Dead end near other nodes")
		button7_2 = QtWidgets.QPushButton("Slab Gaps")
		#
		button8_1 = QtWidgets.QPushButton("Close Nodes")
		button8_1.setToolTip('Close Nodes')
		button8_2 = QtWidgets.QPushButton("Close Slabs")
		button8_2.setToolTip('Close Slabs')
		#
		button9 = QtWidgets.QPushButton("Shortest Path")
		button9.setToolTip('search for shortest path between nodes')
		button10 = QtWidgets.QPushButton("All Paths")
		button10.setToolTip('search for all paths between nodes')
		#
		button7.clicked.connect(self.button_callback)
		button7_1.clicked.connect(self.button_callback)
		button7_2.clicked.connect(self.button_callback)
		button8.clicked.connect(self.button_callback)
		button8_1.clicked.connect(self.button_callback)
		button8_2.clicked.connect(self.button_callback)
		button9.clicked.connect(self.button_callback)
		button10.clicked.connect(self.button_callback)
		#
		searchGridLayout.addWidget(button7, row, 0)
		searchGridLayout.addWidget(button8, row, 1)
		row += 1
		searchGridLayout.addWidget(button7_1, row, 0)
		searchGridLayout.addWidget(button7_2, row, 1)
		row += 1
		searchGridLayout.addWidget(button8_1, row, 0)
		searchGridLayout.addWidget(button8_2, row, 1)
		row += 1
		searchGridLayout.addWidget(button9, row, 0)
		searchGridLayout.addWidget(button10, row, 1)

		row += 1
		button11 = QtWidgets.QPushButton("All Subgraphs")
		button11.setToolTip('Shortest All Subgraphs')
		'''
		button11 = QtWidgets.QPushButton("Shortest Loop")
		button11.setToolTip('Shortest Loop')
		button11.setEnabled(False) # shortest loop does not work, use "All Loops"
		'''
		button12 = QtWidgets.QPushButton("All Loops")
		button12.setToolTip('All Loops')
		#
		button11.clicked.connect(self.button_callback)
		button12.clicked.connect(self.button_callback)
		#
		searchGridLayout.addWidget(button11, row, 0)
		searchGridLayout.addWidget(button12, row, 1)

		# finalize
		searchGroupBox.setLayout(searchGridLayout)
		mainLayout.addWidget(searchGroupBox)

		#
		# analysis group
		analysisGroupBox = QtWidgets.QGroupBox('Analysis')
		#analysisGroupBox.setStyleSheet(open(mystylesheet_css).read())
		analysisGroupBox.setStyleSheet(myStyleSheet)
		analysisGridLayout = QtWidgets.QGridLayout()

		row = 0
		button1 = QtWidgets.QPushButton("Analyze All Diameters")
		button1.clicked.connect(self.button_callback)
		analysisGridLayout.addWidget(button1, row, 0)

		# finalize
		analysisGroupBox.setLayout(analysisGridLayout)
		mainLayout.addWidget(analysisGroupBox)

		#
		# panels group
		panelsGroupBox = QtWidgets.QGroupBox('Panels')
		#viewGroupBox.setStyleSheet('QGroupBox  {color: white;}')
		#panelsGroupBox.setStyleSheet(open(mystylesheet_css).read())
		panelsGroupBox.setStyleSheet(myStyleSheet)
		panelsGridLayout = QtWidgets.QGridLayout()

		numCol = 3
		col = 0
		row = 0
		checkBoxList = ['showNodeList', 'showEdgeList', 'showSearch', 'showContrast', 'showStatus', 'showLineProfile']
		niceNameList = ['Node List', 'Edge List', 'Search List', 'Contrast Panel', 'Status Panel', 'Line Profile Panel']
		for idx, aCheckBoxName in enumerate(checkBoxList):
			check1 = QtWidgets.QCheckBox(niceNameList[idx])
			check1.setChecked(self.mainWindow.options['Panels'][aCheckBoxName])
			check1.setProperty('bobID', aCheckBoxName)
			check1.clicked.connect(self.checkbox_callback)
			self.myWidgetList.append(check1)
			panelsGridLayout.addWidget(check1, row, col)
			col += 1
			if col==numCol:
				row += 1
				col = 0

		"""
		#button2 = QtWidgets.QPushButton("Annotations")
		check1 = QtWidgets.QCheckBox("Nodes")
		check1.setChecked(self.mainWindow.options['Panels']['showNodeList'])
		check1.setProperty('bobID', 'showNodeList')
		check1.clicked.connect(self.checkbox_callback)
		self.myWidgetList.append(check1)
		#
		check2 = QtWidgets.QCheckBox("Edges")
		check2.setChecked(self.mainWindow.options['Panels']['showEdgeList'])
		check2.setProperty('bobID', 'showEdgeList')
		check2.clicked.connect(self.checkbox_callback)
		self.myWidgetList.append(check2)
		#
		check3 = QtWidgets.QCheckBox("Search")
		check3.setChecked(self.mainWindow.options['Panels']['showSearch'])
		check3.setProperty('bobID', 'showSearch')
		check3.clicked.connect(self.checkbox_callback)
		self.myWidgetList.append(check3)

		#
		check4 = QtWidgets.QCheckBox("Contrast")
		check4.setChecked(self.mainWindow.options['Panels']['showContrast'])
		check4.setProperty('bobID', 'showContrast')
		check4.clicked.connect(self.checkbox_callback)
		self.myWidgetList.append(check4)
		#
		check5 = QtWidgets.QCheckBox("Status")
		check5.setChecked(self.mainWindow.options['Panels']['showStatus'])
		check5.clicked.connect(self.checkbox_callback)
		#
		check6 = QtWidgets.QCheckBox("Line Profile")
		check6.setChecked(self.mainWindow.options['Panels']['showLineProfile'])
		check6.clicked.connect(self.checkbox_callback)
		#
		panelsGridLayout.addWidget(check1, row, 0)
		panelsGridLayout.addWidget(check2, row, 1)
		panelsGridLayout.addWidget(check3, row, 2)
		row += 1
		panelsGridLayout.addWidget(check4, row, 0)
		panelsGridLayout.addWidget(check5, row, 1)
		panelsGridLayout.addWidget(check6, row, 2)
		"""

		row += 1
		button7 = QtWidgets.QPushButton("Napari")
		button8 = QtWidgets.QPushButton("Options")
		button9 = QtWidgets.QPushButton("Refresh")
		#
		button7.clicked.connect(self.button_callback)
		button8.clicked.connect(self.button_callback)
		button9.clicked.connect(self.button_callback)
		#
		panelsGridLayout.addWidget(button7, row, 0)
		panelsGridLayout.addWidget(button8, row, 1)
		panelsGridLayout.addWidget(button9, row, 2)

		panelsGroupBox.setLayout(panelsGridLayout)
		mainLayout.addWidget(panelsGroupBox)

		#
		# edit group
		editGroupBox = QtWidgets.QGroupBox('Edit')
		#editGroupBox.setStyleSheet('QGroupBox  {color: white;}')
		#editGroupBox.setStyleSheet(open(mystylesheet_css).read())
		editGroupBox.setStyleSheet(myStyleSheet)
		editGridLayout = QtWidgets.QGridLayout()

		editButtonList = ['- Node', '- Edge', '- Slab', 'To Node']

		numCol = 3
		row=0
		col = 0
		for editButtonName in editButtonList:
			aButton = QtWidgets.QPushButton(editButtonName)
			aButton.setProperty('bobID', editButtonName)
			aButton.clicked.connect(self.button_callback)
			editGridLayout.addWidget(aButton, row, col)

			self.myWidgetList.append(aButton)

			col += 1
			if col == numCol:
				col = 0
				row += 1

		'''
		aCheckbox = QtWidgets.QCheckBox('0,0')
		bCheckbox = QtWidgets.QCheckBox('0,1')
		editGridLayout.addWidget(aCheckbox, row, 0)
		editGridLayout.addWidget(bCheckbox, row, 1)
		row += 1
		aCheckbox = QtWidgets.QCheckBox('1,0')
		bCheckbox = QtWidgets.QCheckBox('1,1')
		editGridLayout.addWidget(aCheckbox, row, 0)
		editGridLayout.addWidget(bCheckbox, row, 1)
		'''

		editGroupBox.setLayout(editGridLayout)
		mainLayout.addWidget(editGroupBox)
