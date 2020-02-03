# 20190806

import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets

from matplotlib.figure import Figure
from matplotlib.backends import backend_qt5agg

import bimpy

class bStackContrastWidget(QtWidgets.QWidget):
	contrastChangeSignal = QtCore.pyqtSignal(object) # object can be a dict

	def __init__(self, mainWindow=None, parent=None):
		super(bStackContrastWidget, self).__init__(parent)

		self.mainWindow = mainWindow

		self.setMaximumHeight(200)

		self.doUpdate = True # set to false to not update on signal/slot

		self.bitDepth = mainWindow.getStack().getHeaderVal('bitDepth')
		if type(self.bitDepth) == str:
			print('\n\n\tFIX THIS bit Depth BUG !!!!!!!!!!', 'self.bitDepth:', self.bitDepth, type(self.bitDepth), '\n\n')
			self.bitDepth = int(self.bitDepth)

		print('bStackContrastWidget.__init__() self.bitDepth:', self.bitDepth, type(self.bitDepth))

		self.buildUI()

	def slot_setSlice(self, myEvent, myValue):
		"""
		myEvent: 'set slice'
		"""
		print('bStackContrastWidget.slot_setSlice() myEvent:', myEvent, 'myValue:', myValue)
		self.setSlice(myValue)

	def slot_UpdateSlice2(self, myEvent):
		#print('myStackSlider.slot_UpdateSlice() signalName:', signalName, 'signalValue:', signalValue)
		eventType = myEvent.eventType
		if eventType in ['select node', 'select edge']:
			sliceIdx = myEvent.sliceIdx
			self.setSlice(sliceIdx)

	def setSlice(self, sliceNumber):
		if not self.doUpdate:
			return
		channel = 0
		data = self.mainWindow.myStackView.mySimpleStack.stack[channel,sliceNumber,:,:]
		data = data.ravel() # returns a copy
		print('data:', type(data), data.shape)
		'''
		hist, bin_edges = np.histogram(data, bins=1024)
		print('hist:', type(hist), 'len:', len(hist))
		'''

		#self.axes.plot(x, intensityProfile,'o-', color=c, zorder=zorder) # Returns a tuple of line objects, thus the comma
		# see: https://stackoverflow.com/questions/35738199/matplotlib-pyplot-hist-very-slow
		#num_bins = 2 ** 13
		num_bins = 2 ** 12 #self.mainWindow.myStackView.mySimpleStack.bitDepth
		print('num_bins:', num_bins)
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

	def buildUI(self):
		minVal = 0
		if self.bitDepth is None:
			print('FIX THIS  ERROR IN BITDEPTH WTF self.bitDepth:', self.bitDepth)
			self.bitDepth = 16 #8
		maxVal = 2**self.bitDepth

		self.myQVBoxLayout = QtWidgets.QVBoxLayout(self)

		#
		# upper/min
		self.upperHBoxLayout = QtWidgets.QHBoxLayout() # don't use self

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
		self.myQVBoxLayout.addLayout(self.upperHBoxLayout) # triggering non trace warning

		#
		# lower/max
		self.lowerHBoxLayout = QtWidgets.QHBoxLayout() # don't use self

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

		self.myQVBoxLayout.addLayout(self.lowerHBoxLayout) # triggering non trace warning

		#
		# histograph
		self.figure = Figure(constrained_layout=True) # need size otherwise square image gets squished in y?
		self.canvas = backend_qt5agg.FigureCanvas(self.figure)
		self.axes = self.figure.add_subplot(111)
		self.axes.patch.set_facecolor("black")
		self.figure.set_facecolor("black")
		self.myQVBoxLayout.addWidget(self.canvas)

		self.setSlice(0)

		#self.setLayout(self.myQVBoxLayout)
