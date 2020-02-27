
"""
Display x/y and intensity as mouse moves over bStackView
"""

#from PyQt5 import QtGui, QtCore, QtWidgets
from qtpy import QtGui, QtCore, QtWidgets

#class bStatusToolbarWidget(QtWidgets.QToolBar):
class bStatusToolbarWidget(QtWidgets.QWidget):
	def __init__(self, mainWindow, numSlices):
		print('bStatusToolbarWidget.__init__')
		#super(QtWidgets.QToolBar, self).__init__(parent)
		super(bStatusToolbarWidget, self).__init__()

		self.mainWindow = mainWindow
		self.numSlices = numSlices
		#self.setMovable(False)

		'''
		myGroupBox = QtWidgets.QGroupBox(self)
		myGroupBox.setTitle('')
		'''

		hBoxLayout = QtWidgets.QHBoxLayout(self)

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
		eventType = myEvent.eventType
		if eventType in ['select node', 'select edge']:
			sliceIdx = myEvent.sliceIdx
			currentSliceStr = 'Slice ' + str(sliceIdx) + '/' + str(self.numSlices)
			self.currentSliceLabel.setText(currentSliceStr)

	def slot_select(self, myEvent):
		print('bStatusToolbarWidget.slot_select() myEvent:', myEvent)
		if myEvent.eventType == 'select node':
			nodeIdx = myEvent.nodeIdx
			if nodeIdx is None:
				return # happens on user key 'esc'
			#self.mySelectRow(itemIdx=nodeIdx)

		elif myEvent.eventType == 'select edge':
			edgeIdx = myEvent.edgeIdx
			if edgeIdx is None:
				return # happens on user key 'esc'
			#self.mySelectRow(itemIdx=edgeIdx)

	def setMousePosition(self, point):
		x = round(point.x(),0)
		y = round(point.y(),0)
		self.xMousePosition.setText(str(x))
		self.xMousePosition.repaint()
		self.yMousePosition.setText(str(y))
		self.yMousePosition.repaint()

		# todo: update pixel intensity
		# self.mainWindow.myStackView
		channel = 1
		image = self.mainWindow.myStackView.mySimpleStack.getImage(channel=channel)
		pixelIntensity = image[x, y] # NOT swapped
		#print('image.shape:', image.shape, image[x, y], image[y, x])
		self.pixelIntensity.setText(str(pixelIntensity))
		self.pixelIntensity.repaint()
