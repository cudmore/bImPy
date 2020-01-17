# 20190806

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
			self.slidingz_checkbox.setChecked(thisValue)
			#self.slidingz_checkbox.setTristate(False)
		else:
			print('WARNING: bStackFeebackWidget.set() not handled', this)

	def slidingz_statechange(self):
		#self.slidingz_checkbox.setTristate(False)
		print('sender:', self.sender().property('bobID'))
		self.mainWindow.signal('toggle sliding z', recursion=False)

	def checkbox_statechange(self):
		#self.slidingz_checkbox.setTristate(False)
		print('bStackFeedbackWidget.checkbox_statechange() sender bobID:', self.sender().property('bobID'))
		#self.mainWindow.signal('toggle sliding z', recursion=False)
		bobID = self.sender().property('bobID')
		if bobID == 'Sliding Z':
			self.mainWindow.signal('toggle sliding z', recursion=False)

	def buildUI(self):

		self.myQHBoxLayout = QtWidgets.QHBoxLayout(self)

		self.currentSlice_Label = QtWidgets.QLabel("current slice:")
		self.myQHBoxLayout.addWidget(self.currentSlice_Label)

		self.numSlices_Label = QtWidgets.QLabel("number of slices label:")
		self.myQHBoxLayout.addWidget(self.numSlices_Label)

		'''
		self.slidingz_checkbox = QtWidgets.QCheckBox('Sliding Z')
		self.slidingz_checkbox.setChecked(False)
		self.slidingz_checkbox.setProperty('bobID', 'sliding z')
		#self.slidingz_checkbox.setTristate()
		self.slidingz_checkbox.stateChanged.connect(self.slidingz_statechange)
		self.myQHBoxLayout.addWidget(self.slidingz_checkbox)
		'''


		checkBoxList = ['Sliding Z', 'Image', 'Tracing', 'Nodes', 'Edges']
		for checkBoxTitle in checkBoxList:
			thisCheckBox = QtWidgets.QCheckBox(checkBoxTitle)
			thisCheckBox.setChecked(False)
			thisCheckBox.setProperty('bobID', checkBoxTitle)
			thisCheckBox.stateChanged.connect(self.checkbox_statechange)
			self.myQHBoxLayout.addWidget(thisCheckBox)

		self.help_Label = QtWidgets.QLabel("Click image and press keyboard 'h' for help")
		self.myQHBoxLayout.addWidget(self.help_Label)
