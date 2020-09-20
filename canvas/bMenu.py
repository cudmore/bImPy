# Robert Cudmore
# 20191117

import os, sys # to make menus on osx, sys.platform == 'darwin'

import webbrowser # to show help

from PyQt5 import QtCore, QtWidgets, QtGui

import logging
bLogger = logging.getLogger('canvasApp')

import canvas

class bMenu:
	def __init__(self, parent):
		"""
		parent: bCanvasApp
		"""
		#self.parent = parent # the parent canvas app
		self.myCanvasApp = parent

		if sys.platform.startswith('darwin') :
			self.myMenuBar = QtGui.QMenuBar() # parentless menu bar for Mac OS
		else :
			self.myMenuBar = parent.menuBar() # refer to the default one

		file = self.myMenuBar.addMenu("File")
		file.addAction('New Canvas ...', self.new, QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_N))
		file.addAction('Open Canvas ...', self.open, QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_O))

		file.addSeparator()

		file.addAction('Save Canvas', self.save, QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_S))

		#file.addSeparator()

		file.addAction('Exit', self.quit, QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Q))

		self.myMenuBar.addMenu(file)

		# options menu
		options = self.myMenuBar.addMenu("Options")
		#options.addAction('Load Scope Config ...', self.loadScopeConfig)
		#options.addSeparator()
		#options.addAction('Load Users Config ...', self.loadUserConfig)
		#options.addSeparator()
		options.addAction('Canvas Options ...', self.showOptionsDialog)
		options.addAction('Set Data Path ...', self.setDataPath)
		options.addSeparator()
		options.addAction('Save Canvas Options ...', self.saveOption)
		options.addSeparator()
		options.addAction('Help ...', self.helpMenu)

		self.myMenuBar.addMenu(options)

		# windows menu
		self.windowMenu = self.myMenuBar.addMenu("Window")
		canvasDict = {}
		self.buildCanvasMenu(canvasDict)

		# help

		# video
		self.videoMenu = self.myMenuBar.addMenu("Video")
		self.videoMenu.addAction('Video Window ...', self.showVideoWindow)

	def showVideoWindow(self):
		self.myCanvasApp.toggleVideo()

	def buildCanvasMenu(self, canvasDict):
		bLogger.info('buildCanvasMenu')

		self.windowMenu.clear()

		canvasList = canvasDict.keys()
		#print('bMenu.buildCanvasMenu() canvasList:', canvasList)

		# get the path to file of the front canvas window
		frontWindow = self.myCanvasApp.myApp.activeWindow()
		activeFile = ''
		if isinstance(frontWindow, canvas.bCanvasWidget):
			activeFile = frontWindow.filePath
			activeFile = os.path.split(activeFile)[1]
			activeFile = os.path.splitext(activeFile)[0]

		if len(canvasList) == 0:
			# one 'None' item
			item = self.windowMenu.addAction('None')
			item.setDisabled(True)
		else:
			for canvasName in canvasList:
				item = self.windowMenu.addAction(canvasName)
				item.setCheckable(True)
				if canvasName == activeFile:
					item.setChecked(True)
				else:
					item.setChecked(False)
				item.triggered.connect(lambda chk, item=canvasName: self.doStuff(chk, item))
				#item = windowMenu.addAction(c, lambda item=item: self.doStuff(item))
				#self.connect(entry,QtCore.SIGNAL('triggered()'), lambda item=item: self.doStuff(item))

	def doStuff(self, checked, item):
		#print('doStuff() checked:', checked, 'item:', item)
		bLogger.info(f'doStuff() checked:{checked} item:{item}')
		self.myCanvasApp.bringCanvasToFront(item)

	def new(self):
		bLogger.info('bMenu.new()')
		self.myCanvasApp.newCanvas()

	def open(self):
		bLogger.info('bMenu.open()')
		self.myCanvasApp.load(askUser=True)

	def save(self):
		bLogger.info('bMenu.save() IS THIS IMPLEMENTED???')
		self.myCanvasApp.save()

	def quit(self):
		bLogger.info('quit menu')
		self.myCanvasApp.myApp.quit()

	'''
	def loadScopeConfig(self):
		print('bMenu.loadScopeConfig')
		self.myCanvasApp.optionsLoad(askUser=True)
	'''

	'''
	def loadUserConfig(self):
		print('bMenu.loadUserConfig() not implemented')
		#self.myCanvasApp.optionsLoad(askUser=True)
	'''

	def setDataPath(self):
		"""
		set ['Users']['xxx']
		"""
		bLogger.info('setDataPath')
		dirStr = QtWidgets.QFileDialog.getExistingDirectory(None)
		if len(dirStr) > 0:
			self.myCanvasApp.optionsSetSavePath(dirStr)

	def showOptionsDialog(self):
		bLogger.info('showOptionsDialog')
		optionsDict = self.myCanvasApp.options
		optionsDialog = canvas.bOptionsDialog(self.myCanvasApp, optionsDict)
		optionsDialog.acceptOptionsSignal.connect(self.myCanvasApp.slot_UpdateOptions)

		if optionsDialog.exec_():
			#print(optionsDialog.localOptions)
			pass

	def saveOption(self):
		self.myCanvasApp.optionsSave()

	def helpMenu(self):
		urlStr = 'https://cudmore.github.io/bImPy/canvas'
		webbrowser.open(urlStr, new=2)
