# Author: Robert Cudmore
# Date: 20190704

import time

import logging
logger = logging.getLogger(__name__)

import skimage # this is needed or else javabridge fails to import ???

try:
	import javabridge
except (ImportError) as e:
	print('bException: bJavaBridge failed to import javabridge e:', e)
	print('end bException')
	
import bioformats

class bJavaBridge:
	"""
	Encapsulates javabridge to be able to use bioformats
	"""
	def __init__(self):
		self.isRunning = False
	def start(self):
		if self.isRunning:
			print('javabridge already running')
		else:
			startTime = time.time()
			javabridge.start_vm(run_headless=True, class_path=bioformats.JARS)
			stopTime = time.time()
			print('bJavaBridge.start() took', round(stopTime - startTime,2), 'seconds to start.')
			self.isRunning = True
	def stop(self):
		if self.isRunning:
			javabridge.kill_vm()
			self.isRunning = False
		else:
			print('javabridge is not running')

if __name__ == '__main__':
	jb = bJavaBridge()

	jb.start()

	jb.stop()
