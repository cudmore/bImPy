# 20200122

from PyQt5 import QtGui, QtCore, QtWidgets

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

		self.lineWidth = 3

		self.setMaximumHeight(200)

		self.myHBoxLayout = QtWidgets.QHBoxLayout(self)

		#
		# to hold control panel
		self.leftVBoxLayout = QtWidgets.QVBoxLayout(self)

		# nudge up button
		nudgeUpButton = QtWidgets.QPushButton('Nudge Up')
		nudgeUpButton.clicked.connect(self.nudgeUp_Callback)
		self.leftVBoxLayout.addWidget(nudgeUpButton)
		# nudge down button
		nudgeUpButton = QtWidgets.QPushButton('Nudge Down')
		nudgeUpButton.clicked.connect(self.nudgeDown_Callback)
		self.leftVBoxLayout.addWidget(nudgeUpButton)

		self.myHBoxLayout.addLayout(self.leftVBoxLayout)

		#
		# to hold plot
		self.figure = Figure(constrained_layout=True) # need size otherwise square image gets squished in y?
		self.canvas = backend_qt5agg.FigureCanvas(self.figure)
		#self.axes = self.figure.add_axes([0, 0, 1, 1]) #remove white border
		self.axes = self.figure.add_subplot(111)
		self.axes.patch.set_facecolor("black")

		self.figure.set_facecolor("black")

		'''
		xFake = np.asarray([1,2,3])
		yFake = np.asarray([0,100,40])
		xPntFake = [1.5, 2.5]
		yPntFake = [5, 5]
		zorder = 1
		#self.myIntensityPlot, = self.axes.plot(xFake, yFake,'.c-', zorder=zorder, picker=5) # Returns a tuple of line objects, thus the comma
		self.axes.plot(xFake, yFake,'.c-', zorder=zorder, picker=5) # Returns a tuple of line objects, thus the comma
		self.axes.plot(xPntFake, yPntFake,'ob-', zorder=zorder, picker=5) # Returns a tuple of line objects, thus the comma
		'''

		self.myHBoxLayout.addWidget(self.canvas)

	def update(self, updateDict):
		xSlabPlot = updateDict['xSlabPlot']
		ySlabPlot = updateDict['ySlabPlot']
		slice = updateDict['slice']
		#print('bLineProfileWidget.update() xSlabPlot:', xSlabPlot, 'ySlabPlot:', ySlabPlot, 'slice:', slice)

		imageSlice = self.mainWindow.getStack().getImage(sliceNum=slice)

		src = (xSlabPlot[0], ySlabPlot[0])
		dst = (xSlabPlot[1], ySlabPlot[1])
		intensityProfile = profile.profile_line(imageSlice, src, dst, linewidth=self.lineWidth)
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

		if goodFit:
			left_y = intensityProfile[leftIdx]
			# cludge because left/right threshold detection has different y ...
			#right_y = oneProfile[rightIdx]
			right_y = left_y
			xPnt = [leftIdx, rightIdx]
			yPnt = [left_y, right_y]
		else:
			print('warning: fit failed')

		# clear entire axes
		self.axes.clear()

		self.axes.patch.set_facecolor("black")
		self.axes.spines['bottom'].set_color('white')
		self.axes.spines['left'].set_color('white')
		self.axes.xaxis.label.set_color('white')
		self.axes.tick_params(axis='x', colors='white')
		self.axes.tick_params(axis='y', colors='white')

		zorder = 1
		self.axes.plot(x, intensityProfile,'oc-', zorder=zorder) # Returns a tuple of line objects, thus the comma
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
			Y = scipy.signal.medfilt(Y, 3)
			half_max = max(Y) / 2.
			half_max = max(Y) * 0.7

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
