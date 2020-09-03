"""
icons are at:
	https://www.flaticon.com/
"""

import functools

from qtpy import QtGui, QtCore, QtWidgets

class MainWindow(QtWidgets.QMainWindow):

	def __init__(self, *args, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)

		self.setWindowTitle("My Awesome App")
		self.setGeometry(50, 50, 500, 300)
		self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))

		label = QtWidgets.QLabel("THIS IS AWESOME!!!")
		label.setAlignment(QtCore.Qt.AlignCenter)

		self.setCentralWidget(label)

		#
		menubar = self.menuBar()
		menubar.setNativeMenuBar(False)
		bimpyMenu = menubar.addMenu('bImPy')
		optionsAction = QtWidgets.QAction('Options', self)
		optionsAction.triggered.connect(self.optionsMenu)
		bimpyMenu.addAction(optionsAction)

		#
		toolbar = QtWidgets.QToolBar("My main toolbar")
		toolbar.setIconSize(QtCore.QSize(32,32))
		self.addToolBar(toolbar)

		saveIcon = QtGui.QIcon("icons/save.png")
		saveAction = QtWidgets.QAction(saveIcon, "Save", self)
		saveAction.setStatusTip("Save")
		saveAction.triggered.connect(self.saveActionCallback)
		toolbar.addAction(saveAction)

		optionsAction = QtWidgets.QAction(QtGui.QIcon("icons/settings.png"), "Options", self)
		optionsAction.setStatusTip("Options")
		optionsAction.triggered.connect(self.optionsActionCallback)
		#optionsAction.setCheckable(True)
		toolbar.addAction(optionsAction)

		toolbar.addSeparator()

		'''
		button_action2 = QtWidgets.QAction(QtGui.QIcon("fugue-icons-3.5.6/icons/bug.png"), "Your button2", self)
		button_action2.setStatusTip("This is your button2")
		button_action2.triggered.connect(self.onMyToolBarButtonClick)
		button_action2.setCheckable(True)
		toolbar.addAction(button_action2)
		'''

		toolList = ['Branch Points', 'Vessels', 'Annotations', 'Search', 'Contrast', 'Line Profile']
		for toolName in toolList:
			theIcon = QtGui.QIcon('icons/' + toolName + '.png')
			theAction = QtWidgets.QAction(theIcon, toolName, self)
			theAction.setStatusTip(toolName)
			callbackFn = functools.partial(self.oneCallback, toolName)
			theAction.triggered.connect(callbackFn)
			'''
			theAction.setStyleSheet("""
			    QMenuBar {
			        background-color: rgb(49,49,49);
			        color: rgb(255,255,255);
			        border: 1px solid ;
			    }

			    QAction::item {
			        background-color: rgb(49,49,49);
			        color: rgb(255,255,255);
			    }

			    QAction::item::selected {
			        background-color: rgb(30,30,30);
			    }
			""")
			'''
			toolbar.addAction(theAction)

		toolbar.addSeparator()

		toolName = 'Help'
		theIcon = QtGui.QIcon('icons/' + toolName + '.png')
		theAction = QtWidgets.QAction(theIcon, toolName, self)
		theAction.setStatusTip(toolName)
		callbackFn = functools.partial(self.oneCallback, toolName)
		theAction.triggered.connect(callbackFn)
		toolbar.addAction(theAction)

		# invert
		toolName = 'Help'
		pixmap = QtGui.QPixmap('icons/' + toolName + '.png')
		mask = pixmap.createMaskFromColor(QtGui.QColor('black'), QtCore.Qt.MaskOutColor)
		pixmap.fill((QtGui.QColor('black')))
		pixmap.setMask(mask)

		toolName = 'Help'
		#theIcon = QtGui.QIcon('icons/' + toolName + '.png')
		theIcon = QtGui.QIcon(pixmap)
		theAction = QtWidgets.QAction(theIcon, toolName, self)
		theAction.setStatusTip(toolName)
		callbackFn = functools.partial(self.oneCallback, toolName)
		theAction.triggered.connect(callbackFn)
		toolbar.addAction(theAction)

		toolbar.addSeparator()

		toolbar.addWidget(QtWidgets.QLabel("Selected"))
		toolbar.addWidget(QtWidgets.QLabel("Node"))

		self.badCheckBox = QtWidgets.QCheckBox()
		self.badCheckBox.stateChanged.connect(self.checkboxChange)
		toolbar.addWidget(QtWidgets.QLabel("Bad"))
		toolbar.addWidget(self.badCheckBox)

		self.myComboBox = QtWidgets.QComboBox()
		self.myComboBox.addItem('xxx')
		self.myComboBox. addItems(["Java", "C#", "Python"])
		self.myComboBox.currentIndexChanged.connect(self.selectionchange)
		toolbar.addWidget(QtWidgets.QLabel("Type"))
		toolbar.addWidget(self.myComboBox)

		self.noteEdit = QtWidgets.QLineEdit()
		self.noteEdit.setText('default text')
		self.noteEdit.editingFinished.connect(self.noteEdited)
		toolbar.addWidget(QtWidgets.QLabel("Note"))
		toolbar.addWidget(self.noteEdit)

		self.setStatusBar(QtWidgets.QStatusBar(self))

	def oneCallback(self, id):
		print('oneCallback() id:', id)

	def optionsMenu(self):
		print('optionsMenu()')

	def checkboxChange(self, onOff):
		"""
		onOff: 0 is off, 2 is on
		"""
		print('checkboxChange() onOff:', onOff)

	def selectionchange(self, selectedIdx):
		print('selectionchange() selectedIdx:', selectedIdx)
		#for count in range(self.myComboBox.count()):
		#	print(self.myComboBox.itemText(count))
		print("Current index",selectedIdx,"selection changed ",self.myComboBox.currentText())

	def noteEdited(self):
		"""
		This signal is emitted when the Return or Enter key is pressed or the line edit loses focus
		"""
		print('noteEdit() self.noteEdit.text()', self.noteEdit.text())

	def saveActionCallback(self, s):
		print('saveActionCallback() s:', s)

	def optionsActionCallback(self, s):
		print('optionsActionCallback() s:', s)

	def edgeActionCallback(self, s):
		print('edgeActionCallback()')

	def onMyToolBarButtonClick(self, s):
		print("click", s)

if __name__ == '__main__':
	app = QtWidgets.QApplication([])
	mw = MainWindow()
	mw.show()
	app.exec_()
