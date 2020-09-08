"""
icons are at:
	https://www.flaticon.com/
"""

import functools

from qtpy import QtGui, QtCore, QtWidgets

import qdarkstyle #see: https://github.com/ColinDuquesnoy/QDarkStyleSheet

class MainWindow(QtWidgets.QMainWindow):

	def __init__(self, *args, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)

		self.setWindowTitle("My Awesome App")
		self.setGeometry(50, 50, 1200, 300)
		self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))

		label = QtWidgets.QLabel("THIS IS AWESOME!!!")
		label.setAlignment(QtCore.Qt.AlignCenter)

		self.setCentralWidget(label)

		# menus
		menubar = self.menuBar()
		menubar.setNativeMenuBar(False)
		bimpyMenu = menubar.addMenu('bImPy')
		optionsAction = QtWidgets.QAction('Options', self)
		optionsAction.triggered.connect(self.optionsMenu)
		bimpyMenu.addAction(optionsAction)

		#
		toolbar = QtWidgets.QToolBar("My main toolbar")
		toolbar.setIconSize(QtCore.QSize(32,32))
		toolbar.setToolButtonStyle( QtCore.Qt.ToolButtonTextUnderIcon )
		'''
		toolbar.setStyleSheet("""QToolBar {
			background-color: #32414B;
		}""")
		'''
		self.addToolBar(toolbar)

		toolNameList = ['Save', 'Options']
		for toolName in toolNameList:
			saveIcon = QtGui.QIcon('icons/' + toolName + '-16.png')
			saveAction = QtWidgets.QAction(saveIcon, toolName, self)
			saveAction.setStatusTip(toolName)
			saveAction.setCheckable(False)
			callbackFn = functools.partial(self.oneCallback, toolName)
			saveAction.triggered.connect(callbackFn)
			toolbar.addAction(saveAction)

		toolbar.addSeparator()

		'''
		button_action2 = QtWidgets.QAction(QtGui.QIcon("fugue-icons-3.5.6/icons/bug.png"), "Your button2", self)
		button_action2.setStatusTip("This is your button2")
		button_action2.triggered.connect(self.onMyToolBarButtonClick)
		button_action2.setCheckable(True)
		toolbar.addAction(button_action2)
		'''

		iconSizeStr = '16'


		toolListNames = ['Branch Points', 'Vessels', 'Annotations', 'Search', 'Contrast', 'Line Profile']
		self.toolList = []
		for index, toolName in enumerate(toolListNames):
			theIcon = QtGui.QIcon('icons/' + toolName + '-' + iconSizeStr + '.png')

			# see: https://stackoverflow.com/questions/45511056/pyqt-how-to-make-a-toolbar-button-appeared-as-pressed
			theAction = QtWidgets.QAction(theIcon, toolName, self)
			theAction.setCheckable(True)
			theAction.setStatusTip(toolName)
			theAction.triggered.connect(lambda checked, index=index: self.oneCallback3(index))

			self.toolList.append(theAction)
			toolbar.addAction(theAction)

		toolbar.addSeparator()

		toolName = 'Help'
		theIcon = QtGui.QIcon('icons/' + toolName + '-16.png')
		theAction = QtWidgets.QAction(theIcon, toolName, self)
		theAction.setStatusTip(toolName)
		callbackFn = functools.partial(self.oneCallback, toolName)
		theAction.triggered.connect(callbackFn)
		toolbar.addAction(theAction)

		toolbar.addSeparator()

		selectedLabel = QtWidgets.QLabel("Selected")
		selectedLabel.setStyleSheet("""
			QLabel {
				background-color: #19232D;
				border: 0px solid #32414B;
				padding: 2px;
				margin: 0px;
				color: #F0F0F0;
			}
		""")
		toolbar.addWidget(selectedLabel)
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

	def oneCallback3(self, index):
		print('oneCallback3() index:', index)
		action = self.toolList[index]
		print(action.statusTip(), action.isChecked())

	def oneCallback2(self, obj):
		print(' oneCallback2() toolTip:', obj.toolTip(), 'isChecked:', obj.isChecked())

	def oneCallback(self, id, checked):
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
	app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
	mw = MainWindow()
	mw.show()
	app.exec_()
