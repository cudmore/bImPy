"""
"""

import os
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

		self.setWindowTitle('xxx toolbar')

		#self.setOrientation(QtCore.Qt.Vertical);
		#self.setOrientation(QtCore.Qt.Horizontal);

		myIconSize = 16 #32
		self.setIconSize(QtCore.QSize(myIconSize,myIconSize))
		self.setToolButtonStyle( QtCore.Qt.ToolButtonTextUnderIcon )

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

		iconSizeStr = '16'

		# checkable e.g. two state buttons
		toolListNames = ['1', '2', '3', 'rgb', 'separator', 'z', 'max', 'separator',
						 'Branch Points', 'Vessels', 'Annotations',
						 'Search', 'Contrast', 'Line Profile', 'Analysis',
						 ]
		self.toolList = []
		toolIndex = 0
		for index, toolName in enumerate(toolListNames):
			if toolName == 'separator':
				self.addSeparator()
			else:
				iconPath = os.path.join(iconsFolderPath, toolName + '-16.png')
				theIcon = QtGui.QIcon(iconPath)

				# see: https://stackoverflow.com/questions/45511056/pyqt-how-to-make-a-toolbar-button-appeared-as-pressed
				theAction = QtWidgets.QAction(theIcon, toolName, self)
				theAction.setCheckable(True)
				theAction.setStatusTip(toolName)
				theAction.triggered.connect(lambda checked, index=toolIndex: self.oneCallback3(index))

				self.toolList.append(theAction)
				self.addAction(theAction)
				toolIndex += 1

		self.addSeparator()

		toolNameList = ['Options', 'Help']
		for toolName in toolNameList:
			iconPath = os.path.join(iconsFolderPath, toolName + '-16.png')
			saveIcon = QtGui.QIcon(iconPath)
			saveAction = QtWidgets.QAction(saveIcon, toolName, self)
			saveAction.setStatusTip(toolName)
			saveAction.setCheckable(False)
			callbackFn = functools.partial(self.oneCallback, toolName)
			saveAction.triggered.connect(callbackFn)
			self.addAction(saveAction)

	def slot_DisplayStateChange(self, key, displayStateDict):
		print('    bToolbar.slot_DisplayStateChange() key:', key)
		if key == 'displayThisStack':
			print('  toggle channel 1/2/3/rgb to displayStateDict[key]', displayStateDict[key])

	def syncWithOptions(self, options):
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
				print('bToolbar.syncWithOptions() case not taken with action name:', name)

	def oneCallback(self, id):
		print('oneCallback() id:', id)

		if id == 'Options':
			bimpy.interface.bOptionsDialog(self.myMainWindow, self.myMainWindow)
		elif id == 'Help':
			urlStr = 'https://cudmore.github.io/bImPy/interface'
			webbrowser.open(urlStr, new=2)

	def oneCallback3(self, index):
		print('oneCallback3() index:', index)
		action = self.toolList[index]
		print('  ' ,action.statusTip(), action.isChecked())
		actionName = action.statusTip()
		isChecked = action.isChecked()

		if actionName == 'Branch Points':
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

