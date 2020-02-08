# 20190806
from functools import partial

#from PyQt5 import QtGui, QtCore, QtWidgets
from qtpy import QtGui, QtCore, QtWidgets

import bimpy

class bStackFeebackWidget(QtWidgets.QWidget):
	#clickStateChange = QtCore.pyqtSignal(str, object)
	clickStateChange = QtCore.Signal(str, object)

	def __init__(self, mainWindow=None, parent=None, numSlices=0):
		super(bStackFeebackWidget, self).__init__(parent)

		self.mainWindow = mainWindow

		self.currentSlice = 0
		self.numSlices = numSlices
		#self.currentIntensity = None

		self.buildUI()

	def slot_StateChange2(self, myEvent):
		eventType = myEvent.eventType
		'''
		if eventType == 'select node':
			sliceIdx = myEvent.sliceIdx
			currentSliceStr = 'Slice ' + str(sliceIdx) + '/' + str(self.numSlices)
			self.currentSlice_Label.setText(currentSliceStr)
		'''
		if eventType in ['select node', 'select edge']:
			sliceIdx = myEvent.sliceIdx
			currentSliceStr = 'Slice ' + str(sliceIdx) + '/' + str(self.numSlices)
			self.currentSlice_Label.setText(currentSliceStr)

	def slot_StateChange(self, signalName, signalValue):
		"""
		signalValue: can be int, str, dict , ...
		"""
		#print('bStackFeebackWidget.slot_StateChange() signalName:', signalName, signalValue)
		#if signalName == 'num slices':
		#	text = str(signalValue)
		#	self.numSlices_Label.setText('of ' + text)
		if signalName == 'set slice':
			text = str(signalValue)
			currentSliceStr = 'Slice ' + text + '/' + str(self.numSlices)
			self.currentSlice_Label.setText(currentSliceStr)

		elif signalName == 'bSignal Sliding Z':
			#title = self.titleFromSignal(signalName)
			#thisCheck = self.findBobID(title)
			thisCheck = self.findBobID(signalName)
			if thisCheck is not None:
				thisCheck.setChecked(signalValue['displaySlidingZ'])
			else:
				print('slot_StateChange() did not find check with BobID title:', title)
		elif signalName == 'bSignal Nodes':
			#title = self.titleFromSignal(signalName)
			#thisCheck = self.findBobID(title)
			thisCheck = self.findBobID(signalName)
			if thisCheck is not None:
				thisCheck.setChecked(signalValue['showNodes'])
			else:
				print('slot_StateChange() did not find check with BobID title:', title)
		elif signalName == 'bSignal Edges':
			#title = self.titleFromSignal(signalName)
			#thisCheck = self.findBobID(title)
			thisCheck = self.findBobID(signalName)
			if thisCheck is not None:
				thisCheck.setChecked(signalValue['showEdges'])
			else:
				print('slot_StateChange() did not find check with BobID title:', title)
		else:
			print('WARNING: bStackFeebackWidget.set() not handled signalName:', signalName, 'signalValue:', signalValue)

	def findBobID(self, bobID):
		"""
		Can not use layout.findChild() or layout.children() ... bug in Qt or PyQt
		see: https://stackoverflow.com/questions/3077192/get-a-layouts-widgets-in-pyqt
		"""
		theRet = None
		for checkbox in self.myCheckboxList:
			currentBobID = checkbox.property('bobID')
			if currentBobID == bobID:
				#print('bStackFeedbackWidget.findBobID() found bobID:', currentBobID)
				theRet = checkbox
				break
		return theRet

	def onClick_Callback(self):
		"""
		Called when user clicks the check box

		this does not work? see here for some ideas:
		https://stackoverflow.com/questions/38437347/qcheckbox-state-change-pyqt4
		"""
		sender = self.sender()

		'''
		#self.slidingz_checkbox.setTristate(False)
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		print('bStackFeedbackWidget.onClick_Callback() sender bobID:', self.sender().property('bobID'), 'isShift:', isShift)
		'''

		title = sender.text()
		value = sender.isChecked()
		print('=== bStackFeedbackWidget.onClick_Callback() title:', title, 'value:', value)

		signal = self.signalFromTitle(title)

		# no matter what is click, we will emit a signal with 'bSignal ' + title
		self.clickStateChange.emit(signal, value)

	def signalFromTitle(self, title):
		""" prepend 'bSignal ' """
		signal = 'bSignal ' + title
		return signal

	def titleFromSignal(self, signal):
		""" remove prepended 'bSignal ' """
		title = signal.replace('bSignal ', '')
		return title

	def optionsButton_Callback(self):
		optionsDialog = bimpy.interface.bOptionsDialog(self, self.mainWindow.myStackView)

	def napariButton_Callback(self):
		self.mainWindow.openNapari()

	def buildUI(self):

		self.myMainLayout = QtWidgets.QHBoxLayout(self)

		currentSliceStr = 'Slice 0 /' + str(self.numSlices)
		self.currentSlice_Label = QtWidgets.QLabel(currentSliceStr)
		self.myMainLayout.addWidget(self.currentSlice_Label)

		#self.numSlices_Label = QtWidgets.QLabel("of")
		#self.myMainLayout.addWidget(self.numSlices_Label)

		self.myCheckboxList = []

		# titles of the check boxes, commands for signal/slot will be 'bCommand <title>'
		#self.checkBoxList = ['Sliding Z', 'Tracing', 'Nodes', 'Edges']
		self.checkBoxList = ['Image', 'Sliding Z', 'Nodes', 'Edges']
		defaultValues = [True, False, True, True]

		for idx, checkBoxTitle in enumerate(self.checkBoxList):
			thisCheckBox = QtWidgets.QCheckBox(checkBoxTitle)

			defaultValue = defaultValues[idx]
			thisCheckBox.setChecked(defaultValue)

			# bobID is the title prepended with 'bCommand '
			thisCheckBox.setProperty('bobID', self.signalFromTitle(checkBoxTitle))

			self.myCheckboxList.append(thisCheckBox)

			thisCheckBox.clicked.connect(self.onClick_Callback)

			self.myMainLayout.addWidget(thisCheckBox)

		optionsButton = QtWidgets.QPushButton('Options')
		optionsButton.clicked.connect(self.optionsButton_Callback)
		self.myMainLayout.addWidget(optionsButton)

		napariButton = QtWidgets.QPushButton('Napari')
		napariButton.clicked.connect(self.napariButton_Callback)
		self.myMainLayout.addWidget(napariButton)

		'''
		self.help_Label = QtWidgets.QLabel("Click image and press keyboard 'h' for help")
		self.myMainLayout.addWidget(self.help_Label)
		'''
