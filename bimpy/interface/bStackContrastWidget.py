# 20190806

import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets

from matplotlib.figure import Figure
from matplotlib.backends import backend_qt5agg

import bimpy

############################################################################
# see: https://www.mfitzp.com/article/qcolorbutton-a-color-selector-tool-for-pyqt/
class myColorButton(QtWidgets.QPushButton):
	'''
	Custom Qt Widget to show a chosen color.

	Left-clicking the button shows the color-chooser, while
	right-clicking resets the color to None (no-color).
	'''

	#colorChanged = pyqtSignal()

	def __init__(self, *args, **kwargs):
		super(myColorButton, self).__init__(*args, **kwargs)

		self._color = None
		self.setMaximumWidth(32)
		self.pressed.connect(self.onColorPicker)

	def setColor(self, color):
		if color != self._color:
			self._color = color
			#self.colorChanged.emit()

		if self._color:
			self.setStyleSheet("background-color: %s;" % self._color)
		else:
			self.setStyleSheet("")

	def getColor(self):
		return self._color

	def onColorPicker(self):
		'''
		Show color-picker dialog to select color.
		'''
		dlg = QtWidgets.QColorDialog(self)
		if self._color:
			dlg.setCurrentColor(QtGui.QColor(self._color))

		if dlg.exec_():
			self.setColor(dlg.currentColor().name())

	"""
	def mousePressEvent(self, e):
		'''
		if e.button() == QtCore.Qt.RightButton:
			self.setColor(None)
		'''
		return super(myColorButton, self).mousePressEvent(e)
	"""

############################################################################
class bStackContrastWidget(QtWidgets.QWidget):
	contrastChangeSignal = QtCore.pyqtSignal(object) # object can be a dict

	def __init__(self, mainWindow=None, parent=None):
		super(bStackContrastWidget, self).__init__(parent)

		self.mainWindow = mainWindow

		self.setMaximumHeight(200)

		self.doUpdate = True # set to false to not update on signal/slot
		self.mySlice = 0

		self._minColor = None
		self._maxColor = None

		self.bitDepth = mainWindow.getStack().getHeaderVal('bitDepth')
		if type(self.bitDepth) == str:
			print('\n\n\tFIX THIS bit Depth BUG !!!!!!!!!!', 'self.bitDepth:', self.bitDepth, type(self.bitDepth), '\n\n')
			self.bitDepth = int(self.bitDepth)
		elif self.bitDepth is None:
			print('ERROR: bStackContrastWidget() got None bitDepth -->> setting to 12')
			self.bitDepth = 12

		print('bStackContrastWidget.__init__() self.bitDepth:', self.bitDepth, type(self.bitDepth))

		self.buildUI()

	def slot_setSlice(self, myEvent, myValue):
		"""
		myEvent: 'set slice'
		"""
		print('bStackContrastWidget.slot_setSlice() myEvent:', myEvent, 'myValue:', myValue)
		self.mySlice = myValue
		self.setSlice(myValue)

	def slot_UpdateSlice2(self, myEvent):
		#print('myStackSlider.slot_UpdateSlice() signalName:', signalName, 'signalValue:', signalValue)
		eventType = myEvent.eventType
		if eventType in ['select node', 'select edge']:
			sliceIdx = myEvent.sliceIdx
			self.mySlice = sliceIdx
			self.setSlice(sliceIdx)

	def setSlice(self, sliceNumber = None):
		if not self.doUpdate:
			return
		if sliceNumber is None:
			sliceNumber = self.mySlice

		channel = 0
		data = self.mainWindow.myStackView.mySimpleStack.stack[channel,sliceNumber,:,:]
		data = data.ravel() # returns a copy
		#print('data:', type(data), data.shape)
		'''
		hist, bin_edges = np.histogram(data, bins=1024)
		print('hist:', type(hist), 'len:', len(hist))
		'''

		#self.axes.plot(x, intensityProfile,'o-', color=c, zorder=zorder) # Returns a tuple of line objects, thus the comma
		# see: https://stackoverflow.com/questions/35738199/matplotlib-pyplot-hist-very-slow
		#num_bins = 2 ** 13
		num_bins = 2 ** self.bitDepth #self.mainWindow.myStackView.mySimpleStack.bitDepth
		print('bStackContrastWidget.setSlice() num_bins:', num_bins)
		doLog = True

		# clear entire axes
		self.axes.clear()

		self.axes.patch.set_facecolor("black")

		n, bins, patches = self.axes.hist(data, num_bins, histtype='stepfilled', log=doLog, color='white', alpha=0.5)

		self.canvas.draw()

	def sliderValueChanged(self):
		theMin = self.minContrastSlider.value()
		theMax = self.maxContrastSlider.value()

		self.minSpinBox.setValue(theMin)
		self.maxSpinBox.setValue(theMax)

		if self.mainWindow is not None:
			#self.mainWindow.signal('contrast change', {'minContrast':theMin, 'maxContrast':theMax})
			#
			myEvent = bimpy.interface.bEvent('contrast change')
			myEvent._minContrast = theMin
			myEvent._maxContrast = theMax
			self.contrastChangeSignal.emit(myEvent)

	def spinBoxValueChanged(self):
		theMin = self.minSpinBox.value()
		theMax = self.maxSpinBox.value()

		self.minContrastSlider.setValue(theMin)
		self.maxContrastSlider.setValue(theMax)

	def bitDepth_Callback(self, idx):
		newBitDepth = self._myBitDepths[idx]
		print('bitDepth_Callback() newBitDepth:', newBitDepth)
		self.bitDepth = newBitDepth

		# update range sliders
		self.minContrastSlider.setMaximum(pow(2,newBitDepth))
		self.maxContrastSlider.setMaximum(pow(2,newBitDepth))

		# update histogram
		self.setSlice()

	def color_Callback(self, idx):
		newColor = self._myColors[idx]
		print('color_Callback() newColor:', newColor)
		self.color = newColor

	def buildUI(self):
		minVal = 0
		if self.bitDepth is None:
			print('FIX THIS  ERROR IN BITDEPTH WTF self.bitDepth:', self.bitDepth)
			self.bitDepth = 16 #8
		maxVal = 2**self.bitDepth

		#self.myQVBoxLayout = QtWidgets.QVBoxLayout(self)
		self.myGridLayout = QtWidgets.QGridLayout(self)

		#
		# upper/min
		#self.upperHBoxLayout = QtWidgets.QHBoxLayout() # don't use self

		spinBoxWidth = 128

		self.minLabel = QtWidgets.QLabel("Min")
		self.minSpinBox = QtWidgets.QSpinBox()
		self.minSpinBox.setMaximumWidth(spinBoxWidth)
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

		# min color
		self.minColorButton = myColorButton() # use *self so we can .getColor()

		#
		# bit depth
		self._myBitDepths = [1, 2, 8, 9, 10, 11, 12, 13, 14, 15, 16, 32]
		bitDepthIdx = self._myBitDepths.index(self.bitDepth) # will sometimes fail
		bitDepthLabel = QtWidgets.QLabel('Bit Depth')
		bitDepthComboBox = QtWidgets.QComboBox()
		for depth in self._myBitDepths:
			bitDepthComboBox.addItem(str(depth))
		bitDepthComboBox.setCurrentIndex(bitDepthIdx)
		bitDepthComboBox.currentIndexChanged.connect(self.bitDepth_Callback)

		row = 0
		col = 0
		self.myGridLayout.addWidget(self.minLabel, row, col)
		col += 1
		self.myGridLayout.addWidget(self.minSpinBox, row, col)
		col += 1
		self.myGridLayout.addWidget(self.minContrastSlider, row, col)
		col += 1
		self.myGridLayout.addWidget(self.minColorButton, row, col)
		col += 1
		self.myGridLayout.addWidget(bitDepthLabel, row, col)
		col += 1
		self.myGridLayout.addWidget(bitDepthComboBox, row, col)
		col += 1
		'''
		self.upperHBoxLayout.addWidget(self.minLabel)
		self.upperHBoxLayout.addWidget(self.minSpinBox)
		self.upperHBoxLayout.addWidget(self.minContrastSlider)
		self.upperHBoxLayout.addWidget(self.minColorButton)
		self.upperHBoxLayout.addWidget(bitDepthLabel)
		self.upperHBoxLayout.addWidget(bitDepthComboBox)
		self.myQVBoxLayout.addLayout(self.upperHBoxLayout) # triggering non trace warning
		'''

		#
		# lower/max
		#self.lowerHBoxLayout = QtWidgets.QHBoxLayout() # don't use self

		self.maxLabel = QtWidgets.QLabel("Max")
		self.maxSpinBox = QtWidgets.QSpinBox()
		self.maxSpinBox.setMaximumWidth(spinBoxWidth)
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

		# max color
		self.maxColorButton = myColorButton() # use *self so we can .getColor()

		# popup for color LUT for image
		self.myColor = 'gray'
		self._myColors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'gray']
		colorIdx = self._myColors.index(self.myColor) # will sometimes fail
		colorLabel = QtWidgets.QLabel('LUT')
		colorComboBox = QtWidgets.QComboBox()
		for color in self._myColors:
			colorComboBox.addItem(color)
		colorComboBox.setCurrentIndex(colorIdx)
		colorComboBox.currentIndexChanged.connect(self.color_Callback)

		histCheckbox = QtWidgets.QCheckBox("Hist")

		row += 1
		col = 0
		self.myGridLayout.addWidget(self.maxLabel, row, col)
		col += 1
		self.myGridLayout.addWidget(self.maxSpinBox, row, col)
		col += 1
		self.myGridLayout.addWidget(self.maxContrastSlider, row, col)
		col += 1
		self.myGridLayout.addWidget(self.maxColorButton, row, col)
		col += 1
		self.myGridLayout.addWidget(colorLabel, row, col)
		col += 1
		self.myGridLayout.addWidget(colorComboBox, row, col)
		col += 1
		self.myGridLayout.addWidget(histCheckbox, row, col)
		col += 1
		'''
		self.lowerHBoxLayout.addWidget(self.maxLabel)
		self.lowerHBoxLayout.addWidget(self.maxSpinBox)
		self.lowerHBoxLayout.addWidget(self.maxContrastSlider)
		self.lowerHBoxLayout.addWidget(self.maxColorButton)
		self.lowerHBoxLayout.addWidget(colorLabel)
		self.lowerHBoxLayout.addWidget(colorComboBox)

		self.myQVBoxLayout.addLayout(self.lowerHBoxLayout) # triggering non trace warning
		'''

		#
		# histograph
		self.figure = Figure() # need size otherwise square image gets squished in y?
		self.canvas = backend_qt5agg.FigureCanvas(self.figure)
		#self.axes = self.figure.add_subplot(111)
		self.axes = self.figure.add_axes([0, 0, 1, 1]) #remove white border
		self.axes.patch.set_facecolor("black")
		self.figure.set_facecolor("black")

		#histHBoxLayout = QtWidgets.QHBoxLayout()
		logCheckbox = QtWidgets.QCheckBox("Log")

		row += 1
		col = 0
		self.myGridLayout.addWidget(logCheckbox, row, col)
		col += 1
		specialCol = 2
		self.myGridLayout.addWidget(self.canvas, row, specialCol)
		col += 1
		'''
		histHBoxLayout.addWidget(logCheckbox)
		histHBoxLayout.addWidget(self.canvas)
		'''

		#
		#self.myQVBoxLayout.addLayout(histHBoxLayout)

		self.setSlice(0)

		#self.setLayout(self.myQVBoxLayout)
