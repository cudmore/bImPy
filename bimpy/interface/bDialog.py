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
