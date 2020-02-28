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

from QtWaitingSpinner import QtWaitingSpinner

import bimpy
#from bimpy import bJavaBridge
#from bimpy.interface import bStackWidget

'''
import logging
logger = logging.getLogger(__name__)
'''


#class bStackBrowser(QtWidgets.QWidget):
class bStackBrowser(QtWidgets.QMainWindow):
	"""
	A window that displays a list of stacks.
	Drag and drop to add a stack.
	Double-click to open a stack in a stack window.
	"""
	def __init__(self, parent=None):
		super(bStackBrowser, self).__init__()

		self.myStackList = []

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

		centralWidget = QtWidgets.QWidget()
		self.setCentralWidget(centralWidget)

		self.myVBoxLayout = QtWidgets.QVBoxLayout()
		centralWidget.setLayout(self.myVBoxLayout)

		# tree
		self.myColumnNames = ['Folder', 'Path', 'File', 'X Pixels', 'Y Pixels', 'Z Pixels']
		#self.myColumnNames = ['File', 'X Pixels', 'Y Pixels', 'Z Pixels']

		self.myTreeWidget = QtWidgets.QTreeWidget()
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
			#tmp = bimpy.interface.bStackWidget(path=path)
			print('starting spinner')
			spinner = QtWaitingSpinner(self.centralWidget())
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

			tmp = bimpy.interface.bStackWidget(path=path)
			tmp.show()

			print('stopping spinner')
			spinner.stop()

			self.myStackList.append(tmp)

	def appendStack(self, path):
		fileName = os.path.basename(path)
		c1 = QtWidgets.QTreeWidgetItem(self.myTreeWidget, ['', path, fileName, 'xxx', 'yyy', 'zzz'])
		#c1 = QtWidgets.QTreeWidgetItem(self.myTreeWidget, [fileName, 'xxx', 'yyy', 'zzz'])

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
			print('error:bStackBrowser._myCol() did not find column name:', str)
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

	app = QtWidgets.QApplication(sys.argv)

	path = '/Users/cudmore/box/DeepVess/data/immuno-stack/mytest.tif'

	# square image: 145, 640, 640
	path = '/Users/cudmore/box/data/nathan/vesselucida/20191017__0001.tif'
	#path = '/Users/cudmore/box/data/bImpy-Data/high-k-video/HighK-aligned-8bit-short.tif'
	#path = '/Users/cudmore/Sites/bImpy-Data/ca-smooth-muscle-oir/ca-smooth-muscle-oir_tif/20190514_0003_ch1.tif'

	# tall image, slice:134, width:1981, height:5783
	#path = '/Users/cudmore/box/data/nathan/vesselucida/tracing_20191217/tracing_20191217.tif'

	path = '/Users/cudmore/box/data/nathan/20200127_gelatin/vesselucida2/20200127__A01_G001_0011_croped.tif'

	#path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/OCTa/PV_Crop_Reslice.tif'

	path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/20191017/20191017__0001.tif'

	#path = '/Users/cudmore/box/data/bImpy-Data/testoir/20191017__0001.oir'


	try:
		mjb = bimpy.bJavaBridge()
		mjb.start()

		myBrowser = bimpy.interface.bStackBrowser()
		myBrowser.show()

		if os.path.isfile(path):
			myBrowser.appendStack(path)
			myBrowser.showStackWindow(path)
		else:
			print('__main__ did not find path:', path)

		mjb.stop()

	except (Exception) as e:
		print('bStackBrowser exception:', e)
		#print(traceback.format_exc())

		mjb.stop()

		raise

	sys.exit(app.exec_())
