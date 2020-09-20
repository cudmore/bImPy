# Author: Robert Cudmore
# Date: 20190703

import os, sys, time, json, glob
from datetime import datetime
from collections import OrderedDict

import bimpy

class bCanvas:
	"""
	A visuospatial convas that brings together different light paths of a scope.
	"""
	def __init__(self, filePath=None, folderPath='', parent=None):
		"""
		filePath: path to _canvas.txt file to load a canvas
		folderPath: to load a converted Igor canvas (DEPRECIATED)
		parent: myCanvasWidget
		"""

		self.myCanvasWidget = parent # use, self.myCanvasWidget.myLogFilePositon
		self._filePath = None #filePath # todo: not used
		self._folderPath = None

		if filePath is not None:
			self._filePath = filePath
			self._folderPath, tmpFilename = os.path.split(filePath)
		print('bCanvas.__init__()')
		print('  _filePath:', self._filePath)
		print('  _folderPath:', self._folderPath)

		'''
		if len(folderPath)>0:
			self._folderPath = folderPath # for Igor canvas
		else:
			self._folderPath, tmpFilename = os.path.split(filePath)
		'''

		#self.optionsLoad()

		self._videoFileList = []
		self._scopeFileList = [] # images off the scope

		if filePath is not None and os.path.isfile(filePath):
			print('  bCanvas.__init__() is loading canvas:', filePath)
			self.load(filePath)
		else:
			# always save when we create a new canvas
			print('  bCanvas.__init__() is saving new canvas:', filePath)
			self.save()
	'''
	def findByName(self, filename):
		for file in self._videoFileList:
			if file.getFileName() == filename:
				return file
		return None
	'''

	'''
	def findScopeFileByName(self, filename):
		for file in self._scopeFileList:
			if file.getFileName() == filename:
				return file
		return None
	'''

	def appendVideo(self, newVideoStack):
		"""
		used when user acquires a new image from video

		see: bCanvasWidget.grabImage()
		"""
		self._videoFileList.append(newVideoStack)

	def importNewScopeFiles(self):
		"""
		look through files in our hard-drive folder and look for new files.
		A new file is one that is not already in self.scopeFileList
		"""
		newStackList = [] # build a list of new files
		listDir = os.listdir(self._folderPath)
		theseFileExtensions = ['.tif', '.oir']

		print('bCanvas.importNewScopeFiles()')
		print('  Looking in self._folderPath:', self._folderPath)
		print('  looking for files ending in theseFileExtensions:', theseFileExtensions)

		for potentialNewFile in listDir:
			tmpFile, fileExt = os.path.splitext(potentialNewFile)

			# adding option to load from folder of .tif
			folderPath = ''
			potentialFolder = os.path.join(self._folderPath, tmpFile)
			if os.path.isdir(potentialFolder):
				print('tmpFile is a folder, potentialFolder:', potentialFolder)
				# load from folder of tif
				fileList = glob.glob(potentialFolder + '/*.tif')
				fileList = sorted(fileList)
				if len(fileList) == 0:
					continue
				folderPath = potentialFolder
				potentialNewFile = fileList[0]
				print('  loading from folder:', folderPath)
				print('  seed file is:', potentialNewFile)
			# was this
			elif not fileExt in theseFileExtensions:
				continue
			#if not potentialNewFile.endswith(thisFileExtension):
			#	continue
			print('  bCanvas.importNewScopeFiles() considering file:', potentialNewFile)# check if file is in self.scopeFileList
			isInList = False
			for loadedScopeFile in self.scopeFileList:
				if loadedScopeFile.getFileName() == potentialNewFile:
					print('    already in self.scopeFileList, potentialNewFile:', potentialNewFile)
					isInList = True
					break
			if not isInList:
				# found a file that is not in scopeFileList
				# we need to find it in bLogFilePosition
				print('   New file:', potentialNewFile, 'find it in bLogFilePosition')
				newFilePath = os.path.join(self._folderPath, potentialNewFile)

				# abb canvas, we need a way to load header or max of .oir files?
				newScopeStack = bimpy.bStack(newFilePath, folderPath=folderPath, loadImages=True)

				# todo: put import in bCanvasWidget or bCanvasApp?
				# todo: at least make api to get motor frorm app
				# flip xMotor/xMotor for app
				if self.myCanvasWidget.myCanvasApp.xyzMotor.swapxy:
					tmp = newScopeStack.header.header['xMotor']
					newScopeStack.header.header['xMotor'] = newScopeStack.header.header['yMotor']
					newScopeStack.header.header['yMotor'] = tmp

				'''
				print('FAKE MOTOR POSITION FOR mp285')
				newScopeStack.header.header['xMotor'] = -2235
				newScopeStack.header.header['yMotor'] = -844.56
				'''

				# append to header
				# todo: on windows use os.path.getctime(path_to_file)
				# see: https://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python
				cTime = os.path.getctime(newFilePath)
				dateStr = time.strftime('%Y%m%d', time.localtime(cTime))
				timeStr = time.strftime('%H:%M:%S', time.localtime(cTime))


				newScopeStack.header.header['date'] = dateStr #time.strftime('%Y%m%d')
				newScopeStack.header.header['time'] = timeStr #datetime.now().strftime("%H:%M:%S.%f")[:-4]
				newScopeStack.header.header['seconds'] = cTime #time.time()
				print('   newScopeStack:', newScopeStack.print())

				print('  saving max')
				newScopeStack.saveMax()
				#print('      ', newScopeStack.header.prettyPrint())
				#print('      todo: fix this, adding fake motor !!! get motor position of file from bLogFilePosition !!!')
				useWatchFolder = self.myCanvasWidget.appOptions()['Scope']['useWatchFolder']
				if useWatchFolder:
					xPos, yPos = self.myCanvasWidget.myLogFilePositon.getFilePositon(potentialNewFile)
					if xPos is not None and yPos is not None:
						newScopeStack.header.header['xMotor'] = xPos
						newScopeStack.header.header['yMotor'] = yPos
					else:
						print('error: bCanvas.importNewScopeFiles() did not find file position for file:', potentialNewFile)
						newScopeStack.header.header['xMotor'] = 0
						newScopeStack.header.header['yMotor'] = 0
				# append to return list
				newStackList.append(newScopeStack)

				self._scopeFileList.append(newScopeStack)
				#print('*** importNewScopeFiles() REMEMBER TO SAVE !!!')

		return newStackList

	@property
	def videoFileList(self):
		return self._videoFileList

	@property
	def scopeFileList(self):
		return self._scopeFileList

	@property
	def enclosingFolder(self):
		""" Name of the enclosing folder"""
		if self._folderPath is None:
			print('error: @property enclosingFolder got None self._folderPath')
			return None
		else:
			return os.path.basename(os.path.normpath(self._folderPath))

	@property
	def videoFolderPath(self):
		if self._folderPath is None:
			print('error: @property videoFolderPath got None self._folderPath')
			return None
		else:
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
					print('*** assigning bitDepth idx:', idx, 'value:', int(import_bitsPerPixel[idx]), 'stack:', stack)
					self.import_stackDict[stack].header['bitDepth'] = int(import_bitsPerPixel[idx])
				else:
					print('*** NOT assigning bitDepth', idx, import_bitsPerPixel[idx], type(import_bitsPerPixel[idx]))
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

	def _saveFileDict(self, stack):
		"""
		Generate a dict to save both (video/scope) files to json

		stack: pointer to stack
		"""
		header = stack.header
		fileDict = OrderedDict()
		# todo: make sure path get filled in in header !!!
		fileName = stack.fileName
		fileDict['filename'] = fileName

		fileDict['folderPath'] = stack.folderPath # to open stack from folder of .tif

		fileDict['date'] = header.header['date']
		fileDict['time'] = header.header['time']
		fileDict['seconds'] = header.header['seconds']

		fileDict['stackType'] = header.stackType
		fileDict['bitDepth'] = header.bitDepth
		fileDict['pixelsPerLine'] = header.pixelsPerLine
		fileDict['linesPerFrame'] = header.linesPerFrame
		fileDict['numImages'] = header.numImages
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
		fileDict['canvasMaxContrast'] = header.bitDepth

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
			thisDict = self._saveFileDict(file)
			saveDict['videoFiles'][fileName] = thisDict

		# scope files
		saveDict['scopeFiles'] = OrderedDict()
		for file in self.scopeFileList:
			fileName = file.fileName
			thisDict = self._saveFileDict(file)
			saveDict['scopeFiles'][fileName] = thisDict

		#print('saveDict:', json.dumps(saveDict, indent=4))

		# write the dictionary to a file
		if self._folderPath is None or self.enclosingFolder is None:
			print('error: bCanvas.Save() got None self._folderPath or self.enclosingFolder')
			print('  -->> not saved')
			return

		saveFilePath = os.path.join(self._folderPath, self.enclosingFolder + '_canvas.txt')
		print('bCanvas.save() saving to:', saveFilePath)
		with open(saveFilePath, 'w') as outfile:
			json.dump(saveDict, outfile, indent=4)

	def load(self, thisFile = None):
		"""
		Load a saved Python canvas

		todo: there should be some fields in saved json that are global to the canvas
		for example, window position
		"""
		#loadFilePath = os.path.join(self._folderPath, self.enclosingFolder + '_canvas.txt')

		print('=== bCanvas.load() thisFile:', thisFile)

		if thisFile is not None:
			if os.path.isfile(thisFile):
				self._filePath = thisFile
				self._folderPath, tmpFilename = os.path.split(self._filePath)
				with open(self._filePath) as f:
					data = json.load(f)
			else:
				print('Warning: bCanvasApp.load() did not load thisFile:', thisFile)
				return

		'''
		print(' ')
		print ('bCanvas.load() loaded:')
		print('data:', json.dumps(data, indent=4))
		'''

		# iterate through keys in data and take action
		# e.g. ('canvasOptions', 'videofiles', 'scopefiles')
		for key, item in data.items():
			#print(key,item)
			if key == 'canvasOptions':
				print('bCanvas.load() key:', key, 'item:', item)
			elif key=='videoFiles':
				for fileName, fileDict in item.items():
					videoFilePath = os.path.join(self.videoFolderPath, fileName)
					print('  bCanvas.load() is loading videoFilePath:', videoFilePath)
					videoStack = bimpy.bStack(videoFilePath, loadImages=True)

					for headerStr,headerValue in fileDict.items():
						if headerStr in videoStack.header.header.keys():
							videoStack.header.header[headerStr] = headerValue
						else:
							# todo: put this back in
							#print('warning: bCanvas.load() did not find VideoFile key "' + headerStr + '" in file', fileName)
							videoStack.header.header[headerStr] = headerValue
					#videoStack.printHeader()
					# append to list
					self._videoFileList.append(videoStack)

			elif key =='scopeFiles':
				for fileName, fileDict in item.items():
					folderPath = fileDict['folderPath'] # to load from folder
					scopeFilePath = os.path.join(self._folderPath, fileName)
					print('  bCanvas.load() is loading folderPath:', folderPath, 'scopeFilePath:', scopeFilePath)

					# todo: we need to load from folder

					# folderPath will trump scopeFilePath
					scopeStack = bimpy.bStack(scopeFilePath, folderPath=folderPath, loadImages=False)
					scopeStack.loadMax()

					for headerStr,headerValue in fileDict.items():
						if headerStr in scopeStack.header.header.keys():
							# don't do this
							scopeStack.header.header[headerStr] = headerValue
							pass
						else:
							# todo: put this back in
							#print('warning: bCanvas.load() did not find ScopeFile key "' + headerStr + '" in file', fileName)
							scopeStack.header.header[headerStr] = headerValue
					#scopeStack.printHeader()

					# append to list
					self._scopeFileList.append(scopeStack)

	# abb 20200914, options are in main bCanvasApp
	'''
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
		optionsFilePath = os.path.join(bundle_dir, 'config', 'bCanvas_Options.json')
		return optionsFilePath

	def optionsDefault(self):
		self._optionsDict = OrderedDict()
		self._optionsDict['version'] = 0.1

		# put this in bCanvasApp
		"""
		self._optionsDict['video'] = OrderedDict()
		self._optionsDict['video']['umWidth'] = 693
		self._optionsDict['video']['umHeight'] = 433
		"""

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
	'''

if __name__ == '__main__':
	try:
		from bJavaBridge import bJavaBridge
		myJavaBridge = bJavaBridge()
		myJavaBridge.start()

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
