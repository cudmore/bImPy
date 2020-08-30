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

import bimpy

################################################################################
#class bStackWidget(QtWidgets.QMainWindow):
class bStackWidget(QtWidgets.QWidget):
	"""
	A widget to display a stack. This includes a bStackView and a bAnnotationTable.
	"""

	optionsStateChange = QtCore.Signal(str, str, bool) # object can be a dict

	def __init__(self, mainWindow=None, parent=None, path=''):
		super(bStackWidget, self).__init__()

		self.mainWindow = mainWindow

		self.options = None
		if not self.optionsLoad():
			self.options_defaults()

		self.path = path

		basename = os.path.basename(self.path)
		self.setWindowTitle(basename)

		self.setObjectName('bStackWidget0')
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

		# holds (left toolbar, vertical), vertical has (contrast/image/feedback)
		self.myHBoxLayout = QtWidgets.QHBoxLayout(self)
		#self.myHBoxLayout.setAlignment(QtCore.Qt.AlignTop)

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
		#searchGroupBox = QtWidgets.QGroupBox('Search')
		#searchGroupBox.setStyleSheet(myStyleSheet)
		self.editTable2 = bimpy.interface.bTableWidget2('node search', self.mySimpleStack.slabList.editDictList, parent=self)
		#searchGroupBox.setLayout(self.editTable2)
		self.myHBoxLayout.addWidget(self.editTable2, stretch=3)
		#self.myHBoxLayout.addWidget(searchGroupBox, stretch=3)
		#
		#
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
		self.editTable2.selectRowSignal.connect(self.statusToolbarWidget.slot_select)

		self.nodeTable2.selectRowSignal.connect(self.mySliceSlider.slot_UpdateSlice2)
		self.edgeTable2.selectRowSignal.connect(self.mySliceSlider.slot_UpdateSlice2)
		self.edgeTable2.selectRowSignal.connect(self.mySliceSlider.slot_UpdateSlice2)
		self.nodeTable2.selectRowSignal.connect(self.myContrastWidget.slot_UpdateSlice2)
		self.edgeTable2.selectRowSignal.connect(self.myContrastWidget.slot_UpdateSlice2)
		self.editTable2.selectRowSignal.connect(self.myContrastWidget.slot_UpdateSlice2)
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
		self.editTable2.selectRowSignal.connect(self.myStackView2.slot_selectNode)
		self.editTable2.selectRowSignal.connect(self.myStackView2.slot_selectEdge)

		self.myStackView2.setSliceSignal.connect(self.mySliceSlider.slot_UpdateSlice)
		self.myStackView2.setSliceSignal.connect(self.statusToolbarWidget.slot_StateChange)
		self.myStackView2.selectNodeSignal.connect(self.nodeTable2.slot_select)
		self.myStackView2.selectNodeSignal.connect(self.statusToolbarWidget.slot_select)
		self.myStackView2.selectEdgeSignal.connect(self.statusToolbarWidget.slot_select)
		self.myStackView2.selectEdgeSignal.connect(self.nodeTable2.slot_select)
		self.myStackView2.selectEdgeSignal.connect(self.edgeTable2.slot_select)

		self.myStackView2.tracingEditSignal.connect(self.nodeTable2.slot_updateTracing)
		self.myStackView2.tracingEditSignal.connect(self.edgeTable2.slot_updateTracing)
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
			self.editTable2.show()
		else:
			self.editTable2.hide()

		# contrast bar
		if self.options['Panels']['showContrast']:
			self.myContrastWidget.show()
			self.myContrastWidget.doUpdates = True
		else:
			self.myContrastWidget.hide()
			self.myContrastWidget.doUpdates = False

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
			self.lineProfileWidget.update(value)

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
			self.mySearchAnnotation.searchFinishedSignal.connect(self.editTable2.slot_SearchFinished)
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
			self.mySearchAnnotation.searchFinishedSignal.connect(self.editTable2.slot_SearchFinished)
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
		self.mySearchAnnotation.searchFinishedSignal.connect(self.editTable2.slot_SearchFinished)
		self.mySearchAnnotation.searchNewHitSignal.connect(self.editTable2.slot_newSearchHit)
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
		#print('=== bStackWidget.keyPressEvent() event.key():', event.key())
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		isControl = modifiers == QtCore.Qt.ControlModifier

		'''
		if isControl and event.key() in [QtCore.Qt.Key_L]:
			self.mySimpleStack.slabList.loadVesselucida_xml()
		'''

		#elif event.key() == QtCore.Qt.Key_BraceLeft: # '['
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
		return 1.0
	
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

		#self.options['Code'] = OrderedDict()
		self.options['Code'] = OrderedDict({
			'optionsVersion': self.optionsVersion(),
			'_verboseSlots': False
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

		self.options['Tracing'] = OrderedDict()
		self.options['Tracing'] = OrderedDict({
			'allowEdit': True,
			'nodePenSize': 5, #**2,
			'nodeColor': 'r',
			'nodeSelectionPenSize': 5, #**2, # make this smaller than nodePenSize (should always be on top) ????
			'nodeSelectionColor': 'y',
			'nodeSelectionFlashPenSize': 15, #**2,
			'nodeSelectionFlashColor': 'm',
			'showTracingAboveSlices': 5,
			'showTracingBelowSlices': 5,
			'tracingPenSize': 2,
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
			'showLeftToolbar': False,
			'showNodeList': False,
			'showEdgeList': False,
			'showSearch': False,
			'showContrast': False,
			#'showFeedback': True,
			'showStatus': True,
			'showLineProfile': False,
			})

		self.options['Stack'] = OrderedDict()
		self.options['Stack'] = OrderedDict({
			'colorLut': 'gray',
			'upSlidingZSlices': 5,
			'downSlidingZSlices': 5,
			})

		# window position and size
		self.options['Window'] = OrderedDict()
		self.options['Window'] = OrderedDict({
			'width': 500,
			'height': 500,
			'left': 5,
			'top': 5,
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
			print('bStackWidget.optionsLoad()', optionsFilePath)
			with open(optionsFilePath) as f:
				self.options = json.load(f)
			#print(self.options)
			
			optionsKeys = self.options.keys()
			if not 'optionsVersion' in optionsKeys:
				print('bStackWidget.optionsLoad() did not find key: optionsVersion')
				self.options = None
				return False
			elif self.options['optionsVersion'] < self.optionsVersion():
				print(f"bStackWidget.optionsLoad() found old file with {self.options['optionsVersion']} < {self.optionsVersion()}")
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

		#self.displayThisStack
		numChannels = self.mySimpleStack.numChannels
		actions = ['Channel 1', 'Channel 2', 'Channel 3', 'RGB']
		for actionStr in actions:
			# make an action
			currentAction = QtWidgets.QAction(actionStr, self, checkable=True)
			# decide if it is checked
			isEnabled = False
			isChecked = False
			if actionStr == 'Channel 1':
				isEnabled = numChannels > 0
				isChecked = self.getStackView().displayStateDict['displayThisStack'] == 'ch1'
			elif actionStr == 'Channel 2':
				isEnabled = numChannels > 1
				isChecked = self.getStackView().displayStateDict['displayThisStack'] == 'ch2'
			elif actionStr == 'Channel 3':
				isEnabled = numChannels > 2
				isChecked = self.getStackView().displayStateDict['displayThisStack'] == 'ch3'
			elif actionStr == 'RGB':
				isEnabled = numChannels > 1
				isChecked = self.getStackView().displayStateDict['displayThisStack'] == 'rgb'
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

		# image
		if userActionStr == 'Channel 1':
			self.getStackView().displayStateDict['displayThisStack'] = 'ch1'
		elif userActionStr == 'Channel 2':
			self.getStackView().displayStateDict['displayThisStack'] = 'ch2'
		elif userActionStr == 'Channel 3':
			self.getStackView().displayStateDict['displayThisStack'] = 'ch3'
		elif userActionStr == 'RGB':
			self.getStackView().displayStateDict['displayThisStack'] = 'rgb'

		#
		# view of tracing
		elif userActionStr == 'Image':
			self.getStackView().displayStateChange('showImage', toggle=True)
			#self.displayStateDict['showImage'] = not self.displayStateDict['showImage']
		elif userActionStr == 'Sliding Z':
			self.getStackView().displayStateDict['displaySlidingZ'] = not self.getStackView().displayStateDict['displaySlidingZ']
		elif userActionStr == 'Nodes':
			#optionsChange('Panels', 'showLeftToolbar', toggle=True, doEmit=True)
			self.getStackView().displayStateDict['showNodes'] = not self.getStackView().displayStateDict['showNodes']
		elif userActionStr == 'Edges':
			self.getStackView().displayStateDict['showEdges'] = not self.getStackView().displayStateDict['showEdges']

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
class bStackView(QtWidgets.QGraphicsView):

	'''
	displayStateChange = QtCore.pyqtSignal(str, object) # object can be a dict
	setSliceSignal = QtCore.pyqtSignal(str, object)
	selectNodeSignal = QtCore.pyqtSignal(object)
	selectEdgeSignal = QtCore.pyqtSignal(object)
	selectSlabSignal = QtCore.pyqtSignal(object)
	tracingEditSignal = QtCore.pyqtSignal(object) # on new/delete/edit of node, edge, slab
	'''

	displayStateChangeSignal = QtCore.Signal(str, object) # object can be a dict
	setSliceSignal = QtCore.Signal(str, object)
	selectNodeSignal = QtCore.Signal(object)
	selectEdgeSignal = QtCore.Signal(object)
	#selectSlabSignal = QtCore.Signal(object)
	tracingEditSignal = QtCore.Signal(object) # on new/delete/edit of node, edge, slab

	def __init__(self, simpleStack, mainWindow=None, parent=None):
		super(bStackView, self).__init__(parent)

		self.setObjectName('bStackView')
		self.setStyleSheet("""
			#bStackView {
				background-color: #222;
			}
		""")

		#self.path = path
		#self.options_defaults()

		#self.napariViewer = None

		self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

		'''
		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.showRightClickMenu)
		'''

		#self.onpick_alreadypicked = False
		self.onpick_lastSeconds = time.time()
		self.onpick_madeNewEdge = False
		self.keyIsDown = None

		self.mySimpleStack = simpleStack #bSimpleStack(path)
		self.mainWindow = mainWindow

		'''
		self.mySelectedNode = None # node index of selected node
		self.mySelectedEdge = None # edge index of selected edge
		self.mySelectedSlab = None # slab index of selected slab
		'''

		#self.displayThisStack = 'ch1'

		self.currentSlice = 0
		self.minContrast = 0
		#self.maxContrast = 2 ** self.mySimpleStack.getHeaderVal('bitDepth')
		print('   bStackView.__init__ got stack bit depth of:', self.mySimpleStack.bitDepth, 'type:', type(self.mySimpleStack.bitDepth))
		self.maxContrast = 2 ** self.mySimpleStack.bitDepth

		self.imgplot = None

		# for click and drag
		self.clickPos = None

		self.displayStateDict = {
			'displayThisStack': 'ch1',
			'displaySlidingZ': False,
			'showImage': True,
			#'showTracing': True,
			'triState': 0, # 0: all, 1: just nodes, 2: just edges, 3: none
			'showNodes': True,
			'showEdges': True,
			'showDeadEnds': True, # not used ???

			'mySelectedNode': None,
			'mySelectedEdge': None,
			'mySelectedEdgeList': [], # abb aics, for ctrl+click multi edge selection
			'mySelectedSlab': None,
		}

		# abb removed 20200307
		self._preComputeAllMasks(loadFromFile=True)

		#
		scene = QtWidgets.QGraphicsScene(self)
		# this works
		#scene.setBackgroundBrush(QtCore.Qt.blue);

		# visually turn off scroll bars
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		#self.horizontalScrollBar().disconnect()
		#self.verticalScrollBar().disconnect()

		#self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

		# was this
		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		# now this
		#self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
		#self.setResizeAnchor(QtGui.QGraphicsView.NoAnchor)

		# this does nothing???
		#self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))

		self.setFrameShape(QtWidgets.QFrame.NoFrame)

		#todo: add interface to turn axes.axis ('on', 'off')
		# image
		#self.figure = Figure(figsize=(width, height), dpi=dpi)
		self.figure = Figure(figsize=(5,5)) # need size otherwise square image gets squished in y?
		self.canvas = backend_qt5agg.FigureCanvas(self.figure)
		#self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		#self.axes = self.figure.add_axes([0, 0, 1, 1], aspect=1) #remove white border
		self.axes = self.figure.add_axes([0, 0, 1, 1]) #remove white border
		#self.axes.set_aspect('equal')
		self.axes.axis('off') #turn off axis labels

		#self.myColorMap = matplotlib.colors.get_cmap('jet')
		#self.myColorMap = matplotlib.colors.Colormap('gray', N=256)
		#self.myColorMap = plt.cm.get_cmap()
		self.myColorMap = matplotlib.cm.get_cmap('gray')

		# OMG, this took many hours to find the right function, set the background of the figure !!!
		self.figure.set_facecolor("black")

		# slab/point list
		'''
		markersize = self.options['Tracing']['tracingPenSize'] #2**2
		markerColor = self.options['Tracing']['tracingColor'] #2**2
		self.mySlabPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, picker=True)
		'''

		# draw lines between slabs in each edge
		zorder = 1
		#self.myEdgePlot, = self.axes.plot([], [],'.c-', zorder=zorder, picker=5) # Returns a tuple of line objects, thus the comma
		colors = 'c'
		tracingPenSize = self.options['Tracing']['tracingPenSize']
		self.myEdgePlot, = self.axes.plot([], [],'.-',
			color=colors, markersize=tracingPenSize,
			zorder=zorder, picker=5) # Returns a tuple of line objects, thus the comma

		# nodes (put this after slab/point list to be on top, order matter)
		# this HAS TO BE declared first, so nodes receive onpick_mpl() first
		# also see self.onpick_alreadypicked to stop double selection (node then edge or edge then node)
		zorder = 2
		markersize = self.options['Tracing']['nodePenSize'] **2
		markerColor = self.options['Tracing']['nodeColor']
		self.myNodePlot = self.axes.scatter([], [],
			marker='o', color=markerColor, s=markersize, edgecolor='none', zorder=zorder, picker=True)
		#self.myNodePlot.set_clim(3, 5)


		# tracing/slabs that are dead end
		'''
		markersize = self.options['Tracing']['deadEndPenSize'] #2**2
		markerColor = self.options['Tracing']['deadEndColor'] #2**2
		self.myDeadEndPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, picker=None)
		'''

		zorder = 3

		# node selection
		markersize = self.options['Tracing']['nodeSelectionPenSize'] **2
		markerColor = self.options['Tracing']['nodeSelectionColor']
		self.myNodeSelectionPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, zorder=zorder, picker=None)

		# flash node selection
		zorder += 1
		markersize = self.options['Tracing']['nodeSelectionFlashPenSize'] **2
		markerColor = self.options['Tracing']['nodeSelectionFlashColor']
		self.myNodeSelectionFlash = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, zorder=zorder, picker=None)

		# edge selection
		zorder += 1
		markersize = self.options['Tracing']['tracingSelectionPenSize'] **2
		markerColor = self.options['Tracing']['tracingSelectionColor']
		self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, zorder=zorder, picker=None)

		# slab selection
		zorder += 1
		markersize = self.options['Tracing']['tracingSelectionPenSize'] **2
		markersize *= 2
		markerColor = self.options['Tracing']['tracingSelectionColor'] #2**2
		self.mySlabSelectionPlot = self.axes.scatter([], [], marker='x', color=markerColor, s=markersize, zorder=zorder, picker=None)

		# flash edge selection
		zorder += 1
		markersize = self.options['Tracing']['tracingSelectionFlashPenSize'] **2
		markerColor = self.options['Tracing']['tracingSelectionFlashColor'] #2**2
		self.myEdgeSelectionFlash = self.axes.scatter([], [], marker='o', color=markerColor, s=markersize, zorder=zorder, picker=None)

		# slab line (perpendicular to tracing to extract line intensity profile)
		zorder += 1
		linewidth = self.options['Tracing']['lineProfileLineSize']
		markersize = self.options['Tracing']['lineProfileMarkerSize']
		c = self.options['Tracing']['lineProfileColor']
		self.mySlabLinePlot, = self.axes.plot([], [], 'o-', color=c, zorder=zorder,
			linewidth=linewidth, markersize=markersize, picker=None) # Returns a tuple of line objects, thus the comma

		#self.canvas.mpl_connect('key_press_event', self.onkey)
		#self.canvas.mpl_connect('button_press_event', self.onclick)
		#self.canvas.mpl_connect('scroll_event', self.onscroll)
		self.canvas.mpl_connect('pick_event', self.onpick_mpl)
		self.canvas.mpl_connect('button_press_event', self.onclick_mpl)
		self.canvas.mpl_connect('motion_notify_event', self.onmove_mpl)

		scene.addWidget(self.canvas)

		self.setScene(scene)

		self.handleFitInView()

		self.displayStateChangeSignal.emit('num slices', self.mySimpleStack.numImages)

	def handleFitInView(self):
		# Auto scale a QGraphicsView
		# http://www.qtcentre.org/threads/42917-Auto-scale-a-QGraphicsView
		'''
		self.setTransform(QtGui.QTransform())
		'''
		self.ensureVisible ( self.scene().itemsBoundingRect() )
		self.fitInView( self.scene().itemsBoundingRect(), QtCore.Qt.KeepAspectRatio )

	def resizeEvent(self, event):
		#print('resizeEvent() itemsBoundingRect:', self.scene().itemsBoundingRect(), self.frameGeometry(), self.pos())

		# abb aics, removed
		#self.handleFitInView()
		pass

	#
	# get/set selections
	def selectedNode(self, nodeIdx=-1):
		if nodeIdx != -1:
			self.displayStateDict['mySelectedNode'] = nodeIdx
		return self.displayStateDict['mySelectedNode']

	def selectedEdge(self, edgeIdx=-1):
		if edgeIdx != -1:
			self.displayStateDict['mySelectedEdge'] = edgeIdx
		return self.displayStateDict['mySelectedEdge']

	# abb aics, first time using 'type hints'
	# since we are working with lists, need multiple functions?
	def selectedEdgeList_get(self, edgeIdx: int = -1):
		return self.displayStateDict['mySelectedEdgeList']

	def selectedEdgeList_append(self, edgeIdxList: list):
		if edgeIdxList == []:
			# clear
			self.displayStateDict['mySelectedEdgeList'] = []
		else:
			# append
			for edgeIdx in edgeIdxList:
				if not edgeIdx in self.displayStateDict['mySelectedEdgeList']:
					self.displayStateDict['mySelectedEdgeList'] += [edgeIdx]
		return self.displayStateDict['mySelectedEdgeList']

	def selectedSlab(self, slabIdx=-1):
		if slabIdx != -1:
			self.displayStateDict['mySelectedSlab'] = slabIdx
		return self.displayStateDict['mySelectedSlab']

	def cancelSelection(self, doEmit=True):
		self.selectNode(None)
		self.selectEdge(None)
		self.selectSlab(None)
		self.selectedEdgeList_append([])
		#
		if doEmit:
			myEvent = bimpy.interface.bEvent('select node', nodeIdx=None)
			self.selectNodeSignal.emit(myEvent)
			myEvent = bimpy.interface.bEvent('select edge', edgeIdx=None)
			self.selectEdgeSignal.emit(myEvent)

	@property
	def options(self):
		return self.mainWindow.options

	def showRightClickMenu(self,pos):
		"""
		Show a right click menu to perform action including toggle interface on/off

		todo: building and then responding to menu is too hard coded here, should generalize???
		"""
		menu = QtWidgets.QMenu()
		#self.menu = QtWidgets.QMenu()

		#self.displayThisStack
		numChannels = self.mySimpleStack.numChannels
		actions = ['Channel 1', 'Channel 2', 'Channel 3', 'RGB']
		for actionStr in actions:
			# make an action
			currentAction = QtWidgets.QAction(actionStr, self, checkable=True)
			# decide if it is checked
			isEnabled = False
			isChecked = False
			if actionStr == 'Channel 1':
				isEnabled = numChannels > 0
				isChecked = self.displayStateDict['displayThisStack'] == 'ch1'
			elif actionStr == 'Channel 2':
				isEnabled = numChannels > 1
				isChecked = self.displayStateDict['displayThisStack'] == 'ch2'
			elif actionStr == 'Channel 3':
				isEnabled = numChannels > 2
				isChecked = self.displayStateDict['displayThisStack'] == 'ch3'
			elif actionStr == 'RGB':
				isEnabled = numChannels > 1
				isChecked = self.displayStateDict['displayThisStack'] == 'rgb'
			currentAction.setEnabled(isEnabled)
			currentAction.setChecked(isEnabled)
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
				isChecked = self.displayStateDict['showImage']
			elif actionStr == 'Sliding Z':
				isChecked = self.displayStateDict['displaySlidingZ']
			elif actionStr == 'Nodes':
				isChecked = self.displayStateDict['showNodes']
			elif actionStr == 'Edges':
				isChecked = self.displayStateDict['showEdges']
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

		print('=== bStackView.showRightClickMenu()')
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

		# image
		if userActionStr == 'Channel 1':
			self.displayStateDict['displayThisStack'] = 'ch1'
		elif userActionStr == 'Channel 2':
			self.displayStateDict['displayThisStack'] = 'ch2'
		elif userActionStr == 'Channel 3':
			self.displayStateDict['displayThisStack'] = 'ch3'
		elif userActionStr == 'RGB':
			self.displayStateDict['displayThisStack'] = 'rgb'

		#
		# view of tracing
		elif userActionStr == 'Image':
			self.displayStateChange('showImage', toggle=True)
			#self.displayStateDict['showImage'] = not self.displayStateDict['showImage']
		elif userActionStr == 'Sliding Z':
			self.displayStateDict['displaySlidingZ'] = not self.displayStateDict['displaySlidingZ']
		elif userActionStr == 'Nodes':
			#optionsChange('Panels', 'showLeftToolbar', toggle=True, doEmit=True)
			self.displayStateDict['showNodes'] = not self.displayStateDict['showNodes']
		elif userActionStr == 'Edges':
			self.displayStateDict['showEdges'] = not self.displayStateDict['showEdges']

		#
		# toolbars
		elif userActionStr == 'Left Toolbar':
			self.mainWindow.optionsChange('Panels', 'showLeftToolbar', toggle=True, doEmit=True)
			#self.options['Panels']['showLeftToolbar'] = not self.options['Panels']['showLeftToolbar']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Contrast Panel':
			self.mainWindow.optionsChange('Panels', 'showContrast', toggle=True, doEmit=True)
			#self.options['Panels']['showContrast'] = not self.options['Panels']['showContrast']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Node List':
			self.mainWindow.optionsChange('Panels', 'showNodeList', toggle=True, doEmit=True)
			#self.options['Panels']['showNodeList'] = not self.options['Panels']['showNodeList']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Edge List':
			self.mainWindow.optionsChange('Panels', 'showEdgeList', toggle=True, doEmit=True)
			#self.options['Panels']['showEdgeList'] = not self.options['Panels']['showEdgeList']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Search List':
			self.mainWindow.optionsChange('Panels', 'showSearch', toggle=True, doEmit=True)
			#self.options['Panels']['showSearch'] = not self.options['Panels']['showSearch']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Status Panel':
			self.mainWindow.optionsChange('Panels', 'showStatus', toggle=True, doEmit=True)
			#self.options['Panels']['showStatus'] = not self.options['Panels']['showStatus']
			#self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Line Profile Panel':
			self.mainWindow.optionsChange('Panels', 'showLineProfile', toggle=True, doEmit=True)
			#self.options['Panels']['showLineProfile'] = not self.options['Panels']['showLineProfile']
			#self.mainWindow.updateDisplayedWidgets()

		# other
		elif userActionStr == 'Options':
			optionsDialog = bimpy.interface.bOptionsDialog(self, self.mainWindow)
		elif userActionStr == 'Napari':
			self.mainWindow.openNapari()
		elif userActionStr == 'Refresh':
			self._preComputeAllMasks()
			self.setSlice()

		else:
			print('    showRightClickMenu() -->> no action taken for userActionStr:', userActionStr)
			userSelectedMenu = False

		# emit a signal
		# todo: this is emitting when self.displayStateDict is not changing, e.g. for user action 'Contrast' and 'Annotations'
		'''
		if userSelectedMenu:
			self.setSlice() # update
			self.displayStateChangeSignal.emit(signalName, self.displayStateDict)
		'''

		#return False
		#print('right click menu return')
		return

	def actionHandler(self):
		sender = self.sender()
		title = sender.text()
		print('bStackView.actionHandler() titel:', title, '    ....    todo: put code in this function to handle right-click menu selection')
		#print('    title:', title)

	def displayStateChange(self, key1, value=None, toggle=False):
		if toggle:
			value = not self.displayStateDict[key1]
		self.displayStateDict[key1] = value
		self.setSlice()
		self.displayStateChangeSignal.emit(key1, self.displayStateDict)

	def addEditMenu(self, menu):
		editMenus = ['Delete Node', 'Delete Edge', 'Delete Slab', '---', 'Slab To Node']

		menu.addSeparator()
		for menuStr in editMenus:
			if menuStr == '---':
				menu.addSeparator()
			else:
				isEnabled = False
				if menuStr == 'Delete Node':
					isEnabled = self.selectedNode() is not None
				if menuStr == 'Delete Edge':
					isEnabled = self.selectedEdge() is not None
				elif menuStr in ['Delete Slab', 'Slab To Node']:
					isEnabled = self.selectedSlab() is not None # if we have a node selection

				myAction = QtWidgets.QAction(menuStr, self)
				myAction.setEnabled(isEnabled)
				menu.addAction(myAction)

	def slot_StateChange(self, signalName, signalValue):
		#print(' bStackView.slot_StateChange() signalName:', signalName, 'signalValue:', signalValue)

		# not sure?
		if signalName == 'set slice':
			self.setSlice(signalValue)

		elif signalName == 'bSignal Image':
			self.displayStateDict['showImage'] = signalValue
			self.setSlice() # just refresh

		elif signalName == 'bSignal Sliding Z':
			self.displayStateDict['displaySlidingZ'] = signalValue
			self.setSlice() # just refresh

		elif signalName == 'bSignal Nodes':
			self.displayStateDict['showNodes'] = signalValue
			self.setSlice() # just refresh

		elif signalName == 'bSignal Edges':
			self.displayStateDict['showEdges'] = signalValue
			self.setSlice() # just refresh

		else:
			print('bStackView.slot_StateChange() did not understand signalName:', signalName)

	def slot_selectNode(self, myEvent):
		myEvent.printSlot('bStackView.slot_selectNode()')
		if len(myEvent.nodeList) > 0:
			self.selectNodeList(myEvent.nodeList)
		else:
			nodeIdx = myEvent.nodeIdx
			snapz = myEvent.snapz
			isShift = myEvent.isShift
			self.selectNode(nodeIdx, snapz=snapz, isShift=isShift)

	def slot_selectEdge(self, myEvent):
		myEvent.printSlot('bStackView.slot_selectEdge()')
		if myEvent.eventType == 'select node':
			return
		edgeList = myEvent.edgeList
		colorList = myEvent.colorList
		if len(edgeList)>0:
			# select a list of edges
			self.selectEdgeList(edgeList, thisColorList=colorList, snapz=True)
		else:
			# select a single edge
			edgeIdx = myEvent.edgeIdx
			slabIdx = myEvent.slabIdx
			snapz = myEvent.snapz
			isShift = myEvent.isShift
			self.selectEdge(edgeIdx, snapz=snapz, isShift=isShift)
		self.selectNode(myEvent.nodeIdx)
		self.selectSlab(myEvent.slabIdx)

	def slot_contrastChange(self, myEvent):
		minContrast = myEvent.minContrast
		maxContrast = myEvent.maxContrast

		if minContrast is not None and maxContrast is not None:
			#print('   minContrast:', minContrast, type(minContrast))
			#print('   maxContrast:', maxContrast, type(maxContrast))
			self.minContrast = minContrast
			self.maxContrast = maxContrast
			self.setSlice() # refresh

	def myEvent(self, event):
		theRet = None
		doUpdate = False

		# abb aics
		if event['type']=='joinTwoEdges':
			selectedEdgeList = self.selectedEdgeList_get()
			print('=== myEvent() joinTwoEdges:', selectedEdgeList)
			if len(selectedEdgeList) != 2:
				print('  please select just two edges')
			else:
				edge1 = selectedEdgeList[0]
				edge2 = selectedEdgeList[1]
				#print('=== bStackView.myEvent() ... join edges', edge1, edge2)

				# this will join two edges (via common node) and make a new longer edge
				# use this mostly when (1) nodes have just two edges
				#		(2) when nodes have 4 edges
				newEdgeIdx, srcNode, dstNode = bimpy.bVascularTracingAics.joinEdges(self.mySimpleStack.slabList, edge1, edge2)

				if newEdgeIdx is  None:
					# did not join (usually when edges are not connected)
					pass
				else:
					print('  newEdgeIdx:', newEdgeIdx, 'srcNode:', srcNode, 'dstNode:', dstNode)

					# fill in new diameter
					self.mySimpleStack.slabList._analyze(thisEdgeIdx=newEdgeIdx)

					# clear multi selection
					self.selectedEdgeList_append([]) # this updates 'state'
					#self.cancelSelection(doEmit=False)

					# select the new edge
					self.selectEdge(newEdgeIdx) # select the new edge

					myEvent = bimpy.interface.bEvent('select edge', edgeIdx=newEdgeIdx)
					self.selectEdgeSignal.emit(myEvent)

					# handled by doUpdate = True
					#self._preComputeAllMasks(fromCurrentSlice=True)
					#self.setSlice() #refresh

					#
					# emit change
					#
					#doUpdate = True

					#
					# update tracing
					# can't just do zMin/zMax because all 'later' edges have changed index
					'''
					zMin, zMax = self.mySimpleStack.slabList.getEdgeMinMax_Z(newEdgeIdx)
					print('  only refresh z:', zMin, zMax)
					self._preComputeAllMasks(firstSlice=zMin, lastSlice=zMax)
					self.setSlice() #refresh
					'''
					self._preComputeAllMasks()
					self.setSlice() #refresh

					#
					# todo: fix this, need to grab edgeDict1 BEFORE join?
					#myEvent = bimpy.interface.bEvent('deleteEdge', edgeIdx=edge1, edgeDict=deleteEdgeDict)
					#self.tracingEditSignal.emit(myEvent)

					#
					# before I emit to tables, I need to refresh the tables
					#self.refreshView()
					self.mainWindow.repopulateAllTables()

					#
					# select the one new edge
					myEvent = bimpy.interface.bEvent('select edge', edgeIdx=newEdgeIdx, slabIdx=None)
					self.selectEdgeSignal.emit(myEvent)

					'''
					newEdgeDict = self.mySimpleStack.slabList.getEdge(newEdgeIdx)
					myEvent = bimpy.interface.bEvent('newEdge', edgeIdx=newEdgeIdx, edgeDict=newEdgeDict)
					myEvent._srcNodeDict = self.mySimpleStack.slabList.getNode(srcNode)
					myEvent._dstNodeDict = self.mySimpleStack.slabList.getNode(dstNode)
					#self.tracingEditSignal.emit(myEvent)
					self.selectEdgeSignal.emit(myEvent)
					'''
					#
					# update the pre/post nodes, they have new edges
					'''
					srcNodeDict = self.mySimpleStack.slabList.getNode(srcNode)
					myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=srcNode, nodeDict=srcNodeDict)
					self.tracingEditSignal.emit(myEvent)
					dstNodeDict = self.mySimpleStack.slabList.getNode(dstNode)
					myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=dstNode, nodeDict=dstNodeDict)
					self.tracingEditSignal.emit(myEvent)
					'''

		elif event['type']=='newNode':
			# this works fine, i need to make it more general to limit amount of code here !!!
			if bimpy.interface.myWarningsDialog('new node', self.options).canceled():
				print('new node cancelled by user')
				return theRet

			x = event['x']
			y = event['y']
			z = event['z']
			print('=== bStackView.myEvent() ... new node x:', x, 'y:', y, 'z:', z)
			newNodeIdx = self.mySimpleStack.slabList.newNode(x,y,z)

			# todo: slect new node

			self._preComputeAllMasks(fromSlice=z)
			self.setSlice() #refresh

			theRet = newNodeIdx

			# emit changes
			nodeDict = self.mySimpleStack.slabList.getNode(newNodeIdx)
			myEvent = bimpy.interface.bEvent('newNode', nodeIdx=newNodeIdx, nodeDict=nodeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='newEdge':
			srcNode = event['srcNode']
			dstNode = event['dstNode']
			print('=== bStackView.myEvent() ... new edge srcNode:', srcNode, 'dstNode:', dstNode)

			newEdgeIdx = self.mySimpleStack.slabList.newEdge(srcNode,dstNode)
			self._preComputeAllMasks(fromCurrentSlice=True)
			self.setSlice() #refresh

			theRet = newEdgeIdx

			# todo: cancel node selection

			#
			# emit changes

			# update new edge
			edgeDict = self.mySimpleStack.slabList.getEdge(newEdgeIdx)
			myEvent = bimpy.interface.bEvent('newEdge', edgeIdx=newEdgeIdx, edgeDict=edgeDict)
			myEvent._srcNodeDict = self.mySimpleStack.slabList.getNode(srcNode)
			myEvent._dstNodeDict = self.mySimpleStack.slabList.getNode(dstNode)
			self.tracingEditSignal.emit(myEvent)

			# update the pre/post nodes, they have new edges
			srcNodeDict = self.mySimpleStack.slabList.getNode(srcNode)
			myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=srcNode, nodeDict=srcNodeDict)
			self.tracingEditSignal.emit(myEvent)

			dstNodeDict = self.mySimpleStack.slabList.getNode(dstNode)
			myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=dstNode, nodeDict=dstNodeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='newSlab':
			edgeIdx = event['edgeIdx']
			x = event['x']
			y = event['y']
			z = event['z']
			print('=== bStackView.myEvent() ... new slab edgeIdx:', edgeIdx)
			newSlabIdx = self.mySimpleStack.slabList.newSlab(edgeIdx, x, y, z)
			self._preComputeAllMasks(fromCurrentSlice=True)
			self.selectedSlab(newSlabIdx) # self.setSlice() will draw new slab
			self.setSlice() #refresh
			theRet = newSlabIdx

			# analyze
			self.mySimpleStack.slabList._analyze(thisEdgeIdx=edgeIdx)

			edgeDict = self.mySimpleStack.slabList.getEdge(edgeIdx)

			# new slab for edge idx mean: listeners should
			myEvent = bimpy.interface.bEvent('newSlab', edgeIdx=edgeIdx, edgeDict=edgeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='deleteNode':
			#objectType = event['objectType']
			deleteNodeIdx = event['objectIdx']
			deleteNodeDict = self.mySimpleStack.slabList.getNode(deleteNodeIdx)
			print('\n=== bStackView.myEvent() ... deleteNode:', deleteNodeIdx, deleteNodeDict)
			wasDeleted = self.mySimpleStack.slabList.deleteNode(deleteNodeIdx)
			if wasDeleted:
				# only here if node is not connected to edges
				self.selectNode(None)
				doUpdate = True
				#
				myEvent = bimpy.interface.bEvent('deleteNode', nodeIdx=deleteNodeIdx, nodeDict=deleteNodeDict)
				self.tracingEditSignal.emit(myEvent)
				#
				myEvent = bimpy.interface.bEvent('select node', nodeIdx=None)
				self.selectNodeSignal.emit(myEvent)

		elif event['type']=='deleteEdge':
			print('\n=== bStackView.myEvent() deleteEdge', event['objectIdx'])
			#objectType = event['objectType']
			deleteEdgeIdx = event['objectIdx']
			deleteEdgeDict = self.mySimpleStack.slabList.getEdge(deleteEdgeIdx)
			print('\n=== bStackView.myEvent() ... deleteEdge:', deleteEdgeIdx, deleteEdgeDict)
			self.mySimpleStack.slabList.deleteEdge(deleteEdgeIdx)
			self.selectEdge(None)
			self.selectSlab(None)
			doUpdate = True
			#
			myEvent = bimpy.interface.bEvent('deleteEdge', edgeIdx=deleteEdgeIdx, edgeDict=deleteEdgeDict)
			self.tracingEditSignal.emit(myEvent)
			#
			myEvent = bimpy.interface.bEvent('selectEdge', edgeIdx=None, slabIdx=None)
			self.selectEdgeSignal.emit(myEvent)

		elif event['type']=='deleteSelection':
			# there is order of execution here, if slab selected then delete slab
			# if no slab selected but edge is selected then delete edge
			# if neither slab or edge is selected but there is a node selection then delete node

			selectedSlabIdx = self.selectedSlab()
			selectedEdgeIdx = self.selectedEdge()
			selectedNodeIdx = self.selectedNode()

			if selectedSlabIdx is not None:
				if bimpy.interface.myWarningsDialog('delete slab', self.options).canceled():
					return theRet
				deleteSlabIdx = selectedSlabIdx
				print('\n=== bStackView.myEvent() ... deleteSelection delete slab:', deleteSlabIdx, 'from edge idx:', selectedEdgeIdx)
				self.mySimpleStack.slabList.deleteSlab(deleteSlabIdx)

				# interface
				self.selectEdge(None)
				self.selectSlab(None)
				doUpdate = True
				#
				selectedEdgeDict = self.mySimpleStack.slabList.getEdge(selectedEdgeIdx)
				myEvent = bimpy.interface.bEvent('deleteSlab', edgeIdx=selectedEdgeIdx, edgeDict=selectedEdgeDict, slabIdx=None)
				self.tracingEditSignal.emit(myEvent)

			elif selectedEdgeIdx is not None:
				deleteEdgeIdx = selectedEdgeIdx
				print('\n=== bStackView.myEvent() ... deleteSelection delete edge idx:', deleteEdgeIdx)
				self.mySimpleStack.slabList.deleteEdge(self.selectedEdge())

				# interface
				self.selectEdge(None)
				self.selectSlab(None)
				doUpdate = True
				#
				#deleteEdgeDict = self.mySimpleStack.slabList.getEdge(deleteEdgeIdx)
				myEvent = bimpy.interface.bEvent('deleteEdge', edgeIdx=deleteEdgeIdx) #, edgeDict=deleteEdgeDict)
				self.tracingEditSignal.emit(myEvent)
				#
				myEvent = bimpy.interface.bEvent('selectEdge', edgeIdx=None, slabIdx=None)
				self.selectEdgeSignal.emit(myEvent)

			elif selectedNodeIdx is not None:
				#delete node, only if it does not have edges !!!
				deleteNodeIdx = selectedNodeIdx
				print('\n=== bStackView.myEvent() ... deleteSelection delete node:', deleteNodeIdx)
				wasDeleted = self.mySimpleStack.slabList.deleteNode(deleteNodeIdx)
				if wasDeleted:
					# only here if node is not connected to edges
					self.selectNode(None)
					doUpdate = True
					#
					#deleteNodeDict = self.mySimpleStack.slabList.getNode(self.selectedNode())
					myEvent = bimpy.interface.bEvent('deleteNode', nodeIdx=deleteNodeIdx) #, nodeDict=deleteNodeDict)
					self.tracingEditSignal.emit(myEvent)
					#
					myEvent = bimpy.interface.bEvent('select node', nodeIdx=None)
					self.selectNodeSignal.emit(myEvent)

		elif event['type']=='analyzeEdge':
			objectIdx = event['objectIdx']

			print('\n=== bStackView.myEvent() ... analyzeEdge:', objectIdx)

			# analyze
			self.mySimpleStack.slabList._analyze(thisEdgeIdx=objectIdx)

			#
			newEdgeDict = self.mySimpleStack.slabList.getEdge(objectIdx)
			myEvent = bimpy.interface.bEvent('updateEdge', edgeIdx=objectIdx, edgeDict=newEdgeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='setType':
			# myEvent = {'event': 'setNodeType', 'newType': title, 'nodeIdx':int(nodeIdx)}
			bobID0 = event['bobID0'] # tells us nodes/edges
			newObjectType = event['newType']
			objectIdx = event['objectIdx']
			print(event)
			if bobID0 == 'nodes':
				self.mySimpleStack.slabList.setNodeType(objectIdx, newObjectType)
			elif bobID0 == 'edges':
				self.mySimpleStack.slabList.setEdgeType(objectIdx, newObjectType)
			#
			if bobID0 == 'nodes':
				newNodeDict = self.mySimpleStack.slabList.getNode(objectIdx)
				myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=objectIdx, nodeDict=newNodeDict)
			elif bobID0 == 'edges':
				newEdgeDict = self.mySimpleStack.slabList.getEdge(objectIdx)
				myEvent = bimpy.interface.bEvent('updateEdge', edgeIdx=objectIdx, edgeDict=newEdgeDict)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='setIsBad':
			bobID0 = event['bobID0'] # tells us nodes/edges
			objectIdx = event['objectIdx']
			isChecked = event['isChecked']
			print(event)
			if bobID0 == 'nodes':
				self.mySimpleStack.slabList.setNodeIsBad(objectIdx, isChecked)
			elif bobID0 == 'edges':
				self.mySimpleStack.slabList.setEdgeIsBad(objectIdx, isChecked)
			#
			if bobID0 == 'nodes':
				newNodeDict = self.mySimpleStack.slabList.getNode(objectIdx)
				myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=objectIdx, nodeDict=newNodeDict)
			elif bobID0 == 'edges':
				newEdgeDict = self.mySimpleStack.slabList.getEdge(objectIdx)
				myEvent = bimpy.interface.bEvent('updateEdge', edgeIdx=objectIdx, edgeDict=newEdgeDict)
			'''
			newNodeDict = self.mySimpleStack.slabList.getNode(nodeIdx)
			myEvent = bimpy.interface.bEvent('updateNode', nodeIdx=nodeIdx, nodeDict=newNodeDict)
			'''
			self.tracingEditSignal.emit(myEvent)

		elif event['type'] == 'cancelSelection':
			self.cancelSelection()

		else:
			print('bStackView.myEvent() not understood event:', event)

		# finalize
		if doUpdate:
			#print('bStackView.myEvent() is updating masks with _preComputeAllMasks()')
			self._preComputeAllMasks(fromCurrentSlice=True)
			self.setSlice() #refresh
		return theRet

	def flashNode(self, nodeIdx, numberOfFlashes):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashEdge() edgeIdx:', edgeIdx, on)
		if nodeIdx is None:
			return
		if numberOfFlashes>0:
			if self.mySimpleStack.slabList is not None:
				x, y, z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)
				self.myNodeSelectionFlash.set_offsets(np.c_[y, x])
				#self.myNodeSelectionFlash.set_offsets(np.c_[x, y])
				#
				QtCore.QTimer.singleShot(20, lambda:self.flashNode(nodeIdx, numberOfFlashes-1))
		else:
			self.myNodeSelectionFlash.set_offsets(np.c_[[], []])
		#
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def flashEdgeList(self, edgeList, on):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashEdge() edgeIdx:', edgeIdx, on)
		if edgeList is None or len(edgeList)==0:
			return
		if on:
			if self.mySimpleStack.slabList is not None:
				theseIndices = []
				for edgeIdx in edgeList:
					theseIndices += self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
				xMasked = self.mySimpleStack.slabList.y[theseIndices]
				yMasked = self.mySimpleStack.slabList.x[theseIndices]
				self.myEdgeSelectionFlash.set_offsets(np.c_[xMasked, yMasked])
				#
				QtCore.QTimer.singleShot(20, lambda:self.flashEdgeList(edgeList, False))
		else:
			self.myEdgeSelectionFlash.set_offsets(np.c_[[], []])
		#
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def flashEdge(self, edgeIdx, on):
		#todo rewrite this to use a copy of selected edge coordinated, rather than grabbing them each time (slow)
		#print('flashEdge() edgeIdx:', edgeIdx, on)
		if edgeIdx is None:
			return
		if on:
			if self.mySimpleStack.slabList is not None:
				theseIndices = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
				xMasked = self.mySimpleStack.slabList.y[theseIndices]
				yMasked = self.mySimpleStack.slabList.x[theseIndices]
				self.myEdgeSelectionFlash.set_offsets(np.c_[xMasked, yMasked])
				#
				QtCore.QTimer.singleShot(20, lambda:self.flashEdge(edgeIdx, False))
		else:
			self.myEdgeSelectionFlash.set_offsets(np.c_[[], []])
		#
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def setSelection(nodeIdx=None, edgeIdx=None, slabIdx=None, clearAll=False):
		if nodeIdx is not None:
			self.selectedNode(nodeIdx)
		if edgeIdx is not None:
			self.selectedEdge(edgeIdx)
		if slabIdx is not None:
			self.selectedSlab(slabIdx)
		if clearAll:
			self.selectedNode(None)
			self.selectedEdge(None)
			self.selectedSlab(None)

	def selectNode(self, nodeIdx, snapz=False, isShift=False):
		print('bStackView.selectNode() nodeIdx:', nodeIdx, type(nodeIdx))
		if nodeIdx is None:
			#print('bStackView.selectNode() nodeIdx:', nodeIdx)
			self.selectedNode(None)
			self.myNodeSelectionPlot.set_offsets(np.c_[[], []])
		else:

			# abb aics todo: tracing bounds check
			if not self.mySimpleStack.slabList.myBoundCheck_Node(nodeIdx):
				return

			if self.mySimpleStack.slabList is not None:
				#print('   bStackView.selectNode() nodeIdx:', nodeIdx, self.mySimpleStack.slabList.getNode(nodeIdx))
				self.mySimpleStack.slabList.printNodeInfo(nodeIdx)

				self.selectedNode(nodeIdx)

				x,y,z = self.mySimpleStack.slabList.getNode_xyz(nodeIdx)

				if snapz:
					z = self.mySimpleStack.slabList.getNode_zSlice(nodeIdx)
					self.setSlice(z)

					#self.zoomToPoint(y, x)
					self.zoomToPoint(x, y)

				self.myNodeSelectionPlot.set_offsets(np.c_[y,x]) # flipped

				markerColor = self.options['Tracing']['nodeSelectionColor']
				markerSize = self.options['Tracing']['nodeSelectionPenSize'] **2
				markerSizes = [markerSize] # set_sizes expects a list, one size per marker
				self.myNodeSelectionPlot.set_color(markerColor)
				self.myNodeSelectionPlot.set_sizes(markerSizes)

				#self.zoomToPoint(x,y)

				QtCore.QTimer.singleShot(10, lambda:self.flashNode(nodeIdx, 2))

		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

		if isShift:
			# select edges connected to node
			if nodeIdx is not None:
				node = self.mySimpleStack.slabList.nodeDictList[nodeIdx]
				edgeList = node['edgeList']
				self.selectEdgeList(edgeList)

	def selectNodeList(self, nodeList):
		print('bStackView.selectNodeList() num nodes:', len(nodeList))

		slabList = []
		#for node in self.mySimpleStack.slabList.nodeIter():
		for nodeIdx in nodeList:
			#print('    node:', node)
			slabIdx = self.mySimpleStack.slabList._getSlabFromNodeIdx(nodeIdx)
			#slabIdx = node['slabIdx']
			slabList.append(slabIdx)

		#print('    slabList:', slabList)
		xMasked = self.mySimpleStack.slabList.x[slabList] #
		yMasked = self.mySimpleStack.slabList.y[slabList]

		self.myNodeSelectionPlot.set_offsets(np.c_[yMasked,xMasked]) # flipped

		markerColor = self.options['Tracing']['nodeSelectionColor']
		markerSize = self.options['Tracing']['nodeSelectionPenSize'] **2
		markerSizes = [markerSize for nodeIdx in nodeList] # set_sizes expects a list, one size per marker
		self.myNodeSelectionPlot.set_color(markerColor)
		self.myNodeSelectionPlot.set_sizes(markerSizes)

		'''
		print('    xMasked:', xMasked)
		print('    yMasked:', yMasked)
		print('    markerColor:', markerColor)
		print('    markerSizes:', markerSizes)
		'''

		#QtCore.QTimer.singleShot(10, lambda:self.flashNode(nodeIdx, 2))

		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def selectEdge(self, edgeIdx, snapz=False, isShift=False, isAlt=False):
		if edgeIdx is None:
			print('bStackView.selectEdge() edgeIdx:', edgeIdx, 'snapz:', snapz)
			#markersize = 10
			#self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color='c', s=markersize, picker=True)
			self.selectedEdge(None)
			#self.selectedSlab(None)
			self.myEdgeSelectionPlot.set_offsets(np.c_[[], []])
		else:
			# abb aics todo: tracing bounds check
			if not self.mySimpleStack.slabList.myBoundCheck_Edge(edgeIdx):
				return

			self.selectedEdge(edgeIdx)

			if self.mySimpleStack.slabList is not None:
				theseIndices = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)

				print('  = bStackView.selectEdge() edgeIdx:', edgeIdx, 'snapz:', snapz)
				self.mySimpleStack.slabList.printEdgeInfo(edgeIdx)
				#print('bStackView.selectEdge() edgeIdx:', edgeIdx, 'snapz:', snapz, 'edgeDict:', self.mySimpleStack.slabList.getEdge(edgeIdx))
				#print('      theseIndices:', theseIndices)
				# todo: add option to snap to a z
				# removed this because it was confusing
				if snapz:
					'''
					z = self.mySimpleStack.slabList.z[theseIndices[0]][0] # not sure why i need trailing [0] ???
					z = int(z)
					'''

					tmpEdgeDict = self.mySimpleStack.slabList.getEdge(edgeIdx)

					#z = self.mySimpleStack.slabList.edgeDictList[edgeIdx]['z']
					z = tmpEdgeDict['z']
					z = int(z)
					self.setSlice(z)

					# snap to point
					# get the (x,y) of the middle slab
					tmp_nSlab = tmpEdgeDict['nSlab']
					middleSlab = int(tmp_nSlab/2)
					middleSlabIdx = tmpEdgeDict['slabList'][middleSlab]
					tmpx, tmpy, tmpz = self.mySimpleStack.slabList.getSlab_xyz(middleSlabIdx)
					self.zoomToPoint(tmpx, tmpy)

				xMasked = self.mySimpleStack.slabList.x[theseIndices] # flipped
				yMasked = self.mySimpleStack.slabList.y[theseIndices]
				self.myEdgeSelectionPlot.set_offsets(np.c_[yMasked, xMasked])

				markerColor = self.options['Tracing']['tracingSelectionColor']
				markerSize = self.options['Tracing']['tracingSelectionPenSize'] **2
				markerSizes = [markerSize] # set_sizes expects a list, one size per marker
				self.myEdgeSelectionPlot.set_color(markerColor)
				self.myEdgeSelectionPlot.set_sizes(markerSizes)

				QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, True))

		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

		if edgeIdx is not None:
			if isAlt:
				# on macOS, meta corresponds to 'control'
				# select immediately connected edges
				colors = ['r', 'g', 'r', 'g']
				edge = self.mySimpleStack.slabList.edgeDictList[edgeIdx]
				selectedEdgeList = [edgeIdx] # could be [edgeIdx]
				colorList = ['y']
				if edge['preNode'] is not None:
					print('   selectEdge() selecting edges on preNode:', edge['preNode'], 'of edgeIdx:', edgeIdx)
					edgeList = self.mySimpleStack.slabList.nodeDictList[edge['preNode']]['edgeList']
					edgeList = list(edgeList) # make a copy
					try:
						repeatIdx = edgeList.index(edgeIdx) # find the index of our original edgeIdx and remove it
						edgeList.pop(repeatIdx)
					except (ValueError) as e:
						print('WARNING: selectEdge() pre node:', edge['preNode'], 'edgeList:', edgeList, 'does not contain:', edgeIdx)
					selectedEdgeList += edgeList
					colorList += [colors[colorIdx] for colorIdx in range(len(edgeList))]
				if edge['postNode'] is not None:
					print('   selectEdge() selecting edges on postNode:', edge['postNode'], 'of edgeIdx:', edgeIdx)
					edgeList = self.mySimpleStack.slabList.nodeDictList[edge['postNode']]['edgeList']
					edgeList = list(edgeList) # make a copy
					try:
						repeatIdx = edgeList.index(edgeIdx) # find the index of our original edgeIdx and remove it
						edgeList.pop(repeatIdx)
					except (ValueError) as e:
						print('WARNING: selectEdge() post node:', edge['postNode'], 'edgeList:', edgeList, 'does not contain:', edgeIdx)
					selectedEdgeList += edgeList
					colorList += [colors[colorIdx] for colorIdx in range(len(edgeList))]
				#print('edgeList:', edgeList)
				self.selectEdgeList(selectedEdgeList, thisColorList=colorList)

	def selectEdgeList(self, edgeList, thisColorList=[], snapz=False):
		if snapz:
			firstEdge = edgeList[0]
			z = self.mySimpleStack.slabList.edgeDictList[firstEdge]['z']
			z = int(z)
			self.setSlice(z)

		#colors = ['r', 'g', 'b']
		slabList = []
		colorList = []
		#colorIdx = 0
		for idx, edgeIdx in enumerate(edgeList):
			edge = self.mySimpleStack.slabList.getEdge(edgeIdx)
			slabs = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
			slabList += slabs
			if len(thisColorList) > 0:
				colorList += [thisColorList[idx] for slab in slabs]
			else:
				#colorList += [colors[colorIdx] for slab in slabs]
				colorList += [edge['color'] for slab in slabs]
			'''
			colorIdx += 1
			if colorIdx==len(colors)-1:
				colorIdx = 0
			'''
		#print('selectEdgeList() slabList:', slabList)
		xMasked = self.mySimpleStack.slabList.x[slabList] # flipped
		yMasked = self.mySimpleStack.slabList.y[slabList]
		self.myEdgeSelectionPlot.set_offsets(np.c_[yMasked, xMasked])
		self.myEdgeSelectionPlot.set_color(colorList)

		# this works but might not be neccessary for an edge selection
		if len(edgeList) < 20:
			QtCore.QTimer.singleShot(10, lambda:self.flashEdgeList(edgeList, True))

		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!
		#QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, True))

	def selectSlab(self, slabIdx, snapz=False):
		if self.mySimpleStack.slabList is None:
			return
		#print('bStackView.selectSlab() slabIdx:', type(slabIdx), slabIdx)

		# always allow cancel
		if slabIdx is None or np.isnan(slabIdx):
			#print('   bStackView.selectSlab() CANCEL slabIdx:', slabIdx, 'snapz:', snapz)
			#markersize = 10
			#self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color='c', s=markersize, picker=True)
			self.selectedSlab(None)
			self.mySlabSelectionPlot.set_offsets(np.c_[[], []])
			self.mySlabLinePlot.set_xdata([])
			self.mySlabLinePlot.set_ydata([])
		else:
			# only if we are showing the line profile panel
			if not self.options['Panels']['showLineProfile']:
				return

			# abb aics todo: tracing bounds check
			if not self.mySimpleStack.slabList.myBoundCheck_Slab(slabIdx):
				return

			# abb kind a bound check
			numSlabs = self.mySimpleStack.slabList.numSlabs()
			if slabIdx > numSlabs-1:
				print('warning: bStackView.selectSlab() got out of bound slabIdx:', slabIdx, 'there are only numSlabs:', numSlabs)
				return

			self.selectedSlab(slabIdx)

			x,y,z = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)
			numSlabs = self.mySimpleStack.slabList.numSlabs()

			if snapz:
				z = int(z)
				self.setSlice(z)

			self.mySlabSelectionPlot.set_offsets(np.c_[y, x]) # flipped

			linewidth = self.options['Tracing']['lineProfileLineSize']
			markersize = self.options['Tracing']['lineProfileMarkerSize']
			c = self.options['Tracing']['lineProfileColor']

			self.mySlabLinePlot.set_linewidth(linewidth)
			self.mySlabLinePlot.set_markersize(markersize)
			self.mySlabLinePlot.set_color(c)

			#
			# draw the orthogonal line
			self.drawSlab(slabIdx)

		#self.canvas.draw()
		self.canvas.draw_idle()
		self.repaint() # this is updating the widget !!!!!!!!

	def drawSlab(self, slabIdx=None, radius=None):
		if radius is None:
			radius = 30 # pixels

		if slabIdx is None:
			slabIdx = self.selectedSlab()
		if slabIdx is None:
			return

		# todo: could pas edgeIdx as a parameter
		edgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(slabIdx)
		if edgeIdx is None:
			print('warning: bStackView.drawSlab() got bad edgeIdx:', edgeIdx)
			return
		edgeSlabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
		thisSlabIdx = edgeSlabList.index(slabIdx) # index within edgeSlabList
		#print('   edgeIdx:', edgeIdx, 'thisSlabIdx:', thisSlabIdx, 'len(edgeSlabList):', len(edgeSlabList))
		# todo: not sure but pretty sure this will not fail?
		if thisSlabIdx==0 or thisSlabIdx==len(edgeSlabList)-1:
			# we were at a slab that was also a node
			return
		prevSlab = edgeSlabList[thisSlabIdx - 1]
		nextSlab = edgeSlabList[thisSlabIdx + 1]
		this_x, this_y, this_z = self.mySimpleStack.slabList.getSlab_xyz(slabIdx)
		prev_x, prev_y, prev_z = self.mySimpleStack.slabList.getSlab_xyz(prevSlab)
		next_x, next_y, next_z = self.mySimpleStack.slabList.getSlab_xyz(nextSlab)
		dy = next_y - prev_y
		dx = next_x - prev_x
		slope = dy/dx
		slope = dx/dy # flipped
		inverseSlope = -1/slope
		x_ = radius / math.sqrt(slope**2 + 1) #
		y_ = x_ * slope
		#y_ = radius / math.sqrt(slope**2 + 1) # flipped
		#x_ = y_ * slope
		xLine1 = this_x - x_ #
		xLine2 = this_x + x_
		yLine1 = this_y + y_
		yLine2 = this_y - y_
		xSlabPlot = [xLine1, xLine2]
		ySlabPlot = [yLine1, yLine2]
		'''
		print('selectSlab() slabIdx:', slabIdx, 'slope:', slope, 'inverseSlope:', inverseSlope)
		print('   slope:', slope, 'inverseSlope:', inverseSlope)
		print('   xSlabPlot:', xSlabPlot)
		print('   ySlabPlot:', ySlabPlot)
		'''
		self.mySlabLinePlot.set_xdata(ySlabPlot) # flipped
		self.mySlabLinePlot.set_ydata(xSlabPlot)

		profileDict = {
			'ySlabPlot': ySlabPlot,
			'xSlabPlot': xSlabPlot,
			'slice': self.currentSlice,
		}

		self.mainWindow.signal('update line profile', profileDict)
		# todo: implement this

		#
		# emit
		selectededge = self.selectedEdge()
		myEvent = bimpy.interface.bEvent('select edge', edgeIdx=selectededge, slabIdx=slabIdx)
		self.selectEdgeSignal.emit(myEvent)

	def loadMasks(self):
		pickleFile = self.mySimpleStack._getSavePath() # tiff file without extension
		pickleFile += '.pickle'
		if os.path.isfile(pickleFile):
			print('  loadMasks() loading maskedNodes from pickleFile:', pickleFile)
			#timer = bimpy.util.bTimer()
			timer = bimpy.util.bTimer(name='loadMasks')
			with open(pickleFile, 'rb') as filename:
				#self.maskedNodes = pickle.load(filename)
				self.maskedEdgesDict = pickle.load(filename)
			print('    loaded mask file from', pickleFile)
			timer.elapsed()
			#
			return True
			#
		else:
			#print('error: _preComputeAllMasks did not find pickle file:', pickleFile)
			return False

	def saveMasks(self):
		pickleFile = self.mySimpleStack._getSavePath() # tiff file without extension
		pickleFile += '.pickle'
		print('    bStackView.saveMasks() saving maskedNodes as pickleFile:', pickleFile)
		with open(pickleFile, 'wb') as fout:
			#pickle.dump(self.maskedNodes, fout)
			pickle.dump(self.maskedEdgesDict, fout)

	###########################################################################
	def _preComputeAllMasks2(self):
		print('_preComputeAllMasks2()')

		timeIt = bimpy.util.bTimer('_preComputeAllMasks2')

		aicsSlabList = []
		aicsSlabList_x = np.empty((0), np.float16) #[]
		aicsSlabList_y = np.empty((0), np.float16) #[]
		aicsSlabList_z = np.empty((0), np.float16) #[]
		aicsSlabList_edgeIdx = np.empty((0), np.uint16) #[]
		aicsSlabList_slabIdx = np.empty((0), np.uint16) #[]

		for edgeIdx, edge in enumerate(self.mySimpleStack.slabList.edgeDictList):
			tmpSlabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx) # includes nodes
			aicsSlabList += tmpSlabList + [np.nan] # abb aics

			# x
			aicsSlabList_x = np.append(aicsSlabList_x, self.mySimpleStack.slabList.x[tmpSlabList])
			aicsSlabList_x = np.append(aicsSlabList_x, np.nan) # abb aics

			# y
			aicsSlabList_y = np.append(aicsSlabList_y, self.mySimpleStack.slabList.y[tmpSlabList])
			aicsSlabList_y = np.append(aicsSlabList_y, np.nan) # abb aics
			# x
			aicsSlabList_z = np.append(aicsSlabList_z, self.mySimpleStack.slabList.z[tmpSlabList])
			aicsSlabList_z = np.append(aicsSlabList_z, np.nan) # abb aics

			# edgeIdx (needs to be float)
			aicsSlabList_edgeIdx = np.append(aicsSlabList_edgeIdx, self.mySimpleStack.slabList.edgeIdx[tmpSlabList])
			aicsSlabList_edgeIdx = np.append(aicsSlabList_edgeIdx, np.nan) # abb aics

			# slabIdx (needs to be float)
			aicsSlabList_slabIdx = np.append(aicsSlabList_slabIdx, tmpSlabList)
			aicsSlabList_slabIdx = np.append(aicsSlabList_slabIdx, np.nan) # abb aics

		#
		# nodes
		nodeIdxMask = np.ma.masked_greater_equal(self.mySimpleStack.slabList.nodeIdx, 0)
		nodeIdxMask = nodeIdxMask.mask

		aicsNodeList_x = self.mySimpleStack.slabList.x[nodeIdxMask]
		aicsNodeList_y = self.mySimpleStack.slabList.y[nodeIdxMask]
		aicsNodeList_z = self.mySimpleStack.slabList.z[nodeIdxMask]
		aicsNodeList_nodeIdx = self.mySimpleStack.slabList.nodeIdx[nodeIdxMask].astype(np.uint16)

		self.maskedEdgesDict = {
			# edges
			'aicsSlabList': aicsSlabList,
			'aicsSlabList_x': aicsSlabList_x,
			'aicsSlabList_y': aicsSlabList_y,
			'aicsSlabList_z': aicsSlabList_z,
			'aicsSlabList_slabIdx': aicsSlabList_slabIdx,
			'aicsSlabList_edgeIdx': aicsSlabList_edgeIdx,
			# nodes
			'aicsNodeList_x': aicsNodeList_x,
			'aicsNodeList_y': aicsNodeList_y,
			'aicsNodeList_z': aicsNodeList_z,
			'aicsNodeList_nodeIdx': aicsNodeList_nodeIdx,

		}

		print(timeIt.elapsed())

		#import sys
		#sys.exit()

	def _preComputeAllMasks(self, fromSlice=None, fromCurrentSlice=False, firstSlice=None, lastSlice=None, loadFromFile=False):
		"""
		Precompute all masks once. When user scrolls through slices this is WAY faster
		On new/delete (node, edge), just compute slices within +/- show tracing

		Parameters:
			fromSlice: compute fromSlice +/- showTracingAboveSlices
			fromCurrentSlice trumps fromSlice
			firstSlice/lastSlice: update slices for a given edge
		"""

		#
		#
		self._preComputeAllMasks2()
		return
		#
		#

		myTimer = bimpy.util.bTimer('_preComputeAllMasks')

		if self.mySimpleStack.slabList is None:
			return

		#
		#
		if loadFromFile:
			loaded = self.loadMasks()
			if loaded:
				myTimer.elapsed()
				return True

		#
		recomputeAll = False
		if fromSlice is None and not fromCurrentSlice and firstSlice is None:
			#recreate all
			self.maskedNodes = []
			recomputeAll = True

		showTracingAboveSlices = self.options['Tracing']['showTracingAboveSlices']
		showTracingBelowSlices = self.options['Tracing']['showTracingBelowSlices']

		#markersize = self.options['Tracing']['nodePenSize'] **2
		default_nodeColor = self.options['Tracing']['nodeColor'] # segmentation fault ???

		sliceRange = range(self.mySimpleStack.numImages)
		if fromCurrentSlice:
			fromSlice = self.currentSlice
		if fromSlice is not None:
			sliceRange = range(fromSlice-showTracingAboveSlices, fromSlice+showTracingBelowSlices)
		# abb aics
		if firstSlice is not None and lastSlice is not None:
			sliceRange = range(firstSlice, lastSlice+1)
			print('  _preComputeAllMasks() is using firstSlice:', firstSlice, 'lastSlice:', lastSlice, 'sliceRange:', sliceRange)

		# abb aics
		#aicsSlabList_x = np.empty((0))

		#for i in range(self.mySimpleStack.numImages):
		print('bStackView._preComputeAllMasks() computing masks for slices:', sliceRange, 'recomputeAll:', recomputeAll, 'nEdges:', len(self.mySimpleStack.slabList.edgeDictList), '...')
		for i in sliceRange:
			# when using fromSlice
			if i<0 or i>self.mySimpleStack.numImages-1:
				continue

			upperz = i - self.options['Tracing']['showTracingAboveSlices']
			lowerz = i + self.options['Tracing']['showTracingBelowSlices']

			# nodes
			#zNodeMasked = np.ma.masked_outside(self.mySimpleStack.slabList.z, upperz, lowerz)
			zNodeMasked0 = np.ma.masked_inside(self.mySimpleStack.slabList.z, upperz, lowerz) # Mask inside a given interval.
			#zNodeMasked0 = zNodeMasked0.ravel()
			#if len(zNodeMasked) > 0:
			if len(zNodeMasked0) > 0:
				xNodeMasked = self.mySimpleStack.slabList.y[zNodeMasked0.mask] # swapping
				yNodeMasked = self.mySimpleStack.slabList.x[zNodeMasked0.mask]
				'''
				xNodeMasked = self.mySimpleStack.slabList.y[~zNodeMasked.mask] # swapping
				yNodeMasked = self.mySimpleStack.slabList.x[~zNodeMasked.mask]
				'''
				#dMasked = self.mySimpleStack.slabList.d[~zNodeMasked.mask]
				nodeIdxMasked = self.mySimpleStack.slabList.nodeIdx[zNodeMasked0.mask]
				'''
				nodeIdxMasked = self.mySimpleStack.slabList.nodeIdx[~zNodeMasked.mask]
				'''
				# abb edgeIdxMasked = self.mySimpleStack.slabList.edgeIdx[~zNodeMasked.mask]
				#slabIdxMasked = self.mySimpleStack.slabList.slabIdx[~zNodeMasked.mask]

				nodeMasked_x = xNodeMasked[~np.isnan(nodeIdxMasked)]
				nodeMasked_y = yNodeMasked[~np.isnan(nodeIdxMasked)]
				nodeMasked_nodeIdx = nodeIdxMasked[~np.isnan(nodeIdxMasked)]
				#nodeMasked_size = [markersize for tmpx in xNodeMasked]
				# now this ... covid ... this is amazing that this works !!!!!!!!!!!
				# covid, store the nEdges for each node, color them in setSlice() ???
				nodeMasked_color = [default_nodeColor if self.mySimpleStack.slabList.nodeDictList[int(float(tmpNodeIdx))]['nEdges']>1 else 'orange' for tmpNodeIdx in nodeMasked_nodeIdx]

				nodeMasked_x = nodeMasked_x.ravel()
				nodeMasked_y = nodeMasked_y.ravel()
				nodeMasked_nodeIdx = nodeMasked_nodeIdx.ravel().astype(int)

				#
				# to draw lines on edges, make a disjoint list (seperated by nan
				# aics was this
				"""
				xEdgeLines = []
				yEdgeLines = []
				# abb dEdgeLines = []
				edgeIdxLines = []
				slabIdxLines = []
				nodeIdxLines = [] # to intercept clicks on edge that are also node
				"""
				aicsSlabList = [] # abb aics
				#aicsSlabList_x = np.empty((0))
				#aicsSlabList_y = np.empty((0))
				#aicsSlabList_z = np.empty((0))
				#aicsSlabList_zMask = []

				timeEdgeIter = bimpy.util.bTimer('time edge iter')
				for edgeIdx, edge in enumerate(self.mySimpleStack.slabList.edgeDictList):
					tmpSlabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
					aicsSlabList += tmpSlabList + [np.nan] # abb aics
				print(timeEdgeIter.elapsed())

				#aicsSlabList_x = self.mySimpleStack.slabList.x[aicsSlabList]
				'''
				nonNanIdxArray = np.where(~np.isnan(aicsSlabList))
				aicsSlabList_x = np.ndarray(aicsSlabList)
				aicsSlabList_x[nonNanIdxArray] =
				'''
				#np.where(np.isnan(aicsSlabList), np.nan, self.mySimpleStack.slabList.x[aicsSlabList])

				aicsSlabList_y = self.mySimpleStack.slabList.y[aicsSlabList]

				aicsSlabList_z = self.mySimpleStack.slabList.z[aicsSlabList]

				#aicsSlabList_zMask = [tmpz if (tmpz>upperz and tmpz<lowerz) else np.nan for tmpz in aicsSlabList_z] # todo: convert to numpy before???
				aicsSlabList_zMask = np.ma.masked_inside(aicsSlabList_z, upperz, lowerz)

				# aics was this
				"""
				aicsSlabList = []
				for edgeIdx, edge in enumerate(self.mySimpleStack.slabList.edgeDictList):
					# slabList will include srcNode/dstNode as slabs
					slabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
					aicsSlabList += slabList + [np.nan] # abb aics
					'''
					print('  edgeIdx:', edgeIdx)
					print('    len(slabList):', len(slabList), 'slabList:', slabList)
					print('    len(aicsSlabList_x)', len(aicsSlabList_x), 'aicsSlabList_x:', aicsSlabList_x)
					print('    self.mySimpleStack.slabList.x.shape:', self.mySimpleStack.slabList.x.shape)
					print('    len(self.mySimpleStack.slabList.x[slabList]):', len(self.mySimpleStack.slabList.x[slabList]), 'self.mySimpleStack.slabList.x[slabList]:', self.mySimpleStack.slabList.x[slabList])
					'''

					#aicsSlabList_y += self.mySimpleStack.slabList.y[slabList].tolist() + [np.nan] # abb aics
					#aicsSlabList_z += self.mySimpleStack.slabList.z[slabList].tolist() + [np.nan] # abb aics
					#aicsSlabList_zMask += [tmpz if (tmpz>upperz and tmpz<lowerz) else np.nan for tmpz in aicsSlabList_z] # todo: convert to numpy before???

					# decide if the slabs are within (upperz, lowerz)
					for slab in slabList:
						zSlab = self.mySimpleStack.slabList.z[slab]
						if zSlab>upperz and zSlab<lowerz:
							# include
							xEdgeLines.append(self.mySimpleStack.slabList.y[slab]) # flipped
							yEdgeLines.append(self.mySimpleStack.slabList.x[slab])
							# dEdgeLines.append(self.mySimpleStack.slabList.d[slab])
							edgeIdxLines.append(edgeIdx)
							slabIdxLines.append(slab)
							nodeIdxLines.append(self.mySimpleStack.slabList.nodeIdx[slab])
						else:
							# exclude
							xEdgeLines.append(np.nan)
							yEdgeLines.append(np.nan)
							# dEdgeLines.append(np.nan)
							edgeIdxLines.append(np.nan)
							slabIdxLines.append(np.nan)
							nodeIdxLines.append(np.nan)

					# edges need to be separated by nan so we don't get a line b/w sequential edges
					# this makes it hard to 'vectorize' this function, (x,y,z) is not in sync with displayed x/y/z
					xEdgeLines.append(np.nan)
					yEdgeLines.append(np.nan)
					# dEdgeLines.append(np.nan)
					edgeIdxLines.append(np.nan)
					slabIdxLines.append(np.nan)
					nodeIdxLines.append(np.nan)
				""" # aics was this

			else:
				# aics was this
				pass
				"""
				# len(zNodeMasked)<1
				nodeMasked_x = []
				nodeMasked_y = []
				nodeMasked_nodeIdx = []
				#nodeMasked_size = []
				nodeMasked_color = []

				xEdgeLines = []
				yEdgeLines = []
				# dEdgeLines = []
				edgeIdxLines = []
				slabIdxLines = []
				nodeIdxLines = []
				"""
			#print('slice i:', i, len(aicsSlabList))

			#aicsSlabList = np.asarray(aicsSlabList, dtype=np.float32) # this has nan

			maskedNodeDict = {
				#'zNodeMasked': zNodeMasked,
				'zNodeMasked0': zNodeMasked0, # abb aics
				'aicsSlabList': aicsSlabList, # abb aics
				'aicsSlabList_x': aicsSlabList_x, # abb aics
				'aicsSlabList_y': aicsSlabList_y, # abb aics
				'aicsSlabList_z': aicsSlabList_z, # abb aics
				'aicsSlabList_z': aicsSlabList_zMask, # abb aics
				'nodeMasked_x': nodeMasked_x,
				'nodeMasked_y': nodeMasked_y,
				'nodeMasked_nodeIdx': nodeMasked_nodeIdx,
				#'nodeMasked_size': nodeMasked_size,
				'nodeMasked_color': nodeMasked_color,
			}
			# aics was this (inside dict {}
			"""
			'xEdgeLines': xEdgeLines,
			'yEdgeLines': yEdgeLines,
			#'dEdgeLines': dEdgeLines,
			'edgeIdxLines': edgeIdxLines,
			'slabIdxLines': slabIdxLines,
			'nodeIdxLines': nodeIdxLines,
			}
			"""

			# abb aics, removed
			# update
			'''
			if fromSlice is not None:
				#print('   updating slide i:', i)
				self.maskedNodes[i] = maskedNodeDict
			else:
				#print('   appending i:', i)
				self.maskedNodes.append(maskedNodeDict)
			'''
			# abb aics, added
			if recomputeAll:
				self.maskedNodes.append(maskedNodeDict)
			else:
				print('  _preComputeAllMasks() i:', i)
				self.maskedNodes[i] = maskedNodeDict

			#print('slice', i, '_preComputeAllMasks() len(x):', len(xMasked), 'len(y)', len(yMasked))

		print(myTimer.elapsed())

	def set_cmap(self, cmapName, minColor, maxColor):
		print('  bStackView.set_cmap() cmapName:', cmapName, 'minColor:', minColor, 'maxColor:', maxColor)
		#cmap = self.options['Stack']['colorLut']

		self.myColorMap = matplotlib.cm.get_cmap(cmapName)

		# this works but make noisy grid in darkness?
		'''
		self.myColorMap.set_under(color=minColor)
		self.myColorMap.set_over(color=maxColor)
		'''

		# this works
		self.imgplot.set_cmap(self.myColorMap)

		# does not work
		#self.imgplot.clim(100, 200)

		# maybe this?
		#self.imgplot.cmap.set_under('black')

		# redraw
		self.canvas.draw_idle()

	#######################################
	def setSlice2(self, index=None):
		#timeSetSlice = bimpy.util.bTimer('time set slice 2')

		if index is None:
			index = self.currentSlice
		if index < 0:
			index = 0
		if index > self.mySimpleStack.numImages-1:
			index = self.mySimpleStack.numImages -1

		self.mySimpleStack.setSlice(index)

		#
		# image
		if self.displayStateDict['showImage']:
			displayThisStack = self.displayStateDict['displayThisStack']
			if self.displayStateDict['displaySlidingZ']:
				upSlices = self.options['Stack']['upSlidingZSlices']
				downSlices = self.options['Stack']['downSlidingZSlices']
				image = self.mySimpleStack.getSlidingZ(index, displayThisStack, upSlices, downSlices, self.minContrast, self.maxContrast)
			else:
				# works
				image = self.mySimpleStack.setSliceContrast(index, thisStack=displayThisStack, minContrast=self.minContrast, maxContrast=self.maxContrast)
				#print('image.shape:', image.shape)

			if self.imgplot is None:
				cmap = self.options['Stack']['colorLut'] #2**2
				# no scale

				# was this
				#self.imgplot = self.axes.imshow(image, cmap=cmap)

				#self.imgplot = self.axes.imshow(image, interpolation='none', cmap=self.myColorMap, alpha=1.0)
				self.imgplot = self.axes.imshow(image, cmap=self.myColorMap)

			else:
				self.imgplot.set_data(image)
		else:
			if self.imgplot is not None:
				self.imgplot.set_data(np.zeros((1,1)))

		#print('\n\ntodo: FIX showTracingAboveSlices')

		showTracingAboveSlices = self.options['Tracing']['showTracingAboveSlices']
		showTracingBelowSlices = self.options['Tracing']['showTracingBelowSlices']
		firstSlice = index - showTracingAboveSlices
		lastSlice = index + showTracingBelowSlices

		#
		# edges
		if self.displayStateDict['showEdges']:
			aicsSlabList_x = self.maskedEdgesDict['aicsSlabList_x']
			aicsSlabList_y = self.maskedEdgesDict['aicsSlabList_y']
			aicsSlabList_z = self.maskedEdgesDict['aicsSlabList_z']

			zMasked = np.ma.masked_inside(aicsSlabList_z, firstSlice, lastSlice) # this unintentionally removes np.nan
			zMasked = zMasked.mask

			nanMasked = np.ma.masked_invalid(aicsSlabList_z) # True if [i] is np.nan
			nanMasked = nanMasked.mask

			finalEdgeMask = np.ma.mask_or(zMasked, nanMasked)

			# always one more step than I expect? Not sure why and really do not understand?
			xEdgeMasked = np.where(finalEdgeMask==True, aicsSlabList_x, np.nan)
			yEdgeMasked = np.where(finalEdgeMask==True, aicsSlabList_y, np.nan)

			# set display
			self.myEdgePlot.set_xdata(yEdgeMasked)
			self.myEdgePlot.set_ydata(xEdgeMasked)

			#self.myEdgePlot.set_linewidth(0)

		else:
			self.myEdgePlot.set_xdata([])
			self.myEdgePlot.set_ydata([])

		#
		# nodes
		if self.displayStateDict['showNodes']:

			aicsNodeList_x = self.maskedEdgesDict['aicsNodeList_x']
			aicsNodeList_y = self.maskedEdgesDict['aicsNodeList_y']
			aicsNodeList_z = self.maskedEdgesDict['aicsNodeList_z']
			aicsNodeList_nodeIdx = self.maskedEdgesDict['aicsNodeList_nodeIdx'] # use for user clicks _onpick

			zNodeMasked = np.ma.masked_inside(aicsNodeList_z, firstSlice, lastSlice) # this unintentionally removes np.nan
			zNodeMasked = zNodeMasked.mask

			xNodeMasked = np.where(zNodeMasked==True, aicsNodeList_x, np.nan)
			yNodeMasked = np.where(zNodeMasked==True, aicsNodeList_y, np.nan)

			self.myNodePlot.set_offsets(np.c_[yNodeMasked, xNodeMasked]) # flipped

		else:
			self.myNodePlot.set_offsets(np.c_[[], []])

		#
		# super important
		self.currentSlice = index # update slice

		#
		# always draw at end
		#self.canvas.draw() # with colormap, causes 'NotImplementedError: Abstract class only'
		self.canvas.draw_idle()

		#print(timeSetSlice.elapsed())

	def setSlice(self, index=None):
		#print('bStackView.setSlice()', index)

		#
		#
		self.setSlice2(index=index)
		return
		#
		#

		"""
		if index is None:
			index = self.currentSlice

		if index < 0:
			index = 0
		if index > self.mySimpleStack.numImages-1:
			index = self.mySimpleStack.numImages -1

		#showImage = True

		self.mySimpleStack.setSlice(index)

		if self.displayStateDict['showImage']:
			#if self.displaySlidingZ:
			displayThisStack = self.displayStateDict['displayThisStack']
			if self.displayStateDict['displaySlidingZ']:
				upSlices = self.options['Stack']['upSlidingZSlices']
				downSlices = self.options['Stack']['downSlidingZSlices']
				image = self.mySimpleStack.getSlidingZ(index, displayThisStack, upSlices, downSlices, self.minContrast, self.maxContrast)
			else:
				# works
				image = self.mySimpleStack.setSliceContrast(index, thisStack=displayThisStack, minContrast=self.minContrast, maxContrast=self.maxContrast)
				#print('image.shape:', image.shape)

			if self.imgplot is None:
				cmap = self.options['Stack']['colorLut'] #2**2
				# this generally works but we need to scale all the tracing?
				'''
				iLeft = 0
				iTop = 0
				iRight = 600 * 0.2
				iBottom = 600 * 0.2
				extent=[iLeft, iRight, iBottom, iTop]
				self.imgplot = self.axes.imshow(image, extent=extent, cmap=cmap)
				'''

				# no scale
				self.imgplot = self.axes.imshow(image, cmap=cmap)
			else:
				self.imgplot.set_data(image)
		else:
			if self.imgplot is not None:
				#image = self.mySimpleStack.setSliceContrast(index, thisStack=self.displayThisStack, minContrast=self.minContrast, maxContrast=self.maxContrast)
				self.imgplot.set_data(np.zeros((1,1)))

		#
		# update point annotations

		# there should always be a tracing, it might just have no points?
		'''
		if self.mySimpleStack.slabList is None:
			# no tracing
			pass
		'''

		if self.displayStateDict['showEdges']:
			# abb aics, was this
			'''
			# lines between slabs of edge
			self.myEdgePlot.set_xdata(self.maskedNodes[index]['xEdgeLines'])
			self.myEdgePlot.set_ydata(self.maskedNodes[index]['yEdgeLines'])

			# does not handle slab diameter
			tracingPenSize = self.options['Tracing']['tracingPenSize']
			self.myEdgePlot.set_markersize(tracingPenSize)
			'''

			# abb aics, faster ???
			timeEdges = bimpy.util.bTimer('time edges')
			try:
				print('aics set slice edge i:', index)
				self.maskedEdgesDict

				zNodeMasked0 = self.maskedNodes[index]['zNodeMasked0'] # this is all we need from _preComputeAllMasks
				aicsSLabList = self.maskedNodes[index]['aicsSlabList'] #
				aicsSLabList_x = self.maskedNodes[index]['aicsSlabList_x'] #
				aicsSLabList_y = self.maskedNodes[index]['aicsSlabList_y'] #
				aicsSLabList_z = self.maskedNodes[index]['aicsSlabList_z'] #
				# nodeIdxMasked size becomes (0,n) ???
				xEdgeMasked = self.mySimpleStack.slabList.x[zNodeMasked0.mask].ravel()
				yEdgeMasked = self.mySimpleStack.slabList.y[zNodeMasked0.mask].ravel()
				edgeIdxMasked = self.mySimpleStack.slabList.edgeIdx[zNodeMasked0.mask].ravel()

				print('  len(self.mySimpleStack.slabList.x)', len(self.mySimpleStack.slabList.x), self.mySimpleStack.slabList.x.shape)
				print('  LONGER with np.nan len(aicsSLabList)', len(aicsSLabList), aicsSLabList.shape)
				print('  len(zNodeMasked0)', len(zNodeMasked0), zNodeMasked0.shape)
				print('  edgeIdxMasked:', edgeIdxMasked.shape)
				print('  xEdgeMasked:', xEdgeMasked.shape)
				print('  yEdgeMasked:', xEdgeMasked.shape)

				# this does not work because we need np.nan inserted between each edge???
				xEdgeMasked = np.where(~np.isnan(edgeIdxMasked), xEdgeMasked, np.nan) #xEdgeMasked[~np.isnan(edgeIdxMasked)]
				yEdgeMasked = np.where(~np.isnan(edgeIdxMasked), yEdgeMasked, np.nan) #xEdgeMasked[~np.isnan(edgeIdxMasked)]

				print('    xEdgeMasked:', xEdgeMasked.shape)
				print('    yEdgeMasked:', yEdgeMasked.shape)

				# set display
				self.myEdgePlot.set_xdata(yEdgeMasked)
				self.myEdgePlot.set_ydata(xEdgeMasked)
			except (KeyError) as e:
				print('EXCEPTION: slice:', index, 'slab keyerror:', e)
			print('  ', timeEdges.elapsed())

		else:
			self.myEdgePlot.set_xdata([])
			self.myEdgePlot.set_ydata([])

		if self.displayStateDict['showNodes']:

			timeNodes = bimpy.util.bTimer('time nodes')
			# covid-19 build a list of colors based on nodes ['nEdges']
			#nodeIdxList = self.maskedNodes[index]['nodeMasked_nodeIdx']

			# was this
			#markersizes = self.maskedNodes[index]['nodeMasked_size'] # list of size
			#markersize = self.options['Tracing']['nodePenSize'] **2
			# was this
			#markerColor = self.options['Tracing']['nodeColor']
			# now this ... covid ... this is amazing that this works !!!!!!!!!!!
			markerColor = self.maskedNodes[index]['nodeMasked_color'] # list of size
			self.myNodePlot.set_color(markerColor)
			#self.myNodePlot.set_sizes(markersize)

			'''
			self.myNodePlot.set_offsets(np.c_[self.maskedNodes[index]['nodeMasked_x'], self.maskedNodes[index]['nodeMasked_y']])
			'''
			#print('setSlice() index:', index, 'color:', self.maskedNodes[index]['colorMasked'])
			#self.myNodePlot.set_array(self.maskedNodes[index]['colorMasked'])
			#self.myNodePlot.set_clim(3, 5)

			# abb aics, faster ???
			try:
				print('aics set nodes slice i:', index)
				zNodeMasked0 = self.maskedNodes[index]['zNodeMasked0'] # this is all we need from _preComputeAllMasks
				# nodeIdxMasked size becomes (0,n) ???
				xNodeMasked = self.mySimpleStack.slabList.x[zNodeMasked0.mask].ravel()
				yNodeMasked = self.mySimpleStack.slabList.y[zNodeMasked0.mask].ravel()
				nodeIdxMasked = self.mySimpleStack.slabList.nodeIdx[zNodeMasked0.mask].ravel()
				'''
				print('  len(zNodeMasked0)', len(zNodeMasked0), zNodeMasked0.shape)
				print('  zNodeMasked0:', zNodeMasked0.mask.shape, zNodeMasked0.data.shape)
				print('  nodeIdxMasked:', nodeIdxMasked.shape, 'internal shape:', self.mySimpleStack.slabList.nodeIdx.shape)
				'''
				xNodeMasked = xNodeMasked[~np.isnan(nodeIdxMasked)]
				yNodeMasked = yNodeMasked[~np.isnan(nodeIdxMasked)]
				'''
				print('  xNodeMasked:', xNodeMasked.shape, 'xNodeMasked:', yNodeMasked.shape)
				'''
				# set display
				self.myNodePlot.set_offsets(np.c_[yNodeMasked, xNodeMasked]) # flipped
			except (KeyError) as e:
				pass
			print('  ', timeNodes.elapsed())

		else:
			self.myNodePlot.set_offsets(np.c_[[], []])

		if self.selectedSlab() is not None:
			self.selectSlab(self.selectedSlab())

		self.currentSlice = index # update slice

		#self.canvas.draw_idle()
		self.canvas.draw()
		"""

	def keyReleaseEvent(self, event):
		self.keyIsDown = None

	# abb aics
	def keyPressEvent(self, event):
		#print('=== bStackView.keyPressEvent() event.key():', event.key())

		self.keyIsDown = event.text()
		key = event.key()

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		isControl = modifiers == QtCore.Qt.ControlModifier # on macOS, this is 'command' (e.g. open-apple)

		print('=== bStackView.keyPressEvent() key:', event.text(), 'isShift:', isShift, 'isControl:', isControl)

		if event.key() in [QtCore.Qt.Key_N]:
			print('=== user hit key "N"')
			"""
			If single node sel or single edge sel
				Show dialog to edit: (isBad, Note, type)
			"""

		elif isControl and event.key() == QtCore.Qt.Key_S:
			self.mainWindow.signal('save')

		elif event.key() in [QtCore.Qt.Key_I]:
			self.mySimpleStack.slabList._printInfo()

		elif event.key() in [QtCore.Qt.Key_Escape]:
			print('=== user hit key "esc"')
			# todo: pass to parent so we can escape out of macOS full screen
			self.cancelSelection()

		elif event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
			self.handleFitInView()

		elif event.key() == QtCore.Qt.Key_R:
			self.refreshView()

		elif event.key() in [QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal]:
			self.zoom('in')
		elif event.key() == QtCore.Qt.Key_Minus:
			self.zoom('out')

		elif event.key() == QtCore.Qt.Key_Z:
			if isShift:
				# set up/down sliding z
				currentValue = self.options['Stack']['upSlidingZSlices']
				num,ok = QtWidgets.QInputDialog.getInt(self,"Set Sliding Z", "Number of slices above and below", value=currentValue)
				if ok:
					self.options['Stack']['upSlidingZSlices'] = num
					self.options['Stack']['downSlidingZSlices'] = num

			self._toggleSlidingZ()
			#
			self.displayStateChangeSignal.emit('bSignal Sliding Z', self.displayStateDict)

		elif event.key() == QtCore.Qt.Key_T:
			'''
			if isShift:
				myDialog = myTracingDialog(self)
				result = myDialog.exec_() # show it
				if result == 1:
					showTracingAboveSlices = myDialog.get_showTracingAboveSlices()
				else:
					# was canceled
					pass
			'''
			# 'triState':, 0, # 0: all, 1: just nodes, 2: just edges, 3: none
			self.displayStateDict['triState'] += 1
			triState = self.displayStateDict['triState']
			if triState == 4:
				self.displayStateDict['triState'] = 0
				triState = 0
			if triState == 0:
				# all
				self.displayStateDict['showNodes'] = True
				self.displayStateDict['showEdges'] = True
			elif triState == 1:
				# just nodes
				self.displayStateDict['showNodes'] = True
				self.displayStateDict['showEdges'] = False
			elif triState == 2:
				# just edges
				self.displayStateDict['showNodes'] = False
				self.displayStateDict['showEdges'] = True
			elif triState == 3:
				# none
				self.displayStateDict['showNodes'] = False
				self.displayStateDict['showEdges'] = False
			#self.displayStateDict['showNodes'] = not self.displayStateDict['showNodes']
			#self.displayStateDict['showEdges'] = not self.displayStateDict['showEdges']
			self.setSlice() #refresh
			#
			self.displayStateChangeSignal.emit('bSignal Nodes', self.displayStateDict)
			self.displayStateChangeSignal.emit('bSignal Edges', self.displayStateDict)

		# ''' block quotes not allowed here '''
		#elif event.key() == QtCore.Qt.Key_N:
		#	self.showNodes = not self.showNodes
		#	self.setSlice() #refresh

		#elif event.key() == QtCore.Qt.Key_E:
		#	self.showEdges = not self.showEdges
		#	self.setSlice() #refresh

		# abb aics
		elif event.key() == QtCore.Qt.Key_J:
			event = {'type':'joinTwoEdges'}
			self.myEvent(event)

		elif event.key() in [QtCore.Qt.Key_D, QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
			#self.showDeadEnds = not self.showDeadEnds
			#self.setSlice() #refresh
			event = {'type':'deleteSelection'}
			self.myEvent(event)

		# move to next/prev slab
		elif key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			selectedSlabIdx = self.selectedSlab()
			if selectedSlabIdx is not None:
				tmpEdgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(selectedSlabIdx)
				if tmpEdgeIdx is None:
					print('warning: move to next/prev slab got bad edge idx:', tmpEdgeIdx)
					return
				tmpSlabList = self.mySimpleStack.slabList.getEdgeSlabList(tmpEdgeIdx) # abb aics, get all including nodes
				try:
					slabIdxInList = tmpSlabList.index(selectedSlabIdx)
				except (ValueError) as e:
					print('warning: bStackWidget.keyPressEvent() did not find slabIdx:', selectedSlabIdx, 'in edge', tmpEdgeIdx, 'list:', tmpSlabList)
					return
				if key ==QtCore.Qt.Key_Left:
					slabIdxInList -= 1
				elif key == QtCore.Qt.Key_Right:
					slabIdxInList += 1
				#print('  moving to slabIdxInList:', slabIdxInList)
				if slabIdxInList==0 or slabIdxInList==len(tmpSlabList)-1:
					print('  --> at end of edge', tmpEdgeIdx)
					return
				try:
					newSlabIdx = tmpSlabList[slabIdxInList]
				except (IndexError) as e:
					print('  at end of edge', tmpEdgeIdx)
					return
				print('  --> selecting slab:', newSlabIdx, 'slab number', slabIdxInList+1, 'of', len(tmpSlabList), 'in edge', tmpEdgeIdx)
				self.selectSlab(newSlabIdx, snapz=True)
			else:
				# abb aics
				if key == QtCore.Qt.Key_Left:
					self.currentSlice -= 1
				else:
					self.currentSlice += 1
				self.setSlice(self.currentSlice)
				#self.displayStateChangeSignal.emit('set slice', self.currentSlice)
				self.setSliceSignal.emit('set slice', self.currentSlice)

		# choose which stack to display
		elif event.key() == QtCore.Qt.Key_1:
			#self.displayThisStack = 'ch1'
			self.displayStateDict['displaySlidingZ'] = False
			self.displayStateDict['displayThisStack'] = 'ch1'
			self.setSlice() # just refresh
		elif event.key() == QtCore.Qt.Key_2:
			numChannels = self.mySimpleStack.numChannels
			if numChannels > 1:
				#self.displayThisStack = 'ch2'
				self.displayStateDict['displayThisStack'] = 'ch2'
				self.setSlice() # just refresh
			else:
				print('warning: stack only has', numChannels, 'channel(s)')
		elif event.key() == QtCore.Qt.Key_3:
			numChannels = self.mySimpleStack.numChannels
			if numChannels > 2:
				#self.displayThisStack = 'ch3'
				self.displayStateDict['displayThisStack'] = 'ch3'
				self.setSlice() # just refresh
			else:
				print('warning: stack only has', numChannels, 'channel(s)')


		elif event.key() == QtCore.Qt.Key_9:
			# not implemented (was for deepvess)
			if self.mySimpleStack._imagesSkel is not None:
				#self.displayThisStack = 'skel'
				self.displayStateDict['displayThisStack'] = 'skel'
				self.setSlice() # just refresh
		# should work, creates a mask from vesselucida tracing
		elif event.key() == QtCore.Qt.Key_0:
			if 1: #self.mySimpleStack._imagesMask is not None:
				#self.displayThisStack = 'mask'
				self.displayStateDict['displayThisStack'] = 'mask'
				self.setSlice() # just refresh

		elif event.key() == QtCore.Qt.Key_P:
			self.mySimpleStack.slabList._printStats()

		else:
			#print('bStackView.keyPressEvent() not handled:', event.text())
			event.setAccepted(False)

	# abb aics
	def refreshView(self):
		"""
		"""
		self._preComputeAllMasks()
		self.setSlice()
		# todo: refresh tables
		self.mainWindow.repopulateAllTables()

	def _toggleSlidingZ(self, isChecked=None):

		if isChecked is not None:
			self.displayStateDict['displaySlidingZ'] = isChecked
		else:
			self.displayStateDict['displaySlidingZ'] = not self.displayStateDict['displaySlidingZ']

		# todo: get rid of this
		thisStack = self.displayStateDict['displayThisStack']
		upSlices = self.options['Stack']['upSlidingZSlices']
		downSlices = self.options['Stack']['downSlidingZSlices']
		self.mySimpleStack.makeSlidingZ(thisStack, upSlices, downSlices)

		self.setSlice() # just refresh

		return self.displayStateDict['displaySlidingZ']

	def zoomToPoint(self, x, y):
		"""
		x/y: units are in x/y of slabList.x and slabList.y (um?)

		we need to figure out what percent of total sceneRect() this corresponds to

		matplotlib has (x,y) as (row,col)
		PyQt is reversed !!!

		for example:
			mpl_x * scene_width / image.shape[1]
		"""

		# abb aics
		# todo convert this to use a % of the total scene rect ?

		sceneRect = self.sceneRect()
		imageHeight = self.mySimpleStack.linesPerFrame
		imageWidth = self.mySimpleStack.pixelsPerLine
		xGuess = x * sceneRect.width() / imageHeight
		yGuess = y * sceneRect.height() / imageWidth

		print('  bStackView.zoomToPoint() x:', x, 'y:', y, 'xScene:', xGuess, 'yScene:', yGuess)

		self.centerOn(yGuess, xGuess) # swapped

	def zoom(self, zoom, pos=None):
		"""
		pass pos to follow mouse location
		"""
		#print('=== bStackView.zoom()', zoom)
		if zoom == 'in':
			zoomFactor = 1.2
		else:
			zoomFactor = 0.8

		# was this
		'''
		transform0 = self.transform()
		self.scale(zoomFactor,zoomFactor)
		transform1 = self.transform()
		#self.zoomToPoint(100,100)
		print('---')
		print('transform0:', transform0)
		print('transform1:', transform1)

		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!
		'''

		transform0 = self.transform()

		followMouse = pos is not None

		'''
		if event.angleDelta().y() > 0:
			zoomFactor = 1.2
		else:
			zoomFactor = 0.8
		'''

		if followMouse:
			oldPos = self.mapToScene(pos)

		#self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
		#self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)

		self.scale(zoomFactor,zoomFactor)

		#super(bStackView, self).scale(zoomFactor,zoomFactor)

		#self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		#self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

		if followMouse:
			newPos = self.mapToScene(pos)
			# Move scene to old position
			delta = newPos - oldPos

			# in previous version of Qt, this was needed
			#self.translate(delta.y(), delta.x())

		'''
		transform1 = self.transform()
		print('--- zoom()')
		print('transform0 h:', transform0.m31(), transform0)
		print('transform1 v:', transform0.m32(), transform1)
		'''

		#self.centerOn(newPos)

		#event.setAccepted(True)
		#super(bStackView,self).wheelEvent(event)

		#self.canvas.draw_idle()
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def wheelEvent(self, event):
		#if self.hasPhoto():

		#print('event.angleDelta().y():', event.angleDelta().y())

		#super().wheelEvent(event)
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		if modifiers == QtCore.Qt.ControlModifier:
			'''
			self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
			self.setResizeAnchor(QtGui.QGraphicsView.NoAnchor)
			'''

			if event.angleDelta().y() > 0:
				self.zoom('in', pos=event.pos())
			else:
				self.zoom('out', pos=event.pos())

		else:
			if event.angleDelta().y() > 0:
				self.currentSlice -= 1
			else:
				self.currentSlice += 1
			self.setSlice(self.currentSlice)
			#self.displayStateChangeSignal.emit('set slice', self.currentSlice)
			self.setSliceSignal.emit('set slice', self.currentSlice)
			#event.setAccepted(True)
		#super().wheelEvent(event)

	def mousePressEvent(self, event):
		"""
		shift+click will create a new node
		n+click (assuming there is a node selected ... will create a new edge)
		"""
		#print('=== bStackView.mousePressEvent()', event.pos())
		super().mousePressEvent(event)
		self.clickPos = event.pos()

		if event.button() == QtCore.Qt.RightButton:
			#print('bStackView.mousePressEvent() right click !!!')
			self.showRightClickMenu(event.pos())
			self.mouseReleaseEvent(event)
		#
		#super().mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		#print('=== bStackView.mouseReleaseEvent()')
		#super().mouseReleaseEvent(event)
		self.clickPos = None
		#event.setAccepted(True)
		super().mouseReleaseEvent(event)

	def mouseMoveEvent(self, event):
		#print('=== bStackView.mouseMoveEvent()', event.pos())
		#super().mouseMoveEvent(event)
		if self.clickPos is not None:
			newPos = event.pos() - self.clickPos
			#print('    newPos:', newPos)
			dx = self.clickPos.x() - newPos.x()
			dy = self.clickPos.y() - newPos.y()
			#print('    dx:', dx, 'dy:', dy)
			self.translate(dx, dy)
			'''
			self.horizontalScrollBar().setValue( self.horizontalScrollBar().value() + dx );
			self.verticalScrollBar().setValue( self.verticalScrollBar().value() + dy );
			'''
		#
		try:
			super().mouseMoveEvent(event)
		except (ModuleNotFoundError) as e:
			print('mouseMoveEvent() caught parent exception e:', e)

	def onmove_mpl(self, event):
		#print('onmove_mpl()', event.xdata, event.ydata)
		"""
		remember: this was a persistent problem that was showing up very occasionally and caused a segmentation fault.
		event.xdata and event.ydata is very occasionally None !!!!
		"""
		if event.xdata is not None and event.ydata is not None:
			thePoint = QtCore.QPoint(event.ydata, event.xdata) # swapped
			self.mainWindow.getStatusToolbar().setMousePosition(thePoint)

			'''
			# trying to get zoom to point working
			x = event.xdata
			y = event.ydata
			print('** onmove_mpl() abb aics, trying to get zoomed snap working x:', x, 'y:', y)
			scenePnt = self.mapToScene(x,y) # swapped
			print('  scenePnt:', scenePnt)

			sceneRect = self.sceneRect()
			print('  sceneRect:', sceneRect, 'w:', sceneRect.width(), 'h:', sceneRect.height())

			# in matplotlib (x,y) is (rows,cols)
			# in PyQt, pnt is (y,x)
			imageHeight = 740
			imageWidth = 740
			xGuess = x * sceneRect.width() / imageHeight
			yGuess = y * sceneRect.height() / imageWidth
			print('  my guess is xGuess:', xGuess, 'yGuess:', yGuess)
			'''

	def onclick_mpl(self, event):
		"""
		onpick() get called first
		"""

		#print('onclick_mpl()')

		if event.xdata is None or event.ydata is None:
			return

		x = event.ydata # swapped
		y = event.xdata
		z = self.currentSlice
		x = round(float(x),2) # we don't want to use <class 'numpy.float64'>
		y = round(float(y),2)
		newNodeEvent = {'type':'newNode','x':x,'y':y,'z':z}

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers & QtCore.Qt.ShiftModifier
		isControl = modifiers & QtCore.Qt.ControlModifier
		nKey = self.keyIsDown == 'n'

		if self.onpick_madeNewEdge:
			self.onpick_madeNewEdge = False
		elif nKey and self.selectedNode() is not None:
			# make a new edge
			print('\n=== bStackWidget.onclick_mpl() new edge ...')
			newNodeIdx = self.myEvent(newNodeEvent)
			newEdgeEvent = {'type':'newEdge','srcNode':self.selectedNode(), 'dstNode':newNodeIdx}
			newEdgeIdx = self.myEvent(newEdgeEvent)
			self.selectNode(None) # cancel self.selectedNode()
			self.selectEdge(newEdgeIdx) # select the new edge
			#
			myEvent = bimpy.interface.bEvent('select edge', edgeIdx=newEdgeIdx)
			self.selectEdgeSignal.emit(myEvent)

		elif isShift:
			if self.selectedEdge() is not None:
				if self.options['Panels']['showLineProfile']:
					# make a new slab
					print('\n=== bStackWidget.onclick_mpl() new slab ...')
					newSlabEvent = {'type':'newSlab','edgeIdx':self.selectedEdge(), 'x':x, 'y':y, 'z':z}
					self.myEvent(newSlabEvent)
				else:
					print('To add slabs, open the line profile panel with keyboard "l"')
			else:
				# make a new node
				print('\n=== bStackWidget.onclick_mpl() new node ...')
				self.myEvent(newNodeEvent)
		elif isControl:
			# abb aics
			# extend to multiple selections
			pass

	def onpick_mpl(self, event):
		"""
		Click to select (node, edge, slab)
		called before onclick_mpl()

		i want to be able to pick both (nodes, slabs) but need to know which one was clicked?
		"""
		# stop onpick being called twice for one mouse down
		# nodes are on top of edges, this lets us pick the node and then not the edge
		# covid-19, was previously boolean, now it is a timer

		#
		# timer to throw out second call on just one click
		# nodes are on top and will be clicked first, second click (on edge artist) will be ignored
		elapsedThreshold = 0.2 # seconds
		now = time.time()
		elapsed = now - self.onpick_lastSeconds
		#print('on pick elapsed:', elapsed, 'elapsedThreshold:', elapsedThreshold)
		if elapsed < elapsedThreshold:
			#print('onpick_mpl() took quick, elapsed:', elapsed)
			self.onpick_lastSeconds = now
			return False
		#print('elapsed:', elapsed)
		self.onpick_lastSeconds = now

		selectionType = None
		thisLine = event.artist
		if thisLine == self.myNodePlot:
			selectionType = 'nodeSelection'
		elif thisLine == self.myEdgePlot:
			selectionType = 'edgeSelection'

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers == QtCore.Qt.ShiftModifier
		isControl = modifiers == QtCore.Qt.ControlModifier # on macOS corresponds to 'command'
		isAlt = modifiers == QtCore.Qt.AltModifier # on macOS correspnds to 'control'

		nKey = self.keyIsDown == 'n'
		print('\n=== bStackView.onpick_mpl() selectionType:', selectionType, 'nKey:', nKey, 'selectionType:', selectionType, 'isShift:', isShift, 'isControl:', isControl, 'isAlt:', isAlt)
		xdata = event.mouseevent.xdata
		ydata = event.mouseevent.ydata
		ind = event.ind

		# find the first ind in bSlabList.id
		firstInd = ind[0]

		#
		# abb aics
		#print('    aics firstInd:', firstInd)
		aicsNodeList_nodeIdx = self.maskedEdgesDict['aicsNodeList_nodeIdx']
		aicsSlabList_edgeIdx = self.maskedEdgesDict['aicsSlabList_edgeIdx']
		aicsSlabList_slabIdx = self.maskedEdgesDict['aicsSlabList_slabIdx']

		# abb aics, added first clause to ctrl/command click multiple edges
		if isControl and selectionType=='edgeSelection':
			#edgeIdx = self.maskedNodes[self.currentSlice]['edgeIdxLines'][firstInd]
			edgeIdx = aicsSlabList_edgeIdx[firstInd]
			edgeIdx = int(edgeIdx)

		elif selectionType=='nodeSelection':
			# abb aics, was this
			'''
			nodeIdx = self.maskedNodes[self.currentSlice]['nodeMasked_nodeIdx'][firstInd]
			if not np.isnan(nodeIdx):
				#print('   converting to node selection')
				selectionType = 'nodeSelection'
				nodeIdx = int(round(nodeIdx)) # why is nodeIDx coming in as numpy.float64 ????
			#print('   nodeIdx:', nodeIdx, type(nodeIdx))
			'''
			nodeIdx = aicsNodeList_nodeIdx[firstInd]
			#print('    aics node idx:', nodeIdx)

		elif selectionType=='edgeSelection':
			# abb aics, was this
			'''
			edgeIdx = self.maskedNodes[self.currentSlice]['edgeIdxLines'][firstInd]
			slabIdx = self.maskedNodes[self.currentSlice]['slabIdxLines'][firstInd]
			nodeIdx = self.maskedNodes[self.currentSlice]['nodeIdxLines'][firstInd]
			#print('   edgeIdx:', edgeIdx, 'slabIdx:', slabIdx, 'is also nodeIdx:', nodeIdx)
			if not np.isnan(nodeIdx):
				#print('   converting to node selection')
				selectionType = 'nodeSelection'
				nodeIdx = int(round(nodeIdx)) # why is nodeIDx coming in as numpy.float64 ????
			'''
			slabIdx = aicsSlabList_slabIdx[firstInd]
			slabIdx = int(slabIdx)
			edgeIdx = aicsSlabList_edgeIdx[firstInd] # needs to be float because of np.nan
			edgeIdx = int(edgeIdx)
			#print('    aics edge idx:', edgeIdx)
			'''
			# check if click was actually on node
			nodeIdx = aicsNodeList_nodeIdx[firstInd]
			if not np.isnan(nodeIdx):
				print('   converting to node selection')
				selectionType = 'nodeSelection'
				nodeIdx = int(round(nodeIdx)) # why is nodeIDx coming in as numpy.float64 ????
			'''
		# was this
		#slabIdx = self.maskedNodes[self.currentSlice]['slabIdxMasked'][firstInd]
		#nodeIdx = self.maskedNodes[self.currentSlice]['nodeIdxMasked'][firstInd]
		#edgeIdx = self.maskedNodes[self.currentSlice]['edgeIdxMasked'][firstInd]

		if self.mainWindow is not None:
			#if nodeIdx >= 0:
			if selectionType=='nodeSelection':
				if nKey and self.selectedNode() is not None:
					print('   need to make a new edge to nodeIdx', nodeIdx)
					self.onpick_madeNewEdge = True
					print('\n=== bStackWidget.onpick() new edge ...')
					#newNodeIdx = self.myEvent(newNodeEvent)
					newEdgeEvent = {'type':'newEdge','srcNode':self.selectedNode(), 'dstNode':nodeIdx}
					newEdgeIdx = self.myEvent(newEdgeEvent)
					self.selectNode(None) # cancel self.selectedNode
					self.selectEdge(newEdgeIdx) # select the new edge
					#
					myEvent = bimpy.interface.bEvent('select edge', edgeIdx=newEdgeIdx, slabIdx=None)
					self.selectEdgeSignal.emit(myEvent)
				else:
					self.selectNode(nodeIdx)
					myEvent = bimpy.interface.bEvent('select node', nodeIdx=nodeIdx)
					self.selectNodeSignal.emit(myEvent)

			# abb aics, added first clause to ctrl/command click multiple edges
			elif isControl and selectionType=='edgeSelection':
				if not np.isnan(edgeIdx):
					edgeList = self.selectedEdgeList_append([edgeIdx]) # append to list
					self.selectEdgeList(edgeList)
				print('    multi edge selection with new edge', edgeIdx, 'edgeList:', edgeList)
				# emit multi edge selection
				myEvent = bimpy.interface.bEvent('append to edge selection', edgeIdx=edgeIdx)
				self.selectEdgeSignal.emit(myEvent)

			elif selectionType=='edgeSelection':
				self.selectEdge(edgeIdx, isShift=isShift, isAlt=isAlt) # abb aics added isShift=isShift
				self.selectSlab(slabIdx)
				myEvent = bimpy.interface.bEvent('select edge', edgeIdx=edgeIdx, slabIdx=slabIdx)
				self.selectEdgeSignal.emit(myEvent)

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
