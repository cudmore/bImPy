import sys, time

from qtpy import QtGui, QtCore, QtWidgets

from bimpy.interface.WaitingSpinner import WaitingSpinner

class bTmpSpinner(QtWidgets.QMainWindow):

	def __init__(self):
		super(bTmpSpinner, self).__init__()

		self.centralWidget = QtWidgets.QWidget()
		self.setCentralWidget(self.centralWidget)

		self.myVBoxLayout = QtWidgets.QVBoxLayout(self)
		self.centralWidget.setLayout(self.myVBoxLayout)

		button1 = QtWidgets.QPushButton('start')
		button1.clicked.connect(self.button_callback)
		self.myVBoxLayout.addWidget(button1)

		button2 = QtWidgets.QPushButton('stop')
		button2.clicked.connect(self.button_callback)
		self.myVBoxLayout.addWidget(button2)

		button3 = QtWidgets.QPushButton('long')
		button3.clicked.connect(self.button_callback)
		self.myVBoxLayout.addWidget(button3)

	def button_callback(self):
		sender = self.sender()
		title = sender.text()

		if title == 'start':
			self.showSpinner()
		elif title == 'stop':
			self.hideSpinner()
		elif title == 'long':
			startTime = time.time()
			while time.time()-startTime < 5:
				pass

	def showSpinner(self):

		print('starting spinner')
		#self.spinner = WaitingSpinner(self.centralWidget())
		self.spinner = WaitingSpinner(self, disableParentWhenSpinning=False)
		self.spinner.setRoundness(70.0)
		self.spinner.setMinimumTrailOpacity(15.0)
		self.spinner.setTrailFadePercentage(70.0)
		self.spinner.setNumberOfLines(12)
		self.spinner.setLineLength(10)
		self.spinner.setLineWidth(5)
		self.spinner.setInnerRadius(10)
		self.spinner.setRevolutionsPerSecond(1)
		self.spinner.setColor(QtGui.QColor(81, 4, 71))
		self.spinner.start()

	def hideSpinner(self):
		print('stopping spinner')
		self.spinner.stop()

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	mainWindow = bTmpSpinner()
	mainWindow.show()

	#bsb.showSpinner()

	#time.sleep(1)
	#input('press a key')

	#bsb.hideSpinner()

	sys.exit(app.exec_())
