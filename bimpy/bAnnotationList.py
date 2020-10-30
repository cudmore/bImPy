"""
20200831

manage, save, load a list of annotation

this is created in bStack

"""

import os, json
from collections import OrderedDict
import csv # used to save
import ast # used to convert string (from file) into dict

import numpy as np
import pandas as pd # used to load
import scipy

import bimpy

class bAnnotationList:
	def __init__(self, bStackObject):
		"""
		path: full path to either (_ch1.tif, _ch2.tif) stack
		"""
		self.mySimpleStack = bStackObject
		self.path = bStackObject.path

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


		# todo: save/load into main h5f file !!!!!!
		print('\ntodo: bAnnotationList needs to save/load into main h5f file !!!!!!!\n')


		# save by appending '_annotationList.csv'
		saveBasePath = os.path.join(folderPath, baseFileName)
		self.saveFilePath = saveBasePath + '_annotationList.csv'

		self.myList = [] # list of defaultDict
		self.myMetaDataList = [] # list of dict holding roi analysis

		# bStack will hold an analysis object, run analysis with
		# x, lineKymograph, lineDiameter = self.analysis.stackLineProfile(src, dst)
		# and insert results into self.myMetaDataList

		self.plotDict = None

		#print('  bAnnotationList() self.saveFilePath:', self.saveFilePath)

		self.caimanDict = None # see self.loadCaiman

		# todo: not sure where to put this
		# parallel of metaDataDict from ShapeAnalysisPlugin

	def numItems(self):
		return len(self.myList)

	def setAnnotationIsBad(self, idx, newValue):
		print('bAnnotationList.setAnnotationIsBad() idx:', idx, 'newValue:', newValue)
		self.myList[idx]['isBad'] = newValue

		print('\nNEED TO FIX THIS bAnnotationList ["isBad"] is getting cast to str !!!!!\n')

		# whe using this to get a list of good caiman ROIs, always print the good list
		goodList = []
		for idx, item in enumerate(self.myList):
			# 20201020 FUCK FUCK FUCK ... these are strings ???
			#print(item['isBad'], type(item['isBad']))
			isBad = item['isBad']
			if isinstance(isBad, str):
				if isBad == 'True':
					pass
				else:
					goodList.append(idx)
			else:
				if item['isBad']:
					pass
				else:
					goodList.append(idx)
		print('good list is now:')
		print(goodList)

	def _getDefaultDict(self):
		"""
		todo: this is problematic, it is out of sync with xxx
		"""

		# this is tricky, annotations need a lot of things to please veryone
		# including 'a'+click general annotation
		# and pyqtgraph line/rect/circle roi

		theDict = OrderedDict()
		theDict['idx'] = None # to work with bTableWidget2.py ... bAnnotationTableWidget()
		theDict['type'] = None
		theDict['x'] = None
		theDict['y'] = None
		theDict['z'] = None

		theDict['isBad'] = False
		theDict['channel'] = self.channel
		theDict['note'] = ''

		# put all pyqtgraph roi into one key as a dict ???
		theDict['roiParams'] = None
		'''
		theDict['pos'] = None # for pyqtgraph roi
		theDict['size'] = None # for pyqtgraph roi
		theDict['pnt1'] = None # for pyqtgraph roi
		theDict['pnt2'] = None # for pyqtgraph roi
		theDict['lineWidth'] = None # for pyqtgraph roi
		'''

		theDict['rowNum'] = None # for napari grid
		theDict['colNum'] = None
		# these might be needed in future when mergin annotations
		# into a big table across many files
		#theDict['baseFileName'] = self.baseFileName
		#theDict['path'] = self.path

		#
		return theDict

	def _getDefaultMetaDataDict(self):
		metaDataDict = {
			'lineDiameter': np.zeros((0)),
			'lineKymograph': np.zeros((1,1)),
			'polygonMin': np.zeros((0)),
			'polygonMax': np.zeros((0)),
			'polygonMean': np.zeros((0)),
		}
		return metaDataDict

	def printList(self):
		print(f'bAnnotationList.printList() with {self.numItems()} items')
		for rowIdx, item in enumerate(self.myList):
			printRow = f'  {rowIdx+1} '
			for k,v in item.items():
				if k == 'path':
					continue
				printRow += f'{k}:{v}, '
			print('  ', printRow)

	def loadCaiman(self, forcePopulate=False):
		"""
		try and load caiman hdf5
		"""
		#caimanPath = '/home/cudmore/data/20201014/inferior/3_nif_inferior_cropped_results.hdf5'
		caimanPath, fileExt = os.path.splitext(self.path)
		caimanPath += '_results.hdf5'
		if not os.path.isfile(caimanPath):
			return
		print('bAnnotationList.loadCaiman() forcePopulate:', forcePopulate, 'is loading caimanPath:', caimanPath)

		self.caimanDict = bimpy.analysis.caiman.readCaiman(caimanPath)

		if self.numItems() == 0 or forcePopulate:

			self.myList = []

			numROI = self.caimanDict['numROI']
			print('  caimen numROI:', numROI)
			z = 1 # caiman roi do not have a z
			for roiIdx in range(numROI):
				(x, y) = bimpy.analysis.caiman.getCentroid(self.caimanDict, roiIdx)

				# flip (x,y)
				'''
				tmp = x
				x = y
				y = tmp
				'''

				print(f'  loadCaiman() adding centroid {roiIdx} at', x, y)
				self.addAnnotation('caiman', x, y, z)

	def load(self):
		"""
		load from _annotationList.csv
		"""
		loadPath = self.saveFilePath

		doLoad = True
		if not os.path.isfile(loadPath):
			#print('  warning: bAnnotationList.load() did not find file:', loadPath)
			doLoad = False

		self.myList = []

		if doLoad:
			print(f'  bAnnotationList.load() loading from {loadPath}')

			# I want to keep the OrderedDict() of self._getDefaultDict

			metaDataDict = self._getDefaultMetaDataDict()

			#
			# load with pandas
			numLoadedLines = 0
			try:
				data = pd.read_csv(loadPath)
			except(pd.errors.EmptyDataError) as e:
				print('ERROR: bAnnotationList.load() got an empty file:', loadPath)
			else:
				# to convert the whole CSV file to a list of dict use
				listOfDict = data.transpose().to_dict().values()
				numLoadedLines = len(listOfDict)
				for line in listOfDict:
					print('pandas line:', line)
					# convert dict value from string to dict
					if 'roiParams' in line.keys():
						#roiParamsLine = line['roiParams'].replace('\'', '\"')
						#print('roiParamsLine:', roiParamsLine)
						#line['roiParams'] = json.loads(roiParamsLine)
						line['roiParams'] = ast.literal_eval(line['roiParams'])
					self.myList.append(line)
					self.myMetaDataList.append(metaDataDict) # empty on load

			'''
			numLoadedLines = 0
			with open(loadPath, 'r') as data:
				for line in csv.DictReader(data):
					# the keys are out of order from what I want
					print('bAnnotationList.load()')
					print('    ', line)
					self.myList.append(line)
					self.myMetaDataList.append(metaDataDict) # empty on load
					numLoadedLines += 1
			'''

			self._preComputeMasks()

			print(f'    loaded {numLoadedLines} lines')

		# caiman rois
		forcePopulate = False
		self.loadCaiman(forcePopulate=forcePopulate)

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

	def addAnnotation(self, type, x, y, z, note='', rowNum=None, colNum=None, roiParams=None):
		"""
		x/y/z: pixels
		rowNum/colNum: for napari grid
		type: added for caiman

		roiParams: dict describing a pyqtgraph roi from (lineROI, rectROI, circleROI)
		"""
		print('bAnnotationList.addAnnotation()')

		x = round(x,4)
		y = round(y,4)
		z = int(z)

		newDict = self._getDefaultDict()
		newDict['idx'] = self.numItems()
		newDict['type'] = type
		newDict['x'] = x
		newDict['y'] = y
		newDict['z'] = z

		if roiParams is not None:
			newDict['roiParams'] = dict(roiParams)
		else:
			newDict['roiParams'] = roiParams

		newDict['rowNum'] = rowNum
		newDict['colNum'] = colNum
		newDict['isBad'] = False
		newDict['note'] = note

		self.myList.append(newDict)

		# each annotation also has metadata for analysis
		metaDataDict = self._getDefaultMetaDataDict()
		self.myMetaDataList.append(metaDataDict)

		newAnnotationIdx = self.numItems() - 1

		print('  addAnnotation() added newDict:')
		print('    ', json.dumps(newDict, indent=4))

		self._preComputeMasks()

		return newAnnotationIdx

	def deleteAnnotation(self, annotationIdx):
		self.myList.pop(annotationIdx)
		self.myMetaDataList.pop(annotationIdx)
		self._rebuildIdx()
		self._preComputeMasks()
		return True

	def _rebuildIdx(self):
		for idx, item in enumerate(self.myList):
			item['idx'] = idx

	# abb caiman to standardize interface
	def getAnnotationDict(self, idx):
		return self.getItemDict(idx)

	def getItemDict(self, annotationIdx):
		return self.myList[annotationIdx]

	def getMetadataDict(self, annotationIdx):
		return self.myMetaDataList[annotationIdx]

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

		typeList = [item['type'] for item in self.myList]

		# annotation (x,y) are in numpy order (vert,horz)
		# flipped
		'''
		tmpList = xList
		xList = yList
		yList = tmpList
		'''

		self.plotDict = {}
		self.plotDict['x'] = xArray
		self.plotDict['y'] = yArray
		self.plotDict['z'] = zArray
		self.plotDict['annotationIndex'] = indexArray
		self.plotDict['typeList'] = typeList

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
