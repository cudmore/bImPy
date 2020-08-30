
"""
Display x/y and intensity as mouse moves over bStackView
"""

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

		currentSliceStr = 'Slice 0 /' + str(self.numSlices)
		self.currentSliceLabel = QtWidgets.QLabel(currentSliceStr)
		hBoxLayout.addWidget(self.currentSliceLabel)

		xMousePosition_ = QtWidgets.QLabel("X (pixel)")
		self.xMousePosition = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(xMousePosition_)
		hBoxLayout.addWidget(self.xMousePosition)

		yMousePosition_ = QtWidgets.QLabel("Y (pixel)")
		self.yMousePosition = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(yMousePosition_)
		hBoxLayout.addWidget(self.yMousePosition)

		pixelIntensity_ = QtWidgets.QLabel("Intensity")
		self.pixelIntensity = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(pixelIntensity_)
		hBoxLayout.addWidget(self.pixelIntensity)

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
		selectedNode_.setFixedWidth(fixedWidth)
		self.selectedNode.setFixedWidth(fixedWidth)
		hBoxLayout2.addWidget(selectedNode_)
		hBoxLayout2.addWidget(self.selectedNode)

		selectedEdge_ = QtWidgets.QLabel("Edge")
		self.selectedEdge = QtWidgets.QLabel("None")
		selectedEdge_.setFixedWidth(fixedWidth)
		self.selectedEdge.setFixedWidth(fixedWidth)
		hBoxLayout2.addWidget(selectedEdge_)
		hBoxLayout2.addWidget(self.selectedEdge)

		selectedSlab_ = QtWidgets.QLabel("Slab")
		self.selectedSlab = QtWidgets.QLabel("None")
		selectedSlab_.setFixedWidth(fixedWidth)
		self.selectedSlab.setFixedWidth(fixedWidth)
		hBoxLayout2.addWidget(selectedSlab_)
		hBoxLayout2.addWidget(self.selectedSlab)

		# works but does not actually resize widgets?
		'''numWidgets = hBoxLayout2.count()
		for widgetIdx in range(numWidgets):
			# itemAt() returns an item, need to call widget() to get the widget
			theWidget = hBoxLayout2.itemAt(widgetIdx).widget()
			print('      theWidget:', theWidget)
			theWidget.setFixedWidth(fixedWidth)
		'''
		
		vBoxLayout = QtWidgets.QVBoxLayout(self)
		vBoxLayout.addLayout(hBoxLayout)
		vBoxLayout.addLayout(hBoxLayout2)
		
			
		# finish
		#myGroupBox.setLayout(hBoxLayout)
		#self.addWidget(myGroupBox)

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

	def setMousePosition(self, point, sliceNumber=None):
		if sliceNumber is None:
			return
		x = round(point.x(),0)
		y = round(point.y(),0)
		self.xMousePosition.setText(str(x))
		self.xMousePosition.repaint()
		self.yMousePosition.setText(str(y))
		self.yMousePosition.repaint()

		# todo: update pixel intensity
		# self.mainWindow.myStackView
		channel = 1
		image = self.mainWindow.getStackView().mySimpleStack.getImage2(channel=channel, sliceNum=sliceNumber)
		if x <0 or y < 0:
			return
		if x > image.shape[0] or y > image.shape[1]:
			return
		pixelIntensity = image[x, y] # NOT swapped
		#print('image.shape:', image.shape, image[x, y], image[y, x])
		self.pixelIntensity.setText(str(pixelIntensity))
		self.pixelIntensity.repaint()
		