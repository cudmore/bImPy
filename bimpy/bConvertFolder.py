import os, sys, time

import javabridge
import bioformats


import Stack

covertIfTifExists = False

def convert(path):
	
	#
	# build a list of .oir files that do not already have converted .tif
	convertTheseOirFiles = []
	for file in os.listdir(path):
		if file.startswith('.'):
			continue
		if file.endswith('.oir'):
	
			filePath = os.path.join(path, file)
		
			myStack = Stack.Stack(filePath)
			savePath = myStack.convert_getSaveFile(channelNumber=1)

			if covertIfTifExists or not os.path.isfile(savePath):
				#print('   output does not exist')
				convertTheseOirFiles.append(filePath)
			
	print('bConvertFolder is converting', len(convertTheseOirFiles), 'oir files in path', path)

	#
	# convert .oir to .tif
	if len(convertTheseOirFiles) > 0:

		with javabridge.vm(
				run_headless=True,
				class_path=bioformats.JARS
				):

			# turn off logging, see:
			# ./bStack_env/lib/python3.7/site-packages/bioformats/log4j.py
		
			log4j = javabridge.JClassWrapper("loci.common.Log4jTools")
			log4j.enableLogging()
			log4j.setRootLevel("WARN")

			for idx, oirFile in enumerate(convertTheseOirFiles):
				print(str(idx+1), 'of', len(convertTheseOirFiles), 'converting:', oirFile)
				Stack.Stack(oirFile).convert()

if __name__ == '__main__':

	startSeconds = time.time()
	
	path = ''
	if len(sys.argv) == 2:
		path = sys.argv[1]
	
	if os.path.isdir(path):
		convert(path)
		stopSeconds = time.time()
		print('bConvertFolder finished in', round(stopSeconds-startSeconds), 'seconds.')
	else:
		print('error: bConvertFolder() expects the full path to a folder with oir files.')
		
