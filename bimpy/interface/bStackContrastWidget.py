# 20190806

import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets
#from qtpy import QtGui, QtCore, QtWidgets

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
	#contrastChangeSignal = QtCore.pyqtSignal(object) # object can be a dict
	contrastChangeSignal = QtCore.Signal(object) # object can be a dict


	def __init__(self, mainWindow=None, parent=None):
		super(bStackContrastWidget, self).__init__(parent)

		self.mainWindow = mainWindow

		self.setMaximumHeight(200)

		self.myDoUpdate = True # set to false to not update on signal/slot
		self.plotLogHist = True

		#self._minColor = None
		#self._maxColor = None

		self.bitDepth = mainWindow.getStack().getHeaderVal('bitDepth')
		if type(self.bitDepth) == str:
			print('\n\n\tFIX THIS bit Depth BUG !!!!!!!!!!', 'self.bitDepth:', self.bitDepth, type(self.bitDepth), '\n\n')
			self.bitDepth = int(self.bitDepth)
		elif self.bitDepth is None:
			print('  WARNING: bStackContrastWidget() got None bitDepth -->> setting to 8')
			self.bitDepth = 8

		#print('  bStackContrastWidget.__init__() self.bitDepth:', self.bitDepth, type(self.bitDepth))

		self.contrastDict = {
			'minContrast': 0,
			'maxContrast': 255,
			'colorLut': 'gray',
			'minColor': None,
			'maxColor': None,
		}

		self.buildUI()

	def slot_setSlice(self, myEvent, myValue):
		"""
		myEvent: 'set slice'
		"""
		#print('bStackContrastWidget.slot_setSlice() myEvent:', myEvent, 'myValue:', myValue)
		self.setSlice(myValue)

	def slot_UpdateSlice2(self, myEvent):
		#print('myStackSlider.slot_UpdateSlice() signalName:', signalName, 'signalValue:', signalValue)
		eventType = myEvent.eventType
		if eventType in ['select node', 'select edge']:
			sliceIdx = myEvent.sliceIdx
			self.setSlice(sliceIdx)

	def setSlice(self, sliceNumber):
		if not self.myDoUpdate:
			return

		# this should be a slot_ like slot_updateChannel()
		# channel is (1,2,3,...) can also be 'rgb'
		channel = self.mainWindow.getStackView().displayStateDict['displayThisStack']

		#print('bStackContrastWidget.setSlice() channel:', channel)

		maxNumChannels = self.mainWindow.getStackView().mySimpleStack.maxNumChannels
		if isinstance(channel,int) and channel < maxNumChannels:
			#data = self.mainWindow.myStackView.mySimpleStack.stack[channel,sliceNumber,:,:]
			#data = self.mainWindow.getStackView().mySimpleStack.getImage(channel=channel, sliceNum=sliceNumber)
			data = self.mainWindow.getStackView().mySimpleStack.getImage2(channel=channel, sliceNum=sliceNumber)
			if data is not None:
				data = data.ravel() # returns a copy
		else:
			data = None

		#self.axes.plot(x, intensityProfile,'o-', color=c, zorder=zorder) # Returns a tuple of line objects, thus the comma
		# see: https://stackoverflow.com/questions/35738199/matplotlib-pyplot-hist-very-slow
		#num_bins = 2 ** 13
		num_bins = 2 ** self.bitDepth #self.mainWindow.getStackView().mySimpleStack.bitDepth
		#print('bStackContrastWidget.setSlice() num_bins:', num_bins)
		#doLog = True

		# clear entire axes
		self.axes.clear()

		# from buildUI()
		'''
		self.axes.patch.set_facecolor("black")
		self.figure.set_facecolor("black")
		'''

		self.axes.patch.set_facecolor("black")

		# we need histtype='stepfilled', otherwise is SUPER SLOW
		if data is not None:
			doLog = self.plotLogHist
			n, bins, patches = self.axes.hist(data, num_bins, histtype='stepfilled', log=doLog, color='white', alpha=1.0)


		#
		self.canvasHist.draw()
		#self.canvasHist.draw_idle()

	def emitChange(self):
		myEvent = bimpy.interface.bEvent('contrast change')
		myEvent.contrastDict = self.contrastDict
		self.contrastChangeSignal.emit(myEvent)

	def sliderValueChanged(self):
		theMin = self.minContrastSlider.value()
		theMax = self.maxContrastSlider.value()

		self.minSpinBox.setValue(theMin)
		self.maxSpinBox.setValue(theMax)

		self.contrastDict['minContrast'] = theMin
		self.contrastDict['maxContrast'] = theMax

		self.emitChange()

	def spinBoxValueChanged(self):
		theMin = self.minSpinBox.value()
		theMax = self.maxSpinBox.value()

		self.minContrastSlider.setValue(theMin)
		self.maxContrastSlider.setValue(theMax)

		self.contrastDict['minContrast'] = theMin
		self.contrastDict['maxContrast'] = theMax

		self.emitChange()

	def color_Callback(self, idx):
		newColor = self._myColors[idx]

		#print('color_Callback() newColor:', newColor)

		self.color = newColor

		minColor = self.minColorButton.getColor()
		maxColor = self.maxColorButton.getColor()

		# set in window
		#self.mainWindow.getStackView().set_cmap(newColor, minColor='black', maxColor='white')

		self.contrastDict['colorLut'] = newColor
		self.contrastDict['minColor'] = minColor
		self.contrastDict['maxColor'] = maxColor

		self.emitChange()

	def checkbox_callback(self, isChecked):
		sender = self.sender()
		title = sender.text()
		bobID = sender.property('bobID')
		print('bStackContrastWidget.checkbox_callback() title:', title, 'isChecked:', isChecked, 'bobID:', bobID)

		if title == 'Histogram':
			#print('  toggle histogram')
			if isChecked:
				self.canvasHist.show()
				self.myDoUpdate = True
				self.logCheckbox.setEnabled(True)
			else:
				self.canvasHist.hide()
				self.myDoUpdate = False
				self.logCheckbox.setEnabled(False)
			self.repaint()
		elif title == 'Log':
			self.plotLogHist = not self.plotLogHist
			self.setSlice()

	def bitDepth_Callback(self, idx):
		newBitDepth = self._myBitDepths[idx]
		print('bitDepth_Callback() newBitDepth:', newBitDepth)
		self.bitDepth = newBitDepth

		# update range sliders
		self.minContrastSlider.setMaximum(pow(2,newBitDepth))
		self.maxContrastSlider.setMaximum(pow(2,newBitDepth))

		# update histogram
		self.setSlice()

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

		spinBoxWidth = 64

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
		self.minColorButton.setColor('black')

		#
		# bit depth
		self._myBitDepths = [1, 2, 8, 9, 10, 11, 12, 13, 14, 15, 16] # don't include 32, it causes an over-run
		bitDepthIdx = self._myBitDepths.index(self.bitDepth) # will sometimes fail
		bitDepthLabel = QtWidgets.QLabel('Bit Depth')
		bitDepthComboBox = QtWidgets.QComboBox()
		bitDepthComboBox.setMaximumWidth(spinBoxWidth)
		for depth in self._myBitDepths:
			bitDepthComboBox.addItem(str(depth))
		bitDepthComboBox.setCurrentIndex(bitDepthIdx)
		bitDepthComboBox.currentIndexChanged.connect(self.bitDepth_Callback)

		histCheckbox = QtWidgets.QCheckBox('Histogram')
		histCheckbox.setChecked(True)
		histCheckbox.clicked.connect(self.checkbox_callback)

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
		self.myGridLayout.addWidget(histCheckbox, row, col)

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
		self.maxColorButton.setColor('white')

		# popup for color LUT for image
		self.myColor = 'gray'
		#self._myColors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'gray']
		#self._myColors = ['gray', 'Reds', 'Greens', 'Blues', 'gray_r', 'Reds_r', 'Greens_r', 'Blues_r',
		#					'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r']
		self._myColors = ['gray', 'red', 'green', 'blue', 'gray_r', 'red_r', 'green_r', 'blue_r',
							'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r']
		colorIdx = self._myColors.index(self.myColor) # will sometimes fail
		colorLabel = QtWidgets.QLabel('LUT')
		colorComboBox = QtWidgets.QComboBox()
		#colorComboBox.setMaximumWidth(spinBoxWidth)
		for color in self._myColors:
			colorComboBox.addItem(color)
		colorComboBox.setCurrentIndex(colorIdx)
		colorComboBox.currentIndexChanged.connect(self.color_Callback)
		#colorComboBox.setEnabled(False)

		# todo: not implemented, turn hist on/off
		self.logCheckbox = QtWidgets.QCheckBox('Log')
		self.logCheckbox.setChecked(self.plotLogHist)
		self.logCheckbox.clicked.connect(self.checkbox_callback)

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
		self.myGridLayout.addWidget(self.logCheckbox, row, col)
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
		self.canvasHist = backend_qt5agg.FigureCanvas(self.figure)
		#self.axes = self.figure.add_subplot(111)
		self.axes = self.figure.add_axes([0, 0, 1, 1]) #remove white border
		self.axes.patch.set_facecolor("black")
		self.figure.set_facecolor("black")

		#histHBoxLayout = QtWidgets.QHBoxLayout()

		#
		# second row
		row += 1
		#col = 0
		#self.myGridLayout.addWidget(self.logCheckbox, row, col)
		col = 0
		specialCol = 2
		self.myGridLayout.addWidget(self.canvasHist, row, specialCol)
		col += 1
		'''
		histHBoxLayout.addWidget(self.logCheckbox)
		histHBoxLayout.addWidget(self.canvasHist)
		'''

		#
		#self.myQVBoxLayout.addLayout(histHBoxLayout)

		self.setSlice(0)

		#self.setLayout(self.myQVBoxLayout)
