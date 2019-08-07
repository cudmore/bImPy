# 20190806

from PyQt5 import QtGui, QtCore, QtWidgets

class bContrastWidget(QtWidgets.QWidget):
	def __init__(self, mainWindow=None, parent=None):
		super(bContrastWidget, self).__init__(parent)
	
		self.mainWindow = mainWindow
		
		self.bitDepth = mainWindow.getStack().bitDepth
		print('self.bitDepth:', self.bitDepth)
		
		self.buildUI()
		
	def sliderValueChanged(self):
		theMin = self.minContrastSlider.value()
		theMax = self.maxContrastSlider.value()
		
		self.minSpinBox.setValue(theMin)
		self.maxSpinBox.setValue(theMax)
		
		if self.mainWindow is not None:
			self.mainWindow.signal('contrast change', {'minContrast':theMin, 'maxContrast':theMax})
			
	def spinBoxValueChanged(self):
		theMin = self.minSpinBox.value()
		theMax = self.maxSpinBox.value()
		
		self.minContrastSlider.setValue(theMin)
		self.maxContrastSlider.setValue(theMax)
		
	def buildUI(self):
		minVal = 0
		maxVal = 2**self.bitDepth
		
		self.myQVBoxLayout = QtWidgets.QVBoxLayout(self)
		
		#
		# upper/min
		self.upperHBoxLayout = QtWidgets.QHBoxLayout(self)
		
		self.minLabel = QtWidgets.QLabel("Min")
		self.minSpinBox = QtWidgets.QSpinBox()
		self.minSpinBox.setMinimum(-1e6) # si user can specify whatever they want
		self.minSpinBox.setMaximum(1e6)
		self.minSpinBox.setValue(minVal)
		self.minSpinBox.valueChanged.connect(self.spinBoxValueChanged)
		#
		self.minContrastSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.minContrastSlider.setMinimum(minVal)
		self.minContrastSlider.setMaximum(maxVal)
		self.minContrastSlider.setValue(minVal)
		self.minContrastSlider.valueChanged.connect(self.sliderValueChanged)
		# inverse checkbox
		# color table
		
		self.upperHBoxLayout.addWidget(self.minLabel)
		self.upperHBoxLayout.addWidget(self.minSpinBox)
		self.upperHBoxLayout.addWidget(self.minContrastSlider)
		self.myQVBoxLayout.addLayout(self.upperHBoxLayout)
		
		#
		# lower/max
		self.lowerHBoxLayout = QtWidgets.QHBoxLayout(self)

		self.maxLabel = QtWidgets.QLabel("Max")
		self.maxSpinBox = QtWidgets.QSpinBox()
		self.maxSpinBox.setMinimum(-1e6) # si user can specify whatever they want
		self.maxSpinBox.setMaximum(1e6)
		self.maxSpinBox.setValue(maxVal)
		self.maxSpinBox.valueChanged.connect(self.spinBoxValueChanged)
		#
		self.maxContrastSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.maxContrastSlider.setMinimum(minVal)
		self.maxContrastSlider.setMaximum(maxVal)
		self.maxContrastSlider.setValue(maxVal)
		self.maxContrastSlider.valueChanged.connect(self.sliderValueChanged)
		# inverse checkbox
		# color table
		
		self.lowerHBoxLayout.addWidget(self.maxLabel)
		self.lowerHBoxLayout.addWidget(self.maxSpinBox)
		self.lowerHBoxLayout.addWidget(self.maxContrastSlider)
		
		self.myQVBoxLayout.addLayout(self.lowerHBoxLayout)

		#self.setLayout(self.myQVBoxLayout)