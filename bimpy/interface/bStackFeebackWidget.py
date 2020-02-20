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

	def slot_selectNode(self, myEvent):
		print('bStackFeebackWidget.slot_SelectNode() myEvent:', myEvent)
		if myEvent.eventType == 'select node':
			deleteNodeButton = self.findBobID('- Node')
			if myEvent.nodeIdx is not None:
				deleteNodeButton.setEnabled(True)
			else:
				deleteNodeButton.setEnabled(False)
			
	def slot_selectEdge(self, myEvent):
		print('bStackFeebackWidget.slot_SelectEdge() myEvent:', myEvent)
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
		print('button_callback() title:', title, 'bobID:', bobID)
		
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
		# view group
		viewGroupBox = QtWidgets.QGroupBox('View')
		#viewGroupBox.setStyleSheet('QGroupBox  {color: white;}')
		viewGroupBox.setStyleSheet(open(mystylesheet_css).read())
		viewGridLayout = QtWidgets.QGridLayout(self)
		
		row = 0
		
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
		
		# sub panel widgets
		row += 1
		button1 = QtWidgets.QPushButton("Contrast")
		button2 = QtWidgets.QPushButton("Annotations")
		button3 = QtWidgets.QPushButton("Status")
		button4 = QtWidgets.QPushButton("Line Profile")
		#
		viewGridLayout.addWidget(button1, row, 0)
		viewGridLayout.addWidget(button2, row, 1)
		row += 1
		viewGridLayout.addWidget(button3, row, 0)
		viewGridLayout.addWidget(button4, row, 1)
				
		# buttons
		row += 1
		button1 = QtWidgets.QPushButton("Napari")
		button2 = QtWidgets.QPushButton("Options")
		button3 = QtWidgets.QPushButton("Refresh")
		#
		viewGridLayout.addWidget(button1, row, 0)
		viewGridLayout.addWidget(button2, row, 1)
		row += 1
		viewGridLayout.addWidget(button3, row, 0)
		#viewGridLayout.addWidget(button4, row, 1)
		
		#
		# does not work
		for rowIdx in range(row):
			print('rowIdx:', rowIdx)
			viewGridLayout.setRowMinimumHeight(rowIdx, 20)
			viewGridLayout.setRowStretch(rowIdx,1)
		viewGroupBox.setLayout(viewGridLayout)
		mainLayout.addWidget(viewGroupBox)
		
		#
		# edit group
		editGroupBox = QtWidgets.QGroupBox('Edit')
		#editGroupBox.setStyleSheet('QGroupBox  {color: white;}')
		editGroupBox.setStyleSheet(open(mystylesheet_css).read())
		editGridLayout = QtWidgets.QGridLayout(self)
		
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
		