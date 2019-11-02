import os, sys, time

import tkinter
from tkinter.filedialog import askdirectory

import javabridge
import bioformats

# we can't do this, we need to import the entire bimpy package !!!
# this took me forever to figure out and in the end is simple ...
#from bimpy import bStack
import bimpy

covertIfTifExists = False

def bConvert(path):

	#
	# build a list of .oir files that do not already have converted .tif
	convertTheseOirFiles = []
	for file in os.listdir(path):
		if file.startswith('.'):
			continue
		if file.endswith('.oir'):

			filePath = os.path.join(path, file)

			myStack = bimpy.bStack(filePath, loadImages=False)
			savePath = myStack.convert_getSaveFile(channelNumber=1)

			print('savePath:', savePath)

			if covertIfTifExists or not os.path.isfile(savePath):
				#print('   output does not exist')
				convertTheseOirFiles.append(filePath)
			else:
				print('skipping file, .tif alread exists', savePath)

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
				aStack = bimpy.bStack(oirFile, loadImages=False)
				aStack.convert()

if __name__ == '__main__':

	startSeconds = time.time()

	path = ''
	if len(sys.argv) == 2:
		path = sys.argv[1]
	else:
		path = '/Users/cudmore/Sites/bImpy-Data/ca-smooth-muscle-oir'
		if os.path.isdir(path):
			pass
		else:
			# ask user
			print('Please select a folder of .oir files')
			root = tkinter.Tk()
			root.withdraw()
			path = askdirectory(initialdir = "/",title = "Select a folder")

	if os.path.isdir(path):
		bConvert(path)
		stopSeconds = time.time()
		print('bConvertFolder finished in', round(stopSeconds-startSeconds), 'seconds.')
	else:
		print('error: bConvertFolder() expects the full path to a folder with oir files.')
