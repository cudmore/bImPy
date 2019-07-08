# Author: Robert Cudmore
# Date: 20190704

import bioformats
import javabridge

class bJavaBridge:
	def __init(self):
		self.isRunning = False
	def start(self):
		javabridge.start_vm(run_headless=True, class_path=bioformats.JARS)
		self.isRunning = True
	def stop(self):
		javabridge.kill_vm()
		self.isRunning = False
		
if __name__ == '__main__':
	import time
	jb = bJavaBridge()
	
	startTime = time.time()
	jb.start()
	stopTime = time.time()
	print('took this seconds to start:', stopTime - startTime)
	
	jb.stop()