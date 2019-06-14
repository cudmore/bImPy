# Author: Robert Cudmore
# Date: 20190424

# Convert a folder of .oir files to .tif

import os, sys

import javabridge
import bioformats

import bStack

class bConvertFolder:

	def __init__(self, path):
		"""
		path: path to folder with oir files
		"""
		
		# make an output path
		outDir = os.path.dirname(path)
		folderName = os.path.basename(outDir)
		print(outDir)
		print(folderName)
		outFolder = folderName + '_out'
		outPath = os.path.join(outDir, outFolder)
		
		for file in os.listdir(path):
			if file.startswith('.'):
				continue
			if file.endswith('oir'):
				print(file)

			inFilePath = os.path.join(path, file)
			fileName = 
			
			outFilePath = os.path.join(outPath, fileName)
			
			myStack = bStack.bStack(inFilePath)
			myStack.loadStack()
			myStack.saveStack(path=outFilePath)
			myStack.saveHeader()
		
if __name__ == '__main__':
	if len(sys.argv) > 1:
		path = sys.argv[1]

		try:
			javabridge.start_vm(
        		run_headless=True,
				class_path=bioformats.JARS,
				)

			bcf = bConvertFolder(path)
			
		finally:
			javabridge.kill_vm()

	else:
		# error
		print('error: usage is bBatchConvertFolder foldername where folderPath is full path to folder to convert')	

