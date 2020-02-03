#20200130

from PyQt5 import QtGui, QtCore, QtWidgets

#import bimpy

class bOptionsDialog(QtWidgets.QDialog):
	"""
	General purpose dialog to set tracing display options.
	For now it is hard coded with pen size and masking

	todo: extend this to handle all options !!!
	"""
	def __init__(self, parent, parentStackView):
		"""
		parent is needed, otherwise self.show() does nothing

		to make modal, use
			self.setWindowModality(QtCore.Qt.ApplicationModal)
		"""
		super(bOptionsDialog, self).__init__(parent)

		self.parentStackView = parentStackView

		self.require_preComputeAllMasks = False #some changes require masks to be regenerated

		print('myTracingDialog.__init__()')

		# make a copy of options to modify
		self.localOptions = dict(self.parentStackView.options)

		self.setWindowTitle('bImPy Options')

		mainLayout = QtWidgets.QVBoxLayout()

		#print('building bOptionsDialog')
		for key1 in self.localOptions.keys():
			groupBox = QtWidgets.QGroupBox(key1)
			layout = QtWidgets.QFormLayout()
			for key2 in self.localOptions[key1].keys():
				#print(key1, key2)
				value = self.localOptions[key1][key2]
				theType = type(value)
				#print('   ', value, theType)
				if isinstance(value, int):
					#print('      is int')
					aSpinBox = QtWidgets.QSpinBox()
					aSpinBox.setValue(value)
					aSpinBox.setProperty('bobID_1', key1)
					aSpinBox.setProperty('bobID_2', key2)
					aSpinBox.valueChanged.connect(self.valueChanged)
					layout.addRow(QtWidgets.QLabel(key2), aSpinBox)

				elif isinstance(value, str):
					#print('      is str')
					aLineEdit = QtWidgets.QLineEdit()
					aLineEdit.setText(value)
					aLineEdit.setProperty('bobID_1', key1)
					aLineEdit.setProperty('bobID_2', key2)
					aLineEdit.textEdited.connect(self.valueChanged)
					layout.addRow(QtWidgets.QLabel(key2), aLineEdit)

				elif isinstance(value, bool):
					print('*** todo: implement bool in options')
					
			groupBox.setLayout(layout)
			mainLayout.addWidget(groupBox)

		self.formGroupBox = QtWidgets.QGroupBox("Form layout")
		layout = QtWidgets.QFormLayout()

		self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Apply |
			QtWidgets.QDialogButtonBox.Reset |
			QtWidgets.QDialogButtonBox.Cancel |
			QtWidgets.QDialogButtonBox.Ok)
		#buttonBox.accepted.connect(self.accept)
		#buttonBox.applied.connect(self.myAccept)
		self.buttonBox.clicked.connect(self.myClicked)
		self.buttonBox.accepted.connect(self.myAccept)
		self.buttonBox.rejected.connect(self.reject)

		#
		#mainLayout = QtWidgets.QVBoxLayout()
		mainLayout.addWidget(self.formGroupBox)
		mainLayout.addWidget(self.buttonBox)
		self.setLayout(mainLayout)

		# this is called from calling function and its return tells us accept/reject, 1/0
		#self.exec_()
		self.show()

	def myClicked(self, button):
		'''
		print('myClicked() button:')
		print('   ', self.buttonBox.buttonRole(button))
		print('   ', QtWidgets.QDialogButtonBox.ApplyRole)
		'''
		buttonRole = self.buttonBox.buttonRole(button)

		if buttonRole == QtWidgets.QDialogButtonBox.ApplyRole:
			print('   apply clicked')
			self.parentStackView.options = self.localOptions
			self.parentStackView.setSlice() # refresh

		elif buttonRole == QtWidgets.QDialogButtonBox.ResetRole:
			print('   reset clicked')

	def valueChanged(self, value):
		"""
		Set value in our local copy of options, self.localOptions
		"""
		if isinstance(value, int):
			pass
		elif isinstance(value, str):
			pass

		print('valueChanged() value:', value, self.sender().property('bobID_1'), self.sender().property('bobID_2'))
		bobID_1 = self.sender().property('bobID_1')
		bobID_2 = self.sender().property('bobID_2')
		try:
			self.localOptions[bobID_1][bobID_2] = value
		except (KeyError) as e:
			print('error in valueChanged() e:', e)

		if bobID_1=='Tracing' and bobID_2=='showTracingAboveSlices':
			self.require_preComputeAllMasks = True
		if bobID_1=='Tracing' and bobID_2=='nodePenSize':
			self.require_preComputeAllMasks = True

		if self.require_preComputeAllMasks:
			print('   require_preComputeAllMasks:', self.require_preComputeAllMasks)

	def myAccept(self):
		"""
		copy our localOptions back into parentStackView.options
		"""
		print('myTracingDialog.myAccept()')

		self.parentStackView.options = self.localOptions

		self.parentStackView.setSlice() # refresh

		self.accept() # close the dialog
