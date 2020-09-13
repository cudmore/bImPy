# Author: Robert Cudmore
# Date: 20190704

import time
import traceback
#import logging
#logger = logging.getLogger(__name__)

import skimage # this is needed or else javabridge fails to import ???

try:
	#print('bJavaBridge.py is trying "import javabridge" ...')
	import javabridge
	import bioformats


	'''
	log4j = javabridge.JClassWrapper("loci.common.Log4jTools")
	log4j.enableLogging()
	log4j.setRootLevel("WARN")
	'''

	"""
	If you get
	    "Could not find Java JRE compatible with x86_64 architecture"
	then do this before running
	    export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-11.0.8.jdk/Contents/Home
	"""


except (ImportError) as e:
	javabridge = None
	bioformats = None
	print('Warning: bImPy bJavaBridge.py exception: failed to import javabridge or bioformats e:', e)
	#print(traceback.format_exc())

class bJavaBridge:
	"""
	Encapsulates javabridge to be able to use bioformats
	"""
	def __init__(self):
		self.isRunning = False
	def start(self):
		if javabridge is None:
			return

		if self.isRunning:
			print('javabridge already running')
		else:
			startTime = time.time()
			javabridge.start_vm(run_headless=True, class_path=bioformats.JARS)
			stopTime = time.time()
			print('bJavaBridge.start() took', round(stopTime - startTime,2), 'seconds to start.')
			self.isRunning = True

			print('  bJavaBridge.start() turning off bioformats logging')
			#bioformats.init_logger()

			# turn off logging, see:
			# ./bStack_env/lib/python3.7/site-packages/bioformats/log4j.py
			try:
				# see: https://github.com/CellProfiler/python-bioformats/blob/master/bioformats/log4j.py
				# loci.formats.FormatHandler
				# 1
				print('  loci.common.Log4jTools')
				log4j = javabridge.JClassWrapper("loci.common.Log4jTools")
				log4j.enableLogging()
				log4j.setRootLevel("WARN")
				# 2
				print('  loci.common.DebugTools')
				log4j = javabridge.JClassWrapper("loci.common.DebugTools")
				log4j.enableLogging()
				log4j.setRootLevel("WARN")

			except (AttributeError) as e:
				print('EXCEPTION in bJavaBridge.start() trying to turn off logging?')
				print('  e:', e)
				print(traceback.format_exc())

			#sys.exit()

	def stop(self):
		if javabridge is None:
			return

		if self.isRunning:
			javabridge.kill_vm()
			self.isRunning = False
			print('bJavaBridge.stop()')
		else:
			print('bJavaBridge.stop() javabridge is not running')

if __name__ == '__main__':
	jb = bJavaBridge()

	jb.start()

	jb.stop()
