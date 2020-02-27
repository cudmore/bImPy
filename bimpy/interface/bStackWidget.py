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

import bimpy

################################################################################
#class bStackWidget(QtWidgets.QMainWindow):
class bStackWidget(QtWidgets.QWidget):
	"""
	A widget to display a stack. This includes a bStackView and a bAnnotationTable.
	"""

	optionsStateChange = QtCore.Signal(str, object) # object can be a dict

	def __init__(self, mainWindow=None, parent=None, path=''):
		super(bStackWidget, self).__init__()

		if not self.optionsLoad():
			self.options_defaults()

		self.path = path

		#self.options_defaults()

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

		#
		#self.mySimpleStack = bSimpleStack(path) # backend stack
		self.mySimpleStack = bimpy.bStack(path) # backend stack
		#

		self.napariViewer = None

		self.myHBoxLayout = QtWidgets.QHBoxLayout(self)

		#
		#
		self.myFeedbackWidget = bimpy.interface.bStackFeebackWidget(self)
		self.myHBoxLayout.addWidget(self.myFeedbackWidget)#, stretch=2)
		#
		#

		self.myVBoxLayout = QtWidgets.QVBoxLayout(self)

		self.myStackView = bStackView(self.mySimpleStack, mainWindow=self) # a visual stack

		self.myContrastWidget = bimpy.interface.bStackContrastWidget(mainWindow=self)

		#self.bStackFeebackWidget = bimpy.interface.bStackFeebackWidget(mainWindow=self, numSlices=self.mySimpleStack.numSlices)

		self.myHBoxLayout2 = QtWidgets.QHBoxLayout(self)

		# a slider to set slice number
		self.mySliceSlider = myStackSlider(self.mySimpleStack.numImages)
		'''
		self.mySliceSlider = QtWidgets.QSlider(QtCore.Qt.Vertical)
		self.mySliceSlider.setMaximum(self.mySimpleStack.numImages)
		self.mySliceSlider.setInvertedAppearance(True) # so it goes from top:0 to bottom:numImages
		self.mySliceSlider.setMinimum(0)
		if self.mySimpleStack.numImages < 2:
			self.mySliceSlider.setDisabled(True)
		# use this
		#self.mySliceSlider.sliderReleased.connect
		#self.mySliceSlider.valueChanged.connect(self.sliceSliderValueChanged)
		'''

		self.myHBoxLayout2.addWidget(self.myStackView)
		self.myHBoxLayout2.addWidget(self.mySliceSlider)

		# add
		self.myVBoxLayout.addWidget(self.myContrastWidget) #, stretch=0.1)
		#self.myVBoxLayout.addWidget(self.bStackFeebackWidget) #, stretch=0.1)
		self.myVBoxLayout.addLayout(self.myHBoxLayout2) #, stretch = 9)

		self.lineProfileWidget = bimpy.interface.bLineProfileWidget(mainWindow=self)
		self.myVBoxLayout.addWidget(self.lineProfileWidget)

		self.statusToolbarWidget = bimpy.interface.bStatusToolbarWidget(mainWindow=self, numSlices=self.mySimpleStack.numSlices)
		#self.addToolBar(QtCore.Qt.BottomToolBarArea, self.statusToolbarWidget)
		self.myVBoxLayout.addWidget(self.statusToolbarWidget) #, stretch = 9)

		#
		# OLD
		#
		# todo: Need to show/hide annotation table
		#self.annotationTable = bimpy.interface.bAnnotationTable(mainWindow=self, parent=None)
		#self.myHBoxLayout.addWidget(self.annotationTable, stretch=3) #, stretch=7) # stretch=10, not sure on the units???

		#
		# NEW
		#
		# nodes
		self.nodeTable2 = bimpy.interface.bTableWidget2('nodes', self.mySimpleStack.slabList.nodeDictList)
		self.myHBoxLayout.addWidget(self.nodeTable2, stretch=3) #, stretch=7) # stretch=10, not sure on the units???
		# edges
		self.edgeTable2 = bimpy.interface.bTableWidget2('edges', self.mySimpleStack.slabList.edgeDictList)
		self.myHBoxLayout.addWidget(self.edgeTable2, stretch=3) #, stretch=7) # stretch=10, not sure on the units???
		# edits
		self.editTable2 = bimpy.interface.bTableWidget2('search', self.mySimpleStack.slabList.editDictList)
		self.myHBoxLayout.addWidget(self.editTable2, stretch=3) #, stretch=7) # stretch=10, not sure on the units???
		#
		#
		#

		'''
		# 20200211
		if self.mySimpleStack.slabList is None:
			self.annotationTable.hide()
			self.showLeftControlBar = False
		else:
			pass
			#self.annotationTable.hide()
		'''

		# vertical layout for contrast/feedback/image
		self.myHBoxLayout.addLayout(self.myVBoxLayout, stretch=5) #, stretch=7) # stretch=10, not sure on the units???

		#
		# signals and slots

		#
		# listen to self.bStackFeebackWidget
		#self.bStackFeebackWidget.clickStateChange.connect(self.myStackView.slot_StateChange)
		#
		# listen to self.myStackView
		#self.myStackView.displayStateChange.connect(self.bStackFeebackWidget.slot_StateChange)
		self.myStackView.setSliceSignal.connect(self.mySliceSlider.slot_UpdateSlice)
		#self.myStackView.setSliceSignal.connect(self.bStackFeebackWidget.slot_StateChange)
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
		self.mySliceSlider.updateSliceSignal.connect(self.myStackView.slot_StateChange)
		#self.mySliceSlider.updateSliceSignal.connect(self.bStackFeebackWidget.slot_StateChange)
		self.mySliceSlider.updateSliceSignal.connect(self.statusToolbarWidget.slot_StateChange)
		self.mySliceSlider.updateSliceSignal.connect(self.myContrastWidget.slot_setSlice)
		#
		# listen to self.annotationTable
		'''
		self.annotationTable.selectNodeSignal.connect(self.myStackView.slot_selectNode) # change to slot_selectNode ???
		self.annotationTable.selectEdgeSignal.connect(self.myStackView.slot_selectEdge) # change to slot_selectNode ???
		'''
		self.nodeTable2.selectRowSignal.connect(self.myStackView.slot_selectNode)
		self.edgeTable2.selectRowSignal.connect(self.myStackView.slot_selectEdge)
		self.editTable2.selectRowSignal.connect(self.myStackView.slot_selectEdge)
		#
		self.nodeTable2.selectRowSignal.connect(self.statusToolbarWidget.slot_StateChange2)
		self.edgeTable2.selectRowSignal.connect(self.statusToolbarWidget.slot_StateChange2)
		self.nodeTable2.selectRowSignal.connect(self.mySliceSlider.slot_UpdateSlice2)
		self.edgeTable2.selectRowSignal.connect(self.mySliceSlider.slot_UpdateSlice2)
		self.nodeTable2.selectRowSignal.connect(self.myContrastWidget.slot_UpdateSlice2)
		self.edgeTable2.selectRowSignal.connect(self.myContrastWidget.slot_UpdateSlice2)
		#
		# listen to edit table, self.
		'''
		self.annotationTable.myEditTableWidget.selectEdgeSignal.connect(self.myStackView.slot_selectEdge)
		self.annotationTable.myEditTableWidget.selectEdgeSignal.connect(self.annotationTable.slot_selectEdge)
		'''
		#
		# listen to bStackContrastWidget
		self.myContrastWidget.contrastChangeSignal.connect(self.myStackView.slot_contrastChange)

		self.updateDisplayedWidgets()

		self.move(750,100)
		#self.resize(2000, 1000)
		#self.resize(2000, 1000)
		self.resize(1500, 512)

		self.myStackView.setSlice(0)

	def getStackView(self):
		return self.myStackView

	'''
	def getFeedbackWidget(self):
		return self.bStackFeebackWidget
	'''

	# todo: remove
	def slot_StateChange_(self, signalName, signalValue):
		print('bStackWidget.slot_StateChange() signalName:', signalName, 'signalValue:', signalValue)
		#if signalName=='set slice':
		#	self.mySliceSlider.setValue(signalValue)

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
			self.bStackFeebackWidget.show()
		else:
			self.bStackFeebackWidget.hide()
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
		print('   === bStackWidget.signal()', 'signal:', signal, 'value:', value)

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

		if signal == 'update line profile':
			# value is profileDIct
			'''
				profileDict = {
					'ySlabPlot': ySlabPlot,
					'xSlabPlot': xSlabPlot,
					'slice': self.currentSlice,
				}
			'''
			self.lineProfileWidget.update(value)

		if signal == 'save':
			self.mySimpleStack.saveAnnotations()
		if signal == 'load':
			self.mySimpleStack.loadAnnotations()
			self.nodeTable2.populate(self.mySimpleStack.slabList.nodeDictList)
			self.edgeTable2.populate(self.mySimpleStack.slabList.edgeDictList)
			self.editTable2.populate(self.mySimpleStack.slabList.editDictList)
		if signal == 'load_xml':
			self.mySimpleStack.loadAnnotations_xml()

	def optionsChange(self, key1, key2, value):
		self.options[key1][key2] = value
		self.optionsStateChange.emit('')

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

		elif event.key() in [QtCore.Qt.Key_F]:
			self.options['Panels']['showFeedback'] = not self.options['Panels']['showFeedback']
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
		print('   [: show/hide list of annotations')
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

	def options_defaults(self):
		print('bStackWidget.options_defaults()')

		self.options = OrderedDict()

		"""
		Possible values are: Accent, Accent_r, Blues, Blues_r, BrBG, BrBG_r, BuGn, BuGn_r, BuPu, BuPu_r, CMRmap, CMRmap_r, Dark2, Dark2_r, GnBu, GnBu_r, Greens, Greens_r, Greys, Greys_r, OrRd, OrRd_r, Oranges, Oranges_r, PRGn, PRGn_r, Paired, Paired_r, Pastel1, Pastel1_r, Pastel2, Pastel2_r, PiYG, PiYG_r, PuBu, PuBuGn, PuBuGn_r, PuBu_r, PuOr, PuOr_r, PuRd, PuRd_r, Purples, Purples_r, RdBu, RdBu_r, RdGy, RdGy_r, RdPu, RdPu_r, RdYlBu, RdYlBu_r, RdYlGn, RdYlGn_r, Reds, Reds_r, Set1, Set1_r, Set2, Set2_r, Set3, Set3_r, Spectral, Spectral_r, Wistia, Wistia_r, YlGn, YlGnBu, YlGnBu_r, YlGn_r, YlOrBr, YlOrBr_r, YlOrRd, YlOrRd_r, afmhot, afmhot_r, autumn, autumn_r, binary, binary_r, bone, bone_r, brg, brg_r, bwr, bwr_r, cividis, cividis_r, cool, cool_r, coolwarm, coolwarm_r, copper, copper_r, cubehelix, cubehelix_r, flag, flag_r, gist_earth, gist_earth_r, gist_gray, gist_gray_r, gist_heat, gist_heat_r, gist_ncar, gist_ncar_r, gist_rainbow, gist_rainbow_r, gist_stern, gist_stern_r, gist_yarg, gist_yarg_r, gnuplot, gnuplot2, gnuplot2_r, gnuplot_r, gray, gray_r, hot, hot_r, hsv, hsv_r, inferno, inferno_r, jet, jet_r, magma, magma_r, nipy_spectral, nipy_spectral_r, ocean, ocean_r, pink, pink_r, plasma, plasma_r, prism, prism_r, rainbow, rainbow_r, seismic, seismic_r, spring, spring_r, summer, summer_r, tab10, tab10_r, tab20, tab20_r, tab20b, tab20b_r, tab20c, tab20c_r, terrain, terrain_r, twilight, twilight_r, twilight_shifted, twilight_shifted_r, viridis, viridis_r, winter, winter_r
		"""

		self.options['Stack'] = OrderedDict()
		self.options['Stack'] = OrderedDict({
			'colorLut': 'gray',
			'upSlidingZSlices': 5,
			'downSlidingZSlices': 5,
			})

		self.options['Tracing'] = OrderedDict()
		self.options['Tracing'] = OrderedDict({
			'nodePenSize': 5, #**2,
			'nodeColor': 'r',
			'nodeSelectionPenSize': 7, #**2,
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
			#'showFeedback': False,
			'showStatus': True,
			'showLineProfile': False,
			})

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
			return True
		else:
			return False

	def optionsFile(self):
		myPath = os.path.dirname(os.path.abspath(__file__))
		optionsFilePath = os.path.join(myPath,'options.json')
		return optionsFilePath

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
		self.setInvertedAppearance(True) # so it goes from top:0 to bottom:numImages
		self.setMinimum(0)
		if numSlices < 2:
			self.setDisabled(True)

		self.sliderMoved.connect(self.updateSlice_Signal)
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

	displayStateChange = QtCore.Signal(str, object) # object can be a dict
	setSliceSignal = QtCore.Signal(str, object)
	selectNodeSignal = QtCore.Signal(object)
	selectEdgeSignal = QtCore.Signal(object)
	selectSlabSignal = QtCore.Signal(object)
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

		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.showRightClickMenu)

		self.onpick_alreadypicked = False
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
			'showNodes': True,
			'showEdges': True,
			'showDeadEnds': True,

			'mySelectedNode': None,
			'mySelectedEdge': None,
			'mySelectedSlab': None,
		}

		self._preComputeAllMasks()

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

		self.displayStateChange.emit('num slices', self.mySimpleStack.numImages)

	#@property
	def selectedNode(self, nodeIdx=-1):
		if nodeIdx is not -1:
			self.displayStateDict['mySelectedNode'] = nodeIdx
		return self.displayStateDict['mySelectedNode']

	def selectedEdge(self, edgeIdx=-1):
		if edgeIdx is not -1:
			self.displayStateDict['mySelectedEdge'] = edgeIdx
		return self.displayStateDict['mySelectedEdge']

	def selectedSlab(self, slabIdx=-1):
		if slabIdx is not -1:
			self.displayStateDict['mySelectedSlab'] = slabIdx
		return self.displayStateDict['mySelectedSlab']

	@property
	def options(self):
		return self.mainWindow.options

	def showRightClickMenu(self,pos):
		"""
		Show a right click menu to perform action including toggle interface on/off

		todo: building and then responding to menu is too hard coded here, should generalize???
		"""
		menu = QtWidgets.QMenu()

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
			# add to menu
			menuAction = menu.addAction(currentAction)

		menu.addSeparator()

		#
		# panels

		annotationsAction = QtWidgets.QAction('Left Toolbar', self, checkable=True)
		annotationsAction.setChecked(self.options['Panels']['showLeftToolbar'])
		annotationsAction.setShortcuts('[')
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
		annotationsAction = QtWidgets.QAction('Search', self, checkable=True)
		annotationsAction.setChecked(self.options['Panels']['showSearch'])
		tmpMenuAction = menu.addAction(annotationsAction)

		# contrast
		contrastAction = QtWidgets.QAction('Contrast', self, checkable=True)
		contrastAction.setChecked(self.options['Panels']['showContrast'])
		tmpMenuAction = menu.addAction(contrastAction)

		# status toolbar
		annotationsAction = QtWidgets.QAction('Status', self, checkable=True)
		annotationsAction.setChecked(self.options['Panels']['showStatus'])
		tmpMenuAction = menu.addAction(annotationsAction)

		# line profile toolbar
		annotationsAction = QtWidgets.QAction('Line Profile', self, checkable=True)
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
		userAction = menu.exec_(self.mapToGlobal(pos))
		if userAction is None:
			# abort when no menu selected
			return
		userActionStr = userAction.text()
		print('=== bStackView.showRightClickMenu() userActionStr:', userActionStr)
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
		if userActionStr == 'Image':
			self.displayStateDict['showImage'] = not self.displayStateDict['showImage']
		elif userActionStr == 'Sliding Z':
			self.displayStateDict['displaySlidingZ'] = not self.displayStateDict['displaySlidingZ']
		elif userActionStr == 'Nodes':
			self.displayStateDict['showNodes'] = not self.displayStateDict['showNodes']
		elif userActionStr == 'Edges':
			self.displayStateDict['showEdges'] = not self.displayStateDict['showEdges']

		#
		# toolbars
		elif userActionStr == 'Left Toolbar':
			self.options['Panels']['showLeftToolbar'] = not self.options['Panels']['showLeftToolbar']
			self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Contrast':
			self.options['Panels']['showContrast'] = not self.options['Panels']['showContrast']
			self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Node List':
			self.options['Panels']['showNodeList'] = not self.options['Panels']['showNodeList']
			self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Edge List':
			self.options['Panels']['showEdgeList'] = not self.options['Panels']['showEdgeList']
			self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Search':
			self.options['Panels']['showSearch'] = not self.options['Panels']['showSearch']
			self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Status':
			self.options['Panels']['showStatus'] = not self.options['Panels']['showStatus']
			self.mainWindow.updateDisplayedWidgets()
		elif userActionStr == 'Line Profile':
			self.options['Panels']['showLineProfile'] = not self.options['Panels']['showLineProfile']
			self.mainWindow.updateDisplayedWidgets()

		# other
		elif userActionStr == 'Options':
			optionsDialog = bimpy.interface.bOptionsDialog(self, self.mainWindow)
		elif userActionStr == 'Napari':
			self.mainWindow.openNapari()
		elif userActionStr == 'Refresh':
			self._preComputeAllMasks()
			self.setSlice()

		else:
			userSelectedMenu = False

		# emit a signal
		# todo: this is emitting when self.displayStateDict is not changing, e.g. for user action 'Contrast' and 'Annotations'
		if userSelectedMenu:
			self.setSlice() # update
			self.displayStateChange.emit(signalName, self.displayStateDict)

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
		nodeIdx = myEvent.nodeIdx
		snapz = myEvent.snapz
		isShift = myEvent.isShift
		self.selectNode(nodeIdx, snapz=snapz, isShift=isShift)

	def slot_selectEdge(self, myEvent):
		print('bStackView.slot_selectEdge() myEvent:', myEvent)
		edgeList = myEvent.edgeList
		if len(edgeList)>0:
			# select a list of edges
			self.selectEdgeList(edgeList, snapz=True)
		else:
			# select a single edge
			edgeIdx = myEvent.edgeIdx
			snapz = myEvent.snapz
			isShift = myEvent.isShift
			self.selectEdge(edgeIdx, snapz=snapz, isShift=isShift)

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
		if event['type']=='newNode':
			x = event['x']
			y = event['y']
			z = event['z']
			print('=== bStackView.myEvent() ... new node x:', x, 'y:', y, 'z:', z)
			newNodeIdx = self.mySimpleStack.slabList.newNode(x,y,z)

			# todo: slect new node

			self._preComputeAllMasks(fromSlice=z)
			self.setSlice() #refresh
			theRet = newNodeIdx
			#
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

			edgeDict = self.mySimpleStack.slabList.getEdge(newEdgeIdx)
			myEvent = bimpy.interface.bEvent('newEdge', edgeIdx=newEdgeIdx, edgeDict=edgeDict)
			myEvent._srcNodeDict = self.mySimpleStack.slabList.getNode(srcNode)
			myEvent._dstNodeDict = self.mySimpleStack.slabList.getNode(dstNode)
			self.tracingEditSignal.emit(myEvent)

		elif event['type']=='newSlab':
			edgeIdx = event['edgeIdx']
			x = event['x']
			y = event['y']
			z = event['z']
			newSlabIdx = self.mySimpleStack.slabList.newSlab(edgeIdx, x, y, z)
			self._preComputeAllMasks(fromCurrentSlice=True)
			self.selectedSlab(newSlabIdx) # self.setSlice() will draw new slab
			self.setSlice() #refresh
			theRet = newSlabIdx

			# todo: emit slab selection

		elif event['type']=='deleteSelection':
			if self.selectedNode() is not None:
				#delete node, only if it does not have edges !!!
				deleteNodeIdx = self.selectedNode()
				deleteNodeDict = self.mySimpleStack.slabList.getNode(self.selectedNode())
				print('\n=== bStackView.myEvent() ... delete node:', deleteNodeIdx, deleteNodeDict)
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

			elif self.selectedEdge() is not None:
				deleteEdgeIdx = self.selectedEdge()
				deleteEdgeDict = self.mySimpleStack.slabList.getEdge(self.selectedEdge())
				print('\n=== bStackView.myEvent() ... delete edge:', self.selectedEdge(), deleteEdgeDict)
				self.mySimpleStack.slabList.deleteEdge(self.selectedEdge())
				self.selectEdge(None)
				self.selectSlab(None)
				doUpdate = True
				#
				myEvent = bimpy.interface.bEvent('deleteEdge', edgeIdx=deleteEdgeIdx, edgeDict=deleteEdgeDict)
				self.tracingEditSignal.emit(myEvent)
				#
				myEvent = bimpy.interface.bEvent('select selectEdge', edgeIdx=None, slabIdx=None)
				self.selectEdgeSignal.emit(myEvent)
		else:
			print('bStackView.myEvent() not understood event:', event)
		# finalize
		if doUpdate:
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
			print('bStackView.selectNode() nodeIdx:', nodeIdx)
			self.selectedNode(None)
			self.myNodeSelectionPlot.set_offsets(np.c_[[], []])
		else:
			if self.mySimpleStack.slabList is not None:
				print('   bStackView.selectNode() nodeIdx:', nodeIdx, self.mySimpleStack.slabList.getNode(nodeIdx))
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
			node = self.mySimpleStack.slabList.nodeDictList[nodeIdx]
			edgeList = node['edgeList']
			self.selectEdgeList(edgeList)
		'''
		if nodeIdx is not None:
			modifiers = QtWidgets.QApplication.keyboardModifiers()
			isShift = modifiers == QtCore.Qt.ShiftModifier
			if isShift:
				node = self.mySimpleStack.slabList.nodeDictList[nodeIdx]
				edgeList = node['edgeList']
				self.selectEdgeList(edgeList)
		'''

	def selectEdgeList(self, edgeList, thisColorList=None, snapz=False):
		if snapz:
			firstEdge = edgeList[0]
			z = self.mySimpleStack.slabList.edgeDictList[firstEdge]['z']
			z = int(z)
			self.setSlice(z)

		colors = ['r', 'g', 'b']
		slabList = []
		colorList = []
		colorIdx = 0
		for idx, edgeIdx in enumerate(edgeList):
			slabs = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
			slabList += slabs
			if thisColorList is not None:
				colorList += [thisColorList[idx] for slab in slabs]
			else:
				colorList += [colors[colorIdx] for slab in slabs]
			colorIdx += 1
			if colorIdx==len(colors)-1:
				colorIdx = 0
		#print('selectEdgeList() slabList:', slabList)
		xMasked = self.mySimpleStack.slabList.x[slabList] # flipped
		yMasked = self.mySimpleStack.slabList.y[slabList]
		self.myEdgeSelectionPlot.set_offsets(np.c_[yMasked, xMasked])
		self.myEdgeSelectionPlot.set_color(colorList)

		QtCore.QTimer.singleShot(10, lambda:self.flashEdgeList(edgeList, True))

		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!
		#QtCore.QTimer.singleShot(10, lambda:self.flashEdge(edgeIdx, True))

	def selectEdge(self, edgeIdx, snapz=False, isShift=False):
		if edgeIdx is None:
			print('bStackView.selectEdge() edgeIdx:', edgeIdx, 'snapz:', snapz)
			#markersize = 10
			#self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color='c', s=markersize, picker=True)
			self.selectedEdge(None)
			#self.selectedSlab(None)
			self.myEdgeSelectionPlot.set_offsets(np.c_[[], []])
		else:
			self.selectedEdge(edgeIdx)

			if self.mySimpleStack.slabList is not None:
				theseIndices = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)

				print('bStackView.selectEdge() edgeIdx:', edgeIdx, 'snapz:', snapz, 'edgeDIct:', self.mySimpleStack.slabList.getEdge(edgeIdx))
				#print('      theseIndices:', theseIndices)
				# todo: add option to snap to a z
				# removed this because it was confusing
				if snapz:
					'''
					z = self.mySimpleStack.slabList.z[theseIndices[0]][0] # not sure why i need trailing [0] ???
					z = int(z)
					'''
					z = self.mySimpleStack.slabList.edgeDictList[edgeIdx]['z']
					z = int(z)
					self.setSlice(z)

					# snap to point
					# get the (x,y) of the middle slab
					tmpEdgeDict = self.mySimpleStack.slabList.getEdge(edgeIdx)
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
			if isShift:
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

	def selectSlab(self, slabIdx, snapz=False):
		if self.mySimpleStack.slabList is None:
			return
		#print('bStackView.selectSlab() slabIdx:', type(slabIdx), slabIdx)

		if slabIdx is None or np.isnan(slabIdx):
			#print('   bStackView.selectSlab() CANCEL slabIdx:', slabIdx, 'snapz:', snapz)
			#markersize = 10
			#self.myEdgeSelectionPlot = self.axes.scatter([], [], marker='o', color='c', s=markersize, picker=True)
			self.selectedSlab(None)
			self.mySlabSelectionPlot.set_offsets(np.c_[[], []])
			self.mySlabLinePlot.set_xdata([])
			self.mySlabLinePlot.set_ydata([])
		else:
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

		self.canvas.draw()
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
			print('warning: bStackView.selectSlab() got bad edgeIdx:', edgeIdx)
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
		'''
		myEvent = bimpy.interface.bEvent(slabIdx=slabIdx)
		self.selectSlabSignal.emit(myEvent)
		'''

	def _preComputeAllMasks(self, fromSlice=None, fromCurrentSlice=False):
		"""
		Precompute all masks once. When user scrolls through slices this is WAY faster
		On new/delete (node, edge), just compute slices within +/- show tracing

		Parameter:
			fromCurrentSlice trumps fromSlice
		"""
		startSeconds = time.time()

		if self.mySimpleStack.slabList is None:
			return

		recomputeAll = False
		if fromSlice is None and not fromCurrentSlice:
			#recreate all
			self.maskedNodes = []
			recomputeAll = True

		showTracingAboveSlices = self.options['Tracing']['showTracingAboveSlices']
		showTracingBelowSlices = self.options['Tracing']['showTracingBelowSlices']

		markersize = self.options['Tracing']['nodePenSize'] **2

		sliceRange = range(self.mySimpleStack.numImages)
		if fromCurrentSlice:
			fromSlice = self.currentSlice
		if fromSlice is not None:
			sliceRange = range(fromSlice-showTracingAboveSlices, fromSlice+showTracingBelowSlices)
		#for i in range(self.mySimpleStack.numImages):
		print('_preComputeAllMasks() computing masks for slices:', sliceRange, 'recomputeAll:', recomputeAll)
		for i in sliceRange:
			# when using fromSlice
			if i<0 or i>self.mySimpleStack.numImages-1:
				continue

			upperz = i - self.options['Tracing']['showTracingAboveSlices']
			lowerz = i + self.options['Tracing']['showTracingBelowSlices']

			#if self.mySimpleStack.slabList is not None:
			#
			# nodes
			zNodeMasked = np.ma.masked_outside(self.mySimpleStack.slabList.z, upperz, lowerz)
			if len(zNodeMasked) > 0:
				xNodeMasked = self.mySimpleStack.slabList.y[~zNodeMasked.mask] # swapping
				yNodeMasked = self.mySimpleStack.slabList.x[~zNodeMasked.mask]
				dMasked = self.mySimpleStack.slabList.d[~zNodeMasked.mask]
				nodeIdxMasked = self.mySimpleStack.slabList.nodeIdx[~zNodeMasked.mask]
				edgeIdxMasked = self.mySimpleStack.slabList.edgeIdx[~zNodeMasked.mask]
				#slabIdxMasked = self.mySimpleStack.slabList.slabIdx[~zNodeMasked.mask]

				nodeMasked_x = xNodeMasked[~np.isnan(nodeIdxMasked)]
				nodeMasked_y = yNodeMasked[~np.isnan(nodeIdxMasked)]
				nodeMasked_nodeIdx = nodeIdxMasked[~np.isnan(nodeIdxMasked)]
				nodeMasked_size = [markersize for tmpx in xNodeMasked]

				nodeMasked_x = nodeMasked_x.ravel()
				nodeMasked_y = nodeMasked_y.ravel()
				nodeMasked_nodeIdx = nodeMasked_nodeIdx.ravel().astype(int)

				#
				# to draw lines on edges, make a disjoint list (seperated by nan
				xEdgeLines = []
				yEdgeLines = []
				dEdgeLines = []
				edgeIdxLines = []
				slabIdxLines = []
				nodeIdxLines = [] # to intercept clicks on edge that are also node
				for edgeIdx, edge in enumerate(self.mySimpleStack.slabList.edgeDictList):
					# slabList will include srcNode/dstNode as slabs
					slabList = self.mySimpleStack.slabList.getEdgeSlabList(edgeIdx)
					# decide if the slabs are within (upperz, lowerz)
					for slab in slabList:
						zSlab = self.mySimpleStack.slabList.z[slab]
						if zSlab>upperz and zSlab<lowerz:
							# include
							xEdgeLines.append(self.mySimpleStack.slabList.y[slab]) # flipped
							yEdgeLines.append(self.mySimpleStack.slabList.x[slab])
							dEdgeLines.append(self.mySimpleStack.slabList.d[slab])
							edgeIdxLines.append(edgeIdx)
							slabIdxLines.append(slab)
							nodeIdxLines.append(self.mySimpleStack.slabList.nodeIdx[slab])
						else:
							# exclude
							xEdgeLines.append(np.nan)
							yEdgeLines.append(np.nan)
							dEdgeLines.append(np.nan)
							edgeIdxLines.append(np.nan)
							slabIdxLines.append(np.nan)
							nodeIdxLines.append(np.nan)
					xEdgeLines.append(np.nan)
					yEdgeLines.append(np.nan)
					dEdgeLines.append(np.nan)
					edgeIdxLines.append(np.nan)
					slabIdxLines.append(np.nan)
					nodeIdxLines.append(np.nan)

			else:
				# len(zNodeMasked)<1
				nodeMasked_x = []
				nodeMasked_y = []
				nodeMasked_nodeIdx = []
				nodeMasked_size = []

				xEdgeLines = []
				yEdgeLines = []
				dEdgeLines = []
				edgeIdxLines = []
				slabIdxLines = []
				nodeIdxLines = []

			maskedNodeDict = {
				'zNodeMasked': zNodeMasked,
				'nodeMasked_x': nodeMasked_x,
				'nodeMasked_y': nodeMasked_y,
				'nodeMasked_nodeIdx': nodeMasked_nodeIdx,
				'nodeMasked_size': nodeMasked_size,

				'xEdgeLines': xEdgeLines,
				'yEdgeLines': yEdgeLines,
				'dEdgeLines': dEdgeLines,
				'edgeIdxLines': edgeIdxLines,
				'slabIdxLines': slabIdxLines,
				'nodeIdxLines': nodeIdxLines,
			}

			# update
			if fromSlice is not None:
				#print('   updating slide i:', i)
				self.maskedNodes[i] = maskedNodeDict
			else:
				#print('   appending i:', i)
				self.maskedNodes.append(maskedNodeDict)

			#
			# slabs/edges dead ends
			'''
			maskedDeadEndDict = {
				'zMasked': [],
				'xMasked': [],
				'yMasked': [],
			}
			for edgeDict in self.mySimpleStack.slabList.edgeDictList:
				if edgeDict['preNode'] is None:
					# include dead end
					# get the z of the first slab
					firstSlabIdx = edgeDict['slabList'][0]
					tmpz = self.mySimpleStack.slabList.z[firstSlabIdx]
					if tmpz > upperz and tmpz < lowerz:
						tmpx = self.mySimpleStack.slabList.x[firstSlabIdx]
						tmpy = self.mySimpleStack.slabList.y[firstSlabIdx]
						maskedDeadEndDict['yMasked'].append(tmpx) # swapping
						maskedDeadEndDict['xMasked'].append(tmpy)
						maskedDeadEndDict['zMasked'].append(tmpz)
				if edgeDict['postNode'] is None:
					# include dead end
					# get the z of the last slab
					lastSlabIdx = edgeDict['slabList'][-1]
					tmpz = self.mySimpleStack.slabList.z[lastSlabIdx]
					if tmpz > upperz and tmpz < lowerz:
						tmpx = self.mySimpleStack.slabList.x[lastSlabIdx]
						tmpy = self.mySimpleStack.slabList.y[lastSlabIdx]
						maskedDeadEndDict['yMasked'].append(tmpx) # swapping
						maskedDeadEndDict['xMasked'].append(tmpy)
						maskedDeadEndDict['zMasked'].append(tmpz)
			self.maskedDeadEnds.append(maskedDeadEndDict)
			'''

			#print('slice', i, '_preComputeAllMasks() len(x):', len(xMasked), 'len(y)', len(yMasked))
		stopSeconds= time.time()
		print('   took', round(stopSeconds-startSeconds,2), 'seconds')

	# todo: remove recursion
	def setSlice(self, index=None):
		#print('bStackView.setSlice()', index)

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
			# lines between slabs of edge
			self.myEdgePlot.set_xdata(self.maskedNodes[index]['xEdgeLines'])
			self.myEdgePlot.set_ydata(self.maskedNodes[index]['yEdgeLines'])

			# does not handle slab diameter
			tracingPenSize = self.options['Tracing']['tracingPenSize']
			self.myEdgePlot.set_markersize(tracingPenSize)
		else:
			self.myEdgePlot.set_xdata([])
			self.myEdgePlot.set_ydata([])

		if self.displayStateDict['showNodes']:

			markersizes = self.maskedNodes[index]['nodeMasked_size'] # list of size
			markerColor = self.options['Tracing']['nodeColor']
			self.myNodePlot.set_color(markerColor)
			self.myNodePlot.set_sizes(markersizes)

			self.myNodePlot.set_offsets(np.c_[self.maskedNodes[index]['nodeMasked_x'], self.maskedNodes[index]['nodeMasked_y']])
			#print('setSlice() index:', index, 'color:', self.maskedNodes[index]['colorMasked'])
			#self.myNodePlot.set_array(self.maskedNodes[index]['colorMasked'])
			#self.myNodePlot.set_clim(3, 5)
		else:
			self.myNodePlot.set_offsets(np.c_[[], []])


		if self.selectedSlab() is not None:
			self.selectSlab(self.selectedSlab())

		self.currentSlice = index # update slice

		self.canvas.draw_idle()

	def zoomToPoint(self, x, y):
		# todo convert this to use a % of the total image ?
		print('bStackView.zoomToPoint() x:', x, 'y:', y)

		scenePnt = self.mapToScene(y,x) # swapped
		print('   rect:', self.sceneRect())
		print('   scenePnt:', scenePnt)

		myTransform = self.transform()
		print('    myTransform:', myTransform)
		print('    translation:', myTransform.m31(), myTransform.m32())
		print('    scale:', myTransform.m11(), myTransform.m22())
		#self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
		#self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)

		'''
		tmp = x
		x = y
		y = tmp

		#self.centerOn(scenePnt)
		#x /= myTransform.m11() # m11() is horizontal, m22() is vertical
		#y /= myTransform.m22()
		dx = myTransform.m31()
		dy = myTransform.m32()

		x = myTransform.m11()*x + myTransform.m21()*y + dx
		y = myTransform.m22()*y + myTransform.m12()*x + dx
		'''

		self.centerOn(y, x) #

		#self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		#self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

		# was working but since adding bStackFeedback (removing stretch) is broken?
		#self.centerOn(y, x) # swapped

		'''
		#self.canvas.draw_idle()
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!
		'''

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

		transform1 = self.transform()
		print('--- zoom()')
		print('transform0 h:', transform0.m31(), transform0)
		print('transform1 v:', transform0.m32(), transform1)

		#self.centerOn(newPos)

		#event.setAccepted(True)
		#super(bStackView,self).wheelEvent(event)

		#self.canvas.draw_idle()
		self.canvas.draw()
		self.repaint() # this is updating the widget !!!!!!!!

	def keyReleaseEvent(self, event):
		self.keyIsDown = None

	def keyPressEvent(self, event):
		#print('=== bStackView.keyPressEvent() event.key():', event.key())

		self.keyIsDown = event.text()
		key = event.key()

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers & QtCore.Qt.ShiftModifier

		if event.key() in [QtCore.Qt.Key_Escape]:
			print('=== user hit key "esc"')
			self.selectNode(None)
			self.selectEdge(None)
			self.selectSlab(None)
			#
			myEvent = bimpy.interface.bEvent('select node', nodeIdx=None)
			self.selectNodeSignal.emit(myEvent)
			myEvent = bimpy.interface.bEvent('select edge', edgeIdx=None)
			self.selectEdgeSignal.emit(myEvent)

			# todo: pass to parent so we can escape out of macOS full screen

		elif event.key() == QtCore.Qt.Key_R:
			self._preComputeAllMasks()
			self.setSlice()

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
			self.displayStateChange.emit('bSignal Sliding Z', self.displayStateDict)

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
			self.displayStateDict['showNodes'] = not self.displayStateDict['showNodes']
			self.displayStateDict['showEdges'] = not self.displayStateDict['showEdges']
			self.setSlice() #refresh
			#
			self.displayStateChange.emit('bSignal Nodes', self.displayStateDict)
			self.displayStateChange.emit('bSignal Edges', self.displayStateDict)

		# ''' block quotes not allowed here '''
		#elif event.key() == QtCore.Qt.Key_N:
		#	self.showNodes = not self.showNodes
		#	self.setSlice() #refresh

		#elif event.key() == QtCore.Qt.Key_E:
		#	self.showEdges = not self.showEdges
		#	self.setSlice() #refresh

		elif event.key() in [QtCore.Qt.Key_D, QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
			#self.showDeadEnds = not self.showDeadEnds
			#self.setSlice() #refresh
			event = {'type':'deleteSelection'}
			self.myEvent(event)

		# move to next/prev slab
		elif key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]:
			if self.selectedSlab() is not None:
				tmpEdgeIdx = self.mySimpleStack.slabList.getSlabEdgeIdx(self.selectedSlab())
				if tmpEdgeIdx is None:
					print('warning: move to next/prev slab got bad edge idx:', tmpEdgeIdx)
					return
				tmpSlabList = self.mySimpleStack.slabList.getEdgeSlabList(tmpEdgeIdx)
				slabIdxInList = tmpSlabList.index(self.selectedSlab())
				if slabIdxInList==0 or slabIdxInList==len(tmpSlabList)-1:
					return
				if key ==QtCore.Qt.Key_Left:
					slabIdxInList -= 1
				elif key == QtCore.Qt.Key_Right:
					slabIdxInList += 1
				newSlabIdx = tmpSlabList[slabIdxInList]
				self.selectSlab(newSlabIdx, snapz=True)

		# choose which stack to display
		elif event.key() == QtCore.Qt.Key_1:
			#self.displayThisStack = 'ch1'
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

		# not implemented (was for deepvess)
		elif event.key() == QtCore.Qt.Key_9:
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

	def _toggleSlidingZ(self, isChecked=None):

		if isChecked is not None:
			self.displayStateDict['displaySlidingZ'] = isChecked
		else:
			self.displayStateDict['displaySlidingZ'] = not self.displayStateDict['displaySlidingZ']

		self.setSlice() # just refresh

		return self.displayStateDict['displaySlidingZ']

	def wheelEvent(self, event):
		#if self.hasPhoto():

		#print('event.angleDelta().y():', event.angleDelta().y())

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

			'''
			transform0 = self.transform()

			oldPos = self.mapToScene(event.pos())
			if event.angleDelta().y() > 0:
				zoomFactor = 1.2
			else:
				zoomFactor = 0.8
			self.scale(zoomFactor,zoomFactor)
			newPos = self.mapToScene(event.pos())
			# Move scene to old position
			delta = newPos - oldPos

			self.translate(delta.y(), delta.x())

			transform1 = self.transform()
			print('--- wheelEvent()')
			print('transform0 h:', transform0.m31(), transform0)
			print('transform1 v:', transform0.m32(), transform1)

			#self.centerOn(newPos)

			#event.setAccepted(True)
			#super(bStackView,self).wheelEvent(event)

			#self.canvas.draw_idle()
			self.canvas.draw()
			self.repaint() # this is updating the widget !!!!!!!!
			'''

		else:
			if event.angleDelta().y() > 0:
				self.currentSlice -= 1
			else:
				self.currentSlice += 1
			self.setSlice(self.currentSlice)
			#self.displayStateChange.emit('set slice', self.currentSlice)
			self.setSliceSignal.emit('set slice', self.currentSlice)
			#event.setAccepted(True)

	def mousePressEvent(self, event):
		"""
		shift+click will create a new node
		n+click (assuming there is a node selected ... will create a new edge)
		"""
		#print('=== bStackView.mousePressEvent()', event.pos())
		self.clickPos = event.pos()
		super().mousePressEvent(event)

	def mouseMoveEvent(self, event):
		#print('=== bStackView.mouseMoveEvent()', event.pos())
		if self.clickPos is not None:
			newPos = event.pos() - self.clickPos
			dx = self.clickPos.x() - newPos.x()
			dy = self.clickPos.y() - newPos.y()
			self.translate(dx, dy)

		super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		#print('=== bStackView.mouseReleaseEvent()')
		self.clickPos = None
		super().mouseReleaseEvent(event)
		event.setAccepted(True)

	def onmove_mpl(self, event):
		#print('onmove_mpl()', event.xdata, event.ydata)
		thePoint = QtCore.QPoint(event.ydata, event.xdata) # swapped
		self.mainWindow.getStatusToolbar().setMousePosition(thePoint)

	def onclick_mpl(self, event):
		"""
		onpick() get called first
		"""

		x = event.ydata # swapped
		y = event.xdata
		z = self.currentSlice
		x = round(x,2)
		y = round(y,2)
		newNodeEvent = {'type':'newNode','x':x,'y':y,'z':z}

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers & QtCore.Qt.ShiftModifier
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
				# make a new slab
				print('\n=== bStackWidget.onclick_mpl() new slab ...')
				newSlabEvent = {'type':'newSlab','edgeIdx':self.selectedEdge(), 'x':x, 'y':y, 'z':z}
				self.myEvent(newSlabEvent)
			else:
				# make a new node
				print('\n=== bStackWidget.onclick_mpl() new node ...')
				self.myEvent(newNodeEvent)

	'''
	def onpick(event):
	    thisline = event.artist
	    xdata = thisline.get_xdata()
	    ydata = thisline.get_ydata()
	    ind = event.ind
	    print ('onpick points:', zip(xdata[ind], ydata[ind]))
	'''

	def onpick_mpl(self, event):
		"""
		Click to select (node, edge, slab)
		called before onclick_mpl()

		i want to be able to pick both (nodes, slabs) but need to know which one was clicked?
		"""
		# stop onpick being called twice for one mouse down
		if self.onpick_alreadypicked:
			self.onpick_alreadypicked = False
			return False
		else:
			self.onpick_alreadypicked = True

		selectionType = None
		thisLine = event.artist
		if thisLine == self.myNodePlot:
			selectionType = 'nodeSelection'
		elif thisLine == self.myEdgePlot:
			selectionType = 'edgeSelection'

		nKey = self.keyIsDown == 'n'
		print('\n=== bStackView.onpick() nKey:', nKey, 'selectionType:', selectionType)
		xdata = event.mouseevent.xdata
		ydata = event.mouseevent.ydata
		ind = event.ind

		# find the first ind in bSlabList.id
		firstInd = ind[0]

		if selectionType=='nodeSelection':
			nodeIdx = self.maskedNodes[self.currentSlice]['nodeMasked_nodeIdx'][firstInd]
			print('   nodeIdx:', nodeIdx)
		elif selectionType=='edgeSelection':
			edgeIdx = self.maskedNodes[self.currentSlice]['edgeIdxLines'][firstInd]
			slabIdx = self.maskedNodes[self.currentSlice]['slabIdxLines'][firstInd]
			nodeIdx = self.maskedNodes[self.currentSlice]['nodeIdxLines'][firstInd]
			print('   edgeIdx:', edgeIdx, 'slabIdx:', slabIdx, 'is also nodeIdx:', nodeIdx)
			if not np.isnan(nodeIdx):
				print('   converting to node selection')
				selectionType = 'nodeSelection'
				nodeIdx = int(round(nodeIdx)) # why is nodeIDx coming in as numpy.float64 ????
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
			elif selectionType=='edgeSelection':
				self.selectEdge(edgeIdx)
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
