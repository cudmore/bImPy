import os
import functools

from qtpy import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QObject, pyqtSlot
#from qtpy.QtCore import pyqtSlot

import bimpy

class bSearchWidget(QtWidgets.QWidget):
    def __init__(self, mainWindow, parent=None):
        super(bSearchWidget, self).__init__(parent)

        self.mainWindow = mainWindow
        self.buildUI()
        self.buildUI2()

    def searchTable(self):
        return self.editTable2

    def buildUI2(self):
        self.editTable2 = bimpy.interface.bTableWidget2('node search', self.mainWindow.mySimpleStack.slabList.editDictList, parent=self)
        self.mainLayout.addWidget(self.editTable2)

    def buildUI(self):
        myPath = os.path.dirname(os.path.abspath(__file__))
        mystylesheet_css = os.path.join(myPath, 'css', 'mystylesheet.css')
        with open(mystylesheet_css) as f:
            myStyleSheet = f.read()

        self.setFixedWidth(330)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)

        #
        # search group
        searchGroupBox = QtWidgets.QGroupBox('Search Parameters')
        searchGroupBox.setStyleSheet(myStyleSheet)

        searchGroupBox2 = QtWidgets.QGroupBox('Search')
        searchGroupBox2.setStyleSheet(myStyleSheet)

        searchGridLayout = QtWidgets.QGridLayout()
        searchGridLayout2 = QtWidgets.QGridLayout()

        row = 0

        spinBoxWidth = 64

        minLabel = QtWidgets.QLabel("Distance Threshold (um)")
        self.minSpinBox = QtWidgets.QSpinBox()
        self.minSpinBox.setMaximumWidth(spinBoxWidth)
        self.minSpinBox.setMinimum(0)
        self.minSpinBox.setMaximum(1e6)
        self.minSpinBox.setValue(10)

        nodeLabel = QtWidgets.QLabel("Nodes")
        nodeLabel.setMaximumWidth(spinBoxWidth)
        self.node1SpinBox = QtWidgets.QSpinBox()
        self.node1SpinBox.setMaximumWidth(spinBoxWidth)
        self.node1SpinBox.setMinimum(0)
        self.node1SpinBox.setMaximum(1e6)
        self.node1SpinBox.setValue(10)
        #
        self.node2SpinBox = QtWidgets.QSpinBox()
        self.node2SpinBox.setMaximumWidth(spinBoxWidth)
        self.node2SpinBox.setMinimum(0)
        self.node2SpinBox.setMaximum(1e6)
        self.node2SpinBox.setValue(20)

        searchGridLayout.addWidget(minLabel, row, 0)
        searchGridLayout.addWidget(self.minSpinBox, row, 1)
        #
        row += 1
        searchGridLayout.addWidget(nodeLabel, row, 0)
        searchGridLayout.addWidget(self.node1SpinBox, row, 1)
        searchGridLayout.addWidget(self.node2SpinBox, row, 2)

        row += 1

        button7 = QtWidgets.QPushButton("Dead end near other slab")
        button7.setToolTip('search for dead end nodes near a slab')
        button8 = QtWidgets.QPushButton("All Dead Ends")
        button8.setToolTip('search for all dead end edges')
        #
        button7_1 = QtWidgets.QPushButton("Dead end near other nodes")
        button7_2 = QtWidgets.QPushButton("Slab Gaps")
        #
        button8_1 = QtWidgets.QPushButton("Close Nodes")
        button8_1.setToolTip('Close Nodes')
        button8_2 = QtWidgets.QPushButton("Close Slabs")
        button8_2.setToolTip('Close Slabs')

        disconnectedEdgesButton = QtWidgets.QPushButton('Disconnected Edges')
        disconnectedEdgesButton.clicked.connect(self.button_callback)

        #
        button9 = QtWidgets.QPushButton("Shortest Path")
        button9.setToolTip('search for shortest path between nodes')
        button10 = QtWidgets.QPushButton("All Paths")
        button10.setToolTip('search for all paths between nodes')
        #
        button7.clicked.connect(self.button_callback)
        button7_1.clicked.connect(self.button_callback)
        button7_2.clicked.connect(self.button_callback)
        button8.clicked.connect(self.button_callback)
        button8_1.clicked.connect(self.button_callback)
        button8_2.clicked.connect(self.button_callback)
        button9.clicked.connect(self.button_callback)
        button10.clicked.connect(self.button_callback)

        row = 0
        searchGridLayout2.addWidget(button7, row, 0)
        searchGridLayout2.addWidget(button8, row, 1)
        row += 1
        searchGridLayout2.addWidget(button7_1, row, 0)
        searchGridLayout2.addWidget(button7_2, row, 1)
        row += 1
        searchGridLayout2.addWidget(button8_1, row, 0)
        searchGridLayout2.addWidget(button8_2, row, 1)
        row += 1
        searchGridLayout2.addWidget(disconnectedEdgesButton, row, 0)
        # these are graph operation, todo: allow user to cancel
        row += 1
        searchGridLayout2.addWidget(button9, row, 0)
        searchGridLayout2.addWidget(button10, row, 1)

        row += 1
        button11 = QtWidgets.QPushButton("All Subgraphs")
        button11.setToolTip('Shortest All Subgraphs')
        '''
        button11 = QtWidgets.QPushButton("Shortest Loop")
        button11.setToolTip('Shortest Loop')
        button11.setEnabled(False) # shortest loop does not work, use "All Loops"
        '''
        button12 = QtWidgets.QPushButton("All Loops (slow)")
        button12.setToolTip('All Loops (slow)')
        #
        button11.clicked.connect(self.button_callback)
        button12.clicked.connect(self.button_callback)
        #
        searchGridLayout2.addWidget(button11, row, 0)
        searchGridLayout2.addWidget(button12, row, 1)

        # finalize
        # was this
        searchGroupBox.setLayout(searchGridLayout)
        self.mainLayout.addWidget(searchGroupBox)

        searchGroupBox2.setLayout(searchGridLayout2)
        self.mainLayout.addWidget(searchGroupBox2)

    '''
    def mousePressEvent(self, event):
        print('bSearchWidget.mousePressEvent()')

        event.setAccepted(False)
        super().mousePressEvent(event)
    '''

    def button_callback(self):
        print('=== bSearchWidget.button_callback()')
        sender = self.sender()
        title = sender.text()
        bobID = sender.property('bobID')
        print('=== bSearchWidget.button_callback() title:', title, 'bobID:', bobID)

        if title == 'Dead end near other slab':
            distThreshold = self.minSpinBox.value()
            self.mainWindow.signal('search 1', value=distThreshold)
        elif title == 'Dead end near other nodes':
            distThreshold = self.minSpinBox.value()
            self.mainWindow.signal('search 1_1', value=distThreshold)
        elif title == 'Slab Gaps':
            distThreshold = self.minSpinBox.value()
            self.mainWindow.signal('search 1_2', value=distThreshold)
        # elif title == '2':
        elif title == 'All Dead Ends':
            self.mainWindow.signal('search 2')
        elif title == 'Close Nodes':
            distThreshold = self.minSpinBox.value()
            self.mainWindow.signal('search 1_5', value=distThreshold)
        elif title == 'Close Slabs':
            distThreshold = self.minSpinBox.value()
            self.mainWindow.signal('search 1_6', value=distThreshold)
        # elif title == '3':
        elif title == 'Shortest Path':
            # shortest path
            node1 = self.node1SpinBox.value()
            node2 = self.node2SpinBox.value()
            self.mainWindow.signal('search 3', value=(node1, node2))
        # elif title == '4':
        elif title == 'All Paths':
            # all paths
            node1 = self.node1SpinBox.value()
            node2 = self.node2SpinBox.value()
            self.mainWindow.signal('search 4', value=(node1, node2))

        # elif title == 'Shortest Loop':
        #	# all paths
        #	node1 = self.node1SpinBox.value()
        #	self.mainWindow.signal('search 5', value=node1)

        elif title == 'All Subgraphs':
            # all subgraphs
            self.mainWindow.signal('search 5')

        elif title == 'All Loops (slow)':
            # all paths
            node1 = self.node1SpinBox.value()
            self.mainWindow.signal('search 6', value=node1)

        elif title == 'Disconnected Edges':
            self.mainWindow.signal('Disconnected Edges')

        #
        # analysis
        elif title == 'Analyze All Diameters':
            self.mainWindow.signal('Analyze All Diameters')  # calls slabList.analyseSlabIntensity()


        else:
            print('    bSearchWidget.button_callback() case not taken:', title)
