"""
20200912
"""

from functools import partial

from PyQt5 import QtCore, QtWidgets, QtGui

class myStatusToolbarWidget(QtWidgets.QToolBar):
	def __init__(self, parent):
		print('myStatusToolbarWidget.__init__')
		super(QtWidgets.QToolBar, self).__init__(parent)

		self.myCanvasWidget = parent

		self.setMovable(False)

		myAlign = QtCore.Qt.AlignLeft # for HBoxLayout

		myGroupBox = QtWidgets.QGroupBox()
		myGroupBox.setTitle('')

		hBoxLayout = QtWidgets.QHBoxLayout()

		self.lastActionLabel = QtWidgets.QLabel("Last Action: None")
		hBoxLayout.addWidget(self.lastActionLabel)

		xMousePosition_ = QtWidgets.QLabel("X (um)")
		xMousePosition_.setMaximumWidth(20)
		self.xMousePosition = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(xMousePosition_, myAlign)
		hBoxLayout.addWidget(self.xMousePosition, myAlign)

		yMousePosition_ = QtWidgets.QLabel("X (um)")
		self.yMousePosition = QtWidgets.QLabel("None")
		hBoxLayout.addWidget(yMousePosition_, myAlign)
		hBoxLayout.addWidget(self.yMousePosition, myAlign)

		# finish
		myGroupBox.setLayout(hBoxLayout)
		self.addWidget(myGroupBox)

	def setMousePosition(self, point):
		self.xMousePosition.setText(str(round(point.x(),1)))
		self.xMousePosition.repaint()
		self.yMousePosition.setText(str(round(point.y(),1)))
		self.yMousePosition.repaint()

class myScopeToolbarWidget(QtWidgets.QToolBar):
	def __init__(self, parent):
		"""
		A Toolbar for controlling the scope. This includes:
			- reading and moving stage/objective position
			- setting the size of a crosshair/box to show current motor position
			- setting x/y step size
			- showing a video window
			- capturing single images from video camera
			- importing scanning files from scope
		"""
		print('myScopeToolbarWidget.__init__')
		super(QtWidgets.QToolBar, self).__init__(parent)

		self.myCanvasWidget = parent

		# works but butons become stupid
		#self.setStyleSheet("""background-color: #19232D;""")

		myVerticalSpacer = 12
		myAlign = QtCore.Qt.AlignLeft # for HBoxLayout

		myGroupBox = QtWidgets.QGroupBox()
		myGroupBox.setTitle('Scope Controller')
		#myGroupBox.setFlat(True)

		# main v box
		vBoxLayout = QtWidgets.QVBoxLayout()
		vBoxLayout.setSpacing(4)

		#
		# arrows for left/right, front/back
		grid = QtWidgets.QGridLayout()

		buttonName = 'move stage left'
		iconPath = self.myCanvasWidget._getIcon('left-arrow.png')
		icon  = QtGui.QIcon(iconPath)
		leftButton = QtWidgets.QPushButton()
		leftButton.setCheckable(False)
		leftButton.setIcon(icon)
		leftButton.setToolTip('Move stage left')
		leftButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'move stage right'
		iconPath = self.myCanvasWidget._getIcon('right-arrow.png')
		icon  = QtGui.QIcon(iconPath)
		rightButton = QtWidgets.QPushButton()
		rightButton.setCheckable(False)
		rightButton.setIcon(icon)
		rightButton.setToolTip('Move stage right')
		rightButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'move stage back'
		iconPath = self.myCanvasWidget._getIcon('up-arrow.png')
		icon  = QtGui.QIcon(iconPath)
		backButton = QtWidgets.QPushButton()
		backButton.setCheckable(False)
		backButton.setIcon(icon)
		backButton.setToolTip('Move stage back')
		backButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'move stage front'
		iconPath = self.myCanvasWidget._getIcon('down-arrow.png')
		icon  = QtGui.QIcon(iconPath)
		frontButton = QtWidgets.QPushButton()
		frontButton.setCheckable(False)
		frontButton.setIcon(icon)
		frontButton.setToolTip('Move stage front')
		frontButton.clicked.connect(partial(self.on_button_click,buttonName))

		grid.addWidget(leftButton, 1, 0) # row, col
		grid.addWidget(rightButton, 1, 2) # row, col
		grid.addWidget(backButton, 0, 1) # row, col
		grid.addWidget(frontButton, 2, 1) # row, col

		vBoxLayout.addLayout(grid)

		#
		# x/y step size
		grid2 = QtWidgets.QGridLayout()

		xStepLabel = QtWidgets.QLabel("X Step (um)")
		self.xStepSpinBox = QtWidgets.QDoubleSpinBox()
		self.xStepSpinBox.setMinimum(0.0)
		self.xStepSpinBox.setMaximum(10000.0) # need something here, otherwise max is 100
		#self.xStepSpinBox.setValue(1000)
		self.xStepSpinBox.valueChanged.connect(self.stepValueChanged)

		yStepLabel = QtWidgets.QLabel("Y Step (um)")
		self.yStepSpinBox = QtWidgets.QDoubleSpinBox()
		self.yStepSpinBox.setMinimum(0)
		self.yStepSpinBox.setMaximum(10000) # need something here, otherwise max is 100
		#self.yStepSpinBox.setValue(500)
		self.yStepSpinBox.valueChanged.connect(self.stepValueChanged)

		# set values of x/y step to Video
		self.crosshairSizeChoice('Video')

		grid2.addWidget(xStepLabel, 0, 0) # row, col
		grid2.addWidget(self.xStepSpinBox, 0, 1) # row, col
		grid2.addWidget(yStepLabel, 1, 0) # row, col
		grid2.addWidget(self.yStepSpinBox, 1, 1) # row, col

		vBoxLayout.addSpacing(myVerticalSpacer) # space before video
		vBoxLayout.addLayout(grid2)

		#
		# read position and report x/y position
		readPositionHBoxLayout = QtWidgets.QHBoxLayout()
		#gridReadPosition = QtWidgets.QGridLayout()

		buttonName = 'read motor position'
		readPositionButton = QtWidgets.QPushButton('Read Position')
		readPositionButton.setToolTip('Read Motor Position')
		readPositionButton.setCheckable(False)
		readPositionButton.clicked.connect(partial(self.on_button_click,buttonName))

		# we will need to set these from code
		xStagePositionLabel_ = QtWidgets.QLabel("X (um)")
		self.xStagePositionLabel = QtWidgets.QLabel("None")
		yStagePositionLabel_ = QtWidgets.QLabel("Y (um)")
		self.yStagePositionLabel = QtWidgets.QLabel("Y (um)")

		'''
		gridReadPosition.addWidget(readPositionButton, 0, 0) # row, col
		gridReadPosition.addWidget(xStagePositionLabel_, 0, 1) # row, col
		gridReadPosition.addWidget(self.xStagePositionLabel, 0, 2) # row, col
		gridReadPosition.addWidget(yStagePositionLabel_, 0, 3) # row, col
		gridReadPosition.addWidget(self.yStagePositionLabel, 0, 4) # row, col
		'''
		readPositionHBoxLayout.addWidget(readPositionButton, myAlign) # row, col
		readPositionHBoxLayout.addWidget(xStagePositionLabel_, myAlign) # row, col
		readPositionHBoxLayout.addWidget(self.xStagePositionLabel, myAlign) # row, col
		readPositionHBoxLayout.addWidget(yStagePositionLabel_, myAlign) # row, col
		readPositionHBoxLayout.addWidget(self.yStagePositionLabel, myAlign) # row, col

		vBoxLayout.addSpacing(myVerticalSpacer) # space before video
		vBoxLayout.addLayout(readPositionHBoxLayout)

		#
		# center crosshair
		crosshair_hBoxLayout = QtWidgets.QHBoxLayout()
		buttonName = 'center canvas on motor position'
		iconPath = self.myCanvasWidget._getIcon('focus.png')
		icon  = QtGui.QIcon(iconPath)
		# QToolButton
		centerCrosshairButton = QtWidgets.QPushButton('Center')
		#centerCrosshairButton = QtWidgets.QToolButton('Center')
		centerCrosshairButton.setToolTip('Center canvas on curent motor position')
		centerCrosshairButton.setIcon(icon)
		centerCrosshairButton.setCheckable(False)
		centerCrosshairButton.clicked.connect(partial(self.on_button_click,buttonName))
		crosshair_hBoxLayout.addWidget(centerCrosshairButton)

		squareSizeLabel_ = QtWidgets.QLabel("Square Size")
		comboBox = QtGui.QComboBox()
		comboBox.addItem("Video")
		comboBox.addItem("1x")
		comboBox.addItem("1.5x")
		comboBox.addItem("2x")
		comboBox.addItem("2.5x")
		comboBox.addItem("3x")
		comboBox.addItem("3.5x")
		comboBox.addItem("4x")
		comboBox.addItem("4.5x")
		comboBox.addItem("5x")
		comboBox.addItem("5.5x")
		comboBox.addItem("6x")
		comboBox.addItem("Hide")
		comboBox.activated[str].connect(self.crosshairSizeChoice)
		crosshair_hBoxLayout.addWidget(squareSizeLabel_)
		crosshair_hBoxLayout.addWidget(comboBox)

		vBoxLayout.addSpacing(myVerticalSpacer) # space before video
		vBoxLayout.addLayout(crosshair_hBoxLayout)

		#
		# show video window and grab video
		video_hBoxLayout = QtWidgets.QHBoxLayout()

		buttonName = 'Live Video'
		#iconPath = os.path.join(os.path.join(self.myParentApp.getCodeFolder(), 'icons/video.png'))
		iconPath = self.myCanvasWidget._getIcon('video.png')
		icon  = QtGui.QIcon(iconPath)
		liveVideoButton = QtWidgets.QPushButton('Video Window')
		liveVideoButton.setToolTip('Show Live Video Window')
		liveVideoButton.setIcon(icon)
		liveVideoButton.setCheckable(True)
		liveVideoButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'Grab Image'
		iconPath = self.myCanvasWidget._getIcon('camera.png')
		icon  = QtGui.QIcon(iconPath)
		grabVideoButton = QtWidgets.QPushButton(buttonName)
		grabVideoButton.setCheckable(False)
		grabVideoButton.setToolTip('Grab image from video')
		grabVideoButton.setIcon(icon)
		grabVideoButton.clicked.connect(partial(self.on_button_click,buttonName))

		video_hBoxLayout.addWidget(liveVideoButton)
		video_hBoxLayout.addWidget(grabVideoButton)

		vBoxLayout.addSpacing(myVerticalSpacer) # space before video
		vBoxLayout.addLayout(video_hBoxLayout)

		#
		# import new files from scope
		scope_hBoxLayout = QtWidgets.QHBoxLayout()

		buttonName = 'Import From Scope'
		iconPath = self.myCanvasWidget._getIcon('import.png')
		icon  = QtGui.QIcon(iconPath)
		importScopeFilesButton = QtWidgets.QPushButton(buttonName)
		importScopeFilesButton.setCheckable(False)
		importScopeFilesButton.setIcon(icon)
		importScopeFilesButton.setToolTip('Import images from scope')
		importScopeFilesButton.clicked.connect(partial(self.on_button_click,buttonName))

		buttonName = 'Canvas Folder'
		iconPath = self.myCanvasWidget._getIcon('folder.png')
		icon  = QtGui.QIcon(iconPath)
		showCanvasFolderButton = QtWidgets.QPushButton('Show Folder')
		showCanvasFolderButton.setToolTip('Show canvas folder')
		showCanvasFolderButton.setIcon(icon)
		showCanvasFolderButton.clicked.connect(partial(self.on_button_click,buttonName))

		scope_hBoxLayout.addWidget(importScopeFilesButton)
		scope_hBoxLayout.addWidget(showCanvasFolderButton)

		vBoxLayout.addSpacing(myVerticalSpacer) # space before video
		vBoxLayout.addLayout(scope_hBoxLayout)

		#
		# finalize

		#
		# add
		myGroupBox.setLayout(vBoxLayout)

		# finish
		self.addWidget(myGroupBox)

	def crosshairSizeChoice(self, text):
		print('crosshairSizeChoice() text:', text)
		options = self.myCanvasWidget.getOptions()
		if text == 'Hide':
			umWidth = 0
			umHeight = 0
			self.myCanvasWidget.getGraphicsView().myCrosshair.setWidthHeight(umWidth, umHeight)
		elif text=='Video':
			umWidth = options['video']['umWidth']
			umHeight = options['video']['umHeight']
			stepFraction = options['video']['stepFraction']
			# set step size
			xStep = umWidth - (umWidth*stepFraction)
			yStep = umHeight - (umHeight*stepFraction)
			self.setStepSize(xStep, yStep)
			# set visible red rectangle
			self.myCanvasWidget.getGraphicsView().myCrosshair.setWidthHeight(umWidth, umHeight)
		else:
			# assuming each option is of form(1x, 1.5x, etc)
			text = text.strip('x')
			zoom = float(text)
			zoomOneWidthHeight = options['scanning']['zoomOneWidthHeight']
			stepFraction = options['scanning']['stepFraction']
			# set step size
			zoomWidthHeight = zoomOneWidthHeight / zoom
			xStep = zoomWidthHeight - (zoomWidthHeight*stepFraction) # always square
			yStep = zoomWidthHeight - (zoomWidthHeight*stepFraction)
			self.setStepSize(xStep, yStep)
			# set visible red rectangle
			self.myCanvasWidget.getGraphicsView().myCrosshair.setWidthHeight(zoomWidthHeight, zoomWidthHeight)

	def getStepSize(self):
		xStep = self.xStepSpinBox.value()
		yStep = self.yStepSpinBox.value()
		return xStep, yStep

	def setStepSize(self, xStep, yStep):
		self.xStepSpinBox.setValue(xStep)
		self.yStepSpinBox.setValue(yStep)

	def stepValueChanged(self):
		xStep = self.xStepSpinBox.value()
		yStep = self.yStepSpinBox.value()
		print('myScopeToolbarWidget.stepValueChanged() xStep:', xStep, 'yStep:', yStep)

	@QtCore.pyqtSlot()
	def on_button_click(self, name):
		print('=== myScopeToolbarWidget.on_button_click() name:', name)
		self.myCanvasWidget.userEvent(name)

#todo: put all this in a grid
class myToolbarWidget(QtWidgets.QToolBar):
	def __init__(self, parent=None):
		"""
		"""
		print('bToolbar.py myToolbarWidget.__init__')
		super(myToolbarWidget, self).__init__(parent)

		# works but buttons become stupid
		#self.setStyleSheet("""background-color: #19232D;""")

		self.myCanvasWidget = parent

		#
		# layers
		layersGroupBox = QtWidgets.QGroupBox('Layers')
		#layersGroupBox.setStyleSheet("""background-color: red;""")
		layersHBoxLayout = QtWidgets.QHBoxLayout()

		checkBoxName = 'Video Layer'
		self.showVideoCheckBox = QtWidgets.QCheckBox('Image')
		self.showVideoCheckBox.setToolTip('Toggle video layer on and off')
		self.showVideoCheckBox.setCheckState(2) # Really annoying it is not 0/1 False/True but 0:False/1:Intermediate/2:True
		self.showVideoCheckBox.clicked.connect(partial(self.on_checkbox_click, checkBoxName, self.showVideoCheckBox))
		#self.addWidget(self.showVideoCheckBox)
		layersHBoxLayout.addWidget(self.showVideoCheckBox)

		checkBoxName = 'Video Squares Layer'
		self.showVideoSquaresCheckBox = QtWidgets.QCheckBox('Squares')
		self.showVideoSquaresCheckBox.setToolTip('Toggle video squares on and off')
		self.showVideoSquaresCheckBox.setCheckState(2) # Really annoying it is not 0/1 False/True but 0:False/1:Intermediate/2:True
		self.showVideoSquaresCheckBox.clicked.connect(partial(self.on_checkbox_click, checkBoxName, self.showVideoSquaresCheckBox))
		layersHBoxLayout.addWidget(self.showVideoSquaresCheckBox)

		checkBoxName = '2P Max Layer'
		self.show2pMaxCheckBox = QtWidgets.QCheckBox('Scanning')
		self.show2pMaxCheckBox.setToolTip('Toggle scanning layer on and off')
		self.show2pMaxCheckBox.setCheckState(2) # Really annoying it is not 0/1 False/True but 0:False/1:Intermediate/2:True
		self.show2pMaxCheckBox.clicked.connect(partial(self.on_checkbox_click, checkBoxName, self.show2pMaxCheckBox))
		#self.addWidget(self.show2pMaxCheckBox)
		layersHBoxLayout.addWidget(self.show2pMaxCheckBox)

		checkBoxName = '2P Squares Layer'
		self.show2pSquaresCheckBox = QtWidgets.QCheckBox('Squares')
		self.show2pSquaresCheckBox.setToolTip('Toggle scanning squares on and off')
		self.show2pSquaresCheckBox.setCheckState(2) # Really annoying it is not 0/1 False/True but 0:False/1:Intermediate/2:True
		self.show2pSquaresCheckBox.clicked.connect(partial(self.on_checkbox_click, checkBoxName, self.show2pSquaresCheckBox))
		#self.addWidget(self.show2pSquaresCheckBox)
		layersHBoxLayout.addWidget(self.show2pSquaresCheckBox)

		layersGroupBox.setLayout(layersHBoxLayout)
		self.addWidget(layersGroupBox)

		#
		# radio buttons to select type of contrast (selected, video layer, scope layer)
		self.contrastGroupBox = QtWidgets.QGroupBox('Image Contrast')

		contrastVBox = QtWidgets.QVBoxLayout()

		contrastRadioHBoxLayout = QtWidgets.QHBoxLayout()
		self.selectedContrast = QtWidgets.QRadioButton('Selected')
		self.videoLayerContrast = QtWidgets.QRadioButton('Video')
		self.scopeLayerContrast = QtWidgets.QRadioButton('Scope')

		# default to selecting 'Selected' image (for contrast adjustment)
		self.selectedContrast.setChecked(True)

		contrastRadioHBoxLayout.addWidget(self.selectedContrast)
		contrastRadioHBoxLayout.addWidget(self.videoLayerContrast)
		contrastRadioHBoxLayout.addWidget(self.scopeLayerContrast)

		contrastVBox.addLayout(contrastRadioHBoxLayout)

		# contrast sliders
		# min
		self.minSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.minSlider.setMinimum(0)
		self.minSlider.setMaximum(255)
		self.minSlider.setValue(0)
		self.minSlider.valueChanged.connect(partial(self.on_contrast_slider, 'minSlider', self.minSlider))
		#self.addWidget(self.minSlider)
		contrastVBox.addWidget(self.minSlider)
		# max
		self.maxSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.maxSlider.setMinimum(0)
		self.maxSlider.setMaximum(255)
		self.maxSlider.setValue(255)
		self.maxSlider.valueChanged.connect(partial(self.on_contrast_slider, 'maxSlider', self.maxSlider))
		#self.addWidget(self.maxSlider)
		contrastVBox.addWidget(self.maxSlider)

		self.contrastGroupBox.setLayout(contrastVBox)
		self.addWidget(self.contrastGroupBox)

		#
		# file list (tree view)
		self.fileList = myTreeWidget(self.myCanvasWidget)

		self.addWidget(self.fileList)

		#itemList = []
		numVideoFiles = len(self.myCanvasWidget.getCanvas().videoFileList)
		for idx, videoFile in enumerate(self.myCanvasWidget.getCanvas().videoFileList):
			#print('   myToolbarWidget appending videoFile to fileList (tree):', videoFile._fileName)
			'''
			print('  ', idx, 'of', numVideoFiles, 'myToobarWidget videoFile:')
			print('  ', videoFile.print())
			'''
			self.fileList.appendStack(videoFile, 'Video Layer')

		numScopeFiles = len(self.myCanvasWidget.getCanvas().scopeFileList)
		for idx, scopeFile in enumerate(self.myCanvasWidget.getCanvas().scopeFileList):
			#print('   myToolbarWidget appending scopeFile to fileList (tree):', scopeFile._fileName)
			'''
			print('  ', idx, 'of', numScopeFiles, 'myToobarWidget scopeFile:')
			print('  ', scopeFile.print())
			'''
			self.fileList.appendStack(scopeFile, '2P Max Layer')

	def appendScopeFile(self, newStack):
		self.fileList.appendStack(newStack, '2P Max Layer') #type: ('Video Layer', '2P Max Layer')

	def appendVideo(self, newStack):
		self.fileList.appendStack(newStack, 'Video Layer') #type: ('Video Layer', '2P Max Layer')

	def getSelectedContrast(self):
		if self.selectedContrast.isChecked():
			return 'selected'
		elif self.videoLayerContrast.isChecked():
			return 'Video Layer'
		elif self.scopeLayerContrast.isChecked():
			return '2P Max Layer'

	def on_contrast_slider(self, name, object):

		theMin = self.minSlider.value()
		theMax = self.maxSlider.value()

		adjustThisLayer = self.getSelectedContrast() # todo: work out the strings I am using !!!!!!!!!!!!!

		selectedItem = None
		selectedItems = self.myCanvasWidget.getGraphicsView().scene().selectedItems() # can be none
		if len(selectedItems) > 0:
			# the first selected item
			selectedItem = selectedItems[0]

		useMaxProject = False
		#todo: work out these string s!!!!!!!! (VIdeo LAyer, 2P Max Layer)
		if adjustThisLayer == 'Video Layer':
			useMaxProject = False
		elif adjustThisLayer == '2P Max Layer':
			# todo: change this in future
			useMaxProject = True
		#elif adjustThisLayer == 'selected':
		#	selectedItems = self.myCanvasWidget.getGraphicsView().scene().selectedItems()
		#	print('NOT IMPLEMENTED')

		print('=== myToolbarWidget.on_contrast_slider() adjustThisLayer:', adjustThisLayer, 'useMaxProject:', useMaxProject, 'theMin:', theMin, 'theMax:', theMax)

		for item in  self.myCanvasWidget.getGraphicsView().scene().items():

			# CHANGE TO GENERALIZE
			#if item.myLayer == 'Video Layer':
			#if item.myLayer == '2P Max Layer':
			#print('item.myLayer:', item.myLayer)

			# decide if we adjust this item
			# noramlly we are using layers
			# there is a special case where we are adjusting the selected it !!!!!!!!!!!!!!!!!!!!
			#adjustThisItem =
			if adjustThisLayer == 'selected':
				adjustThisItem = item == selectedItem
				if item.myLayer == 'Video Layer':
					useMaxProject = False
				elif item.myLayer == '2P Max Layer':
					# todo: change this in future
					useMaxProject = True
			else:
				adjustThisItem = item.myLayer == adjustThisLayer

			#if item.myLayer == adjustThisLayer:
			if adjustThisItem:
				# CHANGE TO GENERALIZE
				# todo: canvas should have one list of stacks (not separate video and scope lists)
				#if adjustThisLayer == 'Video Layer':
				if item.myLayer == 'Video Layer':
					# new 20191229
					#videoFile = self.myCanvasWidget.getCanvas().findByName(item._fileName)
					videoFile = item.myStack
				elif item.myLayer == '2P Max Layer':
					try:
						#videoFile = self.myCanvasWidget.getCanvas().findScopeFileByName(item._fileName)
						videoFile = item.myStack
					except:
						print('exception !!!@@@!!!', len(self.myCanvasWidget.getCanvas().scopeFileList), item._index)
						videoFile = None
				else:
					print('bCanvasWidget.on_contrast_slider() ERRRRRRRORRORORORRORORRORORORORORRORORO')
					continue

				if videoFile is None:
					continue

				umWidth = videoFile.getHeaderVal('umWidth')
				umHeight = videoFile.getHeaderVal('umHeight')
				#print('umWidth:', umWidth)


				# get an contrast enhanced ndarray
				# CHANGE TO GENERALIZE
				#videoImage = videoFile.getImage_ContrastEnhanced(theMin, theMax) # return the original as an nd_array

				# each scope stack needs to know if it is diplaying a real stack OR just a max project
				# where do I put this ???????
				videoImage = videoFile.old_getImage_ContrastEnhanced(theMin, theMax, useMaxProject=useMaxProject) # return the original as an nd_array

				if videoImage is None:
					# error
					pass
				else:
					imageStackHeight, imageStackWidth = videoImage.shape

					#print('mean:', np.mean(videoImage))

					myQImage = QtGui.QImage(videoImage, imageStackWidth, imageStackHeight, QtGui.QImage.Format_Indexed8)

					#
					# try and set color
					if adjustThisLayer == '2P Max Layer':
						colors=[]
						for i in range(256): colors.append(QtGui.qRgb(i/4,i,i/2))
						myQImage.setColorTable(colors)

					pixmap = QtGui.QPixmap(myQImage)
					pixmap = pixmap.scaled(umWidth, umHeight, QtCore.Qt.KeepAspectRatio)

					item.setPixmap(pixmap)
		#firstItem.setPixmap(pixmap)

	def setSelectedItem(self, filename):
		"""
		Respond to user clicking on the image and select the file in the list.
		"""
		#print('myToolbarWidget.setSelectedItem() filename:', filename)
		self.fileList.setSelectedItem(filename)

		'''
		# todo: use self._findItemByFilename()
		items = self.fileList.findItems(filename, QtCore.Qt.MatchFixedString, column=0)
		if len(items)>0:
			item = items[0]
			#print('   item:', item)
			self.fileList.setCurrentItem(item)
		'''

	def setCheckedState(self, filename, doShow):
		"""
		set the visible checkbox
		"""
		#print('myToolbarWidget.setCheckedState() filename:', filename, 'doShow:', doShow)
		self.fileList.setCheckedState(filename, doShow)

		'''
		item = self._findItemByFilename(filename)
		if item is not None:
			column = 0
			item.setCheckState(column, doShow)
		'''

	'''
	def _findItemByFilename(self, filename):
		"""
		Given a filename, return the item. Return None if not found.
		"""
		items = self.fileList.findItems(filename, QtCore.Qt.MatchFixedString, column=0)
		if len(items)>0:
			return items[0]
		else:
			return None
	'''

	'''
	def mousePressEvent(self, event):
		print('myToolbarWidget.mousePressEvent()')
	'''

	'''
	def keyPressEvent(self, event):
		print('myToolbarWidget.keyPressEvent() event:', event)
		print('   enable bring to front and send to back')
	'''

	@QtCore.pyqtSlot()
	def on_button_click(self, name):
		print('=== myToolbarWidget.on_button_click() name:', name)

	@QtCore.pyqtSlot()
	def on_checkbox_click(self, name, checkBoxObject):
		print('=== myToolbarWidget.on_checkbox_click() name:', name, 'checkBoxObject:', checkBoxObject)
		checkState = checkBoxObject.checkState()

		if name == 'Video Layer':
			self.myCanvasWidget.getGraphicsView().hideShowLayer('Video Layer', checkState==2)
		if name =='Video Squares Layer':
			self.myCanvasWidget.getGraphicsView().hideShowLayer('Video Squares Layer', checkState==2)
		if name == '2P Max Layer':
			self.myCanvasWidget.getGraphicsView().hideShowLayer('2P Max Layer', checkState==2)
		if name == '2P Squares Layer':
			self.myCanvasWidget.getGraphicsView().hideShowLayer('2P Squares Layer', checkState==2)

class myTreeWidget(QtWidgets.QTreeWidget):
	def __init__(self, parent=None):
		super(myTreeWidget, self).__init__(parent)
		self.myCanvasWidget = parent

		myColumns = ['Index', 'File', 'Type', 'xPixels', 'yPixels', 'numSlices'] # have to be unique
		self.myColumns = {}
		for idx, column in enumerate(myColumns):
			self.myColumns[column] = idx

		self.setHeaderLabels(myColumns) # 'Show'])
		self.setColumnWidth(self.myColumns['Index'], 40)
		self.setColumnWidth(self.myColumns['File'], 200)
		self.setColumnWidth(self.myColumns['Type'], 20)
		self.setColumnWidth(self.myColumns['xPixels'], 40)
		self.setColumnWidth(self.myColumns['yPixels'], 40)
		self.setColumnWidth(self.myColumns['numSlices'], 40)

		self.itemSelectionChanged.connect(self.fileSelected_callback)
		self.itemChanged.connect(self.fileSelected_changed)

	def appendStack(self, theStack, type):
		"""
		type: ('Video Layer', '2P Max Layer')
		"""

		myIndex = self.topLevelItemCount()
		#print('!!! appendStack() myIndex:', myIndex)

		item = QtWidgets.QTreeWidgetItem(self)
		item.setText(self.myColumns['Index'], str(myIndex+1))
		item.setText(self.myColumns['File'], theStack.getFileName())
		if type == 'Video Layer':
			item.setText(self.myColumns['Type'], 'v')
		elif type == '2P Max Layer':
			item.setText(self.myColumns['Type'], '2p')
		else:
			print('ERROR: myTreeWidget.appendStack() got unknown type???')
			item.setText(self.myColumns['Type'], 'Unknown')
		item.setText(self.myColumns['xPixels'], str(theStack.pixelsPerLine))
		item.setText(self.myColumns['yPixels'], str(theStack.linesPerFrame))
		item.setText(self.myColumns['numSlices'], str(theStack.numImages))
		item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
		item.setCheckState(0, QtCore.Qt.Checked)

		#self.insertTopLevelItems(0, item)
		self.addTopLevelItem(item)


	def setSelectedItem(self, filename):
		"""
		Respond to user clicking on the image and select the file in the list.
		"""
		items = self.findItems(filename, QtCore.Qt.MatchFixedString, column=self.myColumns['File'])
		if len(items)>0:
			item = items[0]
			self.setCurrentItem(item)
		else:
			print('warning: myTreeWidget.setSelectedItem() did not find filename:', filename)

	def setCheckedState(self, filename, doShow):
		"""
		set the visible checkbox
		"""
		items = self.findItems(filename, QtCore.Qt.MatchFixedString, column=self.myColumns['File'])
		if len(items)>0:
			item = items[0]
			column = 0
			item.setCheckState(column, doShow)

	def keyPressEvent(self, event):
		#print('myTreeWidget.keyPressEvent() event.text():', event.text())

		# todo: fix this, this assumes selected file in list is same as selected file in graphics view !
		if event.key() == QtCore.Qt.Key_F:
			#print('f for bring to front')
			self.myCanvasWidget.getGraphicsView().changeOrder('bring to front')
		elif event.key() == QtCore.Qt.Key_B:
			#print('b for send to back')
			self.myCanvasWidget.getGraphicsView().changeOrder('send to back')

		elif event.key() == QtCore.Qt.Key_I:
			selectedItems = self.selectedItems()
			print('key i selectedItems:', selectedItems)
			self.myCanvasWidget.userEvent('print stack info')

		elif event.key() == QtCore.Qt.Key_Left:
			super(myTreeWidget, self).keyPressEvent(event)
		elif event.key() == QtCore.Qt.Key_Right:
			super(myTreeWidget, self).keyPressEvent(event)
		elif event.key() == QtCore.Qt.Key_Up:
			super(myTreeWidget, self).keyPressEvent(event)
		elif event.key() == QtCore.Qt.Key_Down:
			super(myTreeWidget, self).keyPressEvent(event)
		else:
			print('  key not handled:text:', event.text(), 'modifyers:', event.modifiers())
			super(myTreeWidget, self).keyPressEvent(event)

	def mouseDoubleClickEvent(self, event):
		"""
		open a stack on a double-click
		"""
		print('=== myTreeWidget.mouseDoubleClickEvent')
		selectedItems = self.selectedItems()
		if len(selectedItems) > 0:
			selectedItem = selectedItems[0]
			fileName = selectedItem.text(self.myColumns['File'])
			type = selectedItem.text(self.myColumns['Type']) # in ['v', '2p']
			if type == 'v':
				layer = 'Video Layer'
			elif type == '2p':
				layer = '2P Max Layer'
			else:
				# error
				layer = None
			if layer is not None:
				self.myCanvasWidget.openStack(fileName, layer)

	def fileSelected_changed(self, item, col):
		"""
		called when user clicks on check box
		"""
		#print('=== fileSelected_changed() item:', item, 'col:', col, 'is now checked:', item.checkState(0))
		filename = item.text(self.myColumns['File'])
		#isNowChecked = item.checkState(self.myColumns['Index']) # 0:not checked, 2:is checked
		isNowChecked = item.checkState(0) # 0:not checked, 2:is checked
		doShow = True if isNowChecked==2 else False
		#print('   telling self.myQGraphicsView.hideShowItem() filename:', filename, 'doShow:', doShow)
		self.myCanvasWidget.getGraphicsView().hideShowItem(filename, doShow)

	def fileSelected_callback(self):
		"""
		Respond to user click in the file list (selects a file)
		"""
		print('=== myTreeWidget.fileSelected_callback()')
		theItems = self.selectedItems()
		if len(theItems) > 0:
			theItem = theItems[0]
			#selectedRow = self.fileList.currentRow() # self.fileList is a QTreeWidget
			filename = theItem.text(self.myColumns['File'])
			#print('   fileSelected_callback()', filename)
			# visually select image in canvas with yellow square
			self.myCanvasWidget.getGraphicsView().setSelectedItem(filename)
