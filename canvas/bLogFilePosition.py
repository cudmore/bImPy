# Robert Cudmore
# 20191106

"""
Watches a folder for new files and for each new file

1. Read (x,y) position from Prior Deck using bPrior (serial)
2. Append to .txt log file with (yyyymmdd, time, file name, x, y)
"""

import os, time, json
from datetime import datetime
import threading, queue
from collections import OrderedDict

#from canvas import bWatchFolder, bPrior
import canvas

class bLogFilePosition(threading.Thread):
	"""
	To be run as background thred.
	As new files appear in watched folder (path, e.g. bWatchFolder)

	For each new file, log a line to a text file

	On constructor, check if there is already a log file and load it
	"""
	def __init__(self, folderPath, stageController):
		"""
		folderPath: The folder to watch for new 2p scope files
		stageController: stage controller from the main bCanvasApp (we only want one stage controller)
		"""
		threading.Thread.__init__(self)

		print('bLogFilePosition() ready to watch folder, need to call run')
		print('  folderPath:', folderPath)
		print('  stageController:', stageController)

		self.path = folderPath

		# load log file if it exists
		#todo: put this in function, also used by self.run()
		watchFileName = os.path.basename(os.path.normpath(self.path))
		watchFileName += '_watched.txt'
		watchFileLogPath = os.path.join(self.path, watchFileName)
		self.myLogDict = OrderedDict()
		if os.path.isfile(watchFileLogPath):
			print('bLogFilePosition() is loading pre-existing log file watchFileLogPath:', watchFileLogPath)
			with open(watchFileLogPath) as f:
				# load as json!
				self.myLogDict = json.load(f)

		self.myStageController = stageController #bPrior(isReal=realPriorStage)

		self._stop_event = threading.Event()

		self.inQueue = queue.Queue() # queue is infinite length
		self.outQueue = queue.Queue()
		self.errorQueue = queue.Queue()
		self.myWatchFolder = canvas.bWatchFolder(path=self.path,
			inQueue=self.inQueue,
			outQueue=self.outQueue,
			errorQueue=self.errorQueue)
		self.myWatchFolder.daemon = True

		self.myWatchFolder.start()

		self.daemon = True
		self.start()

	# todo: we don't need this ???
	def setWatchFolder(self, path):
		if not os.path.isdir(path):
			print('error: bLogFilePosition.setWatchFolder() got a bad path:',path)
			return
		self.path = path
		self.myWatchFolder.setFolder(path)

	def getFilePositon(self, fileName):
		if fileName in self.myLogDict.keys():
			print('getFilePositon()', fileName, self.myLogDict[fileName])
			xPos = self.myLogDict[fileName]['xPos']
			yPos = self.myLogDict[fileName]['yPos']
			zPos = self.myLogDict[fileName]['zPos']
			return xPos, yPos, zPos
		else:
			return None, None

	def getPositionDict(Self):
		return self.myLogDict

	def run(self):
		print('bLogFilePosition.run()')
		while not self._stop_event.is_set():
			while not self.outQueue.empty():
				# item is file name
				item = self.outQueue.get(block=False)
				print('bLogFilePosition.run() found outQueue item:', item)
				# read position of motor from prior stage
				xPos, yPos, zPos = self.myStageController.readPosition()
				#print('xPos:', xPos, 'yPos:', yPos)

				#datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
				dateStr = datetime.today().strftime('%Y%m%d')
				timeStr = datetime.today().strftime('%H:%M:%S')
				logLine = dateStr + ',' + timeStr + ',' + item + ',' + str(xPos) + ',' + str(yPos)
				print('   logLine:', logLine)

				self.myLogDict[item] = OrderedDict()
				self.myLogDict[item]['filename'] = item
				self.myLogDict[item]['date'] = dateStr
				self.myLogDict[item]['time'] = timeStr
				self.myLogDict[item]['xPos'] = xPos
				self.myLogDict[item]['yPos'] = yPos
				self.myLogDict[item]['zPos'] = zPos
				#self.myLogList.append(logDict)
				# append to log file
				# log file should be in same folder as bWatchFolder path
				# ...
				watchPath = self.myWatchFolder.path
				watchFileName = os.path.basename(os.path.normpath(watchPath))
				watchFileName += '_watched.txt'
				watchFileLogPath = os.path.join(watchPath, watchFileName)
				print('   watchFileLogPath:', watchFileLogPath)
				with open(watchFileLogPath, 'w') as f:
					#f.write(logLine + '\n')
					json.dump(self.myLogDict, f, indent=4) #, sort_keys=True)
				time.sleep(0.1)
			time.sleep(0.1)

if __name__ == '__main__':
	path = None
	'''
	lfp = bLogFilePosition(path=path, realPriorStage=False)

	#path = '/Users/cudmore/Desktop/watchThisFolder'

	while True:
		try:
			pass
		except KeyboardInterrupt:
			pass
	'''
