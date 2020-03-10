# 20200310
# Robert Cudmore

from qtpy import QtGui, QtCore, QtWidgets

msg = QtWidgets.QMessageBox()
msg.setIcon(QtWidgets.QMessageBox.Information)
msg.setWindowTitle("Close Stack")
msg.setText("Sure you want to close? Unsaved changes will be lost...")
msg.setInformativeText("This is additional information")
msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
retval = msg.exec_()
if retval == QtWidgets.QMessageBox.Cancel:
	return
