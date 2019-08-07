# 20190806

from PyQt5 import QtGui, QtCore, QtWidgets

class bStackFeebackWidget(QtWidgets.QWidget):
	def __init__(self, mainWindow=None, parent=None):
		super(bStackFeebackWidget, self).__init__(parent)
		
		self.currentSlice = None
		self.numSlices = None
		self. currentIntensity = None
		
		self.buildUI()
	
	def set(self, this, text):
		text = str(text)
		if this == 'num slices':
			self.numSlices_Label.setText('of ' + text)
		elif this == 'set slice':
			self.currentSlice_Label.setText('slice ' + text)
		else:
			print('WARNING: bStackFeebackWidget.set() not handled', this)
			
	def buildUI(self):
	
		self.myQHBoxLayout = QtWidgets.QHBoxLayout(self)
		
		self.currentSlice_Label = QtWidgets.QLabel("current slice:")
		self.numSlices_Label = QtWidgets.QLabel("number of slices label:")
		#self.currentIntensity_Label = QtWidgets.QLabel("number of slices label:")
		self.help_Label = QtWidgets.QLabel("Click image and press keyboard 'h' for help")

		self.myQHBoxLayout.addWidget(self.currentSlice_Label)
		self.myQHBoxLayout.addWidget(self.numSlices_Label)
		#self.myQHBoxLayout.addWidget(self.currentIntensity_Label)
		self.myQHBoxLayout.addWidget(self.help_Label)
	
