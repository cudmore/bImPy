'''
# Author: Robert Cudmore
# Date: 20190429

Given a path to a folder of oir files.
Generate a txt/csv file with all detection parameter.

We are generating a text file with .csv extension.
This allows double click to open in Microsoft Excel.

To convert actual images, use bConvertFolder.py
'''

import os, sys, time

import tkinter
from tkinter.filedialog import askdirectory

import javabridge
import bioformats

from bimpy import bStack

def convert(path):

	headerList = [] # used to generate one csv file for folder

	tmpPath, enclosingFolder = os.path.split(path)

	with javabridge.vm(
			run_headless=True,
			class_path=bioformats.JARS
			):

		# turn off logging, see:
		# ./bStack_env/lib/python3.7/site-packages/bioformats/log4j.py
		log4j = javabridge.JClassWrapper("loci.common.Log4jTools")
		log4j.enableLogging()
		log4j.setRootLevel("WARN")

		# build a list of oir header dictionaries
		for file in sorted(os.listdir(path)):
			if file.startswith('.'):
				continue
			if file.endswith('.oir'):

				filePath = os.path.join(path, file)

				myStack = bStack(filePath)
				myStack.loadHeader()
				myStack.header.prettyPrint() # print to command line
				headerList.append(myStack.header.header) # used to generate one csv file for folder

				# save the .txt file
				baseFileName = os.path.basename(file)
				baseFileName, ext = baseFileName.split('.')
				textFilePath = os.path.join(path, baseFileName + '.txt')
				with open(textFilePath, 'w') as textFile:
					textFile.write(myStack.header.getMetaData())
		#
		# generate one file with one row for each oir header
		if len(headerList) > 0:
			outFilePath = os.path.join(path, enclosingFolder + '.csv')
			with open(outFilePath, 'w') as outFile:
				print('saving file:', outFilePath)
				for idx, header in enumerate(headerList):
					if idx == 0:
						columnNames = ''
						for k, v in header.items():
							columnNames += k + ','
						outFile.write(columnNames + '\n')
					for k, v in header.items():
						outFile.write(str(v) + ',')
					outFile.write('\n')

if __name__ == '__main__':

	startSeconds = time.time()

	path = ''
	if len(sys.argv) == 2:
		path = sys.argv[1]
	else:
		#path = '/Volumes/t3/data/20190429/20190429_tst2'

		print('Please select a folder of .oir files')
		root = tkinter.Tk()
		root.withdraw()
		path = askdirectory(initialdir = "/",title = "Select a folder")

	# strip trailing '/'
	if path.endswith('/'):
		path = path[:-1]

	print('path:', path)
	if os.path.isdir(path):
		convert(path)
		stopSeconds = time.time()
		print('bConvertFolder_Headers finished in', round(stopSeconds-startSeconds), 'seconds.')
	else:
		print('error: bConvertFolder_Headers() expects the full path to a folder with oir files.')
