"""
#20200913

Generic dialog to edit a dict of [key1][key2]
"""

import json
import copy
from collections import OrderedDict

from PyQt5 import QtCore, QtWidgets, QtGui

def okCancelDialog(text, informativeText=''):
	close = QtWidgets.QMessageBox()
	close.setText(text)
	close.setIcon(QtWidgets.QMessageBox.Question)
	#close.setDetailedText('detailed text') # don't use this
	if informativeText:
		close.setInformativeText(informativeText)
	close.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
	close.setDefaultButton(QtWidgets.QMessageBox.Yes)
	close = close.exec()

	theRet = close == QtWidgets.QMessageBox.Yes
	return theRet

def okDialog(text, informativeText=''):
	close = QtWidgets.QMessageBox()
	close.setText(text)
	close.setIcon(QtWidgets.QMessageBox.Warning)
	#close.setDetailedText('detailed text') # don't use this
	if informativeText:
		close.setInformativeText(informativeText)
	close.setStandardButtons(QtWidgets.QMessageBox.Ok)
	close.setDefaultButton(QtWidgets.QMessageBox.Ok)
	close = close.exec()

	theRet = close == QtWidgets.QMessageBox.Yes
	return theRet

'''
class bOkCancelDialog:
	def __init__(self, title, message):
		self._ok = False

		msg = QtWidgets.QMessageBox()
		msg.setIcon(QtWidgets.QMessageBox.Information)
		msg.setWindowTitle(title)
		msg.setText(message)
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
'''

class bOptionsDialog(QtWidgets.QDialog):
	"""
	General purpose dialog to set tracing display options.
	For now it is hard coded with pen size and masking

	todo: extend this to handle all options !!!
	"""
	acceptOptionsSignal = QtCore.Signal(object) # object can be a dict

	def __init__(self, parent, optionsDict):
		"""
		parent is needed, otherwise self.show() does nothing

		to make modal, use
			self.setWindowModality(QtCore.Qt.ApplicationModal)
		"""
		super(bOptionsDialog, self).__init__(parent)

		#self.accept.connect(parent.slot_UpdateOptions)
		#self.acceptOptionsSignal.connect(parent.slot_UpdateOptions)

		# make a copy of options to modify
		self.localOptions = copy.deepcopy(optionsDict)
		#self.localOptions = OrderedDict(optionsDict)

		self.setWindowTitle('Canvas Options')

		ignorKey1_List = ['version']

		# ignore things like ['video']['left']
		ignoreList = []
		ignoreList.append(('motor', 'motorName')) #####!!!#####
		ignoreList.append(('motor', 'port')) #####!!!#####
		ignoreList.append(('Canvas', 'savePath'))
		ignoreList.append(('video', 'left'))
		ignoreList.append(('video', 'top'))
		ignoreList.append(('video', 'width'))
		ignoreList.append(('video', 'height'))
		ignoreList.append(('video', 'scaleMult'))

		numKeys = len(optionsDict.keys())
		numCols = 3

		mainLayout = QtWidgets.QGridLayout()
		#mainLayout = QtWidgets.QVBoxLayout()

		row = 0
		col = 0
		#print('building bOptionsDialog')
		for key1 in self.localOptions.keys():
			if key1 in ignorKey1_List:
				continue
			groupBox = QtWidgets.QGroupBox(key1)
			layout = QtWidgets.QFormLayout()
			layout.setLabelAlignment(QtCore.Qt.AlignLeft)
			layout.setFormAlignment(QtCore.Qt.AlignLeft)

			for key2 in self.localOptions[key1].keys():
				# don't show certain preferences
				if (key1,key2) in ignoreList:
					continue

				value = self.localOptions[key1][key2]
				theType = type(value)
				#print(key1, key2, theType, value)
				if isinstance(value, bool):
					aCheckbox = QtWidgets.QCheckBox(key2)
					aCheckbox.setChecked(value)
					aCheckbox.setProperty('bobID_1', key1)
					aCheckbox.setProperty('bobID_2', key2)
					aCheckbox.stateChanged.connect(self.checkChanged)
					#
					layout.addRow(aCheckbox)
				elif isinstance(value, int) or isinstance(value, float):
					if isinstance(value, int):
						aSpinBox = QtWidgets.QSpinBox()
					else:
						aSpinBox = QtWidgets.QDoubleSpinBox()
					aSpinBox.setMinimum(0)
					aSpinBox.setMaximum(1e6)
					aSpinBox.setValue(value)
					aSpinBox.setProperty('bobID_1', key1)
					aSpinBox.setProperty('bobID_2', key2)
					aSpinBox.valueChanged.connect(self.valueChanged)
					#
					layout.addRow(QtWidgets.QLabel(key2), aSpinBox)

				elif isinstance(value, str):
					aLineEdit = QtWidgets.QLineEdit()
					aLineEdit.setText(value)
					aLineEdit.setProperty('bobID_1', key1)
					aLineEdit.setProperty('bobID_2', key2)
					aLineEdit.textEdited.connect(self.valueChanged)
					#
					layout.addRow(QtWidgets.QLabel(key2), aLineEdit)

				elif isinstance(value, list):
					# motorNameList makes the dropdown list
					# motorName is what we set
					#print('  bOptionsDialog() making QComboBox:', key1, key2, value)
					aComboBox = QtGui.QComboBox()
					aComboBox.addItems(value) # assumnig value is a list of str
					# set selected item
					useThisKey2 = key2.replace('List', '')
					stringKey2 = self.localOptions[key1][useThisKey2]
					try:
						motorNameIndex = value.index(stringKey2)
						aComboBox.setCurrentIndex(motorNameIndex)
					except (ValueError) as e:
						print('did not find', stringKey2, 'in list', value, '-->> deactivate control')
						aComboBox.setDisabled(True)
					aComboBox.setProperty('bobID_1', key1)
					aComboBox.setProperty('bobID_2', key2)
					aComboBox.activated[str].connect(self.comboBoxSelection)
					layout.addRow(QtWidgets.QLabel(key2), aComboBox)
					if key2.endswith('List'):
						setKey = key2.replace('List', '')

				else:
					print(f'  bOptionsDialog() isinstance not handled:, {key1}, {key2}, "{value}"')

			groupBox.setLayout(layout)

			rowSpan = 1
			colSpan = 1
			mainLayout.addWidget(groupBox, row, col, rowSpan, colSpan)
			#mainLayout.addWidget(groupBox)
			col += 1
			if col == numCols:
				col = 0
				row += 1

		#
		row += 1
		#col = 0
		self.buttonBox = QtWidgets.QDialogButtonBox(
			#QtWidgets.QDialogButtonBox.Apply |
			#QtWidgets.QDialogButtonBox.Reset |
			QtWidgets.QDialogButtonBox.Cancel |
			QtWidgets.QDialogButtonBox.Ok)

		self.buttonBox.clicked.connect(self.myClicked)
		self.buttonBox.accepted.connect(self.myAccept)
		self.buttonBox.rejected.connect(self.reject)

		#
		mainLayout.addWidget(self.buttonBox, row, numCols-1)
		#mainLayout.addWidget(self.buttonBox)
		self.setLayout(mainLayout)

		self.show()

	def myClicked(self, button):
		'''
		print('  myClicked() button:')
		print('   ', self.buttonBox.buttonRole(button))
		print('   ', QtWidgets.QDialogButtonBox.ApplyRole)
		'''
		buttonRole = self.buttonBox.buttonRole(button)

		if buttonRole == QtWidgets.QDialogButtonBox.ApplyRole:
			print('   apply clicked')
			#self.mainWindow.options = self.localOptions
			#self.mainWindow.getStackView().setSlice() # refresh

		elif buttonRole == QtWidgets.QDialogButtonBox.ResetRole:
			print('   reset clicked')

	def checkChanged(self, value):
		"""
		value 0: unchecked
		value 2: checked
		"""
		print('  checkChanged() value:', value, type(value))
		if value == 0:
			value = False
		elif value == 2:
			value = True
		else:
			print('  error in checkChanged')
			return
		bobID_1 = self.sender().property('bobID_1')
		bobID_2 = self.sender().property('bobID_2')
		try:
			self.localOptions[bobID_1][bobID_2] = value
		except (KeyError) as e:
			print('  error in valueChanged() e:', e)

	def comboBoxSelection(self, str):
		bobID_1 = self.sender().property('bobID_1')
		bobID_2 = self.sender().property('bobID_2')
		if bobID_2.endswith('List'):
			setThisKey = bobID_2.replace('List', '')
			try:
				self.localOptions[bobID_1][setThisKey] = str
			except (KeyError) as e:
				print('error in comboBoxSelection() key1:', bobID_1, 'key2:', setThisKey)
				print('  e:', e)

	def valueChanged(self, value):
		"""
		Set value in our local copy of options, self.localOptions
		"""
		if isinstance(value, int):
			pass
		elif isinstance(value, str):
			pass

		print('  valueChanged() value:', value, type(value), self.sender().property('bobID_1'), self.sender().property('bobID_2'))
		bobID_1 = self.sender().property('bobID_1')
		bobID_2 = self.sender().property('bobID_2')
		try:
			self.localOptions[bobID_1][bobID_2] = value
		except (KeyError) as e:
			print('error in valueChanged() e:', e)

	def myAccept(self):
		"""
		copy our localOptions back into mainWindow.options
		"""

		# parent needs to ad a slot_updateOptions() function
		self.acceptOptionsSignal.emit(self.localOptions)

		self.accept() # close the dialog
