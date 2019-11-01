#20190809

import os
from collections import OrderedDict

from PyQt5 import QtGui, QtCore, QtWidgets

#from bSimpleStack import bSimpleStack
from bStackWindow import bStackWidget

class bStackBrowserWidget(QtWidgets.QWidget):
	def __init__(self, parent=None):
		super(bStackBrowserWidget, self).__init__(parent)

		self.myStackList = []

		self.setAcceptDrops(True)

		self.buildUI()

	def showStackWindow(self, path):
		alreadyOpen = False
		for stack in self.myStackList:
			if stack.path == path:
				# bring to front
				alreadyOpen = True
				break
		if alreadyOpen:
			stack.show()
			stack.activateWindow()
			stack.raise_()
		else:
			tmp = bStackWidget(path=path)
			tmp.show()
			self.myStackList.append(tmp)

	def appendStack(self, path):
		fileName = os.path.basename(path)
		c1 = QtWidgets.QTreeWidgetItem(self.myTreeWidget, ['', path, fileName, 'xxx', 'yyy', 'zzz'])

	def buildUI(self):

		self.setWindowTitle('Stack Browser')

		self.myVBoxLayout = QtWidgets.QVBoxLayout(self)

		# tree
		self.myColumnNames = ['Folder', 'Path', 'File', 'X Pixels', 'Y Pixels', 'Z Pixels']

		self.myTreeWidget = QtWidgets.QTreeWidget()
		self.myTreeWidget.setHeaderLabels(self.myColumnNames)

		'''
		cg = QtWidgets.QTreeWidgetItem(self.myTreeWidget, ['Drag and Drop'])
		cg.setExpanded(True)
		'''

		'''
		c1 = QtWidgets.QTreeWidgetItem(self.myTreeWidget, ['', '/Users/cudmore/box/DeepVess/data/immuno-stack/mytest.tif', 'mytest.tif', '512', '512', '100'])
		c1.setText(6, 'xxx')
		'''

		self.myTreeWidget.itemDoubleClicked.connect(self.itemDoubleClicked)

		self.myVBoxLayout.addWidget(self.myTreeWidget)

		self.move(50,50)
		self.resize(700, 300);

	def itemDoubleClicked(self, item, col):
		print('item:', item)
		print('col:', col)
		#path = self.myTreeWidget.selectedItems()[0].text(self._myCol('Path'))
		path = item.text(self._myCol('Path'))
		#print('itemDoubleClicked', path)
		self.showStackWindow(path)

	def _myCol(self, str):
		"""
		given a column name, return the column number
		"""
		theRet = None
		for idx, col in enumerate(self.myColumnNames):
			if col == str:
				theRet = idx
		if theRet is None:
			print('error:bStackBrowserWidget._myCol() did not find column name:', str)
		return theRet

	#
	# drag and drop
	#
	def dragEnterEvent(self, event):
		#print('dragEnterEvent:', event)
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		#print('dragMoveEvent:', event)
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		print('dropEvent:', event)
		if event.mimeData().hasUrls:
			for url in event.mimeData().urls():
				path = url.toLocalFile()
				print('   ', path)
				self.appendStack(path)
		else:
			event.ignore()

if __name__ == '__main__':
	import sys

	app = QtWidgets.QApplication(sys.argv)

	path = '/Users/cudmore/box/DeepVess/data/immuno-stack/mytest.tif'
	path = '/Users/cudmore/box/data/nathan/vesselucida/20191017__0001.tif'
	path = '/Users/cudmore/Sites/bImpy-Data/ca-smooth-muscle-oir/ca-smooth-muscle-oir_tif/20190514_0003_ch1.tif'

	myBrowser = bStackBrowserWidget()
	myBrowser.show()

	myBrowser.appendStack(path)
	myBrowser.showStackWindow(path)
	#tmp = myBrowser.loadStack(path)
	#print('tmp:', tmp)

	sys.exit(app.exec_())
