# 20190806
# 20201223, switching over to proper 3-channels and pyqtgraph
import json

import numpy as np

from qtpy import QtGui, QtCore, QtWidgets
#from qtpy import QtGui, QtCore, QtWidgets

import pyqtgraph as pg

#import matplotlib.figure
#from matplotlib.figure import Figure
#from matplotlib.backends import backend_qt5agg

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
	contrastChangeSignal = QtCore.Signal(object, object) # object can be a dict

	def __init__(self, sliceData, parent=None):
		"""
		"""
		super(bHistogramWidget, self).__init__(parent)
		self.sliceImage = sliceData

		self.channelKey = None

		self.myMaxHeight = 120 # adjust based on number of channel
		self.myMaxWidth = 300 # adjust based on number of channel
		self.setMaximumHeight(self.myMaxHeight)
		self.setMaximumWidth(self.myMaxWidth)
		self.plotLogHist = True

		self.bitDepth = 8

		self.brush = (128, 128, 128, 80)
		self.contrastDict = {
					'channelKey': None,
					'minContrast': 0,
					'maxContrast': 255,
					'colorLut': 'gray',
					'minColor': None,
					'maxColor': None,
					'brush': (0.6, 0.6, 0.6, 0.8)
					}

		self.buildUI()

	def setChannelKey(self, channelKey, brush=None):
		"""
		channelKey is 1/2/3 then 4/5/6 then 7/8/9
			for (raw, mask, skel, edt)
		"""
		if brush is not None:
			self.brush = brush
		self.channelKey = channelKey
		self.contrastDict['channelKey'] = channelKey

	def slot_setImage(self, sliceImage=None):
		"""
		can be 1 or 3 planes, 3 is for rgb
		"""

		#print('bHistogramWidget.slot_setImage()')

		if sliceImage is None:
			sliceImage = self.sliceImage
		else:
			# a new slice to display
			self.sliceImage = sliceImage

		#print('  self.sliceImage.shape:', self.sliceImage.shape)

		y,x = np.histogram(self.sliceImage, bins=255)

		if self.plotLogHist:
			y = np.log10(y)

		self.pgHist.setData(x=x, y=y)
		self.pgHist.setBrush(self.contrastDict['brush'])

		self.update()

	def setContrastDict(self, contrastDict):
		"""
		  "12": {
		    "minContrast": 0,
		    "maxContrast": 255,
		    "colorLut": "gray",
		    "minColor": null,
		    "maxColor": null
		  }
		"""
		self.contrastDict = contrastDict

		minContrast = contrastDict['minContrast']
		maxContrast = contrastDict['maxContrast']

		self.minSpinBox.setValue(minContrast)
		self.minSpinBox.update()

		self.maxSpinBox.setValue(maxContrast)
		self.maxSpinBox.update()

		self.minContrastSlider.setMinimum(minContrast)
		self.minContrastSlider.setMaximum(2**8)
		self.minContrastSlider.setValue(minContrast)
		self.minContrastSlider.update()

		self.maxContrastSlider.setMinimum(minContrast)
		self.maxContrastSlider.setMaximum(2**8)
		self.maxContrastSlider.setValue(maxContrast)
		self.maxContrastSlider.update()

		self.update()

	def getContrastDict(self):
		return self.contrastDict

	def emitChange(self):
		"""
		signal to pyqt graph that the contrast has changed"
		"""
		'''
		myEvent = bimpy.interface.bEvent('contrast change')
		myEvent.contrastDict = self.contrastDict
		'''

		#print('bHistogramWidget.emitChange()')
		#print(json.dumps(self.contrastDict, indent=2))

		self.contrastChangeSignal.emit(self.channelKey, self.contrastDict)

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
				self.pgPlotWidget.show()
				#self.pgHist.show()
				self.myDoUpdate = True
				self.logCheckbox.setEnabled(True)
			else:
				#self.canvasHist.hide()
				#self.myGridLayout.addWidget(self.pgPlotWidget
				self.pgPlotWidget.hide()
				#self.pgHist.hide()
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

		#self.minLabel = QtWidgets.QLabel("Min")
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
		'''
		self._myBitDepths = [1, 2, 8, 9, 10, 11, 12, 13, 14, 15, 16]
		bitDepthIdx = self._myBitDepths.index(self.bitDepth) # will sometimes fail
		bitDepthLabel = QtWidgets.QLabel('Bit Depth')
		bitDepthComboBox = QtWidgets.QComboBox()
		#bitDepthComboBox.setMaximumWidth(spinBoxWidth)
		for depth in self._myBitDepths:
			bitDepthComboBox.addItem(str(depth))
		bitDepthComboBox.setCurrentIndex(bitDepthIdx)
		bitDepthComboBox.currentIndexChanged.connect(self.bitDepth_Callback)
		'''

		'''
		histCheckbox = QtWidgets.QCheckBox('Histogram')
		histCheckbox.setChecked(True)
		histCheckbox.clicked.connect(self.checkbox_callback)
		'''

		row = 0
		col = 0
		#self.myGridLayout.addWidget(self.minLabel, row, col)
		#col += 1
		self.myGridLayout.addWidget(self.minSpinBox, row, col)
		col += 1
		self.myGridLayout.addWidget(self.minContrastSlider, row, col)
		col += 1
		# don't remove this code, need to implement min/max color
		'''
		self.myGridLayout.addWidget(self.minColorButton, row, col)
		col += 1
		'''

		'''
		self.myGridLayout.addWidget(bitDepthLabel, row, col)
		col += 1
		self.myGridLayout.addWidget(bitDepthComboBox, row, col)
		col += 1
		self.myGridLayout.addWidget(histCheckbox, row, col)
		'''

		#self.maxLabel = QtWidgets.QLabel("Max")
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
		'''

		'''
		# todo: not implemented, turn hist on/off
		self.logCheckbox = QtWidgets.QCheckBox('Log')
		self.logCheckbox.setChecked(self.plotLogHist)
		self.logCheckbox.clicked.connect(self.checkbox_callback)
		'''

		row += 1
		col = 0
		#self.myGridLayout.addWidget(self.maxLabel, row, col)
		#col += 1
		self.myGridLayout.addWidget(self.maxSpinBox, row, col)
		col += 1
		self.myGridLayout.addWidget(self.maxContrastSlider, row, col)
		col += 1
		# don't remove this code, need to implement min/max color
		'''
		self.myGridLayout.addWidget(self.maxColorButton, row, col)
		col += 1
		'''

		'''
		self.myGridLayout.addWidget(colorLabel, row, col)
		col += 1
		self.myGridLayout.addWidget(colorComboBox, row, col)
		col += 1
		self.myGridLayout.addWidget(self.logCheckbox, row, col)
		col += 1
		'''

		#
		# pyqtgraph histogram
		# don't actually use image on building, wait until self.slot_setImage()
		x = [np.nan, np.nan]
		y = [np.nan]
		'''
		print(np.min(self.sliceImage), self.sliceImage.dtype)
		sliceImage = self.sliceImage
		print('bHistogramWidget.buildUI()', np.min(sliceImage), sliceImage.dtype)
		y,x = np.histogram(sliceImage, bins=255)

		if self.plotLogHist:
			y = np.log10(y)
		'''

		self.pgPlotWidget = pg.PlotWidget()
		self.pgHist = pg.PlotCurveItem(x, y, stepMode=True, fillLevel=0, brush=self.brush)
		self.pgPlotWidget.addItem(self.pgHist)

		# remove the y-axis, it is still not ligned up perfectly !!!
		#w.getPlotItem().hideAxis('bottom')
		self.pgPlotWidget.getPlotItem().hideAxis('left')
		self.pgPlotWidget.getPlotItem().hideAxis('bottom')

		row += 1
		specialCol = 1
		self.myGridLayout.addWidget(self.pgPlotWidget, row, specialCol)

class bStackContrastWidget2(QtWidgets.QWidget):
	contrastChangeSignal = QtCore.Signal(dict) # object can be a dict

	def __init__(self, parent=None, sliceData=None, usePyQtGraphIndex=True):
		"""
		imageData: )channels x rows, cols) tells us bit depth and number of hist
		"""
		super(bStackContrastWidget2, self).__init__(parent)

		self.histList = None # holds 3 instances of bHistogramWidget
		self.keyList = None # list of channels 1,2,3,... we are showing

		self.sliceImage = sliceData
		self.usePyQtGraphIndex = usePyQtGraphIndex

		#self.myMaxHeight = 300 # adjust based on number of channel
		#self.setMaximumHeight(self.myMaxHeight)

		self.myDoUpdate = True # set to false to not update on signal/slot
		self.plotLogHist = True

		self.bitDepth = 8

		numImages = 3*4 # 3 channels * (raw, mask, skel, edt)
		imageTypeList = range(1,numImages+1,1)

		self.contrastDict = {}
		for i in imageTypeList:
			self.contrastDict[i] = {
					'minContrast': 0,
					'maxContrast': 255,
					'colorLut': 'gray',
					'minColor': None,
					'maxColor': None,
					'brush': (0.6, 0.6, 0.6, 0.8),
			}

		self.buildUI2()

	def getKeyDict(self):
		return self.contrastDict

	def slot_setImage_new(self, keyList=None, sliceImage=None):
		"""
		keyList: list of len 1 or 3
		"""
		print('slot_setImage_new() keyList:', keyList)
		if sliceImage is None:
			print('  sliceImage: None')
		else:
			print('  sliceImage:', sliceImage.shape)

		self.keyList = keyList

		# hide all 3
		for hist in self.histList:
			hist.hide()

		# show from key list
		for idx, key in enumerate(keyList):
			if not key in self.contrastDict.keys():
				self.contrastDict[key] = {
							'channelKey': key,
							'minContrast': 0,
							'maxContrast': 255,
							'colorLut': 'gray',
							'minColor': None,
							'maxColor': None,
							'brush': (0.6, 0.6, 0.6, 0.8)
							}

			self.histList[idx].show()
			self.histList[idx].setChannelKey(key)
			self.histList[idx].setContrastDict(self.contrastDict[key])
			#print('  todo: slot_setImage_new() needs to set hist', idx, 'to key', key)
			self.histList[idx].slot_setImage(sliceImage)

		return self.contrastDict

	def slot_setImage(self, sliceImage=None):
		"""
		update our self.keyList histograms (0,1,2) with new sliceImage data
		"""

		'''
		print('bStackContrastWidget2.slot_setImage()')
		if sliceImage is None:
			print('  sliceImage: None')
		else:
			print('  sliceImage:', sliceImage.shape)
		'''

		if len(sliceImage.shape) == 2:
			numChan = 1
		else:
			if self.usePyQtGraphIndex:
				numChan = sliceImage.shape[2]
			else:
				numChan = sliceImage.shape[0]

		#print('  update 1 or 3 hist using slice data')
		#print('  self.keyList:', self.keyList)

		#for idx, key in enumerate(self.keyList):
		for idx in range(numChan):
			if numChan == 1:
				oneChannelSliceImage = sliceImage
			else:
				if self.usePyQtGraphIndex:
					oneChannelSliceImage = sliceImage[:,:,idx]
				else:
					oneChannelSliceImage = sliceImage[idx,:,:]
			self.histList[idx].slot_setImage(oneChannelSliceImage)

	def emitChange(self, channelKey, contrastDict):
		"""
		signal to pyqt graph that the contrast has changed"
		"""
		print('  bStackContrastWidget2.emitChange')
		self.contrastDict[channelKey] = contrastDict

		self.contrastChangeSignal.emit(self.contrastDict)

	def buildUI2(self):
		self.myVBoxLayout = QtWidgets.QVBoxLayout(self)

		# always prepare 3 channels and don't use self.sliceImage

		'''
		print('bStackContrastWidget.buildUI2()', self.sliceImage.shape)
		if len(self.sliceImage.shape) == 2:
			numChan = 1
		else:
			if self.usePyQtGraphIndex:
				numChan = self.sliceImage.shape[2]
			else:
				numChan = self.sliceImage.shape[0]

		print('numChan:', numChan)
		'''
		numChan = 3
		self.histList = [None] * numChan
		for chanNumber in range(numChan):
			actualChan = chanNumber + 1
			'''
			if self.usePyQtGraphIndex:
				sliceImage = self.sliceImage[:,:,chanNumber]
			else:
				if numChan==1:
					sliceImage = self.sliceImage[:,:]
				else:
					sliceImage = self.sliceImage[chanNumber,:,:]
			'''
			sliceImage = None
			#
			oneHist = bHistogramWidget(sliceData=sliceImage)
			oneHist.contrastChangeSignal.connect(self.emitChange)
			#
			self.histList[chanNumber] = oneHist
			self.myVBoxLayout.addWidget(oneHist)

def main():
	import tifffile
	path = '/media/cudmore/data1/san-density/SAN7/SAN7_head/aicsAnalysis/20201202__0002_ch2.tif'
	path = '/Users/cudmore/data/san-density/SAN7/SAN7_head/aicsAnalysis/20201202__0002_ch2.tif'
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

if __name__ == '__main__':
	main()
