from qtpy import QtGui, QtCore, QtWidgets

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("My Awesome App")

        label = QtWidgets.QLabel("THIS IS AWESOME!!!")
        label.setAlignment(QtCore.Qt.AlignCenter)

        self.setCentralWidget(label)

        toolbar = QtWidgets.QToolBar("My main toolbar")
        self.addToolBar(toolbar)

        button_action = QtWidgets.QAction("Your button", self)
        button_action.setStatusTip("This is your button")
        button_action.triggered.connect(self.onMyToolBarButtonClick)
        toolbar.addAction(button_action)

        self.setStatusBar(QtWidgets.QStatusBar(self))


    def onMyToolBarButtonClick(self, s):
        print("click", s)

if __name__ == '__main__':
	app = QtWidgets.QApplication([])
	mw = MainWindow()
	mw.show()
	app.exec_()
