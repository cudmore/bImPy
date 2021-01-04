"""
"""

import os, json
import functools
import webbrowser

from qtpy import QtGui, QtCore, QtWidgets

import bimpy

class bToolBar(QtWidgets.QToolBar):
	def __init__(self, mainWindow, parent=None):
		super(bToolBar, self).__init__(parent)

		self.myMainWindow = mainWindow

		tmpPath = os.path.dirname(os.path.abspath(__file__))
		iconsFolderPath = os.path.join(tmpPath,'icons')

		#print('bToolBar() tmpPath:', tmpPath)
		#print('bToolBar() iconsFolderPath:', iconsFolderPath)

		self.setWindowTitle('Stack toolbar')

		#self.setOrientation(QtCore.Qt.Vertical);
		#self.setOrientation(QtCore.Qt.Horizontal);

		myIconSize = 12 #32
		#self.setIconSize(QtCore.QSize(myIconSize,myIconSize))
		self.setToolButtonStyle( QtCore.Qt.ToolButtonTextUnderIcon )

		myFontSize = 10
		myFont = self.font();
		myFont.setPointSize(myFontSize);
		self.setFont(myFont)

		toolNameList = ['Save']
		for toolName in toolNameList:
			iconPath = os.path.join(iconsFolderPath, toolName + '-16.png')
			saveIcon = QtGui.QIcon(iconPath)
			saveAction = QtWidgets.QAction(saveIcon, toolName, self)
			saveAction.setStatusTip(toolName)
			saveAction.setCheckable(False)
			callbackFn = functools.partial(self.oneCallback, toolName)
			saveAction.triggered.connect(callbackFn)
			self.addAction(saveAction)

		self.addSeparator()

		# checkable e.g. two state buttons
		toolListNames = ['1', '2', '3', 'rgb', 'separator', 'sliding-z',
						'separator',
						'Branch Points', 'Vessels', 'Annotations',
						'separator',
						'Tracing', '-', '+',
						'separator',
						# todo remove this and move below into hamburger
						#'Search', 'Contrast', 'Line Profile', 'Analysis',
						 ]

		# make ['1', '2', '3', 'rgb'] disjoint selections
		channelActionGroup = QtWidgets.QActionGroup(self)

		numChannels = self.myMainWindow.getMyStack().numChannels

		self.toolList = []
		toolIndex = 0
		for index, toolName in enumerate(toolListNames):
			if toolName == 'separator':
				self.addSeparator()
			else:
				if toolName == '3' and numChannels<3:
					continue
				iconPath = os.path.join(iconsFolderPath, toolName + '-16.png')
				theIcon = QtGui.QIcon(iconPath)

				# see: https://stackoverflow.com/questions/45511056/pyqt-how-to-make-a-toolbar-button-appeared-as-pressed
				theAction = QtWidgets.QAction(theIcon, toolName, self)

				isCheckable = True
				if toolName in ['+', '-']:
					isCheckable = False
				theAction.setCheckable(isCheckable)

				theAction.setStatusTip(toolName) # USED BY CALLBACK, do not change
				theAction.triggered.connect(lambda checked, index=toolIndex: self.oneCallback3(index))

				# add channels to group
				if toolName in ['1', '2', '3', 'rgb']:
					channelActionGroup.addAction(theAction)

				# set keyboard shortcuts
				if toolName == '1':
					theAction.setShortcut('1')# or 'Ctrl+r' or '&r' for alt+r
					theAction.setToolTip('View Channel 1 [1]')
				elif toolName == '2':
					theAction.setShortcut('2')# or 'Ctrl+r' or '&r' for alt+r
					theAction.setToolTip('View Channel 2 [2]')
				elif toolName == '3':
					theAction.setShortcut('3')# or 'Ctrl+r' or '&r' for alt+r
					theAction.setToolTip('View Channel 3 [3]')
				elif toolName == 'rgb':
					theAction.setToolTip('View RGB Image')

				elif toolName == 'sliding-z':
					theAction.setShortcut('z')# or 'Ctrl+r' or '&r' for alt+r
					theAction.setToolTip('Toggle Sliding-Z [z]')

				elif toolName == 'Branch Points':
					theAction.setToolTip('Toggle Branch Point List')
				elif toolName == 'Vessels':
					theAction.setToolTip('Toggle Vessels List')
				elif toolName == 'Annotations':
					theAction.setToolTip('Toggle Annotations List')

				elif toolName == 'Tracing':
					theAction.setShortcut('t')# or 'Ctrl+r' or '&r' for alt+r
					theAction.setToolTip('Toggle Tracing [t]')
				elif toolName == '-':
					theAction.setShortcut('-')# or 'Ctrl+r' or '&r' for alt+r
					theAction.setToolTip('Reduce Tracing Size [-]')
				elif toolName == '+':
					theAction.setShortcut('=')# or 'Ctrl+r' or '&r' for alt+r
					theAction.setToolTip('Increase Tracing Size [=]')

				# moved down
				'''
				elif toolName == 'Search':
					theAction.setShortcut('Ctrl+f')# or 'Ctrl+r' or '&r' for alt+r
					theAction.setToolTip('Search Annotations [Ctrl+f]')
				elif toolName == 'Contrast':
					theAction.setShortcut('c')# or 'Ctrl+r' or '&r' for alt+r
					theAction.setToolTip('Toggle Contrast [c]')
				elif toolName == 'Line Profile':
					theAction.setShortcut('l')# or 'Ctrl+r' or '&r' for alt+r
					theAction.setToolTip('Toggle Line Profile [l]')
					#theAction.setShortcutVisibleInContextMenu(True)
				'''

				#
				# add action
				self.toolList.append(theAction)
				self.addAction(theAction)
				toolIndex += 1

		#
		# checkbox to toggle user set type with 1,2,3,...
		toolName = 'Set Type'
		self.setTypeCheckBox = QtWidgets.QCheckBox(toolName)
		#callbackFn = functools.partial(self.oneCallback, toolName)
		# why is checkbox color inverted?
		# don't do this, it turns off user checking
		#setTypeCheckBox.setCheckable(isCheckable)
		self.setTypeCheckBox.stateChanged.connect(self.setType_callback)
		self.addWidget(self.setTypeCheckBox)

		#
		# put actions in hamburger combo box
		myHamburger = QtWidgets.QToolButton()
		myHamburger.setPopupMode(QtWidgets.QToolButton.InstantPopup)
		hamburgerPath = os.path.join(iconsFolderPath, 'Hamburger' + '-16.png')
		hamburgerIcon = QtGui.QIcon(hamburgerPath)
		myHamburger.setArrowType(QtCore.Qt.NoArrow)
		myHamburger.setIcon(hamburgerIcon)
		myHamburger.setIconSize(QtCore.QSize(myIconSize*2,myIconSize*2))
		self.addWidget(myHamburger)

		#toolNameList = ['Options', 'Help']
		toolNameList = ['Search', 'Contrast', 'Line Profile', 'Caiman', 'Plot', 'Status',
						'separator',
						'Options', 'Help']
		for toolName in toolNameList:
			if toolName == 'separator':
				theAction = QtWidgets.QAction('---', self)
				myHamburger.addAction(theAction)
				continue

			isChecked = False
			isCheckable = False
			useIcon = True
			if toolName in ['Search', 'Contrast', 'Line Profile', 'Caiman', 'Status']:
				isCheckable = True
				# we have icons for these but they collide with state checkbox in menu
				useIcon = False
			if useIcon:
				iconPath = os.path.join(iconsFolderPath, toolName + '-16.png')
				saveIcon = QtGui.QIcon(iconPath)
				theAction = QtWidgets.QAction(saveIcon, toolName, self)
			else:
				theAction = QtWidgets.QAction(toolName, self)
			theAction.setStatusTip(toolName)
			theAction.setCheckable(isCheckable)
			callbackFn = functools.partial(self.oneCallback, toolName)
			theAction.triggered.connect(callbackFn)

			if toolName == 'Status':
				theAction.setChecked(True)

			# set shortcuts and tooltip
			if toolName == 'Search':
				theAction.setShortcut('Ctrl+f')# or 'Ctrl+r' or '&r' for alt+r
				theAction.setToolTip('Search Annotations [Ctrl+f]')
				theAction.setShortcutVisibleInContextMenu(True)
			elif toolName == 'Contrast':
				theAction.setShortcut('c')# or 'Ctrl+r' or '&r' for alt+r
				theAction.setToolTip('Toggle Contrast [c]')
				theAction.setShortcutVisibleInContextMenu(True)
			elif toolName == 'Line Profile':
				theAction.setShortcut('l')# or 'Ctrl+r' or '&r' for alt+r
				theAction.setToolTip('Toggle Line Profile [l]')
				theAction.setShortcutVisibleInContextMenu(True)
			elif toolName == 'Caiman':
				#theAction.setShortcut('l')# or 'Ctrl+r' or '&r' for alt+r
				theAction.setToolTip('Toggle Caiman Annotation Analysis')
				#theAction.setShortcutVisibleInContextMenu(True)
			elif toolName == 'Plot':
				theAction.setShortcut('p')# or 'Ctrl+r' or '&r' for alt+r
				theAction.setToolTip('Plot [p]')
				theAction.setShortcutVisibleInContextMenu(True)
			elif toolName == 'Status':
				theAction.setShortcut('s')# or 'Ctrl+r' or '&r' for alt+r
				theAction.setToolTip('Status Bar [s]')
				theAction.setShortcutVisibleInContextMenu(True)

			# add to hamburger QToolButton
			myHamburger.addAction(theAction)

	def slot_DisplayStateChange(self, key, displayStateDict):
		print('    bToolbar.slot_DisplayStateChange() key:', key)
		if key == 'displayThisStack':
			print('  toggle channel 1/2/3/rgb to displayStateDict[key]', displayStateDict[key])

	def setType_callback(self, state):
		print('setType_callback() state:', state)

	def syncWithOptions(self, options):
		print('=== bToolbar.syncWithOption()')
		"""
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

		"""

		# todo: add another sync() function to handle displayStateDict
		# the state of these tools are associated with tracing in
		# bPyQtGraph.displayStateDict
		ignoreTools = ['1', '2', '3', 'rgb', 'sliding-z', 'Tracing', '-', '+']

		for item in self.toolList:
			name = item.statusTip()
			#print('name:', name)
			if name == 'Branch Points':
				isChecked = options['Panels']['showNodeList']
				item.setChecked(isChecked)
			elif name == 'Vessels':
				isChecked = options['Panels']['showEdgeList']
				item.setChecked(isChecked)
			elif name == 'Annotations':
				isChecked = options['Panels']['showAnnotations']
				item.setChecked(isChecked)
			elif name == 'Search':
				isChecked = options['Panels']['showSearch']
				item.setChecked(isChecked)
			elif name == 'Contrast':
				isChecked = options['Panels']['showContrast']
				item.setChecked(isChecked)
			elif name == 'Line Profile':
				isChecked = options['Panels']['showLineProfile']
				item.setChecked(isChecked)
			else:
				if name not in ignoreTools:
					print('  bToolbar.syncWithOptions() case not taken with action name:', name)

	def oneCallback(self, id):
		print('bToolbar.oneCallback() id:', id)

		if id == 'Save':
			self.myMainWindow.signal('save')
		elif id == 'Search':
			self.myMainWindow.optionsChange('Panels', 'showSearch', toggle=True, doEmit=True)
		elif id == 'Contrast':
			self.myMainWindow.optionsChange('Panels', 'showContrast', toggle=True, doEmit=True)
		elif id == 'Line Profile':
			self.myMainWindow.optionsChange('Panels', 'showLineProfile', toggle=True, doEmit=True)
		elif id == 'Caiman':
			self.myMainWindow.optionsChange('Panels', 'showCaiman', toggle=True, doEmit=True)
		elif id == 'Plot':
			# todo: what happens when this is closed???
			self.myMainWindow.showPlotWidget()
		elif id == 'Status':
			self.myMainWindow.optionsChange('Panels', 'showStatus', toggle=True, doEmit=True)
		#elif id == 'Napari':
		#	self.myMainWindow.optionsChange('Panels', 'showStatus', toggle=True, doEmit=True)

		elif id == 'Options':
			bimpy.interface.bOptionsDialog(self.myMainWindow, self.myMainWindow)
		elif id == 'Help':
			urlStr = 'https://cudmore.github.io/bImPy-Docs/interface'
			webbrowser.open(urlStr, new=2)

		else:
			print('  bToolBar.oneCallback() did not understand id:', id)

	def oneCallback3(self, index):
		"""
		this REQUIRES a list of actions, self.tooList
		"""
		action = self.toolList[index]
		actionName = action.statusTip()
		isChecked = action.isChecked()
		print('bToolbar.oneCallback3() index:', index, 'actionName:', actionName, 'isChecked:', isChecked)

		# if 'set types' is checked then 1,2,3,...,0 set type
		# todo: HOW DO I HANDLE THIS ????
		if self.setTypeCheckBox.isChecked():
			handleActionNames = [str(x) for x in range(10)] # 0..9
			if actionName in handleActionNames:
				#
				print('\n')
				print('   bToolBar.oneCallback3() tell ... bPyQtGraph to set selected object type')
				print('\n')

				#

				# need to set type of selected object (not set channel 1,2,3,...,0)
				# like bTableWidget2.menuActionHandler()
				print('!!! bToolBar.oneCallback3() need to set type not channel !!!')
				newValue = int(actionName)
				print('  todo: newValue:', newValue)
				type = 'setType'
				print('  todo: detect selection type !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! hard coded edges')
				objectType = 'edges'
				print('  todo: detect objectIndex !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! hard coded 5')
				objectIndex = 5
				myEvent = {'type': type, 'objectType': objectType,
							'newValue': newValue,
							'objectIdx':int(objectIndex)}
				print(json.dumps(myEvent, indent=4))

				# todo: I don't want this to be getStackView() e.g. bPyQtGraph
				# i should send it to the main bStackWidget, this hold a view of the stack
				# it could be bPyQtGraph OR bNapari !!!!
				self.myMainWindow.getStackView().myEvent(myEvent)

		# todo: we need to handle 0,1,2,3,... if 'set types' is checked but process others normally

		if actionName == '1':
			self.myMainWindow.getStackView().displayStateChange('displayThisStack', value=1)
		elif actionName == '2':
			self.myMainWindow.getStackView().displayStateChange('displayThisStack', value=2)
		elif actionName == '3':
			self.myMainWindow.getStackView().displayStateChange('displayThisStack', value=3)
		elif actionName == 'rgb':
			self.myMainWindow.getStackView().displayStateChange('displayThisStack', value='rgb')

		elif actionName == 'sliding-z':
			self.myMainWindow.getStackView().displayStateChange('displaySlidingZ', toggle=True)

		elif actionName == 'Branch Points':
			self.myMainWindow.optionsChange('Panels', 'showNodeList', toggle=True, doEmit=True)
		elif actionName == 'Vessels':
			self.myMainWindow.optionsChange('Panels', 'showEdgeList', toggle=True, doEmit=True)
		elif actionName == 'Annotations':
			self.myMainWindow.optionsChange('Panels', 'showAnnotations', toggle=True, doEmit=True)
		elif actionName == 'Search':
			self.myMainWindow.optionsChange('Panels', 'showSearch', toggle=True, doEmit=True)
		elif actionName == 'Contrast':
			self.myMainWindow.optionsChange('Panels', 'showContrast', toggle=True, doEmit=True)
		elif actionName == 'Line Profile':
			self.myMainWindow.optionsChange('Panels', 'showLineProfile', toggle=True, doEmit=True)

		elif actionName == 'Tracing':
			self.myMainWindow.getStackView().toggleTracing()
		elif actionName == '-':
			self.myMainWindow.getStackView().incrementDecrimentTracing('decrease')
		elif actionName == '+':
			self.myMainWindow.getStackView().incrementDecrimentTracing('increase')

		else:
			print('  -->> action not taken')
