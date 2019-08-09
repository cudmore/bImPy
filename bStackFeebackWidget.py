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
			self.slidingz_checkbox.setCheckState(thisValue)
			#self.slidingz_checkbox.setTristate(False)
		else:
			print('WARNING: bStackFeebackWidget.set() not handled', this)
			
	def slidingz_statechange(self):
		#self.slidingz_checkbox.setTristate(False)
		self.mainWindow.signal('toggle sliding z', noRecursion=True)
	
	def buildUI(self):
	
		self.myQHBoxLayout = QtWidgets.QHBoxLayout(self)
		
		self.currentSlice_Label = QtWidgets.QLabel("current slice:")
		self.numSlices_Label = QtWidgets.QLabel("number of slices label:")
		#self.currentIntensity_Label = QtWidgets.QLabel("number of slices label:")
		self.help_Label = QtWidgets.QLabel("Click image and press keyboard 'h' for help")

		self.slidingz_checkbox = QtWidgets.QCheckBox('Sliding Z')
		self.slidingz_checkbox.setChecked(False)
		#self.slidingz_checkbox.setTristate()
		self.slidingz_checkbox.stateChanged.connect(self.slidingz_statechange)
		
		self.myQHBoxLayout.addWidget(self.currentSlice_Label)
		self.myQHBoxLayout.addWidget(self.numSlices_Label)
		self.myQHBoxLayout.addWidget(self.slidingz_checkbox)
		#self.myQHBoxLayout.addWidget(self.currentIntensity_Label)
		self.myQHBoxLayout.addWidget(self.help_Label)
	
