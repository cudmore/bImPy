# 20190806
from functools import partial

from PyQt5 import QtGui, QtCore, QtWidgets

class bStackFeebackWidget(QtWidgets.QWidget):
	def __init__(self, mainWindow=None, parent=None):
		super(bStackFeebackWidget, self).__init__(parent)

		self.mainWindow = mainWindow

		self.currentSlice = None
		self.numSlices = None
		self.currentIntensity = None

		self.buildUI()

	def setFeedback(self, this, thisValue):
		if this == 'num slices':
			text = str(thisValue)
			self.numSlices_Label.setText('of ' + text)
		elif this == 'set slice':
			text = str(thisValue)
			self.currentSlice_Label.setText('slice ' + text)
		elif this == 'sliding z':
			#self.slidingz_checkbox.setChecked(thisValue)
			#self.slidingz_checkbox.setTristate(False)
			thisCheck = self.findBobID('Sliding Z')
			thisCheck.setChecked(thisValue)
		else:
			print('WARNING: bStackFeebackWidget.set() not handled', this)

	'''
	def slidingz_statechange(self):
		#self.slidingz_checkbox.setTristate(False)
		print('sender:', self.sender().property('bobID'))
		self.mainWindow.signal('toggle sliding z', recursion=False)
	'''

	def toggleInterface(event, toThis):
		if event == 'toggle tracing':
			tracingCheckboxWidget = self.findBobID('Tracing')
			tracingCheckboxWidget.setChecked(toThis)

	def findBobID(self, bobID):
		"""

		Can not use layout.findChild() or layout.children() ... bug in Qt or PyQt

		see: https://stackoverflow.com/questions/3077192/get-a-layouts-widgets-in-pyqt
		"""
		theRet = None
		'''
		numChildren = self.myMainLayout.count()
		for childIdx in range(numChildren):
			item = self.myMainLayout.itemAt(childIdx)
			widget = item.widget()
			currentBobID = widget.property('bobID')
			if currentBobID == bobID:
				print('bStackFeedbackWidget.findBobID() found bobID:', currentBobID)
				theRet = widget
				break
		return theRet
		'''

		for checkbox in self.myCheckboxList:
			currentBobID = checkbox.property('bobID')
			if currentBobID == bobID:
				print('bStackFeedbackWidget.findBobID() found bobID:', currentBobID)
				theRet = checkbox
				break
		return theRet

	def checkbox_statechange(self, checkbox):
		"""
		Called when user clicks the check box

		this does not work? see here for some ideas:
		https://stackoverflow.com/questions/38437347/qcheckbox-state-change-pyqt4
		"""
		#self.slidingz_checkbox.setTristate(False)
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		print('bStackFeedbackWidget.checkbox_statechange() sender bobID:', self.sender().property('bobID'), 'isShift:', isShift)
		#self.mainWindow.signal('toggle sliding z', recursion=False)
		bobID = self.sender().property('bobID')
		print('bobID:', type(bobID), bobID)

		widget = self.findBobID(bobID)
		if widget == None:
			print('warning: checkbox_statechange() did not find widget with bobID:', bobID)
			return

		# get the current state
		value = widget.isChecked()
		print('checkbox_statechange() got widget for', bobID, 'and value is:', type(value), value)

		#self.mainWindow.signal('toggle tracing', value=value, recursion=False)

		if bobID == 'Sliding Z':
			self.mainWindow.signal('toggle sliding z', value=value, recursion=False)
		elif bobID == 'Tracing':
			self.mainWindow.signal('toggle tracing', value=value, recursion=False)
		else:
			print('bStackFeedbackWidget.checkbox_statechange() case not taken, bobID:', bobID)
		print('done')

	def buildUI(self):

		self.myMainLayout = QtWidgets.QHBoxLayout(self)

		self.currentSlice_Label = QtWidgets.QLabel("current slice:")
		self.myMainLayout.addWidget(self.currentSlice_Label)

		self.numSlices_Label = QtWidgets.QLabel("number of slices label:")
		self.myMainLayout.addWidget(self.numSlices_Label)

		self.myCheckboxList = []

		checkBoxList = ['Sliding Z', 'Tracing', 'Nodes', 'Edges']
		idx = 0
		for checkBoxTitle in checkBoxList:
			thisCheckBox = QtWidgets.QCheckBox(checkBoxTitle)
			thisCheckBox.setChecked(False)
			thisCheckBox.setProperty('bobID', checkBoxTitle)

			self.myCheckboxList.append(thisCheckBox)

			slot = partial(self.checkbox_statechange, self.myCheckboxList[idx])

			thisCheckBox.stateChanged.connect(lambda x: slot())
			#thisCheckBox.stateChanged.connect(self.checkbox_statechange)


			self.myMainLayout.addWidget(thisCheckBox)

			idx += 1

		self.help_Label = QtWidgets.QLabel("Click image and press keyboard 'h' for help")
		self.myMainLayout.addWidget(self.help_Label)

		self.findBobID('Nodes')
