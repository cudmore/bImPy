# 20200122

#from PyQt5 import QtGui, QtCore, QtWidgets
from qtpy import QtGui, QtCore, QtWidgets

# these three can remove once bLineProfile.py is done
from skimage.measure import profile
import scipy
from scipy.optimize import curve_fit

import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends import backend_qt5agg

class bLineProfileWidget(QtWidgets.QWidget):
	def __init__(self, mainWindow=None):
		super(bLineProfileWidget, self).__init__()

		self.mainWindow = mainWindow

		self.updateDict = None

		self.lineLength = 5
		self.lineWidth = 3
		self.medianFilter = 5
		self.halfHeight = 0.5

		self.doUpdate = True # set to false to not update on signal/slot

		self.setMaximumHeight(200)

		self.myHBoxLayout = QtWidgets.QHBoxLayout(self)

		#
		# to hold control panel
		self.leftGridLayout = QtWidgets.QGridLayout() # abb aics, removed (self)

		myRow = 0

		# nudge up button
		nudgeUpButton = QtWidgets.QPushButton('Nudge Up')
		nudgeUpButton.clicked.connect(self.nudgeUp_Callback)
		self.leftGridLayout.addWidget(nudgeUpButton, myRow, 0)
		# nudge down button
		nudgeUpButton = QtWidgets.QPushButton('Nudge Down')
		nudgeUpButton.clicked.connect(self.nudgeDown_Callback)
		self.leftGridLayout.addWidget(nudgeUpButton, myRow, 1)

		myRow += 1

		# line length for intensity profile
		myLabel = QtWidgets.QLabel('Line Length (pixels)')
		lineWidthSpinBox = QtWidgets.QSpinBox()
		lineWidthSpinBox.setMinimum(1)
		lineWidthSpinBox.setValue(self.lineLength)
		lineWidthSpinBox.valueChanged.connect(self.lineLength_Callback)
		self.leftGridLayout.addWidget(myLabel, myRow, 0)
		self.leftGridLayout.addWidget(lineWidthSpinBox, myRow, 1)

		myRow += 1

		# line width for intensity profile
		myLabel = QtWidgets.QLabel('Line Width (pixels)')
		lineWidthSpinBox = QtWidgets.QSpinBox()
		lineWidthSpinBox.setMinimum(1)
		lineWidthSpinBox.setValue(self.lineWidth)
		lineWidthSpinBox.valueChanged.connect(self.lineWidth_Callback)
		self.leftGridLayout.addWidget(myLabel, myRow, 0)
		self.leftGridLayout.addWidget(lineWidthSpinBox, myRow, 1)

		myRow += 1

		# size (pixels) of median filter
		myLabel = QtWidgets.QLabel('Median Filter (pixels)')
		medianFilterSpinbox = QtWidgets.QSpinBox()
		medianFilterSpinbox.setMinimum(0)
		medianFilterSpinbox.setValue(self.medianFilter)
		medianFilterSpinbox.valueChanged.connect(self.medianFilter_Callback)
		self.leftGridLayout.addWidget(myLabel, myRow, 0)
		self.leftGridLayout.addWidget(medianFilterSpinbox, myRow, 1)

		myRow += 1

		# half height b/w 0.0 and 1.0
		myLabel = QtWidgets.QLabel('Half Height')
		halfHeightSpinbox = QtWidgets.QDoubleSpinBox()
		halfHeightSpinbox.setMinimum(0.0)
		halfHeightSpinbox.setMaximum(1.0)
		halfHeightSpinbox.setSingleStep(0.05)
		halfHeightSpinbox.setValue(self.halfHeight)
		halfHeightSpinbox.valueChanged.connect(self.halfHeight_Callback)
		self.leftGridLayout.addWidget(myLabel, myRow, 0)
		self.leftGridLayout.addWidget(halfHeightSpinbox, myRow, 1)

		myRow += 1

		# report results
		self.myMin = QtWidgets.QLabel('Min: None')
		self.myMax = QtWidgets.QLabel('Max: None')
		self.mySNR = QtWidgets.QLabel('SNR: None')
		self.myDiameter = QtWidgets.QLabel('Diameter (pixels): None')
		self.leftGridLayout.addWidget(self.myMin, myRow, 0)
		self.leftGridLayout.addWidget(self.myMax, myRow, 1)

		myRow += 1

		self.leftGridLayout.addWidget(self.mySNR, myRow, 0)
		self.leftGridLayout.addWidget(self.myDiameter, myRow, 1)

		self.myHBoxLayout.addLayout(self.leftGridLayout)

		#
		# to hold plot
		self.figure = Figure(constrained_layout=True) # need size otherwise square image gets squished in y?
		self.canvas = backend_qt5agg.FigureCanvas(self.figure)
		#self.axes = self.figure.add_axes([0, 0, 1, 1]) #remove white border
		self.axes = self.figure.add_subplot(111)
		self.axes.patch.set_facecolor("black")

		self.figure.set_facecolor("black")

		self.myHBoxLayout.addWidget(self.canvas)

	def lineLength_Callback(self, value):
		print('lineLength_Callback() value:', value)
		self.lineLength = value
		self.mainWindow.getStackView().drawSlab(radius=value)

	def lineWidth_Callback(self, value):
		self.lineWidth = value
		if self.updateDict is not None:
			self.update(self.updateDict)

	def medianFilter_Callback(self, value):
		self.medianFilter = value
		if self.updateDict is not None:
			self.update(self.updateDict)

	def halfHeight_Callback(self, value):
		self.halfHeight = value
		if self.updateDict is not None:
			self.update(self.updateDict)

	def update(self, updateDict):
		"""
		Update the line profile
		We need too much info here ???
		"""
		if not self.doUpdate:
			return

		self.updateDict = updateDict

		xSlabPlot = updateDict['xSlabPlot']
		ySlabPlot = updateDict['ySlabPlot']
		slice = updateDict['slice']
		#print('bLineProfileWidget.update() xSlabPlot:', xSlabPlot, 'ySlabPlot:', ySlabPlot, 'slice:', slice)

		imageSlice = self.mainWindow.getStack().getImage2(channel=1, sliceNum=slice)

		src = (xSlabPlot[0], ySlabPlot[0])
		dst = (xSlabPlot[1], ySlabPlot[1])
		try:
			# abb aics added mode='constant'
			intensityProfile = profile.profile_line(imageSlice, src, dst, linewidth=self.lineWidth, mode='constant')
		except(ValueError) as e:
			print('abb aics bLineProfileWidget.update() got nan???')
			return

		# smooth it
		if self.medianFilter > 0:
			intensityProfile = scipy.ndimage.median_filter(intensityProfile, self.medianFilter)

		x = np.asarray([a for a in range(len(intensityProfile))]) # make alist of x points (todo: should be um, not points!!!)

		if np.isnan(intensityProfile[0]):
			print('\nERROR: line profile was nan?\n')
			return
		'''
		print('   intensityProfile:', type(intensityProfile), intensityProfile.shape, intensityProfile)
		print('   x:', type(x), x.shape, x)
		'''

		yFit, FWHM, leftIdx, rightIdx = self._fit(x,intensityProfile)
		#print('   yFit:', yFit, 'FWHM:', FWHM, 'leftIdx:', leftIdx, 'rightIdx:', rightIdx)

		goodFit = not np.isnan(leftIdx)

		minVal = round(np.nanmin(intensityProfile),2)
		maxVal = round(np.nanmax(intensityProfile),2)
		snrVal = round(maxVal - minVal, 2)
		minStr = 'Min: ' + str(minVal)
		self.myMin.setText(minStr)
		maxStr = 'Max: ' + str(maxVal)
		self.myMax.setText(maxStr)
		snrStr = 'SNR: ' + str(snrVal)
		self.mySNR.setText(snrStr)

		if goodFit:
			left_y = intensityProfile[leftIdx]
			# cludge because left/right threshold detection has different y ...
			#right_y = oneProfile[rightIdx]
			right_y = left_y
			xPnt = [leftIdx, rightIdx]
			yPnt = [left_y, right_y]

			# interface
			diamStr = 'Diameter (pixels): ' + str(int(rightIdx-leftIdx)) # points !!!
			self.myDiameter.setText(diamStr) # points !!!
		else:
			print('warning: fit failed')
			self.myDiameter.setText('Diameter (pixels): None')

		# clear entire axes
		self.axes.clear()

		self.axes.patch.set_facecolor("black")
		self.axes.spines['bottom'].set_color('white')
		self.axes.spines['left'].set_color('white')
		self.axes.xaxis.label.set_color('white')
		self.axes.tick_params(axis='x', colors='white')
		self.axes.tick_params(axis='y', colors='white')

		zorder = 1
		c = self.mainWindow.getStackView().options['Tracing']['lineProfileColor']
		self.axes.plot(x, intensityProfile,'o-', color=c, zorder=zorder) # Returns a tuple of line objects, thus the comma
		if goodFit:
			zorder = 2
			self.axes.plot(x, yFit,'r-', zorder=zorder) # gaussian
			zorder = 3
			self.axes.plot(xPnt, yPnt,'ob-', zorder=zorder)

		self.axes.set_xlabel('Line Pixels')
		self.axes.set_ylabel('Intensity')


		'''
		self.myIntensityPlot.set_xdata(x)
		self.myIntensityPlot.set_ydata(intensityProfile)
		'''

		#self.canvas.draw_idle()
		self.canvas.draw()

	def nudgeUp_Callback(self):
		"""
		"""
		print('bLineProfileWidget.nudgeUp_Callback()')
		#self.mainWindow.signal('save')

	def nudgeDown_Callback(self):
		"""
		"""
		print('bLineProfileWidget.nudgeDown_Callback()')
		#self.mainWindow.signal('save')

	def _fit(self, x, y):
		"""
		x: np.ndarray of x, e.g. pixels or um
		y: np.ndarray of line intensity profile
		returns:
			yfit: ndarray of gaussian file
			fwhm: scalar with full width at half maximal (heuristic calculation)
			left_idx:
			right_idx:
		for fitting a gaussian, see:
		https://stackoverflow.com/questions/44480137/how-can-i-fit-a-gaussian-curve-in-python
		for finding full width half maximal, see:
		https://stackoverflow.com/questions/10582795/finding-the-full-width-half-maximum-of-a-peak
		"""
		n = len(x)                          #the number of data
		mean = sum(x*y)/n                   #
		sigma = sum(y*(x-mean)**2)/n        #
		#mean = sum(y)/n                   #
		#sigma = sum((y-mean)**2)/n        #
		'''
		print('fitGaussian mean:', mean)
		print('fitGaussian sigma:', sigma)
		'''

		def myGaussian(x, amplitude, mean, stddev):
		    return amplitude * np.exp(-((x - mean) / 4 / stddev)**2)

		# see: https://stackoverflow.com/questions/10582795/finding-the-full-width-half-maximum-of-a-peak
		def FWHM(X,Y):
			#Y = scipy.signal.medfilt(Y, 3)
			#half_max = max(Y) / 2.
			half_max = max(Y) * self.halfHeight

			# for explanation of this wierd syntax
			# see: https://docs.scipy.org/doc/numpy/reference/generated/numpy.where.html
			#whr = np.where(Y > half_max)
			#print('   half_max:', half_max)
			whr = np.asarray(Y > half_max).nonzero()
			if len(whr[0]) > 2:
				left_idx = whr[0][0]
				right_idx = whr[0][-1]
				fwhm = X[right_idx] - X[left_idx]
			else:
				left_idx = np.nan
				right_idx = np.nan
				fwhm = np.nan
			return fwhm, left_idx, right_idx #return the difference (full width)

		try:
			#print('x.shape:', x.shape)
			popt,pcov = curve_fit(myGaussian,x,y)
			yFit = myGaussian(x,*popt)
			myFWHM, left_idx, right_idx = FWHM(x,y)
			return yFit, myFWHM, left_idx, right_idx
		except RuntimeError as e:
			#print('... fitGaussian() error: ', e)
			return np.full((x.shape[0]), np.nan), np.nan, np.nan, np.nan
		except:
			print('\n... ... fitGaussian() error: exception in bAnalysis.fitGaussian() !!!')
			raise
			return np.full((x.shape[0]), np.nan), np.nan, np.nan, np.nan
			#return None, None, None, None
