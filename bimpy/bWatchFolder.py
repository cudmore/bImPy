# Robert H Cudmore
# 20191106

"""
Watch a folder for new files
"""

import os, time
import threading, queue

class bWatchFolder(threading.Thread):
	def __init__(self, path=None, inQueue=None, outQueue=None, errorQueue=None):
		"""
		path: full path to the folder to watch
		"""
		if path is not None and not os.path.isdir(path):
			print('error: bWatchFolder() got a bad path:',path)
			return
		self.path = path

		self.fileListSet = set()
		if path is not None:
			self.fileListSet = set(os.listdir(path))

		print('bWatchFolder() fileListSet:', self.fileListSet)

		threading.Thread.__init__(self)

		self._stop_event = threading.Event()

		self.inQueue = inQueue
		self.outQueue = outQueue
		self.errorQueue = errorQueue

	def setFolder(self, path):
		if path is None or os.path.isdir(path):
			self.path = path
		else:
			print('error bWatchFolder.setFolder() got bad path:', path)

	def stop(self):
		"""
		call stop() then join() to ensure thread is done
		"""
		self._stop_event.set()

	def run(self):
		print('bWatchFolder.run() started')
		try:
			while not self._stop_event.is_set():
				if self.path is not None:
					newFileListSet = set(os.listdir(self.path))
					#print('newFileListSet:', newFileListSet)
					for file in newFileListSet:
						if file not in self.fileListSet:
							print('bWatchFolder.run() new file:', file)
							# add the file to our list of files
							self.fileListSet.add(file)
							# transmit that we found a new file
							self.outQueue.put(file)
				# make sure not to remove this
				time.sleep(0.1)
		except Exception as e:
			self.errorQueue.put(e)
			raise
		print('bWatchFolder.run() ended')

if __name__ == '__main__':
	path = '/Users/cudmore/Desktop/watchThisFolder'

	inQueue = queue.Queue() # queue is infinite length
	outQueue = queue.Queue()
	errorQueue = queue.Queue()

	try:
		wf = bWatchFolder(path, inQueue=inQueue, outQueue=outQueue, errorQueue=errorQueue)
		# start thread
		wf.daemon = True
		wf.start()

		while True:
			try:
				exc = errorQueue.get(block=False)
				print('bWatchFolder() received errorQueue:', exc)
				pass
			except queue.Empty:
				pass

			while not outQueue.empty():
				'''
				We got a new item (file), have bCanvas:
					- read bPrior (x,y) motor position
					- append (date, time, file, x, y,) to .txt file
				'''
				item = outQueue.get(block=False)
				print('bWatchFolder.main() found outQueue item:', item)
		time.sleep(0.1)
	except KeyboardInterrupt:
		pass
	except:
		print('main() except clause')
		raise
	finally:
		# stop thread
		wf.stop()
		wf.join() # wait for it to really stop
