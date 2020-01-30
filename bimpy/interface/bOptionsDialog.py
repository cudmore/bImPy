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
		"""
		super(bOptionsDialog, self).__init__(parent)

		self.parentStackView = parentStackView

		self.require_preComputeAllMasks = False

		print('myTracingDialog.__init__()')

		#self.setWindowModality(QtCore.Qt.ApplicationModal)

		# make a copy of options to modify
		self.localOptions = dict(self.parentStackView.options)


		self.formGroupBox = QtWidgets.QGroupBox("Form layout")
		layout = QtWidgets.QFormLayout()

		# requires _preComputeAllMasks()
		showTracingAboveSlices = self.localOptions['Tracing']['showTracingAboveSlices']
		self.showTracingAboveSlices_spinbox = QtWidgets.QSpinBox()
		self.showTracingAboveSlices_spinbox.setValue(showTracingAboveSlices)
		self.showTracingAboveSlices_spinbox.setProperty('bobID_1', 'Tracing')
		self.showTracingAboveSlices_spinbox.setProperty('bobID_2', 'showTracingAboveSlices')
		self.showTracingAboveSlices_spinbox.valueChanged.connect(self.valueChanged)

		tracingPenSize = self.localOptions['Tracing']['tracingPenSize']
		self.tracingPenSize_spinbox = QtWidgets.QSpinBox()
		self.tracingPenSize_spinbox.setMaximum(100)
		self.tracingPenSize_spinbox.setValue(tracingPenSize)
		self.tracingPenSize_spinbox.setProperty('bobID_1', 'Tracing')
		self.tracingPenSize_spinbox.setProperty('bobID_2', 'tracingPenSize')
		self.tracingPenSize_spinbox.valueChanged.connect(self.valueChanged)

		layout.addRow(QtWidgets.QLabel("+/- Slices:"), self.showTracingAboveSlices_spinbox)
		layout.addRow(QtWidgets.QLabel("Pen Size:"), self.tracingPenSize_spinbox)

		self.formGroupBox.setLayout(layout)

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
		mainLayout = QtWidgets.QVBoxLayout()
		mainLayout.addWidget(self.formGroupBox)
		mainLayout.addWidget(self.buttonBox)
		self.setLayout(mainLayout)

		self.setWindowTitle('Tracing Display Options')

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

	def valueChanged(self, int):
		"""
		Set value in our local copy of options, self.localOptions
		"""
		print('valueChanged() int:', int, self.sender().property('bobID_1'), self.sender().property('bobID_2'))
		bobID_1 = self.sender().property('bobID_1')
		bobID_2 = self.sender().property('bobID_2')
		try:
			self.localOptions[bobID_1][bobID_2] = int
		except (KeyError) as e:
			print('error in valueChanged() e:', e)

		if bobID_1=='Tracing' and bobID_2=='showTracingAboveSlices':
			self.require_preComputeAllMasks = True
			print('require_preComputeAllMasks:', self.require_preComputeAllMasks)

	def myAccept(self):
		"""
		copy our localOptions back into parentStackView.options
		"""
		print('myTracingDialog.myAccept()')

		self.parentStackView.options = self.localOptions

		self.parentStackView.setSlice() # refresh

		self.accept() # close the dialog
