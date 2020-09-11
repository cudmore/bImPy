# Robert Cudmore
# 20191117

import sys # to make menus on osx, sys.platform == 'darwin'

from PyQt5 import QtCore, QtWidgets, QtGui

import logging
bLogger = logging.getLogger('canvasApp')

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

		file.addSeparator()

		file.addAction('Exit', self.quit, QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Q))

		self.myMenuBar.addMenu(file)

		# options menu
		options = self.myMenuBar.addMenu("Options")
		options.addAction('Load Scope Config ...', self.loadScopeConfig)
		options.addSeparator()
		options.addAction('Load Users Config ...', self.loadUserConfig)
		self.myMenuBar.addMenu(options)

	'''
	def processtrigger(self,q):
		print(q.text()+" is triggered")
	'''

	def new(self):
		print('=== bMenu.new')
		self.myCanvasApp.newCanvas()

	def open(self):
		print('bMenu.open() a canvas')
		self.myCanvasApp.load(askUser=True)

	def save(self):
		print('bMenu.save()')
		self.myCanvasApp.save()

	def quit(self):
		print('bMenu.quit')
		bLogger.info('quit menu')
		self.myCanvasApp.myApp.quit()

	def loadScopeConfig(self):
		print('bMenu.loadScopeConfig')
		self.myCanvasApp.optionsLoad(askUser=True)

	def loadUserConfig(self):
		print('bMenu.loadUserConfig() not implemented')
		#self.myCanvasApp.optionsLoad(askUser=True)
