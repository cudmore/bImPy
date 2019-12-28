# Robert Cudmore
# 20191117

import sys # to make menus on osx, sys.platform == 'darwin'

from PyQt5 import QtCore, QtWidgets, QtGui

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

		file.addAction('Save', self.save, QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_S))

		self.myMenuBar.addMenu(file)

	'''
	def processtrigger(self,q):
		print(q.text()+" is triggered")
	'''

	def new(self):
		print('=== bMenu.new')
		self.myCanvasApp.newCanvas()

	def open(self):
		print('bMenu.open')
		fname = QtWidgets.QFileDialog.getOpenFileName(caption='xxx load a canvas')
		print('bMenu.open() got user file selection:', fname)
		return 0

	def save(self):
		print('bMenu.save')
