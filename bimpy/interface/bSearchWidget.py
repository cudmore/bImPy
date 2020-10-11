import os
import json
import functools

from collections import OrderedDict

from qtpy import QtGui, QtCore, QtWidgets
#from PyQt5.QtCore import QObject, pyqtSlot
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
		# search parameters group
		searchGroupBox = QtWidgets.QGroupBox('Search Parameters')
		searchGroupBox.setStyleSheet(myStyleSheet)

		# search buttons group
		self.searchGroupBox2 = QtWidgets.QGroupBox('Search')
		self.searchGroupBox2.setStyleSheet(myStyleSheet)

		# search results
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

		joinedEdgesButton = QtWidgets.QPushButton("Joined Edges")
		joinedEdgesButton.setToolTip('Edges joined by a single node')

		# just use edge table
		#disconnectedEdgesButton = QtWidgets.QPushButton('Disconnected Edges')
		#disconnectedEdgesButton.clicked.connect(self.button_callback)

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
		joinedEdgesButton.clicked.connect(self.button_callback)
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
		searchGridLayout2.addWidget(joinedEdgesButton, row, 0)
		row += 1
		# just use edge table
		#searchGridLayout2.addWidget(disconnectedEdgesButton, row, 0)
		#row += 1

		# these are graph operation, todo: allow user to cancel
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
		searchGroupBox.setLayout(searchGridLayout)
		self.mainLayout.addWidget(searchGroupBox)

		self.searchGroupBox2.setLayout(searchGridLayout2)
		self.mainLayout.addWidget(self.searchGroupBox2)

		#
		# todo: rewrite above to add each group box sequentially, then we can mix/match

		#
		# search results group
		searchResultsGroupBox = QtWidgets.QGroupBox('Search Results')
		searchResultsGroupBox.setStyleSheet(myStyleSheet)

		searchResultsLayout = QtWidgets.QHBoxLayout()

		# set these as we receive slot_ on search progress
		# searched 28 nodes of 400 and found 12
		self.searchedLabel = QtWidgets.QLabel("Node 28")
		##self.searchOfLabel = QtWidgets.QLabel("of 400")
		##self.searchFoundLabel = QtWidgets.QLabel("found 12")

		self.cancelSearchButton = QtWidgets.QPushButton("Cancel")
		self.cancelSearchButton.setToolTip('Cancel Search')
		self.cancelSearchButton.clicked.connect(self.cancelSearch_callback)
		self.cancelSearchButton.setMaximumWidth(32)
		self.cancelSearchButton.setEnabled(False) # start disabled

		searchResultsLayout.addWidget(self.searchedLabel)
		#searchResultsLayout.addWidget(self.searchOfLabel)
		#searchResultsLayout.addWidget(self.searchFoundLabel)
		searchResultsLayout.addWidget(self.cancelSearchButton)

		# finalize
		searchResultsGroupBox.setLayout(searchResultsLayout)
		self.mainLayout.addWidget(searchResultsGroupBox)

	'''
	def mousePressEvent(self, event):
		print('bSearchWidget.mousePressEvent()')

		event.setAccepted(False)
		super().mousePressEvent(event)
	'''

	def _updateSearchGroup(self, newHitDict, finished=False):
		"""
		update the 'search results' as we get new search hits
		"""
		searchType = newHitDict['searchType']
		numSearched = newHitDict['numSearched']
		numToSearch = newHitDict['numToSearch']
		numFound = newHitDict['numFound']
		#self.searchedLabel.setText(f'{searchType} {numSearched}')
		'''
		self.searchedLabel.setText(f'{numSearched}')
		self.searchOfLabel.setText(f'of {numToSearch}')
		self.searchFoundLabel.setText(f'found {numFound}')
		'''
		try:
			newText = f'{numSearched:,} of {numToSearch:,} found {numFound}'
			self.searchedLabel.setText(newText)
		except (TypeError) as e:
			pass

		if finished:
			# turn of cancel button
			print('  _updateSearchGroup() turning off cancel')
			self.cancelSearchButton.setEnabled(False)
			self.searchGroupBox2.setEnabled(True)

	def slot_newSearch(self, newHitDict):
		"""
		update interface with number of objects we are about to search
		"""
		self._updateSearchGroup(newHitDict)

	def slot_newSearchHit(self, newHitDict):
		#print('bSearchWidget.slot_newSearchHit()')
		self._updateSearchGroup(newHitDict)

	def slot_finishedSearch(self, newHitDict):
		print('bSearchWidget.slot_finishedSearch()')
		self._updateSearchGroup(newHitDict, finished=True)

	def _getSearchParamDict(self):
		theDict = OrderedDict()
		theDict['distanceThreshold'] = self.minSpinBox.value()
		theDict['node1'] = self.node1SpinBox.value()
		theDict['node2'] = self.node2SpinBox.value()
		return theDict

	def cancelSearch_callback(self):
		print('\ncancelSearch_callback() !!!!!\n')
		self.mySearchAnnotation.doCancel = True

	def button_callback(self):
		print('=== bSearchWidget.button_callback()')
		sender = self.sender()
		title = sender.text()
		#bobID = sender.property('bobID')
		print('=== bSearchWidget.button_callback() title:', title) #, 'bobID:', bobID)

		self.doSearch(title)
		return

		# OLD REMOVE

		"""
		if title == 'Dead end near other slab':
			#distThreshold = self.minSpinBox.value()
			#self.mainWindow.signal('search 1', value=distThreshold)
			# abb oct2020
			self.doSearch(title)

		elif title == 'Dead end near other nodes':
			distThreshold = self.minSpinBox.value()
			self.mainWindow.signal('search 1_1', value=distThreshold)
		elif title == 'Slab Gaps':
			distThreshold = self.minSpinBox.value()
			self.mainWindow.signal('search 1_2', value=distThreshold)
		# elif title == '2':
		elif title == 'All Dead Ends':
			self.mainWindow.signal('search 2')

		##
		##
		# abb oct2020 use this as example for all others
		elif title == 'Close Nodes':
			#distThreshold = self.minSpinBox.value()
			# was this
			#self.mainWindow.signal('search 1_5', value=distThreshold)
			#searchParams = self._getSearchParamDict()
			self.doSearch(title)
		##
		##

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
			print('	bSearchWidget.button_callback() case not taken:', title)
		"""

	def doSearch(self, searchName):
		"""
		start a search based on button clicks

		todo: expand threshold to a dict of search criterion

		parameters:
			searchName: name/title of the button
		"""

		fn = None
		params = None
		searchType = None # will always be in (node search, edge search)

		if searchName == 'Close Nodes':
			fn = bimpy.interface.bSearchAnnotations.searchCloseNodes
			thresholdDist = self._getSearchParamDict()['distanceThreshold']
			params = thresholdDist # pass None for no parameters
			searchType = 'node search'
			#self.startSearch(fn, params, searchType)

		elif searchName == 'Dead end near other nodes':
			fn = bimpy.interface.bSearchAnnotations.searchDeadEnd2
			thresholdDist = self._getSearchParamDict()['distanceThreshold']
			params = thresholdDist # pass None for no parameters
			searchType = 'node search'

		elif searchName == 'Dead end near other slab':
			fn = bimpy.interface.bSearchAnnotations.searchDeadEnd
			thresholdDist = self._getSearchParamDict()['distanceThreshold']
			params = thresholdDist # pass None for no parameters
			searchType = 'node search'

		elif searchName == 'All Dead Ends':
			fn = bimpy.interface.bSearchAnnotations.allDeadEnds
			params = () # pass None for no parameters
			searchType = 'edge search'

		elif searchName == 'Slab Gaps':
			fn = bimpy.interface.bSearchAnnotations.searchSlabGaps
			thresholdDist = self._getSearchParamDict()['distanceThreshold']
			params = thresholdDist # pass None for no parameters
			searchType = 'edge search'

		elif searchName == 'Close Slabs':
			fn = bimpy.interface.bSearchAnnotations.searchCloseSlabs
			thresholdDist = self._getSearchParamDict()['distanceThreshold']
			params = thresholdDist # pass None for no parameters
			searchType = 'edge search'

		elif searchName == 'Joined Edges':
			fn = bimpy.interface.bSearchAnnotations.searchJoinEdges
			params = () # pass None for no parameters
			searchType = 'edge search'

		elif searchName == 'All Subgraphs':
			fn = bimpy.interface.bSearchAnnotations.allSubgraphs
			params = () # pass None for no parameters
			searchType = 'edge search'

		else:
			print(f'warning: bSearchWidget.doSearch() did not understand searchName: "{searchName}"')

		if fn is not None and params is not None and searchType is not None:
			self.startSearch(fn, params, searchType)
		else:
			print('error: did not perform search')

	def cancelSearch(self):
		self.mySearchAnnotation.cancelSearch()

	def startSearch(self, fn, params, searchType):
		"""
		Start a background search thread
		Use keyboard q to quit

		fn: pointer to search function to run, like: bimpy.bSearchAnnotations.searchDeadEnd2
		params:
		searchType: ('node search', 'edgeSearch') defines the type of object in search results
		"""

		# enable cancel button
		self.cancelSearchButton.setEnabled(True)
		# disable search button
		self.searchGroupBox2.setEnabled(False)

		# self.mainWindow is bStackWidget
		self.mySearchAnnotation = bimpy.interface.bSearchAnnotations(self.mainWindow.getMyStack().slabList,
							fn = fn,
							params = params,
							searchType = searchType)
		# connect self.mySearchAnnotation to *self to give feedback

		# the feedback
		self.mySearchAnnotation.searchNewSearchSignal.connect(self.slot_newSearch)
		self.mySearchAnnotation.searchNewHitSignal.connect(self.slot_newSearchHit)
		self.mySearchAnnotation.searchFinishedSignal.connect(self.slot_finishedSearch)

		# the table of results
		self.mySearchAnnotation.searchNewHitSignal.connect(self.searchTable().slot_newSearchHit)
		self.mySearchAnnotation.searchFinishedSignal.connect(self.searchTable().slot_SearchFinished)

		# start the actualsearch
		self.mySearchAnnotation.start()

		#print('xxx back in main thread')
