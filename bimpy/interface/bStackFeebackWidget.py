# 20190806
from functools import partial

from PyQt5 import QtGui, QtCore, QtWidgets

class bStackFeebackWidget(QtWidgets.QWidget):
	clickStateChange = QtCore.pyqtSignal(str, object)

	def __init__(self, mainWindow=None, parent=None):
		super(bStackFeebackWidget, self).__init__(parent)

		self.mainWindow = mainWindow

		self.currentSlice = None
		self.numSlices = None
		self.currentIntensity = None

		self.buildUI()

	def slot_StateChange(self, signalName, signalValue):
		"""
		signalValue: can be int, str, dict , ...
		"""
		print('bStackFeebackWidget.slot_StateChange() signalName:', signalName, signalValue)
		if signalName == 'num slices':
			text = str(signalValue)
			self.numSlices_Label.setText('of ' + text)
		elif signalName == 'set slice':
			text = str(signalValue)
			self.currentSlice_Label.setText('slice ' + text)

		elif signalName == 'sliding z':
			thisCheck = self.findBobID('Sliding Z')
			if thisCheck is not None:
				thisCheck.setChecked(thisValue)
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

		#self.slidingz_checkbox.setTristate(False)
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		print('bStackFeedbackWidget.onClick_Callback() sender bobID:', self.sender().property('bobID'), 'isShift:', isShift)
		#self.mainWindow.signal('toggle sliding z', recursion=False)

		#bobID = self.sender().property('bobID')
		#print('bobID:', type(bobID), bobID)

		'''
		widget = self.findBobID(bobID)
		if widget == None:
			print('warning: onClick_Callback() did not find widget with bobID:', bobID)
			return
		'''

		# get the current state
		title = sender.text()
		value = sender.isChecked()
		#value = widget.isChecked()
		#print('!!!***!!!   onClick_Callback() got widget for', bobID, 'and value is:', type(value), value)
		print('!!!***!!! onClick_Callback() title:', title, 'value:', value)

		#self.mainWindow.signal('toggle tracing', value=value, recursion=False)

		if title == 'Sliding Z':
			self.clickStateChange.emit('Sliding Z', value)
			#self.mainWindow.signal('toggle sliding z', value=value, recursion=False)
		elif title == 'Tracing':
			self.clickStateChange.emit('Tracing', value)
			#self.mainWindow.signal('toggle tracing', value=value, recursion=False)
		else:
			print('bStackFeedbackWidget.onClick_Callback() case not taken, title:', title)
		print('done')

	def buildUI(self):

		self.myMainLayout = QtWidgets.QHBoxLayout(self)

		self.currentSlice_Label = QtWidgets.QLabel("current slice:")
		self.myMainLayout.addWidget(self.currentSlice_Label)

		self.numSlices_Label = QtWidgets.QLabel("number of slices label:")
		self.myMainLayout.addWidget(self.numSlices_Label)

		self.myCheckboxList = []

		self.checkBoxList = ['Sliding Z', 'Tracing', 'Nodes', 'Edges']
		#idx = 0
		for checkBoxTitle in self.checkBoxList:
			thisCheckBox = QtWidgets.QCheckBox(checkBoxTitle)
			thisCheckBox.setChecked(False)
			thisCheckBox.setProperty('bobID', checkBoxTitle)

			self.myCheckboxList.append(thisCheckBox)

			#slot = partial(self.onClick_Callback, self.myCheckboxList[idx])

			thisCheckBox.clicked.connect(self.onClick_Callback)
			#thisCheckBox.clicked.connect(lambda x: slot())
			#thisCheckBox.stateChanged.connect(lambda x: slot())
			#thisCheckBox.stateChanged.connect(self.onClick_Callback)


			self.myMainLayout.addWidget(thisCheckBox)

			#idx += 1

		self.help_Label = QtWidgets.QLabel("Click image and press keyboard 'h' for help")
		self.myMainLayout.addWidget(self.help_Label)

		#self.findBobID('Nodes')
