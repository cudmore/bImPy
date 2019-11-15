# Author: Robert Cudmore
# Date: 20190703

import os, sys, json
from collections import OrderedDict

import bimpy

class bCanvas:
	"""
	A visuospatial convas that brings together different light paths of a scope.
	"""
	def __init__(self, filePath=None, folderPath=''):
		"""
		filePath: path to .txt file to load a canvas
		folderPath: to load a converted Igor canvas
		"""
		self._filePath = filePath # todo: not used
		self._folderPath = folderPath # for Igor canvas

		self.optionsLoad()

		self._videoFileList = []
		self._scopeFileList = [] # images off the scope

		if filePath is not None:
			self.load()

	@property
	def videoFileList(self):
		return self._videoFileList

	@property
	def scopeFileList(self):
		return self._scopeFileList

	@property
	def enclosingFolder(self):
		""" Name of the enclosing folder"""
		return os.path.basename(os.path.normpath(self._folderPath))

	@property
	def videoFolderPath(self):
		return os.path.join(self._folderPath, self.enclosingFolder + '_video')

	def importIgorCanvas(self):
		"""
		Import Igor Canvas .txt file to grab xMotor/xMotor for each video and scope file
		"""
		# igor canvas file converted manually to .txt (in Igor)
		canvasTextFile = os.path.join(self._folderPath, 'cX' + self.enclosingFolder + '_T.txt')
		with open(canvasTextFile) as f:
			lines = f.readlines()
		for line in lines:
			#print(line)
			if line.startswith('StackName'):
				import_stackNameList = line.split(',')
			if line.startswith('stackType'):
				import_stackTypeList = line.split(',')
			if line.startswith('numSlices'):
				import_numSlicesList = line.split(',')

			if line.startswith('bitsPerPixel'):
				import_bitsPerPixel = line.split(',')
				print('=== import_bitsPerPixel:', import_bitsPerPixel)
			if line.startswith('pixelsPerLine'):
				import_pixelsPerLine = line.split(',')
			if line.startswith('linesPerFrame'):
				import_linesPerFrame = line.split(',')

			if line.startswith('vWidth'):
				import_vWidthList = line.split(',')
			if line.startswith('vHeight'):
				import_vHeightList = line.split(',')
			if line.startswith('motorx'):
				import_xMotorList = line.split(',')
			if line.startswith('motory'):
				import_yMotorList = line.split(',')
		# put what we loaded into a dictionary with stack name as key(s)
		self.import_stackDict = OrderedDict()
		for idx, stack in enumerate(import_stackNameList):
			stack = stack.rstrip()
			if idx>0 and len(stack) > 0: # idx>0 because first column is 'row' labels
				stack = stack.replace('_ch1', '')
				stack = stack.replace('_ch2', '')
				#print('stack: "' + stack + '"')
				self.import_stackDict[stack] = bimpy.bStackHeader() #OrderedDict()
				print(import_xMotorList[idx])
				self.import_stackDict[stack].header['stackType'] = import_stackTypeList[idx]
				self.import_stackDict[stack].header['numImages'] = int(import_numSlicesList[idx]) # just for video
				self.import_stackDict[stack].header['numChannels'] = 1 # just for video

				if len(import_bitsPerPixel[idx]) > 0:
					print('*** assigning bitsperpixel idx:', idx, 'value:', int(import_bitsPerPixel[idx]), 'stack:', stack)
					self.import_stackDict[stack].header['bitsPerPixel'] = int(import_bitsPerPixel[idx])
				else:
					print('*** NOT assigning bitsperpixel', idx, import_bitsPerPixel[idx], type(import_bitsPerPixel[idx]))
				self.import_stackDict[stack].header['xPixels'] = int(import_pixelsPerLine[idx]) # just for video
				self.import_stackDict[stack].header['yPixels'] = int(import_linesPerFrame[idx]) # just for video

				self.import_stackDict[stack].header['umWidth'] = float(import_vWidthList[idx]) # just for video
				self.import_stackDict[stack].header['umHeight'] = float(import_vHeightList[idx]) # just for video
				self.import_stackDict[stack].header['xMotor'] = float(import_xMotorList[idx])
				self.import_stackDict[stack].header['yMotor'] = float(import_yMotorList[idx])
		#print(self.import_stackDict)

	def buildFromScratch(self, folderPath=''):
		"""
		Given a folder path, build canvas from scratch
		"""
		if len(folderPath) > 0:
			self._folderPath = folderPath
		if not os.path.isdir(self._folderPath):
			# error
			print('error: bCanvas.buildFromScratch() did not find folderPath:', self._folderPath)

		#
		# video
		self._videoFileList = []

		videoFolderPath = self.videoFolderPath
		for videoFile in sorted(os.listdir(videoFolderPath)):
			if videoFile.startswith('.'):
				continue
			videoFilePath = os.path.join(videoFolderPath, videoFile)
			if not os.path.isfile(videoFilePath):
				continue

			print('bCanvas.buildFromScratch() videoFilePath:', videoFilePath)
			#videoTif = self.openVideoFile(videoFilePath)
			# 20190708, was this
			#videoFile = bVideoFile(self, videoFilePath)
			videoFile = bimpy.bStack(videoFilePath)
			videoFile.loadHeader() # at least makes default bStackHeader()
			#videoFile.getHeaderFromDict(self.import_stackDict)
			videoFile.header.importVideoHeaderFromIgor(self.import_stackDict)
			videoFile.loadStack()
			# this is only for import from igor
			# append to list
			self._videoFileList.append(videoFile)

		#
		# scope
		self._scopeFileList = []

		possibleImageFiles = ['.tif', '.oir']

		for scopeFile in sorted(os.listdir(self._folderPath)):
			if scopeFile.startswith('.'):
				continue

			baseScopeFileName, fileExtension = os.path.splitext(scopeFile)
			if fileExtension not in possibleImageFiles:
					continue

			scopeFilePath = os.path.join(self._folderPath, scopeFile)

			if not os.path.isfile(scopeFilePath):
				continue

			#print('bCanvas.buildFromScratch() scopeFilePath:', scopeFilePath)
			tmpStack = bimpy.bStack(scopeFilePath, loadImages=False)
			tmpStack.loadHeader()

			#print('tmpStack.header.prettyPrint():', tmpStack.header.prettyPrint())
			#print('tmpStack.header.getMetaData():', tmpStack.header.getMetaData())

			#if scopeFile in fakeMotorPositons.keys():
			baseScopeFileName = 'X' + baseScopeFileName
			print('baseScopeFileName:', baseScopeFileName)
			if baseScopeFileName in self.import_stackDict.keys():
				print('   **************** bCanvas.buildFromScratch() is adding motor position to header [[[FAKE DATA]]]')
				tmpStack.header.header['xMotor'] = self.import_stackDict[baseScopeFileName].header['xMotor']
				tmpStack.header.header['yMotor'] = self.import_stackDict[baseScopeFileName].header['yMotor']
				#tmpStack.header.header['xMotor'] = fakeMotorPositons[scopeFile]['xMotor']
				#tmpStack.header.header['yMotor'] = fakeMotorPositons[scopeFile]['yMotor']
			else:
				print ('   WARNING: scopeFile', baseScopeFileName, 'does not have an x/y motor position')

			self._scopeFileList.append(tmpStack)

	def _saveFile(self, stack):
		"""
		Generate a dict to save both (video/scope) files to json

		stack: pointer to stack
		"""
		header = stack.header
		fileDict = OrderedDict()
		# todo: make sure path get filled in in header !!!
		fileName = stack.fileName
		fileDict['filename'] = fileName

		fileDict['stackType'] = header.stackType
		fileDict['umWidth'] = header.umWidth
		fileDict['umHeight'] = header.umHeight
		fileDict['xMotor'] = header.xMotor
		fileDict['yMotor'] = header.yMotor
		fileDict['bitDepth'] = header.bitDepth # not necc?

		# canvas specific
		# is it visible in the canvas? Checkbox next to filname in canvas.
		fileDict['canvasIsVisible'] = True
		# contrast setting in canvas
		fileDict['canvasMinContrast'] = 0
		fileDict['canvasMaxContrast'] = 256

		return fileDict

	def save(self):
		"""
		Save the canvas to a text file

		todo: really need to define the minimal information required to reload a stack
		- each file (video and scanning) has a header we can quickly load?
		"""

		saveDict = OrderedDict() # the dictionary we will save

		# make a canvas options header
		saveDict['canvasOptions'] = OrderedDict()
		saveDict['canvasOptions']['windowWidth'] = 640
		saveDict['canvasOptions']['windowWidth'] = 480

		# video files
		saveDict['videoFiles'] = OrderedDict()
		for file in self.videoFileList:
			fileName = file.fileName
			thisDict = self._saveFile(file)
			saveDict['videoFiles'][fileName] = thisDict

		# scope files
		saveDict['scopeFiles'] = OrderedDict()
		for file in self.scopeFileList:
			fileName = file.fileName
			thisDict = self._saveFile(file)
			saveDict['scopeFiles'][fileName] = thisDict

		print('saveDict:', json.dumps(saveDict, indent=4))

		# write the dictionary to a file
		saveFilePath = os.path.join(self._folderPath, self.enclosingFolder + '_canvas.txt')
		with open(saveFilePath, 'w') as outfile:
			json.dump(saveDict, outfile)

	def load(self):
		"""
		Load a saved Python canvas

		todo: there should be some fields in saved json that are global to the canvas
		for example, window position
		"""
		#loadFilePath = os.path.join(self._folderPath, self.enclosingFolder + '_canvas.txt')

		with open(self._filePath) as f:
			data = json.load(f)
		print(' ')
		print ('bCanvas.load() loaded:')
		print('data:', json.dumps(data, indent=4))
		# iterate through keys in data and take action
		# e.g. ('canvasOptions', 'videofiles', 'scopefiles')
		for key, item in data.items():
			#print(key,item)
			if key == 'canvasOptions':
				print(item)
			elif key=='videoFiles':
				for file in item:
					print(file)
				#if stackType == 'bMovie':
				#	loadPath = os.path.join(self.videoFolderPath
			elif key =='scopeFiles':
				for file in item:
					pass
					#print(file)

	@property
	def optionsFile(self):
		"""
		Return the options .json file name
		"""

		if getattr(sys, 'frozen', False):
			# we are running in a bundle (frozen)
			bundle_dir = sys._MEIPASS
		else:
			# we are running in a normal Python environment
			bundle_dir = os.path.dirname(os.path.abspath(__file__))
		optionsFilePath = os.path.join(bundle_dir, 'bCanvas_Options.json')
		return optionsFilePath

	def optionsDefault(self):
		self._optionsDict = OrderedDict()
		self._optionsDict['version'] = 0.1

		self._optionsDict['video'] = OrderedDict()
		self._optionsDict['video']['umWidth'] = 693
		self._optionsDict['video']['umHeight'] = 433

	def optionsLoad(self):
		if not os.path.isfile(self.optionsFile):
			self.optionsDefault()
			self.optionsSave()
		else:
			with open(self.optionsFile) as f:
				self._optionsDict = json.load(f)

	def optionsSave(self):
		with open(self.optionsFile, 'w') as outfile:
			json.dump(self._optionsDict, outfile, indent=4, sort_keys=True)

if __name__ == '__main__':
	try:
		from bJavaBridge import bJavaBridge
		myJavaBridge = bJavaBridge()
		myJavaBridge.start()

		folderPath = '/Users/cudmore/Dropbox/data/20190429/20190429_tst2'
		folderPath = '/Users/cudmore/box/data/nathan/canvas/20190429_tst2'
		bc = bCanvas(folderPath=folderPath)
		#print(bc._optionsDict)

		bc.buildFromScratch()

		for videoFile in bc.videoFileList:
			print(videoFile._header)

		bc.save()

		'''
		tmpPath = '/Users/cudmore/Dropbox/data/20190429/20190429_tst2/20190429_tst2_0012.oir'
		from bStackHeader import bStackHeader
		tmpHeader = bStackHeader(tmpPath)
		tmpHeader.prettyPrint()
		'''

	finally:
		myJavaBridge.stop()
