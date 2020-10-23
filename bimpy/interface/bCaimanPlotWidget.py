import sys

import numpy as np

from qtpy import QtCore, QtGui, QtWidgets

#from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

import qdarkstyle

import bimpy

class bCaimanPlotWidget0(QtWidgets.QMainWindow):
	#mainWindowSignal = QtCore.Signal(object)
	toolbarChangedSignal = QtCore.Signal(object)

	def __init__(self, parent=None, stackObject=None):
		super(bCaimanPlotWidget0, self).__init__(parent)
		self.myParent = parent
		self.myStack = stackObject

		# as a QMainWindow
		centralWidget = QtWidgets.QWidget(self)
		self.setCentralWidget(centralWidget)

		self.setMaximumHeight(200)

		myToolbar = bCaimanToolBar()
		self.addToolBar(myToolbar)

		self.myVBoxLayout = QtWidgets.QVBoxLayout(self)
		centralWidget.setLayout(self.myVBoxLayout)

		self.myPlotWidget = bCaimanPlotWidget(parent=None, stackObject=stackObject)
		self.myVBoxLayout.addWidget(self.myPlotWidget)

		# signals/slots
		myToolbar.caimanToolbarChange.connect(self.slot_toolbarchanged)

		self.toolbarChangedSignal.connect(self.myPlotWidget.slot_detectionChanged)

	def slot_selectAnnotation(self, myEvent):
		# tell our pyqtgraph plot to select
		myEvent.printSlot('bCaimanWidget0.slot_selectAnnotation()')
		annotationIdx = myEvent.nodeIdx
		self.myPlotWidget.selectAnnotation(annotationIdx)

	def slot_toolbarchanged(self, theDict):
		print('bCaimanPlotWidget0.slot_toolbarchanged() theDict:', theDict)
		# update self.myPlotWidget
		self.toolbarChangedSignal.emit(theDict)

	def slot_setSlice(self, myEvent, myValue):
		print('bCaimanPlotWidget0.slot_setSlice() needs to set slice to myValue:', myValue)
		self.myPlotWidget.slot_SetSlice(myValue)

class bCaimanPlotWidget(pg.PlotWidget):

	# signals
	selectAnnotationSignal = QtCore.Signal(object)

	def __init__(self, parent=None, stackObject=None):
		super(bCaimanPlotWidget, self).__init__(parent=parent)

		self.mainWindow = parent # usually bStackWidget
		self.myStack = stackObject

		self.mySelectedAnnotation = None # keep track so we can refresh when detection params change
		self.spikeDetectOn = True
		self.myThresh = 0.15
		self.myRefractoryPeriod = 0.15

		#keep this up-to-date so we can select with rect-roi
		self.xData = np.zeros(1) * np.nan #[] #
		self.yData = np.zeros(1) * np.nan #[]

		# setting pen=None disables line drawing
		xFake = []
		yFake = []
		self.myPointPlot = self.plot(xFake, yFake,
							#symbol='o', symbolSize=8, symbolBrush=('r'),
							#symbolPen=None,
							connect='finite')
		self.myPointPlot.sigPointsClicked.connect(self.onMouseClicked_points)
		#self.myPointPlot.sigMouseMoved.connect(self.onMouseMoved_points)
		#self.getPlotItem().getViewBox().mouseDragEvent = self.myDrag

		self.mySpikePlot = self.plot(xFake, yFake,
							pen=None,
							symbol='o', symbolSize=8, symbolBrush=('r'),
							#symbolPen=None,
							)

		self.myPointPlotSelection = self.plot([], [],
							#symbol='o', symbolSize=10, symbolBrush=('y'),
							#symbolPen=None,
							connect='finite')

		# a vertical line to indicate slice
		self.showSliceLine = True
		self.sliceLineNum = 0 # keep track so we can toggle with
		self.sliceMarker = pg.InfiniteLine(
											pos=0,
											angle=90,
											pen='w',
											movable=False)
		self.addItem(self.sliceMarker)

		self.getPlotItem().setLabel('left', 'f/f_0')
		self.getPlotItem().setLabel('bottom', 'frames')

		self.selectAnnotation(1)

	def getCaimanDict(self):
		return self.myStack.annotationList.caimanDict

	def onMouseClicked_points(self, item, points):
		theIdx = points[0].index()
		print('=== onMouseClicked_annotations() theIdx:', theIdx)
		self.selectAnnotation(theIdx)

	def selectAnnotation(self, idx=None):
		if self.getCaimanDict() is None:
			return
		if idx == None:
			idx = self.mySelectedAnnotation
		print('bCaimanPlotWidget.selectAnnotation() idx:', idx)
		print('  myThresh:', self.myThresh, 'myRefractoryPeriod:', self.myRefractoryPeriod)
		print('  self.spikeDetectOn:', self.spikeDetectOn)

		self.mySelectedAnnotation = idx

		caimanTrace, spikeTimes = bimpy.analysis.caiman.bCaiman.getCaimanTrace(
										self.getCaimanDict(),
										idx,
										thresh=self.myThresh,
										refractoryPoints=self.myRefractoryPeriod,
										doDetect=self.spikeDetectOn)

		xSel = [x for x in range(caimanTrace.size)]

		print('  caimanTrace.shape:', caimanTrace.shape)
		print('  xSel:', len(xSel))
		print('  spikeTimes:', spikeTimes)

		self.myPointPlotSelection.setData(xSel, caimanTrace)

		if self.spikeDetectOn:
			xSpikes = [spikeTime for spikeTime in spikeTimes]
			ySpikes = [caimanTrace[spikeTime] for spikeTime in spikeTimes]
			self.mySpikePlot.setData(xSpikes, ySpikes)
		else:
			self.mySpikePlot.setData([], [])

		# force update
		self.update()

	# todo: make this a slot
	def slot_SetSlice(self, sliceNumber=None):
		"""
		sliceNumber: pass None to not update self.sliceLineNum
		"""
		print('bCaimanPlotWidget.slotSetSlice() sliceNumber:', sliceNumber)

		if sliceNumber is not None:
			self.sliceLineNum = sliceNumber

		if self.showSliceLine:
			self.sliceMarker.show()
			self.sliceMarker.setValue(self.sliceLineNum)
		else:
			self.sliceMarker.hide()
		# force update
		self.update()

	def slot_selectAnnotation(self, myEvent):
		myEvent.printSlot('bCaimanPlotWidget.slot_selectAnnotation()')
		annotationIdx = myEvent.nodeIdx
		# keep track of our current annotation
		self.selectAnnotation(annotationIdx)

	def slot_detectionChanged(self, theDict):
		# redetect self.mySelectedAnnotation
		print('bCaimanPlotWidget.slot_detectionChanged() theDict:', theDict)
		self.spikeDetectOn = theDict['spikeDetectOn']
		self.myThresh = theDict['thresh']
		self.myRefractoryPeriod = theDict['refractoryPoints']
		self.showSliceLine = theDict['sliceLineOn']
		# update
		self.selectAnnotation()
		self.slot_SetSlice(sliceNumber=None) # pass none to not update self.sliceLineNum

# this is not going to work because our widget is just a pyqtgraph plot???
class bCaimanToolBar(QtWidgets.QToolBar):
	caimanToolbarChange = QtCore.Signal(object)

	def __init__(self, parent=None):
		super(bCaimanToolBar, self).__init__(parent)

		self.theThresh = 0.15
		self.theRefractoryPoints = 10 # corresponds to image frame rate

		#
		# show slice line
		self.spikeDetectOn = True
		spikeDetectCheckBox = QtWidgets.QCheckBox('Spike Detect')
		spikeDetectCheckBox.setCheckState(QtCore.Qt.Checked)
		spikeDetectCheckBox.stateChanged.connect(self.spikeDetect_callback)
		self.addWidget(spikeDetectCheckBox)

		#
		# threshold label and spin box
		myLabel = QtWidgets.QLabel('Threshold')
		self.addWidget(myLabel)

		threshSpinBox = QtWidgets.QDoubleSpinBox()
		threshSpinBox.setMinimum(0.0)
		threshSpinBox.setValue(self.theThresh)
		threshSpinBox.setSingleStep(0.01)
		threshSpinBox.valueChanged.connect(self.threshold_Callback)
		self.addWidget(threshSpinBox)

		#
		# refractory label and spin box
		myLabel = QtWidgets.QLabel('Refractory Points')
		self.addWidget(myLabel)

		refractorySpinBox = QtWidgets.QSpinBox()
		refractorySpinBox.setMinimum(0)
		refractorySpinBox.setValue(self.theRefractoryPoints)
		refractorySpinBox.valueChanged.connect(self.refractory_Callback)
		self.addWidget(refractorySpinBox)

		#
		# show slice line
		self.sliceLineOn = True
		sliceLineCheckBox = QtWidgets.QCheckBox('Slice Line')
		sliceLineCheckBox.setCheckState(QtCore.Qt.Checked)
		sliceLineCheckBox.stateChanged.connect(self.sliceLine_callback)
		self.addWidget(sliceLineCheckBox)

	def _getEmitDict(self):
		theDict = {}
		theDict['thresh'] = self.theThresh
		theDict['refractoryPoints'] = self.theRefractoryPoints
		theDict['sliceLineOn'] = self.sliceLineOn
		theDict['spikeDetectOn'] = self.spikeDetectOn
		return theDict

	def spikeDetect_callback(self, state):
		"""
		state: 2==On, 0==Off
		"""
		print('spikeDetect_callback() state:', state)
		self.spikeDetectOn = state == 2

		# emit
		self.caimanToolbarChange.emit(self._getEmitDict())

	def sliceLine_callback(self, state):
		"""
		state: 2==On, 0==Off
		"""
		print('sliceLine_callback() state:', state)
		self.sliceLineOn = state == 2

		# emit
		self.caimanToolbarChange.emit(self._getEmitDict())

	def threshold_Callback(self, value):
		# re-run analysis on selected annotation
		print('bCaimanToolBar.threshold_Callback() value:', value)
		self.theThresh = value

		#
		emitDict = self._getEmitDict()
		self.caimanToolbarChange.emit(emitDict)

	def refractory_Callback(self, value):
		# re-run analysis on selected annotation
		print('bCaimanToolBar.refractory_Callback() value:', value)
		self.refractoryPoints = value

		#
		emitDict = self._getEmitDict()
		self.caimanToolbarChange.emit(emitDict)

def main(path):
	myStack = bimpy.bStack(path, loadImages=False, loadTracing=True)

	app = QtWidgets.QApplication(sys.argv)

	'''
	print(2)
	myPlot = bPyQtPlot(None, myStack)
	myPlot.show()
	'''

	#myPlotWidget = bCaimanPlotWidget(parent=None, stackObject=myStack)
	myPlotWidget = bCaimanPlotWidget0(parent=None, stackObject=myStack)
	myPlotWidget.show()

	sys.exit(app.exec_()) # this will loop

if __name__ == '__main__':

	path = '/media/cudmore/data/20201014/inferior/2_nif_inferior_cropped_aligned.tif'
	main(path)
