"""
"""

import os
import functools

from qtpy import QtGui, QtCore, QtWidgets

class bToolBar(QtWidgets.QToolBar):
	def __init__(self, parent=None):
		super(bToolBar, self).__init__(parent)

		tmpPath = os.path.dirname(os.path.abspath(__file__))
		iconsFolderPath = os.path.join(tmpPath,'icons')

		#print('bToolBar() tmpPath:', tmpPath)
		#print('bToolBar() iconsFolderPath:', iconsFolderPath)

		self.setWindowTitle('xxx toolbar')

		#self.setOrientation(QtCore.Qt.Vertical);
		self.setOrientation(QtCore.Qt.Horizontal);

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

		toolListNames = ['Branch Points', 'Vessels', 'Annotations', 'Search', 'Contrast', 'Line Profile']
		self.toolList = []
		for index, toolName in enumerate(toolListNames):
			iconPath = os.path.join(iconsFolderPath, toolName + '-16.png')
			theIcon = QtGui.QIcon(iconPath)

			# see: https://stackoverflow.com/questions/45511056/pyqt-how-to-make-a-toolbar-button-appeared-as-pressed
			theAction = QtWidgets.QAction(theIcon, toolName, self)
			theAction.setCheckable(True)
			theAction.setStatusTip(toolName)
			theAction.triggered.connect(lambda checked, index=index: self.oneCallback3(index))

			self.toolList.append(theAction)
			self.addAction(theAction)

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

		'''
		toolName = 'Help'
		theIcon = QtGui.QIcon('icons/' + toolName + '-' + iconSizeStr + '.png')
		theAction = QtWidgets.QAction(theIcon, toolName, self)
		theAction.setStatusTip(toolName)
		callbackFn = functools.partial(self.oneCallback, toolName)
		theAction.triggered.connect(callbackFn)
		self.addAction(theAction)
		'''

	def oneCallback(self, id, checked):
		print('oneCallback() id:', id)

	def oneCallback3(self, index):
		print('oneCallback3() index:', index)
		action = self.toolList[index]
		print(action.statusTip(), action.isChecked())
