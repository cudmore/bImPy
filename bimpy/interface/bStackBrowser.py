#20190809

import os
import traceback

#from PyQt5 import QtGui, QtCore, QtWidgets
from qtpy import QtGui, QtCore, QtWidgets

#import bimpy
from bimpy import bJavaBridge
from bimpy.interface import bStackWidget

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

		print('0 buildUI')
		centralWidget = QtWidgets.QWidget()
		self.setCentralWidget(centralWidget)

		print('1 buildUI')
		self.myVBoxLayout = QtWidgets.QVBoxLayout()
		centralWidget.setLayout(self.myVBoxLayout)

		print('2 buildUI')
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
			tmp = bStackWidget(path=path)
			tmp.show()

			# this works
			'''
			napariViewer = bNapari(path='', theStack=tmp.mySimpleStack)
			tmp.attachNapari(napariViewer)
			'''

			self.myStackList.append(tmp)


	def appendStack(self, path):
		fileName = os.path.basename(path)
		c1 = QtWidgets.QTreeWidgetItem(self.myTreeWidget, ['', path, fileName, 'xxx', 'yyy', 'zzz'])

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
		print('dropEvent:', event)
		if event.mimeData().hasUrls:
			for url in event.mimeData().urls():
				path = url.toLocalFile()
				print('bStackBrowser.dropEvent() path:', path)

				acceptedExtensions = ['.tif', '.oir']

				filename, extension = os.path.splitext(path)
				if extension in acceptedExtensions:
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

	path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/OCTa/PV_Crop_Reslice.tif'
	#path = '/Users/cudmore/box/data/bImpy-Data/vesselucida/20191017/20191017__0001.tif'

	#path = '/Users/cudmore/box/data/bImpy-Data/testoir/20191017__0001.oir'


	doJavabridge = False
	try:
		if doJavabridge:
			print('bStackBrowser __main__ starting bJavabridge')
			mjb = bJavaBridge()
			mjb.start()

		myBrowser = bStackBrowser()
		myBrowser.show()

		if os.path.isfile(path):
			myBrowser.appendStack(path)
			myBrowser.showStackWindow(path)
		else:
			print('__main__ did not find path:', path)
		#tmp = myBrowser.loadStack(path)
		#print('tmp:', tmp)

		'''
		from skimage import data
		import napari

		#with napari.gui_qt():
		viewer = napari.view_image(data.astronaut(), rgb=True)
		'''

		if doJavabridge:
			print('bStackBrowser __main__ stopping bJavabridge')
			mjb.stop()

	except (Exception) as e:
		print('exception:', e)
		print(traceback.format_exc())

		if doJavabridge:
			mjb.stop()

		raise

	sys.exit(app.exec_())
