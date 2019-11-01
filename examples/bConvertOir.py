#!/usr/local/bin/python3

'''
Author: Robert Cudmore
Date: 20190425

Purpose:
	Given full path to Olympus .oir file, convert it to tiff

	Steps are:
	   - open oir
	   - save tiff into <folder>_tif
	   - save max project into <folder>_tif/max
	   - save header information into <folder>_tif

Output:
	Creates a new folder <folder>_tif

Usage
	python bConvertOir.py /Users/cudmore/Dropbox/data/nathan/20190401/tmp/20190401__0011.oir
'''

import os, sys, time

import javabridge

import bioformats

print('bioformats.JARS:', bioformats.JARS)

#from bimpy import bStack
import bimpy

if __name__ == '__main__':

	startSeconds = time.time()

	path = sys.argv[1]
	print('bConvertOir', path)

	with javabridge.vm(
			run_headless=True,
			class_path=bioformats.JARS
			):

		log4j = javabridge.JClassWrapper("loci.common.Log4jTools")
		log4j.enableLogging()
		log4j.setRootLevel("WARN")

		myStack = bimpy.bStack.bStack(path)

		savePath = myStack.convert_getSaveFile(channelNumber=1)

		if os.path.isfile(savePath):
			print('bConvertOir did not convert, destination file exists', savePath)
		else:
			myStack.convert()

	stopSeconds = time.time()
	print('bConvertOir took', round(stopSeconds-startSeconds), 'seconds')
