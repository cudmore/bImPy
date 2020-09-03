
"""
Display x/y and intensity as mouse moves over bStackView
"""

import numpy as np

#from PyQt5 import QtGui, QtCore, QtWidgets
from qtpy import QtGui, QtCore, QtWidgets

#class bStatusToolbarWidget(QtWidgets.QToolBar):
class bStatusToolbarWidget(QtWidgets.QWidget):
	def __init__(self, mainWindow, numSlices):
		#print('bStatusToolbarWidget.__init__')
		#super(QtWidgets.QToolBar, self).__init__(parent)
		super(bStatusToolbarWidget, self).__init__()

		self.mainWindow = mainWindow
		self.numSlices = numSlices
		#self.setMovable(False)

		'''
		myGroupBox = QtWidgets.QGroupBox(self)
		myGroupBox.setTitle('')
		'''

		hBoxLayout = QtWidgets.QHBoxLayout()

		myAlign = QtCore.Qt.AlignLeft
		
		image_ = QtWidgets.QLabel("Channel")
		self.imageLabel = QtWidgets.QLabel("")
		hBoxLayout.addWidget(image_)
		hBoxLayout.addWidget(self.imageLabel, myAlign)

		currentSliceStr = 'Slice 0 /' + str(self.numSlices)
		self.currentSliceLabel = QtWidgets.QLabel(currentSliceStr)
		hBoxLayout.addWidget(self.currentSliceLabel, myAlign)

		xMousePosition_ = QtWidgets.QLabel("X (pixel)")
		self.xMousePosition = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(xMousePosition_)
		hBoxLayout.addWidget(self.xMousePosition, myAlign)

		yMousePosition_ = QtWidgets.QLabel("Y (pixel)")
		self.yMousePosition = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(yMousePosition_)
		hBoxLayout.addWidget(self.yMousePosition, myAlign)

		pixelIntensity_ = QtWidgets.QLabel("Intensity")
		self.pixelIntensity = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(pixelIntensity_)
		hBoxLayout.addWidget(self.pixelIntensity, myAlign)

		'''
		self.lastActionLabel = QtWidgets.QLabel("Last Action: None")
		hBoxLayout.addWidget(self.lastActionLabel)
		'''


		#
		# seconds row
		hBoxLayout2 = QtWidgets.QHBoxLayout()

		fixedWidth = 35

		selectedNode_ = QtWidgets.QLabel("Node")
		self.selectedNode = QtWidgets.QLabel("None")
		#selectedNode_.setFixedWidth(fixedWidth)
		#self.selectedNode.setFixedWidth(fixedWidth)
		hBoxLayout2.addWidget(selectedNode_)
		hBoxLayout2.addWidget(self.selectedNode, myAlign)

		selectedEdge_ = QtWidgets.QLabel("Edge")
		self.selectedEdge = QtWidgets.QLabel("None")
		#selectedEdge_.setFixedWidth(fixedWidth)
		#self.selectedEdge.setFixedWidth(fixedWidth)
		hBoxLayout2.addWidget(selectedEdge_)
		hBoxLayout2.addWidget(self.selectedEdge, myAlign)

		selectedSlab_ = QtWidgets.QLabel("Slab")
		self.selectedSlab = QtWidgets.QLabel("None")
		#selectedSlab_.setFixedWidth(fixedWidth)
		#self.selectedSlab.setFixedWidth(fixedWidth)
		hBoxLayout2.addWidget(selectedSlab_)
		hBoxLayout2.addWidget(self.selectedSlab, myAlign)

		# works but does not actually resize widgets?
		'''numWidgets = hBoxLayout2.count()
		for widgetIdx in range(numWidgets):
			# itemAt() returns an item, need to call widget() to get the widget
			theWidget = hBoxLayout2.itemAt(widgetIdx).widget()
			print('      theWidget:', theWidget)
			theWidget.setFixedWidth(fixedWidth)
		'''

		#
		# third row
		hBoxLayout3 = QtWidgets.QHBoxLayout()
		
		spinBoxWidth = 64
		
		# here we set one value for both
		showTracingAboveSlices = self.mainWindow.options['Tracing']['showTracingAboveSlices']
		
		plusMinusLabel_ = QtWidgets.QLabel("+/- Slices")
		self.plusMinusSpinBox = QtWidgets.QSpinBox()
		self.plusMinusSpinBox.setMaximumWidth(spinBoxWidth)
		self.plusMinusSpinBox.setMinimum(0)
		self.plusMinusSpinBox.setMaximum(1e6)
		self.plusMinusSpinBox.setValue(showTracingAboveSlices)
		self.plusMinusSpinBox.setProperty('bobID_1', 'Tracing')
		self.plusMinusSpinBox.setProperty('bobID_2', 'showTracingAboveSlices')
		self.plusMinusSpinBox.valueChanged.connect(self.valueChanged)
		hBoxLayout3.addWidget(plusMinusLabel_, myAlign)
		hBoxLayout3.addWidget(self.plusMinusSpinBox, myAlign)

		#
		# add all rows to vBoxLayout
		vBoxLayout = QtWidgets.QVBoxLayout(self)
		vBoxLayout.addLayout(hBoxLayout)
		vBoxLayout.addLayout(hBoxLayout2)
		vBoxLayout.addLayout(hBoxLayout3)


		# finish
		#myGroupBox.setLayout(hBoxLayout)
		#self.addWidget(myGroupBox)

	def valueChanged(self, value):
		"""
		Set value in our local copy of options, self.localOptions
		"""
		bobID_1 = self.sender().property('bobID_1')
		bobID_2 = self.sender().property('bobID_2')
		print(f'valueChanged() value: {value} type(value), bobID_1:{bobID_1}, bobID_2:{bobID_2}')

		if bobID_2 == 'showTracingAboveSlices':
			self.mainWindow.options['Tracing']['showTracingAboveSlices'] = value
			self.mainWindow.options['Tracing']['showTracingBelowSlices'] = value
			# todo: make this either a main window event() or a signal/slot
			self.mainWindow.getStackView()._preComputeAllMasks()
			self.mainWindow.getStackView().setSlice()
			
	def slot_DisplayStateChange(self, key, theDict):
		"""
		update based on theDict myQtGraphPlotWidget.displayStateDict
		"""
		print('bStatusToolbarWidget.slot_DisplayStateChange() key:', key, 'theDict:', theDict)
		if key == 'displayThisStack':
			theStr = str(theDict[key])
			self.imageLabel.setText(theStr)
			#self.repaint()

	def slot_StateChange(self, signalName, signalValue):
		"""
		signalValue: can be int, str, dict , ...
		"""
		if signalName == 'set slice':
			text = str(signalValue)
			currentSliceStr = 'Slice ' + text + '/' + str(self.numSlices)
			self.currentSliceLabel.setText(currentSliceStr)

	def slot_StateChange2(self, myEvent):
		myEvent.printSlot('bStatusToolbarWidget.slot_StateChange2()')
		eventType = myEvent.eventType
		if eventType in ['select node', 'select edge']:
			sliceIdx = myEvent.sliceIdx
			currentSliceStr = 'Slice ' + str(sliceIdx) + '/' + str(self.numSlices)
			self.currentSliceLabel.setText(currentSliceStr)
			self.repaint()
		elif eventType in ['select edge list']:
			edgeListStr = str(myEvent.edgeList)
			self.selectedEdge.setText(edgeListStr)
			self.repaint()

	def slot_select(self, myEvent):
		myEvent.printSlot('bStatusToolbarWidget.slot_select()')
		if myEvent.eventType == 'select node':
			nodeIdx = myEvent.nodeIdx
			nodeIdxStr = str(nodeIdx)
			self.selectedNode.setText(nodeIdxStr)
			self.repaint()

		elif myEvent.eventType == 'select edge':
			edgeIdx = myEvent.edgeIdx
			edgeIdxStr = str(edgeIdx)
			self.selectedEdge.setText(edgeIdxStr)

			# slab, there is no 'select slab', it is part of 'select edge'
			slabIdx = myEvent.slabIdx
			slabIdxStr = str(slabIdx)
			self.selectedSlab.setText(slabIdxStr)

			self.repaint()

	def setMousePosition(self, channel, sliceNumber, x, y):
		#channel = channel - 1
		
		#x = round(point.x(),0)
		#y = round(point.y(),0)
		x = int(x)
		y = int(y)
		self.xMousePosition.setText(str(x))
		self.xMousePosition.repaint()
		self.yMousePosition.setText(str(y))
		self.yMousePosition.repaint()

		# todo: update pixel intensity
		# self.mainWindow.myStackView
		pixelIntensity = self.mainWindow.getStackView().mySimpleStack.getPixel(channel, sliceNumber, x, y)
		if np.isnan(pixelIntensity):
			pixelIntensityStr = ''
		else:
			pixelIntensityStr = str(pixelIntensity)
		'''
		image = self.mainWindow.getStackView().mySimpleStack.getImage2(channel=channel, sliceNum=sliceNumber)
		if x <0 or y < 0:
			return
		if x > image.shape[0] or y > image.shape[1]:
			return
		pixelIntensity = image[x, y] # NOT swapped
		'''

		#print('image.shape:', image.shape, image[x, y], image[y, x])
		self.pixelIntensity.setText(pixelIntensityStr)
		self.pixelIntensity.repaint()
