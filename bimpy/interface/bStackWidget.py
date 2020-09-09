# 20190802

# goal: make a stack window and overlay tracing from deepvess

import os, time
from collections import OrderedDict
import math
import json

import numpy as np

#from PyQt5 import QtGui, QtCore, QtWidgets
from qtpy import QtGui, QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends import backend_qt5agg

import matplotlib.cm
#import matplotlib.pyplot as plt
#t = plt.cm.get_cmap()

import tifffile
import h5py
import pickle # to save masks

# testing, remember to remove
#import pyqtgraph as pg

import qdarkstyle #see: https://github.com/ColinDuquesnoy/QDarkStyleSheet

import bimpy

################################################################################
# 20200908 switched over to QMainWindow (finally) just needed to make QWidget and set as CentralWidget
# #class bStackWidget(QtWidgets.QWidget):
class bStackWidget(QtWidgets.QMainWindow):
	"""
	A widget to display a stack. This includes a bStackView and a bAnnotationTable.
	"""

	optionsStateChange = QtCore.Signal(str, str, bool) # object can be a dict

	def __init__(self, mainWindow=None, parent=None, path=''):
		super(bStackWidget, self).__init__()

		self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

		self.mainWindow = mainWindow

		self.options = None
		if not self.optionsLoad():
			self.options_defaults()

		self.path = path
		self.mySearchAnnotation = None

		basename = os.path.basename(self.path)
		self.setWindowTitle(basename)

		self.setObjectName('bStackWidget0')
		'''
		self.setStyleSheet("""
			#bStackWidget0 {
				background-color: #222;
			}
			.QLabel {
				color: #bbb;
			}
			.QCheckBox {
				color: #bbb;
			}
		""")
		'''

		# only used by GroupBox
		myPath = os.path.dirname(os.path.abspath(__file__))
		mystylesheet_css = os.path.join(myPath, 'css', 'mystylesheet.css')
		with open(mystylesheet_css) as f:
			myStyleSheet = f.read()

		#
		self.mySimpleStack = bimpy.bStack(path) # backend stack

		#
		# search for close nodes (very slow)
		#self.mySimpleStack.slabList.search()

		self.napariViewer = None

		# abb to QMainWindow
		centralWidget = QtWidgets.QWidget(self)
		self.setCentralWidget(centralWidget)

		self.myToolbar = bimpy.interface.bToolBar(self, parent=None)
		self.myToolbar.syncWithOptions(self.options)
		self.addToolBar(self.myToolbar)
		'''
		# to hold horizontal toolbar then the rest
		self.myMainVBoxLayout = QtWidgets.QVBoxLayout(self)

		#
		self.myToolbar = bimpy.interface.bToolBar(self)
		#self.addToolBar(self.myToolbar)
		self.myMainVBoxLayout.addWidget(self.myToolbar)#, stretch=2)
		'''

		# holds (left toolbar, vertical), vertical has (contrast/image/feedback)
		self.myHBoxLayout = QtWidgets.QHBoxLayout(self)

		centralWidget.setLayout(self.myHBoxLayout)

		'''
		self.myMainVBoxLayout.addLayout(self.myHBoxLayout)#, stretch=2)
		'''

		#
		#
		self.myFeedbackWidget = bimpy.interface.bLeftToolbarWidget(self)

		self.myHBoxLayout.addWidget(self.myFeedbackWidget)#, stretch=2)
		#
		#

		self.myVBoxLayout = QtWidgets.QVBoxLayout()

		# testing pyqtgraph (removing self.myStackView on 20200829)
		self.myStackView = None
		#self.myStackView = bStackView(self.mySimpleStack, mainWindow=self) # a visual stack
		# abb
		self.myStackView2 = bimpy.interface.bPyQtGraph.myPyQtGraphPlotWidget(self, self.mySimpleStack) # a visual stack

		self.myContrastWidget = bimpy.interface.bStackContrastWidget(mainWindow=self)

		self.myHBoxLayout2 = QtWidgets.QHBoxLayout()

		# a slider to set slice number
		self.mySliceSlider = myStackSlider(self.mySimpleStack.numImages)

		if self.myStackView is not None:
			self.myHBoxLayout2.addWidget(self.myStackView)
		self.myHBoxLayout2.addWidget(self.myStackView2)
		self.myHBoxLayout2.addWidget(self.mySliceSlider)

		#
		self.myVBoxLayout.addWidget(self.myContrastWidget) #, stretch=0.1)
		#self.myVBoxLayout.addWidget(self.bLeftToolbarWidget) #, stretch=0.1)
		self.myVBoxLayout.addLayout(self.myHBoxLayout2) #, stretch = 9)

		self.lineProfileWidget = bimpy.interface.bLineProfileWidget(mainWindow=self)
		self.myVBoxLayout.addWidget(self.lineProfileWidget)

		self.statusToolbarWidget = bimpy.interface.bStatusToolbarWidget(mainWindow=self, numSlices=self.mySimpleStack.numSlices)
		#self.addToolBar(QtCore.Qt.BottomToolBarArea, self.statusToolbarWidget)
		self.myVBoxLayout.addWidget(self.statusToolbarWidget) #, stretch = 9)

		#
		# nodes
		self.nodeTable2 = bimpy.interface.bTableWidget2('nodes', self.mySimpleStack.slabList.nodeDictList, parent=self)
		self.nodeTable2.hideColumns(['x', 'y', 'skelID', 'slabIdx'])
		self.myHBoxLayout.addWidget(self.nodeTable2, stretch=2)

		# edges
		self.edgeTable2 = bimpy.interface.bTableWidget2('edges', self.mySimpleStack.slabList.edgeDictList, parent=self)
		self.edgeTable2.hideColumns(['skelID', 'color', 'slabList'])
		self.myHBoxLayout.addWidget(self.edgeTable2, stretch=2)

		# edits/search
		self.searchWidget = bimpy.interface.bSearchWidget(self)
		self.myHBoxLayout.addWidget(self.searchWidget, stretch=3)
		#self.editTable2 = bimpy.interface.bTableWidget2('node search', self.mySimpleStack.slabList.editDictList, parent=self)
		#self.myHBoxLayout.addWidget(self.editTable2, stretch=3)

		#
		# annotation list
		self.annotationTable = bimpy.interface.bAnnotationTableWidget(self.mySimpleStack.annotationList.myList, parent=self)
		self.annotationTable.hideColumns(['rowNum', 'colNum', 'path'])
		self.myHBoxLayout.addWidget(self.annotationTable, stretch=2)
		#

		# vertical layout for contrast/image/feedback
		self.myHBoxLayout.addLayout(self.myVBoxLayout, stretch=5) #, stretch=7) # stretch=10, not sure on the units???

		#
		# signals and slots

		# listen to bStackWidget
		self.optionsStateChange.connect(self.myFeedbackWidget.slot_OptionsStateChange)

		#
		# listen to self.bLeftToolbarWidget
		#self.bLeftToolbarWidget.clickStateChange.connect(self.myStackView.slot_StateChange)
		#
		# listen to self.myStackView
		if self.myStackView is not None:
			self.myStackView.displayStateChangeSignal.connect(self.myFeedbackWidget.slot_DisplayStateChange)
			self.myStackView.setSliceSignal.connect(self.mySliceSlider.slot_UpdateSlice)
			#self.myStackView.setSliceSignal.connect(self.bLeftToolbarWidget.slot_StateChange)
			self.myStackView.setSliceSignal.connect(self.statusToolbarWidget.slot_StateChange)
			self.myStackView.selectNodeSignal.connect(self.nodeTable2.slot_select)
			self.myStackView.selectNodeSignal.connect(self.statusToolbarWidget.slot_select)
			self.myStackView.selectEdgeSignal.connect(self.statusToolbarWidget.slot_select)
			self.myStackView.selectEdgeSignal.connect(self.nodeTable2.slot_select)
			self.myStackView.selectEdgeSignal.connect(self.edgeTable2.slot_select)
			self.myStackView.tracingEditSignal.connect(self.nodeTable2.slot_updateTracing)
			self.myStackView.tracingEditSignal.connect(self.edgeTable2.slot_updateTracing)

			if self.myFeedbackWidget is not None:
				self.myStackView.selectNodeSignal.connect(self.myFeedbackWidget.slot_selectNode)
				self.myStackView.selectEdgeSignal.connect(self.myFeedbackWidget.slot_selectEdge)
			'''
			# todo: implement this in bTableWidget2
			self.myStackView.tracingEditSignal.connect(self.annotationTable.slot_updateTracing)
			'''
			self.myStackView.setSliceSignal.connect(self.myContrastWidget.slot_setSlice)
		#
		# listen to self.mySliceSlider
		if self.myStackView is not None:
			self.mySliceSlider.updateSliceSignal.connect(self.myStackView.slot_StateChange)
		#self.mySliceSlider.updateSliceSignal.connect(self.bLeftToolbarWidget.slot_StateChange)
		self.mySliceSlider.updateSliceSignal.connect(self.statusToolbarWidget.slot_StateChange)
		self.mySliceSlider.updateSliceSignal.connect(self.myContrastWidget.slot_setSlice)
		#
		# listen to self.annotationTable
		'''
		self.annotationTable.selectNodeSignal.connect(self.myStackView.slot_selectNode) # change to slot_selectNode ???
		self.annotationTable.selectEdgeSignal.connect(self.myStackView.slot_selectEdge) # change to slot_selectNode ???
		'''
		# node/edge/search tables
		if self.myStackView is not None:
			self.nodeTable2.selectRowSignal.connect(self.myStackView.slot_selectNode)
			self.edgeTable2.selectRowSignal.connect(self.myStackView.slot_selectEdge)
			self.editTable2.selectRowSignal.connect(self.myStackView.slot_selectNode)
			self.editTable2.selectRowSignal.connect(self.myStackView.slot_selectEdge)
		#
		# was this
		#self.nodeTable2.selectRowSignal.connect(self.statusToolbarWidget.slot_StateChange2)
		#self.edgeTable2.selectRowSignal.connect(self.statusToolbarWidget.slot_StateChange2)
		#self.editTable2.selectRowSignal.connect(self.statusToolbarWidget.slot_StateChange2)
		self.nodeTable2.selectRowSignal.connect(self.statusToolbarWidget.slot_select)
		self.edgeTable2.selectRowSignal.connect(self.statusToolbarWidget.slot_select)

		self.searchWidget.searchTable().selectRowSignal.connect(self.statusToolbarWidget.slot_select)

		self.nodeTable2.selectRowSignal.connect(self.mySliceSlider.slot_UpdateSlice2)
		self.edgeTable2.selectRowSignal.connect(self.mySliceSlider.slot_UpdateSlice2)
		self.edgeTable2.selectRowSignal.connect(self.mySliceSlider.slot_UpdateSlice2)
		self.nodeTable2.selectRowSignal.connect(self.myContrastWidget.slot_UpdateSlice2)
		self.edgeTable2.selectRowSignal.connect(self.myContrastWidget.slot_UpdateSlice2)
		self.searchWidget.searchTable().selectRowSignal.connect(self.myContrastWidget.slot_UpdateSlice2)
		#
		# listen to edit table, self.
		'''
		self.annotationTable.myEditTableWidget.selectEdgeSignal.connect(self.myStackView.slot_selectEdge)
		self.annotationTable.myEditTableWidget.selectEdgeSignal.connect(self.annotationTable.slot_selectEdge)
		'''
		#
		# listen to bStackContrastWidget
		if self.myStackView is not None:
			self.myContrastWidget.contrastChangeSignal.connect(self.myStackView.slot_contrastChange)

		##
		##
		# abb PyQtGraph
		self.myContrastWidget.contrastChangeSignal.connect(self.myStackView2.slot_contrastChange)

		self.mySliceSlider.updateSliceSignal.connect(self.myStackView2.slot_StateChange)
		self.nodeTable2.selectRowSignal.connect(self.myStackView2.slot_selectNode)
		self.edgeTable2.selectRowSignal.connect(self.myStackView2.slot_selectEdge)
		self.searchWidget.searchTable().selectRowSignal.connect(self.myStackView2.slot_selectNode)
		self.searchWidget.searchTable().selectRowSignal.connect(self.myStackView2.slot_selectEdge)

		self.myStackView2.displayStateChangeSignal.connect(self.statusToolbarWidget.slot_DisplayStateChange)
		self.myStackView2.displayStateChangeSignal.connect(self.myFeedbackWidget.slot_DisplayStateChange)
		#
		self.myStackView2.setSliceSignal.connect(self.mySliceSlider.slot_UpdateSlice)
		self.myStackView2.setSliceSignal.connect(self.statusToolbarWidget.slot_StateChange)
		self.myStackView2.selectNodeSignal.connect(self.nodeTable2.slot_select)
		self.myStackView2.selectNodeSignal.connect(self.statusToolbarWidget.slot_select)
		self.myStackView2.selectEdgeSignal.connect(self.statusToolbarWidget.slot_select)
		self.myStackView2.selectEdgeSignal.connect(self.nodeTable2.slot_select)
		self.myStackView2.selectEdgeSignal.connect(self.edgeTable2.slot_select)

		#
		# new annotation table using bAnnotationList (from bStack)
		self.myStackView2.selectAnnotationSignal.connect(self.annotationTable.slot_select)
		self.annotationTable.selectRowSignal.connect(self.myStackView2.slot_selectAnnotation)

		self.myStackView2.tracingEditSignal.connect(self.nodeTable2.slot_updateTracing)
		self.myStackView2.tracingEditSignal.connect(self.edgeTable2.slot_updateTracing)
		self.myStackView2.tracingEditSignal.connect(self.annotationTable.slot_updateTracing)
		# end abb PyQtGraph
		##
		##

		self.updateDisplayedWidgets()

		left = self.options['Window']['left']
		top = self.options['Window']['top']
		width = self.options['Window']['width']
		height = self.options['Window']['height']

		self.move(left,top)
		self.resize(width, height)

		if self.myStackView is not None:
			self.myStackView.setSlice(0)
		self.myStackView2.setSlice(0)

	def getMyStack(self):
		return self.mySimpleStack

	def getStackView(self):
		if self.myStackView is not None:
			return self.myStackView
		return self.myStackView2

	def mousePressEvent(self, event):
		"""
		This is a PyQt callback (not PyQtGraph)
		Set event.setAccepted(False) to keep propogation so we get to PyQt callbacks like
			self.onMouseClicked_scene(), _slabs(), _nodes()
		"""
		#print('mousePressEvent() event:', event)
		if event.button() == QtCore.Qt.RightButton:
			self.showRightClickMenu(event.pos())
			self.mouseReleaseEvent(event)
		else:
			event.setAccepted(False)
			super().mousePressEvent(event)

	def moveEvent(self, event):
		xy = self.mapToGlobal(QtCore.QPoint(0,0))
		#print('moveEvent()', xy.x(), xy.y())
		self.options['Window']['left'] = xy.x()
		self.options['Window']['top'] = xy.y()

		#print('bStackWindow.moveEvent()', self.options['Window'])

	def resizeEvent(self, event):
		width = self.frameGeometry().width()
		height = self.frameGeometry().height()
		self.options['Window']['width'] = width
		self.options['Window']['height'] = height
		#print('bStackWidget.resizeVent()', self.options['Window'])

	'''
	def getLeftToolbarWidget(self):
		return self.bLeftToolbarWidget
	'''

	# todo: remove
	'''
	def slot_StateChange_(self, signalName, signalValue):
		print('bStackWidget.slot_StateChange() signalName:', signalName, 'signalValue:', signalValue)
		#if signalName=='set slice':
		#	self.mySliceSlider.setValue(signalValue)
	'''

	#def attachNapari(self, napariViewer):
	#	self.napariViewer = napariViewer

	def openNapari(self):
		if self.napariViewer is None:
			self.napariViewer = bimpy.interface.bNapari(path='', theStack=self.mySimpleStack, myStackWidget=self)

	def getStatusToolbar(self):
		return self.statusToolbarWidget

	def updateDisplayedWidgets(self):
		# left control bar
		'''
		if self.options['Panels']['showAnnotations']:
			self.annotationTable.show()
		else:
			self.annotationTable.hide()
		'''

		if self.options['Panels']['showToolbar']:
			self.myToolbar.show()
		else:
			self.myToolbar.hide()

		if self.options['Panels']['showLeftToolbar']:
			self.myFeedbackWidget.show()
		else:
			self.myFeedbackWidget.hide()

		if self.options['Panels']['showNodeList']:
			self.nodeTable2.show()
		else:
			self.nodeTable2.hide()

		if self.options['Panels']['showEdgeList']:
			self.edgeTable2.show()
		else:
			self.edgeTable2.hide()

		if self.options['Panels']['showSearch']:
			self.searchWidget.show()
		else:
			self.searchWidget.hide()

		if self.options['Panels']['showAnnotations']:
			self.annotationTable.show()
		else:
			self.annotationTable.hide()

		# contrast bar
		if self.options['Panels']['showContrast']:
			self.myContrastWidget.show()
			self.myContrastWidget.myDoUpdate = True
		else:
			self.myContrastWidget.hide()
			self.myContrastWidget.myDoUpdate = False

		# feedback bar
		'''
		if self.options['Panels']['showFeedback']:
			self.bLeftToolbarWidget.show()
		else:
			self.bLeftToolbarWidget.hide()
		'''

		if self.options['Panels']['showStatus']:
			self.statusToolbarWidget.show()
		else:
			self.statusToolbarWidget.hide()

		if self.options['Panels']['showLineProfile']:
			self.lineProfileWidget.show()
			self.lineProfileWidget.doUpdate = True
		else:
			self.lineProfileWidget.hide()
			self.lineProfileWidget.doUpdate = False

		self.repaint()

	# get rid of this
	def getStack(self):
		return self.mySimpleStack

	def signal(self, signal, value=None):
		print('  === bStackWidget.signal()', 'signal:', signal, 'value:', value)

		# used for my vesselucida edit list
		"""
		if signal == 'selectEdgeListFromTable':
			print('=== bStackWidget.signal() selectEdgeListFromTable value:', value)
			self.myStackView.selectEdgeList(value, snapz=True)
			#self.selectEdgeList(value, snapz=True)
			# would require multiple selection
			'''
			if not fromTable:
				self.annotationTable.selectEdgeRow(value)
			'''
		"""

		if signal == 'cancelSelection':
			self.getStackView().cancelSelection()

		if signal == 'Analyze All Diameters':
			# abb aics to run in parallel

			# in series
			serialTimer = bimpy.util.bTimer('Analyze All Diameters (serial version)')

			self.mySimpleStack.slabList.analyzeSlabIntensity()

			print(serialTimer.elapsed())

			# multiprocessing does not work inside PyQt5, need to make a thread clas and spawn/run
			'''
			#bimpy.bVascularTracingAics.analyzeSlabIntensity2(self.mySimpleStack.slabList)

			# in parallel
			type = signal
			paramDict = {}
			paramDict['radius'] = 20
			paramDict['lineWidth'] = 5
			paramDict['medianFilter'] = 3

			workerTimer = bimpy.util.bTimer('Analyze All Diameters (parallel version)')
			self.tmpWorkThread = bimpy.bVascularTracingAics.myWorkThread(self.mySimpleStack.slabList, type, paramDict)
			#workThread.workerThreadFinishedSignal[object].connect(self.add)
			#self.tmpWorkThread.start()
			self.tmpWorkThread.run()

			print(workerTimer.elapsed())
			'''

			# abb aics update edge list (we set ['Diam2'])
			self.edgeTable2.populate(self.mySimpleStack.slabList.edgeDictList)

		if signal == 'update line profile':
			# value is profileDict
			'''
				profileDict = {
					'ySlabPlot': ySlabPlot,
					'xSlabPlot': xSlabPlot,
					'slice': self.currentSlice,
				}
			'''
			self.lineProfileWidget.updateLineProfile(value)

		if signal == 'save':
			startTime = time.time()
			h5FilePath = self.mySimpleStack.saveAnnotations()
			'''
			if h5FilePath is not None:
				with h5py.File(h5FilePath, "a") as f:
					# slabs are in a dataset
					#slabData = np.column_stack((self.x, self.y, self.z, self.d, self.int, self.edgeIdx, self.nodeIdx,))
					#f.create_dataset('slabs', data=slabData)
					print('    bStackWidget saving maskedNodes ...')
					maskData = str(self.getStackView().maskedNodes)
					f.create_dataset('masks', data=maskData)
			'''
			#print('   saving maskedNodes')
			# see second answer: https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
			if h5FilePath is not None:
				self.getStackView().saveMasks()
				'''
				maskFilePath = h5FilePath + '.pickle'
				# json_dump = json.dumps({'a': a, 'aa': [2, (2, 3, 4), a], 'bb': [2]}, cls=NumpyEncoder)
				print('    saving maskedNodes as:', maskFilePath)
				with open(maskFilePath, 'wb') as fout:
					#json.dump(self.getStackView().maskedNodes, fout, cls=myNumpyEncoder)
					pickle.dump(self.getStackView().maskedNodes, fout)
				'''
			print('  saved', h5FilePath, 'in', round(time.time()-startTime,2), 'seconds')

		elif signal == 'load':
			startTime = time.time()
			h5FilePath = self.mySimpleStack.loadAnnotations()
			if h5FilePath is not None:
				self.getStackView().loadMasks()
				'''
				maskFilePath = h5FilePath + '.pickle'
				print('    loading maskedNodes from:', maskFilePath)
				with open(maskFilePath, 'rb') as filename:
					self.getStackView().maskedNodes = pickle.load(filename)
				'''
			print('  loaded in', round(time.time()-startTime,2), 'seconds')
			self.nodeTable2.populate(self.mySimpleStack.slabList.nodeDictList)
			self.edgeTable2.populate(self.mySimpleStack.slabList.edgeDictList)
			#self.editTable2.populate(self.mySimpleStack.slabList.editDictList)

		elif signal == 'load_xml':
			self.mySimpleStack.loadAnnotations_xml()

		elif signal == 'save stack copy':
			print('todo: fix "save stack copy"')
			return
			# save the currently viewed stack (always prompt for name)

			# get full path to save to
			displayThisStack = self.getStackView().displayStateDict['displayThisStack']
			print('displayThisStack:', displayThisStack)
			filePath = self.mySimpleStack.saveStackCopy(displayThisStack)
			# ask user if ok
			file = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', filePath)
			file = file[0]
			if len(file) > 0:
				#tifffile.imsave(file, self.mySimpleStack.getStack(displayThisStack))
				print('\n\t\tALWAYS SAVING SLIDING Z\n\n')
				tifffile.imsave(file, self.mySimpleStack._slidingz)

		#
		# search
		elif signal == 'Disconnected Edges':
			self.mySearchAnnotation = bimpy.bSearchAnnotations(self.mySimpleStack.slabList,
								fn = bimpy.bSearchAnnotations.searchDisconnectedEdges,
								params = None,
								searchType='edge search')
			self.mySearchAnnotation.searchFinishedSignal.connect(self.searchWidget.searchTable().slot_SearchFinished)
			self.mySearchAnnotation.start()

		elif signal == 'search 1':
			thresholdDist = value
			'''
			searchObj = bimpy.bSearchAnnotations(self.mySimpleStack.slabList)
			results = searchObj.searchDeadEnd(thresholdDist=thresholdDist)
			self.editTable2.populate(results)
			self.editTable2._type = 'edge search'
			'''

			self.mySearchAnnotation = bimpy.bSearchAnnotations(self.mySimpleStack.slabList,
								fn = bimpy.bSearchAnnotations.searchDeadEnd,
								params = thresholdDist,
								searchType='edge search')
			self.mySearchAnnotation.searchFinishedSignal.connect(self.searchWidget.searchTable().slot_SearchFinished)
			self.mySearchAnnotation.start()

		elif signal == 'search 1_1':
			thresholdDist = value
			'''
			searchObj = bimpy.bSearchAnnotations(self.mySimpleStack.slabList)
			results = searchObj.searchDeadEnd2(thresholdDist=thresholdDist)
			self.editTable2.populate(results)
			self.editTable2._type = 'node search'
			'''

			'''
			self.mySearchAnnotation = bimpy.bSearchAnnotations(self.mySimpleStack.slabList,
								fn = bimpy.bSearchAnnotations.searchDeadEnd2,
								params = thresholdDist,
								searchType='node search')
			self.mySearchAnnotation.searchFinishedSignal.connect(self.editTable2.slot_SearchFinished)
			self.mySearchAnnotation.searchNewHitSignal.connect(self.editTable2.slot_newSearchHit)
			self.mySearchAnnotation.start()
			'''

			fn = bimpy.bSearchAnnotations.searchDeadEnd2
			params = thresholdDist # pass None for no parameters
			searchType = 'node search'
			self.startSearch(fn, params, searchType)

		elif signal == 'search 1_2':
			thresholdDist = value
			searchObj = bimpy.bSearchAnnotations(self.mySimpleStack.slabList)
			results = searchObj.searchBigGaps(thresholdDist=thresholdDist)
			self.editTable2.populate(results)
			self.editTable2._type = 'edge search'

		elif signal == 'search 1_5':
			'''
			thresholdDist = value
			searchObj = bimpy.bSearchAnnotations(self.mySimpleStack.slabList)
			results = searchObj.searchCloseNodes(thresholdDist=thresholdDist)
			self.editTable2.populate(results)
			self.editTable2._type = 'node search'
			'''

			thresholdDist = value
			fn = bimpy.bSearchAnnotations.searchCloseNodes
			params = thresholdDist # pass None for no parameters
			searchType = 'node search'
			self.startSearch(fn, params, searchType)

		elif signal == 'search 1_6':
			thresholdDist = value
			searchObj = bimpy.bSearchAnnotations(self.mySimpleStack.slabList)
			results = searchObj.searchCloseSlabs(thresholdDist=thresholdDist)
			self.editTable2.populate(results)
			self.editTable2._type = 'edge search'

		elif signal == 'search 2':
			searchObj = bimpy.bSearchAnnotations(self.mySimpleStack.slabList)
			results = searchObj.allDeadEnds()
			self.editTable2.populate(results)
			self.editTable2._type = 'edge search'

		elif signal == 'search 3':
			searchObj = bimpy.bSearchAnnotations(self.mySimpleStack.slabList)
			results = searchObj.shortestPath(value)
			if results is not None:
				self.editTable2.populate(results)
				self.editTable2._type = 'edge search'

		elif signal == 'search 4':
			searchObj = bimpy.bSearchAnnotations(self.mySimpleStack.slabList)
			results = searchObj.allPaths(value)
			if results is not None:
				self.editTable2.populate(results)
				self.editTable2._type = 'edge search'

		#elif signal == 'search 5':
		#	searchObj = bimpy.bSearchAnnotations(self.mySimpleStack.slabList)
		#	results = searchObj.shortestLoop(value)
		#	if results is not None:
		#		self.editTable2.populate(results)
		#		self.editTable2._type = 'edge search'

		elif signal == 'search 5':
			searchObj = bimpy.bSearchAnnotations(self.mySimpleStack.slabList)
			results = searchObj.allSubgraphs()
			if results is not None:
				self.editTable2.populate(results)
				self.editTable2._type = 'edge search'

		elif signal == 'search 6':
			searchObj = bimpy.bSearchAnnotations(self.mySimpleStack.slabList)
			results = searchObj.allLoops(value)
			if results is not None:
				self.editTable2.populate(results)
				self.editTable2._type = 'edge search'

	def startSearch(self, fn, params, searchType):
		"""
		Start a background search thread
		Use keyboard q to quit

		fn: pointer to search function to run, like: bimpy.bSearchAnnotations.searchDeadEnd2
		params:
		searchType: ('node search', 'edgeSearch') defines the type of object in search results
		"""
		self.mySearchAnnotation = bimpy.bSearchAnnotations(self.mySimpleStack.slabList,
							fn = fn,
							params = params,
							searchType = searchType)
		# self.searchWidget.searchTable()
		self.mySearchAnnotation.searchFinishedSignal.connect(self.searchWidget.searchTable().slot_SearchFinished)
		self.mySearchAnnotation.searchNewHitSignal.connect(self.searchWidget.searchTable().slot_newSearchHit)
		self.mySearchAnnotation.start()

	def optionsChange(self, key1, key2, value=None, toggle=False, doEmit=False):
		if toggle:
			value = not self.options[key1][key2]
		self.options[key1][key2] = value
		self.updateDisplayedWidgets()
		if doEmit:
			self.optionsStateChange.emit(key1, key2, value)

	# abb aics
	def repopulateAllTables(self):
		self.nodeTable2.populate(self.mySimpleStack.slabList.nodeDictList)
		self.edgeTable2.populate(self.mySimpleStack.slabList.edgeDictList)

		# this is populated after each search (We do not have a local copy?)
		#self.editTable2.populate(self.mySimpleStack.slabList.edgeDictList)

	def keyPressEvent(self, event):
		print('=== bStackWidget.keyPressEvent() event.key():', event.key())

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		isControl = modifiers == QtCore.Qt.ControlModifier

		'''
		if isControl and event.key() in [QtCore.Qt.Key_L]:
			self.mySimpleStack.slabList.loadVesselucida_xml()
		'''

		#elif event.key() == QtCore.Qt.Key_BraceLeft: # '['

		# pyqtgraph widget uses 't' to show/hide tracing
		'''
		if event.text() == 't':
			self.options['Panels']['showToolbar'] = not self.options['Panels']['showToolbar']
			self.updateDisplayedWidgets()
		'''

		if event.text() == '[':
			self.options['Panels']['showLeftToolbar'] = not self.options['Panels']['showLeftToolbar']
			self.updateDisplayedWidgets()

		elif event.key() in [QtCore.Qt.Key_L]:
			self.options['Panels']['showLineProfile'] = not self.options['Panels']['showLineProfile']
			self.updateDisplayedWidgets()

		elif event.key() in [QtCore.Qt.Key_C]:
			self.options['Panels']['showContrast'] = not self.options['Panels']['showContrast']
			self.updateDisplayedWidgets()

		elif event.key() in [QtCore.Qt.Key_H]:
			self.printHelp()

		elif event.key() in [QtCore.Qt.Key_B]:
			print('set selected edge to bad ... need to implement this')
			'''
			selectedEdge = self.myStackView.selectedEdge()
			self.mySimpleStack.setAnnotation('toggle bad edge', selectedEdge)
			# force refresh of table, I need to use model/view/controller !!!!
			self.annotationTable._refreshRow(selectedEdge)
			'''

		elif event.key() in [QtCore.Qt.Key_Q]:
			# quit search
			if self.mySearchAnnotation is not None:
				self.mySearchAnnotation.continueSearch = False

		elif event.text() == 'i':
			self.mySimpleStack.print()

		else:
			#print('bStackWidget.keyPressEvent() not handled', event.text())
			event.setAccepted(False)

	def printHelp(self):
		print('=============================================================')
		print('bStackWidget help')
		print('==============================================================')
		print(' Navigation')
		print('   mouse wheel: scroll through images')
		print('   command + mouse wheel: zoom in/out (follows mouse position)')
		print('   +/-: zoom in/out (follows mouse position)')
		print('   click + drag: pan')
		print(' Show/Hide interface')
		print('   t: show/hide tracing')
		print('   [: show/hide left toolbar')
		print('   c: show/hide contrast bar')
		print('   l: show/hide line profile bar')
		print('   f: show/hide feedback bar')
		print('   esc: cancel node and edge selection (cyan)')
		print(' Stacks To Display')
		print('   1: Channel 1 - Raw Data')
		print('   2: Channel 2 - Raw Data')
		print('   3: Channel 3 - Raw Data')
		#print('   9: Skeleton mask - DeepVess')
		print('   0: Segmentation mask - Vesselucida/DeepVess')
		print(' Sliding Z-Projection')
		print('   z: toggle sliding z-projection on/off, will apply to all "Stacks To Display"')
		print(' ' )

	def optionsVersion(self):
		return 1.4

	def options_defaults(self):
		print('bStackWidget.options_defaults()')

		self.options = OrderedDict()

		"""
		Possible values are: Accent, Accent_r, Blues, Blues_r, BrBG, BrBG_r, BuGn, BuGn_r, BuPu, BuPu_r, CMRmap,
		CMRmap_r, Dark2, Dark2_r, GnBu, GnBu_r, Greens, Greens_r, Greys, Greys_r, OrRd, OrRd_r, Oranges,
		Oranges_r, PRGn, PRGn_r, Paired, Paired_r, Pastel1, Pastel1_r, Pastel2, Pastel2_r, PiYG, PiYG_r,
		PuBu, PuBuGn, PuBuGn_r, PuBu_r, PuOr, PuOr_r, PuRd, PuRd_r, Purples, Purples_r, RdBu, RdBu_r,
		RdGy, RdGy_r, RdPu, RdPu_r, RdYlBu, RdYlBu_r, RdYlGn, RdYlGn_r, Reds, Reds_r, Set1, Set1_r,
		Set2, Set2_r, Set3, Set3_r, Spectral, Spectral_r, Wistia, Wistia_r, YlGn, YlGnBu, YlGnBu_r,
		YlGn_r, YlOrBr, YlOrBr_r, YlOrRd, YlOrRd_r, afmhot, afmhot_r, autumn, autumn_r, binary, binary_r,
		bone, bone_r, brg, brg_r, bwr, bwr_r, cividis, cividis_r, cool, cool_r, coolwarm, coolwarm_r,
		copper, copper_r, cubehelix, cubehelix_r, flag, flag_r, gist_earth, gist_earth_r, gist_gray,
		gist_gray_r, gist_heat, gist_heat_r, gist_ncar, gist_ncar_r, gist_rainbow, gist_rainbow_r,
		gist_stern, gist_stern_r, gist_yarg, gist_yarg_r, gnuplot, gnuplot2, gnuplot2_r, gnuplot_r,
		gray, gray_r, hot, hot_r, hsv, hsv_r, inferno, inferno_r, jet, jet_r, magma, magma_r, nipy_spectral,
		nipy_spectral_r, ocean, ocean_r, pink, pink_r, plasma, plasma_r, prism, prism_r, rainbow, rainbow_r,
		seismic, seismic_r, spring, spring_r, summer, summer_r, tab10, tab10_r, tab20, tab20_r, tab20b,
		tab20b_r, tab20c, tab20c_r, terrain, terrain_r, twilight, twilight_r, twilight_shifted,
		twilight_shifted_r, viridis, viridis_r, winter, winter_r
		"""

		self.options['Tracing'] = OrderedDict()
		self.options['Tracing'] = OrderedDict({
			'allowEdit': True,
			'nodePenSize': 15, #**2,
			'nodeColor': 'r',
			'nodeSelectionPenSize': 5, #**2, # make this smaller than nodePenSize (should always be on top) ????
			'nodeSelectionColor': 'y',
			'nodeSelectionFlashPenSize': 15, #**2,
			'nodeSelectionFlashColor': 'm',
			'showTracingAboveSlices': 5,
			'showTracingBelowSlices': 5,
			'tracingPenWidth': 5, # lines between slabs
			'tracingPenSize': 10, # slabs
			'tracingColor': 'c',
			'tracingSelectionPenSize': 2,
			'tracingSelectionColor': 'y',
			'tracingSelectionFlashPenSize': 15,
			'tracingSelectionFlashColor': 'm',
			'lineProfileLineSize': 2,
			'lineProfileMarkerSize': 3,
			'lineProfileColor': 'm',
			'deadEndPenSize': 5,
			'deadEndColor': 'b',
			})

		# hide and show various interface widgets
		self.options['Panels'] = OrderedDict({
			#'showAnnotations': False,
			'showToolbar': True,
			'showLeftToolbar': False,
			'showNodeList': False,
			'showEdgeList': False,
			'showSearch': False,
			'showAnnotations': False,
			'showContrast': False,
			#'showFeedback': True,
			'showStatus': True,
			'showLineProfile': False,
			})

		self.options['Stack'] = OrderedDict()
		self.options['Stack'] = OrderedDict({
			'colorLut': 'gray',
			'upSlidingZSlices': 2,
			'downSlidingZSlices': 2,
			})

		# window position and size
		self.options['Window'] = OrderedDict()
		self.options['Window'] = OrderedDict({
			'width': 500,
			'height': 500,
			'left': 5,
			'top': 5,
			})

		self.options['Warnings'] = OrderedDict()
		self.options['Warnings'] = OrderedDict({
			'warnOnNewNode': True,
			'warnOnNewEdge': True,
			'warnOnNewSlab': True,
			#
			'warnOnDeleteNode': True,
			'warnOnDeleteEdge': True,
			'warnOnDeleteSlab': True,
		})

		#self.options['Code'] = OrderedDict()
		self.options['Code'] = OrderedDict({
			'optionsVersion': self.optionsVersion(),
			'_verboseSlots': False
		})

		# this is hard coded in bEvent class
		'''
		# debug
		self.options['Debug'] = OrderedDict({
			'verboseSlots': True,
		})
		'''

	def optionsSave(self):
		optionsFilePath = self.optionsFile()
		print('optionsSave()', optionsFilePath)
		with open(optionsFilePath, 'w') as f:
			json.dump(self.options, f, indent=4)

	def optionsLoad(self):
		optionsFilePath = self.optionsFile()
		if os.path.exists(optionsFilePath):
			print('  bStackWidget.optionsLoad()', optionsFilePath)
			with open(optionsFilePath) as f:
				self.options = json.load(f)
			#print(self.options)

			optionsKeys = self.options.keys()
			if not 'Code' in optionsKeys:
				print(f"  bStackWidget.optionsLoad() found old file with no 'Options' key")
				self.options = None
				return False
			elif self.options['Code']['optionsVersion'] < self.optionsVersion():
				print(f"  bStackWidget.optionsLoad() found old file with {self.options['Code']['optionsVersion']} < {self.optionsVersion()}")
				self.options = None
				return False
			return True
		else:
			self.options = None
			return False

	def optionsFile(self):
		myPath = os.path.dirname(os.path.abspath(__file__))
		optionsFilePath = os.path.join(myPath,'options.json')
		return optionsFilePath

	def showRightClickMenu(self,pos):
		"""
		Show a right click menu to perform action including toggle interface on/off

		todo: building and then responding to menu is too hard coded here, should generalize???
		"""
		menu = QtWidgets.QMenu()
		#self.menu = QtWidgets.QMenu()

		numChannels = self.mySimpleStack.numChannels # number of channels in stack
		maxNumChannels = self.mySimpleStack.maxNumChannels
		#actions = ['Channel 1', 'Channel 2', 'Channel 3', 'RGB', 'Channel 1 Mask', 'Channel 2 Mask', 'Channel 3 Mask']
		actionsList = []
		isEnabledList = []
		isCheckedList = []
		for i in range(numChannels):
			chanNumber = i + 1
			actionsList.append(f'Channel {chanNumber}')
			isEnabled = self.mySimpleStack.hasChannelLoaded(chanNumber)
			isEnabledList.append(isEnabled)
			isChecked = self.getStackView().displayStateDict['displayThisStack'] == i+1
			isCheckedList.append(isChecked)
		for i in range(numChannels):
			chanNumber = i + 1
			actionsList.append(f'Channel {chanNumber} Mask')
			actualChanNumber = maxNumChannels + i
			isEnabled = self.mySimpleStack.hasChannelLoaded(actualChanNumber)
			isEnabledList.append(isEnabled)
			isChecked = self.getStackView().displayStateDict['displayThisStack'] == i+1+maxNumChannels
			isCheckedList.append(isChecked)
		for i in range(numChannels):
			chanNumber = i + 1
			actionsList.append(f'Channel {chanNumber} Skel')
			actualChanNumber = 2 * maxNumChannels + i
			isEnabled = self.mySimpleStack.hasChannelLoaded(actualChanNumber)
			isEnabledList.append(isEnabled)
			isChecked = self.getStackView().displayStateDict['displayThisStack'] == i+1+maxNumChannels
			isCheckedList.append(isChecked)
		if numChannels>1:
			actionsList.append('RGB')
			isEnabledList.append(True)
			isChecked = self.getStackView().displayStateDict['displayThisStack'] == 'rgb' # lower case !!!
			isCheckedList.append(isChecked)

		for i, actionStr in enumerate(actionsList):
			# make an action
			currentAction = QtWidgets.QAction(actionStr, self, checkable=True)
			# decide if it is checked
			isEnabled = isEnabledList[i]
			isChecked = self.getStackView().displayStateDict['displayThisStack'] == i+1
			isChecked = isCheckedList[i]

			currentAction.setEnabled(isEnabled)
			currentAction.setChecked(isChecked)
			# add to menu
			menuAction = menu.addAction(currentAction)

		menu.addSeparator()

		#
		# view
		actions = ['Image', 'Sliding Z', 'Nodes', 'Edges']
		for actionStr in actions:
			# make an action
			currentAction = QtWidgets.QAction(actionStr, self, checkable=True)
			# decide if it is checked
			isChecked = False
			if actionStr == 'Image':
				isChecked = self.getStackView().displayStateDict['showImage']
			elif actionStr == 'Sliding Z':
				isChecked = self.getStackView().displayStateDict['displaySlidingZ']
			elif actionStr == 'Nodes':
				isChecked = self.getStackView().displayStateDict['showNodes']
			elif actionStr == 'Edges':
				isChecked = self.getStackView().displayStateDict['showEdges']
			currentAction.setChecked(isChecked)
			currentAction.triggered.connect(self.actionHandler)
			# add to menu
			#menuAction = self.menu.addAction(currentAction)
			menuAction = menu.addAction(currentAction)

		menu.addSeparator()

		#
		# panels

		annotationsAction = QtWidgets.QAction('Left Toolbar', self, checkable=True)
		annotationsAction.setChecked(self.options['Panels']['showLeftToolbar'])
		#annotationsAction.setShortcuts('[')
		tmpMenuAction = menu.addAction(annotationsAction)

		# nodes
		annotationsAction = QtWidgets.QAction('Node List', self, checkable=True)
		annotationsAction.setChecked(self.options['Panels']['showNodeList'])
		tmpMenuAction = menu.addAction(annotationsAction)
		# edges
		annotationsAction = QtWidgets.QAction('Edge List', self, checkable=True)
		annotationsAction.setChecked(self.options['Panels']['showEdgeList'])
		tmpMenuAction = menu.addAction(annotationsAction)
		# search
		annotationsAction = QtWidgets.QAction('Search List', self, checkable=True)
		annotationsAction.setChecked(self.options['Panels']['showSearch'])
		tmpMenuAction = menu.addAction(annotationsAction)
		# annotations
		annotationsAction = QtWidgets.QAction('Annotation List', self, checkable=True)
		annotationsAction.setChecked(self.options['Panels']['showAnnotations'])
		tmpMenuAction = menu.addAction(annotationsAction)

		# contrast
		contrastAction = QtWidgets.QAction('Contrast Panel', self, checkable=True)
		contrastAction.setChecked(self.options['Panels']['showContrast'])
		tmpMenuAction = menu.addAction(contrastAction)

		# status toolbar
		annotationsAction = QtWidgets.QAction('Status Panel', self, checkable=True)
		annotationsAction.setChecked(self.options['Panels']['showStatus'])
		tmpMenuAction = menu.addAction(annotationsAction)

		# line profile toolbar
		annotationsAction = QtWidgets.QAction('Line Profile Panel', self, checkable=True)
		annotationsAction.setChecked(self.options['Panels']['showLineProfile'])
		tmpMenuAction = menu.addAction(annotationsAction)

		# napari
		menu.addSeparator()
		napariAction = QtWidgets.QAction('Napari', self, checkable=False)
		tmpMenuAction = menu.addAction(napariAction)

		# options
		menu.addSeparator()
		optionsAction = QtWidgets.QAction('Options', self, checkable=False)
		tmpMenuAction = menu.addAction(optionsAction)

		# options
		menu.addSeparator()
		refeshAction = QtWidgets.QAction('Refresh', self, checkable=False)
		tmpMenuAction = menu.addAction(refeshAction)

		#
		# edits
		self.addEditMenu(menu)

		#
		# get the action selection from user

		print('=== bStackWidget.showRightClickMenu()')
		# was this
		userAction = menu.exec_(self.mapToGlobal(pos))
		# now this
		'''
		self.menu.move(self.mapToGlobal(pos))
		self.menu.show()
		'''

		#userAction = None
		if userAction is None:
			# abort when no menu selected
			return
		userActionStr = userAction.text()
		print('    showRightClickMenu() userActionStr:', userActionStr)
		signalName = 'bSignal ' + userActionStr
		userSelectedMenu = True

		doStackRefresh = False

		# image
		maxNumChannels = self.mySimpleStack.maxNumChannels
		if userActionStr == 'Channel 1':
			#self.getStackView().displayStateDict['displayThisStack'] = 1
			#doStackRefresh = True
			self.getStackView().displayStateChange('displayThisStack', value=1)
		elif userActionStr == 'Channel 2':
			#self.getStackView().displayStateDict['displayThisStack'] = 2
			#doStackRefresh = True
			self.getStackView().displayStateChange('displayThisStack', value=2)
		elif userActionStr == 'Channel 3':
			#self.getStackView().displayStateDict['displayThisStack'] = 3
			#doStackRefresh = True
			self.getStackView().displayStateChange('displayThisStack', value=3)

		elif userActionStr == 'Channel 1 Mask':
			#self.getStackView().displayStateDict['displayThisStack'] = 4
			#doStackRefresh = True
			self.getStackView().displayStateChange('displayThisStack', value=4)
		elif userActionStr == 'Channel 2 Mask':
			#self.getStackView().displayStateDict['displayThisStack'] = 4+1
			#doStackRefresh = True
			self.getStackView().displayStateChange('displayThisStack', value=4+1)
		elif userActionStr == 'Channel 3 Mask':
			#self.getStackView().displayStateDict['displayThisStack'] = 4+2
			#doStackRefresh = True
			self.getStackView().displayStateChange('displayThisStack', value=4+2)

		elif userActionStr == 'Channel 1 Skel':
			#self.getStackView().displayStateDict['displayThisStack'] = 7
			#doStackRefresh = True
			self.getStackView().displayStateChange('displayThisStack', value=7)
		elif userActionStr == 'Channel 2 Skel':
			#self.getStackView().displayStateDict['displayThisStack'] = 7+1
			#doStackRefresh = True
			self.getStackView().displayStateChange('displayThisStack', value=7+1)
		elif userActionStr == 'Channel 3 Skel':
			#self.getStackView().displayStateDict['displayThisStack'] = 7+2
			#doStackRefresh = True
			self.getStackView().displayStateChange('displayThisStack', value=7+2)

		elif userActionStr == 'RGB':
			#self.getStackView().displayStateDict['displayThisStack'] = 'rgb'
			#doStackRefresh = True
			self.getStackView().displayStateChange('displayThisStack', value='rgb')

		#
		# view of tracing
		elif userActionStr == 'Image':
			self.getStackView().displayStateChange('showImage', toggle=True)
			doStackRefresh = True
			#self.displayStateDict['showImage'] = not self.displayStateDict['showImage']
		elif userActionStr == 'Sliding Z':
			#self.getStackView().displayStateDict['displaySlidingZ'] = not self.getStackView().displayStateDict['displaySlidingZ']
			#doStackRefresh = True
			self.getStackView().displayStateChange('displaySlidingZ', toggle=True)
		elif userActionStr == 'Nodes':
			#optionsChange('Panels', 'showLeftToolbar', toggle=True, doEmit=True)
			self.getStackView().displayStateDict['showNodes'] = not self.getStackView().displayStateDict['showNodes']
			doStackRefresh = True
		elif userActionStr == 'Edges':
			self.getStackView().displayStateDict['showEdges'] = not self.getStackView().displayStateDict['showEdges']
			doStackRefresh = True

		#
		# toolbars
		elif userActionStr == 'Left Toolbar':
			self.optionsChange('Panels', 'showLeftToolbar', toggle=True, doEmit=True)
			#self.options['Panels']['showLeftToolbar'] = not self.options['Panels']['showLeftToolbar']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Contrast Panel':
			self.optionsChange('Panels', 'showContrast', toggle=True, doEmit=True)
			#self.options['Panels']['showContrast'] = not self.options['Panels']['showContrast']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Node List':
			self.optionsChange('Panels', 'showNodeList', toggle=True, doEmit=True)
			#self.options['Panels']['showNodeList'] = not self.options['Panels']['showNodeList']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Edge List':
			self.optionsChange('Panels', 'showEdgeList', toggle=True, doEmit=True)
			#self.options['Panels']['showEdgeList'] = not self.options['Panels']['showEdgeList']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Search List':
			self.optionsChange('Panels', 'showSearch', toggle=True, doEmit=True)
			#self.options['Panels']['showSearch'] = not self.options['Panels']['showSearch']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Annotation List':
			self.optionsChange('Panels', 'showAnnotations', toggle=True, doEmit=True)
			#self.options['Panels']['showSearch'] = not self.options['Panels']['showSearch']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Status Panel':
			self.optionsChange('Panels', 'showStatus', toggle=True, doEmit=True)
			#self.options['Panels']['showStatus'] = not self.options['Panels']['showStatus']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Line Profile Panel':
			self.optionsChange('Panels', 'showLineProfile', toggle=True, doEmit=True)
			#self.options['Panels']['showLineProfile'] = not self.options['Panels']['showLineProfile']
			#self.mainWindow.updateDisplayedWidgets()

		# other
		elif userActionStr == 'Options':
			optionsDialog = bimpy.interface.bOptionsDialog(self, self)
		elif userActionStr == 'Napari':
			self.openNapari()
		elif userActionStr == 'Refresh':
			self.getStackView()._preComputeAllMasks()

		else:
			print('    showRightClickMenu() -->> no action taken for userActionStr:', userActionStr)
			userSelectedMenu = False

		# emit a signal
		# todo: this is emitting when self.getStackView().displayStateDict is not changing, e.g. for user action 'Contrast' and 'Annotations'
		'''
		if userSelectedMenu:
			self.setSlice() # update
			self.displayStateChangeSignal.emit(signalName, self.getStackView().displayStateDict)
		'''

		if doStackRefresh:
			self.getStackView().setSlice()

		#return False
		#print('right click menu return')
		return

	def actionHandler(self):
		sender = self.sender()
		title = sender.text()
		print('bStackView.actionHandler() titel:', title, '    ....    todo: put code in this function to handle right-click menu selection')
		#print('    title:', title)

	def addEditMenu(self, menu):
		editMenus = ['Delete Node', 'Delete Edge', 'Delete Slab', '---', 'Slab To Node']

		menu.addSeparator()
		for menuStr in editMenus:
			if menuStr == '---':
				menu.addSeparator()
			else:
				isEnabled = False
				if menuStr == 'Delete Node':
					isEnabled = self.getStackView().selectedNode() is not None
				if menuStr == 'Delete Edge':
					isEnabled = self.getStackView().selectedEdge() is not None
				elif menuStr in ['Delete Slab', 'Slab To Node']:
					isEnabled = self.getStackView().selectedSlab() is not None # if we have a node selection

				myAction = QtWidgets.QAction(menuStr, self)
				myAction.setEnabled(isEnabled)
				menu.addAction(myAction)

################################################################################
class myStackSlider(QtWidgets.QSlider):
	"""
	Assuming stack is not going to change slices
	"""

	# signal/emit
	#updateSliceSignal = QtCore.pyqtSignal(str, object) # object can be a dict
	updateSliceSignal = QtCore.Signal(str, object) # object can be a dict

	def __init__(self, numSlices):
		super(myStackSlider, self).__init__(QtCore.Qt.Vertical)
		self.setMaximum(numSlices-1)
		self.setMinimum(0)
		#self.setMaximum(0)
		#self.setMinimum(numSlices-1)
		self.setInvertedAppearance(True) # so it goes from top:0 to bottom:numImages
		self.setInvertedControls(True)
		if numSlices < 2:
			self.setDisabled(True)

		#
		# slider signal
		# valueChanged()	Emitted when the slider's value has changed. The tracking() determines whether this signal is emitted during user interaction.
		# sliderPressed()	Emitted when the user starts to drag the slider.
		# sliderMoved()	Emitted when the user drags the slider.
		# sliderReleased()	Emitted when the user releases the slider.

		self.sliderMoved.connect(self.updateSlice_Signal)
		self.valueChanged.connect(self.updateSlice_Signal) # abb 20200829
		#self.valueChanged.connect(self.sliceSliderValueChanged)

	def slot_UpdateSlice2(self, myEvent):
		#print('myStackSlider.slot_UpdateSlice() signalName:', signalName, 'signalValue:', signalValue)
		eventType = myEvent.eventType
		if eventType in ['select node', 'select edge']:
			sliceIdx = myEvent.sliceIdx
			self.setValue(sliceIdx)

	def slot_UpdateSlice(self, signalName, signalValue):
		#print('myStackSlider.slot_UpdateSlice() signalName:', signalName, 'signalValue:', signalValue)
		self.setValue(signalValue)

	def updateSlice_Signal(self):
		self.updateSliceSignal.emit('set slice', self.value())

'''
# see second answer: https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
class myNumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
'''

################################################################################
#class bStackView(QtWidgets.QWidget):

if __name__ == '__main__':
	import sys
	#from bimpy.interface import bStackWidget

	#path = '/Users/cudmore/box/DeepVess/data/invivo/20190613__0028.tif'
	if len(sys.argv) == 2:
		path = sys.argv[1]
	else:
		path = '/Users/cudmore/box/DeepVess/data/immuno-stack/mytest.tif'
		#path = '/Users/cudmore/box/DeepVess/data/invivo/20190613__0028.tif'

		# works well
		path = '/Users/cudmore/box/data/bImpy-Data/deepvess/mytest.tif'
		path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/20191017__0001.tif'

		# for this one, write code to revover tracing versus image scale
		# x/y=0.3107, z=0.5

		#path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/high_mag_top_of_node/tracing_20191217.tif'

	print('!!! bStackWidget __main__ is creating QApplication')
	app = QtWidgets.QApplication(sys.argv)

	sw = bStackWidget(mainWindow=app, parent=None, path=path)
	sw.show()
	sw.myStackView.setSlice(0)

	'''
	sw2 = bStackWidget(mainWindow=app, parent=None, path=path)
	sw2.show()
	sw2.setSlice(0)
	'''

	#print('app.topLevelWidgets():', app.topLevelWidgets())

	print('bStackWidget __main__ done')
	sys.exit(app.exec_())
