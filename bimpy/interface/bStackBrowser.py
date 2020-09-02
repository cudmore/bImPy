#20190809

import os
import traceback

#from PyQt5 import QtGui, QtCore, QtWidgets
from qtpy import QtGui, QtCore, QtWidgets

# we are not using bioformats, just testing if it is installed
try:
	import bioformats
except (Exception) as e:
	#print('exception: bStackBrowser failed to import bioformats e:', e)
	bioformats = None

#from bimpy.interface.WaitingSpinner import WaitingSpinner

import bimpy
#from bimpy import bJavaBridge
#from bimpy.interface import bStackWidget

'''
import logging
logger = logging.getLogger(__name__)
'''


class bFileTree(QtWidgets.QTreeWidget):
	def __init__(self, myStackBrowser):
		super(bFileTree, self).__init__()
		self.myStackBrowser = myStackBrowser

	def keyPressEvent(self, event):
		#print('=== bStackView.keyPressEvent() event.key():', event.key())

		keyStr = event.text()
		key = event.key()

		modifiers = QtWidgets.QApplication.keyboardModifiers()
		isShift = modifiers & QtCore.Qt.ShiftModifier

		if event.key() in [QtCore.Qt.Key_I]:
			print('=== user hit key "i"')
		elif isShift and event.key() in [QtCore.Qt.Key_P]:
			print('=== user hit key "P" ... scale the image')
		elif event.key() in [QtCore.Qt.Key_D, QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
			print('=== user hit key "d", close selected stack')
			selRow = self.currentIndex().row()
			print('    bFileTree.keyPressEvent() selRow:', selRow)
			self.myStackBrowser.closeStack(selRow)

#class bStackBrowser(QtWidgets.QWidget):
class bStackBrowser(QtWidgets.QMainWindow):
	"""
	A window that displays a list of stacks.
	Drag and drop to add a stack.
	Double-click to open a stack in a stack window.
	"""
	def __init__(self, parent=None):
		super(bStackBrowser, self).__init__()

		self.myFileList = [] # list of files that have been dropped
		self.myStackList = [] # stacks we have opened in a window

		self.setAcceptDrops(True)

		self.buildUI()

		myMenubar = self.menuBar()
		viewMenu = myMenubar.addMenu("View")

		# use setChecked()
		feedbackAction = QtWidgets.QAction("Feedback", self, checkable=True)
		feedbackAction.triggered.connect(self.feedbackMenu_Callback)
		viewMenu.addAction(feedbackAction)

	def feedbackMenu_Callback(self):
		print('feedbackMenu_Callback()')

	def buildUI(self):

		self.setWindowTitle('Stack Browser')

		self.centralWidget = QtWidgets.QWidget()
		self.setCentralWidget(self.centralWidget)

		self.myVBoxLayout = QtWidgets.QVBoxLayout()
		self.centralWidget.setLayout(self.myVBoxLayout)

		# tree
		self.myColumnNames = ['Folder', 'File', 'X Pixels', 'Y Pixels', 'Z Pixels', 'xVoxel', 'yVoxel', 'zVoxel', 'nNodes', 'nEdges', 'nGraphs']
		#self.myColumnNames = ['File', 'X Pixels', 'Y Pixels', 'Z Pixels']

		#self.myTreeWidget = QtWidgets.QTreeWidget()
		self.myTreeWidget = bFileTree(myStackBrowser=self)

		self.myTreeWidget.setHeaderLabels(self.myColumnNames)

		# set column widths
		#self.myTreeWidget.headerView().resizeSection(2, 500);
		header = self.myTreeWidget.header()
		header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
		header.setStretchLastSection(False)
		#header.setSectionResizeMode(5, QtWidgets.QHeaderView.Stretch)

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
		self.resize(700, 300)


	def closeStack(self, selRow):
		if bimpy.interface.myOkCancelDialog('close stack').canceled():
			return
		'''
		msg = QtWidgets.QMessageBox()
		msg.setIcon(QtWidgets.QMessageBox.Information)
		msg.setWindowTitle("Close Stack")
		msg.setText("Sure you want to close? Unsaved changes will be lost...")
		msg.setInformativeText("This is additional information")
		msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
		retval = msg.exec_()
		if retval == QtWidgets.QMessageBox.Cancel:
			return
		'''
		self.myFileList.pop(selRow)

		if self.myStackList[selRow] is not None:
			self.myStackList[selRow].close()
		self.myStackList.pop(selRow)

		# remove from tree
		self.myTreeWidget.takeTopLevelItem(selRow)

	def showStackWindow(self, rowIdx):
		path = self.myFileList[rowIdx]
		alreadyOpen = self.myStackList[rowIdx] is not None
		'''
		alreadyOpen = False
		for stack in self.myStackList:
			if stack.path == path:
				# bring to front
				alreadyOpen = True
				break
		'''
		if alreadyOpen:
			self.myStackList[rowIdx].show()
			self.myStackList[rowIdx].activateWindow()
			self.myStackList[rowIdx].raise_()
			'''
			stack.show()
			stack.activateWindow()
			stack.raise_()
			'''
		else:
			#tmp = bimpy.interface.bStackWidget(path=path)
			'''
			print('starting spinner')
			spinner = WaitingSpinner(self.myTreeWidget)
			spinner.setRoundness(70.0)
			spinner.setMinimumTrailOpacity(15.0)
			spinner.setTrailFadePercentage(70.0)
			spinner.setNumberOfLines(12)
			spinner.setLineLength(10)
			spinner.setLineWidth(5)
			spinner.setInnerRadius(10)
			spinner.setRevolutionsPerSecond(1)
			spinner.setColor(QtGui.QColor(81, 4, 71))
			spinner.start()
			'''

			tmp = bimpy.interface.bStackWidget(path=path, mainWindow=self)
			#self.myStackList.append(tmp)
			self.myStackList[rowIdx] = tmp
			tmp.show()

			# fill in columns
			nNodes = tmp.getMyStack().slabList.numNodes()
			nEdges = tmp.getMyStack().slabList.numEdges()

			updateItem = self.myTreeWidget.topLevelItem(rowIdx)
			nNodesCol = self.myColumnNames.index('nNodes') # this sometimes throws an exception
			updateItem.setText(nNodesCol, str(nNodes))
			nEdgesCol = self.myColumnNames.index('nEdges') # this sometimes throws an exception
			updateItem.setText(nEdgesCol, str(nEdges))

			'''
			print('stopping spinner')
			spinner.stop()
			'''


	def appendStack(self, path):
		print('appendStack() path:', path)

		try:
			existingIndex = self.myFileList.index(path)
			print('warning: file is already loaded:', path)
			return
		except (ValueError) as e:
			# not in list
			pass

		fileName = os.path.basename(path)

		parentFolderName = os.path.basename(os.path.dirname(path))

		header = bimpy.bStackHeader(path=path)
		xPixels = str(header.pixelsPerLine)
		yPixels = str(header.linesPerFrame)
		zPixels = str(header.numImages)
		#
		xVoxel = str(round(header.xVoxel,3))
		yVoxel = str(round(header.yVoxel,3))
		zVoxel = str(round(header.zVoxel,3))

		#print('xPixels:', xPixels, type(xPixels))

		self.myFileList.append(path)
		self.myStackList.append(None)

		c1 = QtWidgets.QTreeWidgetItem(self.myTreeWidget, [parentFolderName, fileName, xPixels, yPixels, zPixels, xVoxel, yVoxel, zVoxel])
		#c1 = QtWidgets.QTreeWidgetItem(self.myTreeWidget, [fileName, 'xxx', 'yyy', 'zzz'])

	def itemDoubleClicked(self, item, col):
		rowIdx = self.myTreeWidget.currentIndex().row()
		print('=== bStackBrowser.itemDoubleClicked() rowIdx:', rowIdx, 'item:', item, 'col:', col)

		#path = self.myTreeWidget.selectedItems()[0].text(self._myCol('Path'))
		#path = item.text(self._myCol('Path'))
		#print('itemDoubleClicked', path)

		# put back in
		#path = self.myFileList[rowIdx]
		self.showStackWindow(rowIdx)

	'''
	def _myCol(self, str):
		"""
		given a column name, return the column number
		"""
		theRet = None
		for idx, col in enumerate(self.myColumnNames):
			if col == str:
				theRet = idx
		if theRet is None:
			print('error:bStackBrowser._myCol() did not find column name:', str)
		return theRet
	'''

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
		print('=== bStackBrowser.dropEvent:')
		if event.mimeData().hasUrls:
			for url in event.mimeData().urls():
				path = url.toLocalFile()
				print('   path:', path)

				acceptedExtensions = ['.tif', '.oir']

				filename, extension = os.path.splitext(path)
				if extension in acceptedExtensions:
					if not path.endswith('.tif') and bioformats is None:
						print('   error: bStackBrowser.dropEvent() did not import bioformats, will only be able to open .tif files')
					else:
						self.appendStack(path)
				'''
				if path.endswith('.tif'):
					self.appendStack(path)
				else:
					print('error: can only drop .tif files')
				'''
		else:
			event.ignore()

if __name__ == '__main__':
	import sys

	useBioformats = False
	for i, arg in enumerate(sys.argv):
		#print('i:', i, 'arg:', arg)
		if arg == '--bioformats':
			useBioformats = True

	app = QtWidgets.QApplication(sys.argv)

	#
	path = '/Users/cudmore/box/Sites/DeepVess/data/20191017/blur/20191017__0001_z.tif'
	path = '/Users/cudmore/box/Sites/DeepVess/data/20191017/blur/20191017__0001.tif'

	path = '/Users/cudmore/box/Sites/DeepVess/data/invivo/blur/20190613__0028.tif'

	# this one xml tracing is broekn
	path = '/Users/cudmore/box/data/nathan/vascular-tracing/20191017/tifs/20191017_0001.tif'
	path = '/Users/cudmore/box/data/nathan/vascular-tracing/20191017/tifs/20191017_0002.tif'

	path = '/Users/cudmore/box/data/sami/Cell_1/1_5ADVMLEG1L1_ch2.tif'

	# abb aics
	path = '/Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch2.tif'

	# tryin z-expanded stack 'a'
	path = '/Users/cudmore/Box/data/20200717/aicsAnalysis/20200717__A01_G001_0014a_ch2.tif'
	try:
		if useBioformats:
			mjb = bimpy.bJavaBridge()
			mjb.start()

		myBrowser = bimpy.interface.bStackBrowser()
		myBrowser.show()

		if os.path.isfile(path):
			myBrowser.appendStack(path)
			myBrowser.showStackWindow(0)
		else:
			print('__main__ did not find path:', path)

		#mjb.stop()

	except (Exception) as e:
		print('bStackBrowser exception:', e)
		#print(traceback.format_exc())

		if useBioformats:
			mjb.stop()

		raise

	sys.exit(app.exec_()) # this will loop

	# this is never called ???
	'''
	if useBioformats:
		mjb.stop()
	print('bStackBrowser finished ...')
	'''
