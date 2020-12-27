# 20190806

import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets
#from qtpy import QtGui, QtCore, QtWidgets

import pyqtgraph as pg

import matplotlib.figure
#from matplotlib.figure import Figure
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
"""
display sliceData as a histogram

does not know about any other widgets!!!
"""

class bHistogramWidget(QtWidgets.QWidget):
	contrastChangeSignal = QtCore.Signal(object) # object can be a dict

	def __init__(self, sliceData, channelNumber, usePyQtGraphIndex=True, parent=None):
		"""
		sliceData either xy or xyc
		channelNumber: use this on emit change so parent know which channel changed
		usePyQtGraphIndex: if true us (width, height, slice) otherwise use np (slice, width, height)
		"""
		super(bHistogramWidget, self).__init__(parent)
		self.sliceImage = sliceData
		self.channelNumber = channelNumber
		self.usePyQtGraphIndex = usePyQtGraphIndex

		self.myMaxHeight = 200 # adjust based on number of channel
		self.setMaximumHeight(self.myMaxHeight)
		self.plotLogHist = True

		self.bitDepth = 8

		self.contrastDict = {
					'channel': self.channelNumber,
					'minContrast': 0,
					'maxContrast': 255,
					'colorLut': 'gray',
					'minColor': None,
					'maxColor': None,
					}

		self.buildUI()

	def slot_setImage(self, sliceImage=None):
		"""
		can be 1 or 3 planes, 3 is for rgb
		"""

		print('bStackContrastWidget2.slot_setImage()')

		if sliceImage is None:
			sliceImage = self.sliceImage
		else:
			# a new slice to display
			self.sliceImage = sliceImage

		if len(sliceImage.shape) == 2:
			self.numChannels = 1
		else:
			if self.usePyQtGraphIndex:
				self.numChannels = sliceImage.shape[2] # using pyqtgraph (row,col,slice)
			else:
				self.numChannels = sliceImage.shape[0] # using numpy (slice,row,col)

		print('  self.numChannels:', self.numChannels)


		y,x = np.histogram(self.sliceImage, bins=255)

		if self.plotLogHist:
			y = np.log10(y)

		self.pgHist.setData(x=x, y=y)

		self.update()

	def getContrastDict(self):
		return self.contrastDict

	def emitChange(self):
		"""
		signal to pyqt graph that the contrast has changed"
		"""
		myEvent = bimpy.interface.bEvent('contrast change')
		myEvent.contrastDict = self.contrastDict

		print('bHistogramWidget.emitChange()', self.contrastDict)

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
		self.color = newColor

		# don't remove this code, need to implement min/max color
		'''
		minColor = self.minColorButton.getColor()
		maxColor = self.maxColorButton.getColor()
		'''

		self.contrastDict['colorLut'] = newColor

		# don't remove this code, need to implement min/max color
		'''
		self.contrastDict['minColor'] = minColor
		self.contrastDict['maxColor'] = maxColor
		'''

		self.emitChange()

	def checkbox_callback(self, isChecked):
		sender = self.sender()
		title = sender.text()
		print('bStackContrastWidget.checkbox_callback() title:', title, 'isChecked:', isChecked)

		if title == 'Histogram':
			#print('  toggle histogram')
			if isChecked:
				#self.canvasHist.show()
				self.pgHist.show()
				self.myDoUpdate = True
				self.logCheckbox.setEnabled(True)
			else:
				#self.canvasHist.hide()
				self.pgHist.hide()
				self.myDoUpdate = False
				self.logCheckbox.setEnabled(False)
			self.repaint()
		elif title == 'Log':
			self.plotLogHist = not self.plotLogHist
			self.slot_setImage()

	def bitDepth_Callback(self, idx):
		newBitDepth = self._myBitDepths[idx]
		print('bbStackContrastWidget.bitDepth_Callback() newBitDepth:', newBitDepth)
		self.bitDepth = newBitDepth

		# update range sliders
		self.minContrastSlider.setMaximum(pow(2,newBitDepth))
		self.maxContrastSlider.setMaximum(pow(2,newBitDepth))

		# update histogram
		self.slot_setImage()

	def buildUI(self):
		minVal = 0
		maxVal = 2**self.bitDepth

		#self.myQVBoxLayout = QtWidgets.QVBoxLayout(self)
		self.myGridLayout = QtWidgets.QGridLayout(self)

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

		# don't remove this code, need to implement min/max color
		'''
		# min color
		self.minColorButton = myColorButton() # use *self so we can .getColor()
		self.minColorButton.setColor('black')
		'''

		#
		# bit depth
		# don't include 32, it causes an over-run
		self._myBitDepths = [1, 2, 8, 9, 10, 11, 12, 13, 14, 15, 16]
		bitDepthIdx = self._myBitDepths.index(self.bitDepth) # will sometimes fail
		bitDepthLabel = QtWidgets.QLabel('Bit Depth')
		bitDepthComboBox = QtWidgets.QComboBox()
		#bitDepthComboBox.setMaximumWidth(spinBoxWidth)
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
		# don't remove this code, need to implement min/max color
		'''
		self.myGridLayout.addWidget(self.minColorButton, row, col)
		col += 1
		'''
		self.myGridLayout.addWidget(bitDepthLabel, row, col)
		col += 1
		self.myGridLayout.addWidget(bitDepthComboBox, row, col)
		col += 1
		self.myGridLayout.addWidget(histCheckbox, row, col)

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

		# don't remove this code, need to implement min/max color
		'''
		# max color
		self.maxColorButton = myColorButton() # use *self so we can .getColor()
		self.maxColorButton.setColor('white')
		'''

		# popup for color LUT for image
		self.myColor = 'gray'
		# todo: add some more colors
		#self._myColors = ['gray', 'red', 'green', 'blue', 'gray_r', 'red_r', 'green_r', 'blue_r',
		#					'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r']
		self._myColors = ['gray', 'red', 'green', 'blue', 'gray_r']
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
		# don't remove this code, need to implement min/max color
		'''
		self.myGridLayout.addWidget(self.maxColorButton, row, col)
		col += 1
		'''
		self.myGridLayout.addWidget(colorLabel, row, col)
		col += 1
		self.myGridLayout.addWidget(colorComboBox, row, col)
		col += 1
		self.myGridLayout.addWidget(self.logCheckbox, row, col)
		col += 1

		#
		# pyqtgraph histogram
		print(np.min(self.sliceImage), self.sliceImage.dtype)
		sliceImage = self.sliceImage
		'''
		if self.plotLogHist:
			sliceImage = self.sliceImage[self.sliceImage != 0]
			sliceImage = np.log10(sliceImage)
		else:
			sliceImage = self.sliceImage
		'''
		print('bHistogramWidget.buildUI()', np.min(sliceImage), sliceImage.dtype)
		y,x = np.histogram(sliceImage, bins=255)

		if self.plotLogHist:
			y = np.log10(y)

		if self.channelNumber == 1:
			brush = (255, 0, 0, 80)
		elif self.channelNumber == 2:
			brush = (0, 255, 0, 80)
		elif self.channelNumber == 3:
			brush = (0, 0, 255, 80)

		self.pgPlotWidget = pg.PlotWidget()
		self.pgHist = pg.PlotCurveItem(x, y, stepMode=True, fillLevel=0, brush=brush)
		self.pgPlotWidget.addItem(self.pgHist)

		# remove the y-axis, it is still not ligned up perfectly !!!
		#w.getPlotItem().hideAxis('bottom')
		self.pgPlotWidget.getPlotItem().hideAxis('left')

		row += 1
		specialCol = 2
		self.myGridLayout.addWidget(self.pgPlotWidget, row, specialCol)

class bStackContrastWidget2(QtWidgets.QWidget):
	contrastChangeSignal = QtCore.Signal(object) # object can be a dict

	def __init__(self, parent=None, sliceData=None, usePyQtGraphIndex=True):
		"""
		imageData: )channels x rows, cols) tells us bit depth and number of hist
		"""
		super(bStackContrastWidget2, self).__init__(parent)

		self.sliceImage = sliceData
		self.usePyQtGraphIndex = usePyQtGraphIndex

		#self.myMaxHeight = 300 # adjust based on number of channel
		#self.setMaximumHeight(self.myMaxHeight)

		self.myDoUpdate = True # set to false to not update on signal/slot
		self.plotLogHist = True

		self.bitDepth = 8

		self.contrastDict = {
			'1': {
					'minContrast': 0,
					'maxContrast': 255,
					'colorLut': 'gray',
					'minColor': None,
					'maxColor': None,
					},
			'2': {
					'minContrast': 0,
					'maxContrast': 255,
					'colorLut': 'gray',
					'minColor': None,
					'maxColor': None,
					},
			'3': {
					'minContrast': 0,
					'maxContrast': 255,
					'colorLut': 'gray',
					'minColor': None,
					'maxColor': None,
					},
		}

		self.buildUI2()

	def old_slot_setImage(self, sliceImage=None):
		"""
		can be 1 or 3 planes, 3 is for rgb
		"""

		print('bStackContrastWidget2.slot_setImage()')

		if sliceImage is None:
			sliceImage = self.sliceImage
		else:
			# a new slice to display
			self.sliceImage = sliceImage

		if len(sliceImage.shape) == 2:
			self.numChannels = 1
		else:
			self.numChannels = sliceImage.shape[2] # using pyqtgraph (roew,col,slice)

		print('  self.numChannels:', self.numChannels)

		maxNumChannels = 3
		for i in range(self.numChannels):
			self.axes[i].clear() # clear entire axes
			self.axes[i].patch.set_facecolor("black")

		doLog = self.plotLogHist
		# we need histtype='stepfilled', otherwise is SUPER SLOW
		for i in range(self.numChannels):
			if self.numChannels == 1:
				data = sliceImage[:,:]
			else:
				data = sliceImage[:,:,i] # using pyqtgraph indexing !!!
			data = data.ravel()
			num_bins = 2 ** self.bitDepth
			n, bins, patches = self.axes[i].hist(data, num_bins,
									histtype='stepfilled',
									log=doLog,
									color='white',
									alpha=1.0)

		#
		self.canvasHist.draw()
		#self.canvasHist.draw_idle()

	def old_getContrastDict(self):
		return self.contrastDict

	def old_emitChange(self):
		"""
		signal to pyqt graph that the contrast has changed"
		"""
		myEvent = bimpy.interface.bEvent('contrast change')
		myEvent.contrastDict = self.contrastDict
		self.contrastChangeSignal.emit(myEvent)

	def emitChange(self, bEventObject):
		"""
		signal to pyqt graph that the contrast has changed"
		"""
		print('  bStackContrastWidget2.emitChange')
		self.contrastChangeSignal.emit(bEventObject)

	def old_sliderValueChanged(self):
		sender = self.sender()
		title = sender.text()

		theMin = self.minContrastSlider.value()
		theMax = self.maxContrastSlider.value()

		self.minSpinBox.setValue(theMin)
		self.maxSpinBox.setValue(theMax)

		self.contrastDict['minContrast'] = theMin
		self.contrastDict['maxContrast'] = theMax

		self.emitChange()

	def old_spinBoxValueChanged(self):
		theMin = self.minSpinBox.value()
		theMax = self.maxSpinBox.value()

		self.minContrastSlider.setValue(theMin)
		self.maxContrastSlider.setValue(theMax)

		self.contrastDict['minContrast'] = theMin
		self.contrastDict['maxContrast'] = theMax

		self.emitChange()

	def old_color_Callback(self, idx):
		newColor = self._myColors[idx]

		#print('color_Callback() newColor:', newColor)

		self.color = newColor

		# don't remove this code, need to implement min/max color
		'''
		minColor = self.minColorButton.getColor()
		maxColor = self.maxColorButton.getColor()
		'''

		# set in window
		#self.mainWindow.getStackView().set_cmap(newColor, minColor='black', maxColor='white')

		self.contrastDict['colorLut'] = newColor
		# don't remove this code, need to implement min/max color
		'''
		self.contrastDict['minColor'] = minColor
		self.contrastDict['maxColor'] = maxColor
		'''

		self.emitChange()

	def old_checkbox_callback(self, isChecked):
		sender = self.sender()
		title = sender.text()
		print('bStackContrastWidget.checkbox_callback() title:', title, 'isChecked:', isChecked)

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
			self.slot_setImage()

	def old_bitDepth_Callback(self, idx):
		newBitDepth = self._myBitDepths[idx]
		print('bbStackContrastWidget.itDepth_Callback() newBitDepth:', newBitDepth)
		self.bitDepth = newBitDepth

		# update range sliders
		self.minContrastSlider.setMaximum(pow(2,newBitDepth))
		self.maxContrastSlider.setMaximum(pow(2,newBitDepth))

		# update histogram
		self.slot_setImage()

	def buildUI2(self):
		self.myVBoxLayout = QtWidgets.QVBoxLayout(self)

		if len(self.sliceImage.shape) == 2:
			numChan = 1
		else:
			if self.usePyQtGraphIndex:
				numChan = self.sliceImage.shape[2]
			else:
				numChan = self.sliceImage.shape[0]

		print('numChan:', numChan)

		for chanNumber in range(numChan):
			actualChan = chanNumber + 1
			if self.usePyQtGraphIndex:
				sliceImage = self.sliceImage[:,:,chanNumber]
			else:
				sliceImage = self.sliceImage[chanNumber,:,:]
			#
			oneHist = bHistogramWidget(sliceData=sliceImage,
									channelNumber=actualChan,
									usePyQtGraphIndex=self.usePyQtGraphIndex)
			oneHist.contrastChangeSignal.connect(self.emitChange)
			#
			self.myVBoxLayout.addWidget(oneHist)

	def old_buildUI(self):
		minVal = 0
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

		# don't remove this code, need to implement min/max color
		'''
		# min color
		self.minColorButton = myColorButton() # use *self so we can .getColor()
		self.minColorButton.setColor('black')
		'''

		#
		# bit depth
		# don't include 32, it causes an over-run
		self._myBitDepths = [1, 2, 8, 9, 10, 11, 12, 13, 14, 15, 16]
		bitDepthIdx = self._myBitDepths.index(self.bitDepth) # will sometimes fail
		bitDepthLabel = QtWidgets.QLabel('Bit Depth')
		bitDepthComboBox = QtWidgets.QComboBox()
		#bitDepthComboBox.setMaximumWidth(spinBoxWidth)
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
		# don't remove this code, need to implement min/max color
		'''
		self.myGridLayout.addWidget(self.minColorButton, row, col)
		col += 1
		'''
		self.myGridLayout.addWidget(bitDepthLabel, row, col)
		col += 1
		self.myGridLayout.addWidget(bitDepthComboBox, row, col)
		col += 1
		self.myGridLayout.addWidget(histCheckbox, row, col)

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

		# don't remove this code, need to implement min/max color
		'''
		# max color
		self.maxColorButton = myColorButton() # use *self so we can .getColor()
		self.maxColorButton.setColor('white')
		'''

		# popup for color LUT for image
		self.myColor = 'gray'
		# todo: add some more colors
		#self._myColors = ['gray', 'red', 'green', 'blue', 'gray_r', 'red_r', 'green_r', 'blue_r',
		#					'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r']
		self._myColors = ['gray', 'red', 'green', 'blue', 'gray_r']
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
		# don't remove this code, need to implement min/max color
		'''
		self.myGridLayout.addWidget(self.maxColorButton, row, col)
		col += 1
		'''
		self.myGridLayout.addWidget(colorLabel, row, col)
		col += 1
		self.myGridLayout.addWidget(colorComboBox, row, col)
		col += 1
		self.myGridLayout.addWidget(self.logCheckbox, row, col)
		col += 1

		#
		# histograph
		self.figure = matplotlib.figure.Figure() # need size otherwise square image gets squished in y?
		self.canvasHist = backend_qt5agg.FigureCanvas(self.figure)
		#self.axes = self.figure.add_subplot(111)
		self.numChannels = 3
		self.axes = [None] * self.numChannels
		for i in range(self.numChannels):
			#self.axes[i] = self.figure.add_axes([0, 0, 1, 1]) #remove white border
			self.axes[i] = self.figure.add_subplot(self.numChannels, 1, i+1) #remove white border
			self.axes[i].patch.set_facecolor("black")
		self.figure.set_facecolor("black")

		# pyqt histogram
		y,x = np.histogram(self.sliceImage, bins=255)

		## notice that len(x) == len(y)+1
		## We are required to use stepMode=True so that PlotCurveItem will interpret this data correctly.

		# this works beautifully
		'''
		self.pgPlotWidget = pg.PlotWidget()
		self.curve = pg.PlotCurveItem(x, y, stepMode=True, fillLevel=0, brush=(0, 0, 255, 80))
		self.pgPlotWidget.addItem(self.curve)
		self.myGridLayout.addWidget(self.pgPlotWidget, row, col)
		'''

		channelNumber = 1
		oneHist = bHistogramWidget(sliceData=self.sliceImage, channelNumber=channelNumber)
		self.myGridLayout.addWidget(oneHist, row, col)

		#
		# second row
		row += 1
		col = 0
		specialCol = 2
		self.myGridLayout.addWidget(self.canvasHist, row, specialCol)
		col += 1

if __name__ == '__main__':
	import sys
	import tifffile
	path = '/media/cudmore/data1/san-density/SAN7/SAN7_head/aicsAnalysis/20201202__0002_ch2.tif'
	sliceData = tifffile.imread(path)

	# sliceData is (slice,m,n)
	#sliceNum = 10
	theseSlices = [10, 50, 100]
	theseSlices = [10, 50, 120]
	sliceData = sliceData[theseSlices, :, :]

	app = QtWidgets.QApplication(sys.argv)
	w = bStackContrastWidget2(sliceData=sliceData, usePyQtGraphIndex=False)
	w.show()

	# abb 20201109, program is not quiting on error???
	sys.exit(app.exec_())
