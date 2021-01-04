# 20200310
# Robert Cudmore

from qtpy import QtGui, QtCore, QtWidgets

class myOkCancelDialog:
	def __init__(self, type):
		self._ok = False

		if type == 'close stack':
			title = 'Close Stack'
			messageText = 'Sure you want to close? Unsaved changes will be lost...'
		elif type == 'new node':
			title = 'New Node'
			messageText = 'Sure you want to make a new node?'

		msg = QtWidgets.QMessageBox()
		msg.setIcon(QtWidgets.QMessageBox.Information)
		msg.setWindowTitle(title)
		msg.setText(messageText)
		#msg.setText("Sure you want to close? Unsaved changes will be lost...")
		#msg.setInformativeText("This is additional information")
		msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
		retval = msg.exec_()
		if retval == QtWidgets.QMessageBox.Cancel:
			self._ok = False
		else:
			self._ok = True

	def ok(self):
		return self._ok == True
	def canceled(self):
		return self._ok == False

class myWarningsDialog:
	def __init__(self, type, options):
		self._ok = True

		# dialog title does not work on osX?
		if type == 'new node':
			doIt = options['Warnings']['warnOnNewNode']
			title = 'New Node'
			messageText = 'Sure you want to make a new node?'
		#
		if type == 'delete node':
			doIt = options['Warnings']['warnOnDeleteNode']
			title = 'Delete Node'
			messageText = 'Sure you want to delete node?'
		if type == 'delete slab':
			doIt = options['Warnings']['warnOnDeleteSlab']
			title = 'Delete Slab'
			messageText = 'Sure you want to delete slab?'

		if doIt:
			msg = QtWidgets.QMessageBox()
			msg.setIcon(QtWidgets.QMessageBox.Information)
			msg.setWindowTitle(title)
			msg.setText(messageText)
			#msg.setText("Sure you want to close? Unsaved changes will be lost...")
			#msg.setInformativeText("This is additional information")
			msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
			retval = msg.exec_()
			if retval == QtWidgets.QMessageBox.Cancel:
				self._ok = False
			else:
				self._ok = True

	def ok(self):
		return self._ok == True
	def canceled(self):
		return self._ok == False

class setMovieDialog(QtWidgets.QDialog):
	def __init__(self, startSlice, stopSlice, stepSlice=1, fps=7, parent=None):
		super(setMovieDialog, self).__init__(parent)

		self.answerDict = {
			'startSlice': startSlice,
			'stopSlice': stopSlice,
			'stepSlice': stepSlice,
			'fps': fps,
		}

		self.buildUI()

	def getAnswer(self):
		return self.answerDict

	def setAnswerValue(self, val):
		keyStr = self.sender().property('bobId')
		self.answerDict[keyStr] = val

	def buildUI(self):
		layout = QtWidgets.QFormLayout()

		startLabel_ = QtWidgets.QLabel('Start Slice')
		self.startSliceSpinBox = QtWidgets.QSpinBox()
		self.startSliceSpinBox.setProperty('bobId', 'startSlice')
		self.startSliceSpinBox.setMinimum(0)
		self.startSliceSpinBox.setMaximum(1e6)
		self.startSliceSpinBox.setValue(self.answerDict['startSlice'])
		self.startSliceSpinBox.valueChanged.connect(self.setAnswerValue)
		layout.addRow(startLabel_, self.startSliceSpinBox)

		stopLabel_ = QtWidgets.QLabel('Stop Slice')
		self.stopSliceSpinBox = QtWidgets.QSpinBox()
		self.stopSliceSpinBox.setProperty('bobId', 'stopSlice')
		self.stopSliceSpinBox.setMinimum(0)
		self.stopSliceSpinBox.setMaximum(1e6)
		self.stopSliceSpinBox.setValue(self.answerDict['stopSlice'])
		self.stopSliceSpinBox.valueChanged.connect(self.setAnswerValue)
		layout.addRow(stopLabel_, self.stopSliceSpinBox)

		stepLabel_ = QtWidgets.QLabel('Step Slice')
		self.stepSliceSpinBox = QtWidgets.QSpinBox()
		self.stepSliceSpinBox.setProperty('bobId', 'stepSlice')
		self.stepSliceSpinBox.setMinimum(1)
		self.stepSliceSpinBox.setMaximum(self.answerDict['stopSlice']-1)
		self.stepSliceSpinBox.setValue(self.answerDict['stepSlice'])
		self.stepSliceSpinBox.valueChanged.connect(self.setAnswerValue)
		layout.addRow(stepLabel_, self.stepSliceSpinBox)

		fpsLabel_ = QtWidgets.QLabel('Frames Per second')
		self.fpsSpinBox = QtWidgets.QSpinBox()
		self.fpsSpinBox.setProperty('bobId', 'fps')
		self.fpsSpinBox.setMinimum(1)
		self.fpsSpinBox.setMaximum(90)
		self.fpsSpinBox.setValue(self.answerDict['fps'])
		self.fpsSpinBox.valueChanged.connect(self.setAnswerValue)
		layout.addRow(fpsLabel_, self.fpsSpinBox)

		# ok/cancel
		okButton = QtWidgets.QPushButton('Ok')
		okButton.setDefault(True)
		okButton.clicked.connect(self.ok_callback)

		cancelButton = QtWidgets.QPushButton('Cancel')
		cancelButton.clicked.connect(self.cancel_callback)

		layout.addRow(cancelButton, okButton)

		#
		self.setLayout(layout)
		self.setWindowTitle("Save Movie Parameters")

	def ok_callback(self):
		self.accept()

	def cancel_callback(self):
		self.reject()

if __name__ == '__main__':
	import sys

	app = QtWidgets.QApplication(sys.argv)
	smd = setMovieDialog(startSlice=1, stopSlice=100, stepSlice=2, fps=7)
	ok = smd.exec_()
	print('ok:', ok)
	answer = smd.getAnswer()
	print('answer:', answer)

	sys.exit(app.exec_())
