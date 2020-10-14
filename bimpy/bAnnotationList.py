"""
20200831
"""

import os
from collections import OrderedDict
import json
import csv

import numpy as np

class bAnnotationList:
	def __init__(self, path):
		"""
		path: full path to either (_ch1.tif, _ch2.tif) stack
		"""
		self.path = path

		saveBasePath, tmpExt = os.path.splitext(self.path)
		folderPath, baseFileName = os.path.split(saveBasePath)

		channel = None
		if baseFileName.endswith('_ch1'):
			channel = 1
		elif baseFileName.endswith('_ch2'):
			channel = 2
		elif baseFileName.endswith('_ch2'):
			channel = 3
		else:
			pass
			#print('bAnnotationList.__init__() got bad baseFileName:', baseFileName, 'no (_ch1,_ch2,_ch3)')
			#print('  self.path:', self.path)
		self.channel = channel

		# remove _ch1/_ch2
		baseFileName = baseFileName.replace('_ch1', '')
		baseFileName = baseFileName.replace('_ch2', '')
		baseFileName = baseFileName.replace('_ch3', '')
		self.baseFileName = baseFileName

		# save by appending '_annotationList.csv'
		saveBasePath = os.path.join(folderPath, baseFileName)
		self.saveFilePath = saveBasePath + '_annotationList.csv'

		self.myList = [] # list of defaultDict

		self.plotDict = None

		#print('  bAnnotationList() self.saveFilePath:', self.saveFilePath)

	def numItems(self):
		return len(self.myList)

	def defaultDict(self):
		theDict = OrderedDict()
		theDict['idx'] = None # to work with bTableWidget2.py ... bAnnotationTableWidget()
		theDict['baseFileName'] = self.baseFileName
		theDict['channel'] = self.channel
		theDict['x'] = None
		theDict['y'] = None
		theDict['z'] = None
		theDict['rowNum'] = None # for napari grid
		theDict['colNum'] = None
		theDict['note'] = ''
		# keep this at end
		theDict['path'] = self.path
		return theDict

	def printList(self):
		print(f'bAnnotationList.printList() with {self.numItems()} items')
		for rowIdx, item in enumerate(self.myList):
			printRow = f'  {rowIdx+1} '
			for k,v in item.items():
				if k == 'path':
					continue
				printRow += f'{k}:{v}, '
			print('  ', printRow)

	def load(self):
		"""
		load from _annotationList.csv
		"""
		loadPath = self.saveFilePath

		if not os.path.isfile(loadPath):
			#print('  warning: bAnnotationList.load() did not find file:', loadPath)
			return

		self.myList = []

		print(f'  bAnnotationList.load() loading from {loadPath}')
		numLoadedLines = 0
		with open(loadPath, 'r') as data:
			for line in csv.DictReader(data):
				#print('  ', line)
				self.myList.append(line)
				numLoadedLines += 1

		self._preComputeMasks()

		print(f'    loaded {numLoadedLines} lines')

	def save(self):
		"""
		save to _annotationList.csv
		"""
		if self.numItems() == 0:
			#print('  bAnnotationList.save() nothing in list')
			return

		savePath = self.saveFilePath

		print(f'  bAnnotationList.save() saving {self.numItems()} annotation to {savePath}')

		keys = self.myList[0].keys()
		with open(savePath, 'w', newline='') as output_file:
			dict_writer = csv.DictWriter(output_file, keys)
			dict_writer.writeheader()
			dict_writer.writerows(self.myList)

	def addAnnotation(self, x, y, z, note='', rowNum=None, colNum=None):
		"""
		x/y/z: pixels
		rowNum/colNum: for napari grid
		"""
		x = round(x,4)
		y = round(y,4)
		z = int(z)

		newDict = self.defaultDict()
		newDict['idx'] = self.numItems()
		newDict['x'] = x
		newDict['y'] = y
		newDict['z'] = z
		newDict['rowNum'] = rowNum
		newDict['colNum'] = colNum
		newDict['note'] = note

		self.myList.append(newDict)

		newAnnotationIdx = self.numItems() - 1

		self._preComputeMasks()

		return newAnnotationIdx

	def deleteAnnotation(self, annotationIdx):
		self.myList.pop(annotationIdx)
		self._rebuildIdx()
		self._preComputeMasks()
		return True

	def _rebuildIdx(self):
		for idx, item in enumerate(self.myList):
			item['idx'] = idx

	def getItemDict(self, annotationIdx):
		return self.myList[annotationIdx]

	def getAnnotation_xyz(self, annotationIdx):
		x = self.myList[annotationIdx]['x']
		y = self.myList[annotationIdx]['y']
		z = self.myList[annotationIdx]['z']

		# on load these are (incorrectly) cast to str
		x = float(x)
		y = float(y)
		z = int(z)

		return x,y,z

	def getMaskDict(self):
		return self.plotDict

	def _preComputeMasks(self):
		"""
		self.plotDict: creat this
		"""

		# todo: make explicit for loop to just loop once and assign (xArray, yArray, zArray)
		xList = [item['x'] for item in self.myList]
		xArray = np.asarray(xList, dtype=np.float32)

		yList = [item['y'] for item in self.myList]
		yArray = np.asarray(yList, dtype=np.float32)

		zList = [item['z'] for item in self.myList]
		zArray = np.asarray(zList, dtype=np.uint16)

		indexList = [item['idx'] for item in self.myList]
		indexArray = np.asarray(indexList, dtype=np.uint16)

		self.plotDict = {}
		self.plotDict['x'] = xArray
		self.plotDict['y'] = yArray
		self.plotDict['z'] = zArray
		self.plotDict['annotationIndex'] = indexArray

		#return self.plotDict

if __name__ == '__main__':

	path = '/Users/cudmore/data/20200717/aicsAnalysis/20200717__A01_G001_0014_ch2.tif'

	# make new list
	myAnnotationList = bAnnotationList(path)

	if 0:
		# append object, save

		x = 10
		y = 20
		z = 30
		rowNum = None
		colNum = None
		note = 'xxx'
		myAnnotationList.addAnnotation(x, y, z, note=note, rowNum=rowNum, colNum=colNum)
		myAnnotationList.printList()
		myAnnotationList.save()

	if 1:
		myAnnotationList.load()
		myAnnotationList.printList()

		myAnnotationList._preComputeMasks()
		print('plotDict:')
		print('  ', myAnnotationList.plotDict)
