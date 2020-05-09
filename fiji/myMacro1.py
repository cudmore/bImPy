"""

Important, we are using MorphoLibJ
	https://imagej.net/MorphoLibJ

To install MorphoLibJ

	- In ImageJ2 (including Fiji), you just need to add the IJPB-plugins site to your list of update sites:
	- Select Help  › Update... from the menu to start the updater.
	- Click on Manage update sites. This brings up a dialog where you can activate additional update sites.
	- Activate the IJPB-plugins update site and close the dialog. Now you should see an additional jar file for download.
	- Click Apply changes and restart ImageJ.

Given a base name like ''
Process as:
	1) Mean
	2) Otsu Threshold
	3) invert LUT
	4) 3D fill holes
	5) 3d euclidean distance map
		convert edm from 32-bit to 8-bit
	6) save both
		mask (result after step 4)
		euclidean distance mapchannelImp

Output of manually recorded macro
	selectWindow("20200420_distalHEAD__ch2.tif");
	run("Mean 3D...", "x=3 y=3 z=2");
	setAutoThreshold("Otsu dark");
	//run("Threshold...");
	setAutoThreshold("Otsu dark");
	setOption("BlackBackground", false);
	run("Convert to Mask", "method=Otsu background=Dark calculate");
	run("Invert LUT");
	run("3D Fill Holes");
	run("3D Distance Map", "map=EDT image=20200420_distalHEAD__ch2 mask=Same threshold=1 inverse");

	selectWindow("20200420_distalHEAD__ch2.tif");
	saveAs("Tiff", "/Users/cudmore/box/data/nathan/20200420/sandbox/20200420_distalHEAD__ch2_mask.tif");
	selectWindow("EDT");
	saveAs("Tiff", "/Users/cudmore/box/data/nathan/20200420/sandbox/20200420_distalHEAD__ch2_edm.tif");

"""


from __future__ import print_function  # Only needed for Python 2, MUST be first import
import os, sys
import json

from ij import IJ, ImagePlus, WindowManager
from ij.io import DirectoryChooser, OpenDialog
from ij.process import ImageConverter

# allows us to import our own .py files, e.g. 'import simpleFileInfo
import inspect
thisFilePath = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0)))
print(' .  thisFilePath:', thisFilePath)
sys.path.append(thisFilePath)

import simpleFileInfo

######################################################################
def runEDM(imp=None):

	print('=== runEDM()')
		
	#
	# get info from original imp (make a copy below)
	myInfoDict = simpleFileInfo.getImpInfo(imp, '')
	print(json.dumps(myInfoDict, indent=4))
	filePath = myInfoDict['filePath']
	filePathNoExtension = filePath.split('.')[0] # assuming folders in path DO NOT have '.'
	print(' .  filePathNoExtension:', filePathNoExtension)

	impOriginalWindowTitle = imp.getTitle()
	
	#
	# make a copy of imp
	print(imp)
	print(' . === making copy of imp')
	imp = imp.duplicate() 
	imp.show()
	
	#
	# work on the copy image (mean and mask will be performed on this copy 'in place')
	impWindowTitle = imp.getTitle()
	impImage = impWindowTitle.split('.')[0] # used by 3D Distance Map
	print(' .  impWindowTitle:', impWindowTitle)
	print('   impImage:', impImage)

	#
	# mean
	print(' . === mean 3D filter')
	IJ.run("Mean 3D...", "x=3 y=3 z=2")
	
	#
	# threshold
	#IJ.setAutoThreshold("Otsu dark")
	#IJ.setOption("BlackBackground", true);
	print(' . === Otsu threshold')
	IJ.run("Convert to Mask", "method=Otsu background=Dark calculate")
	
	# invert
	IJ.run("Invert LUT")
	
	#
	# fill holes
	print(' . === fill holes')
	IJ.run("3D Fill Holes") # does not seem to do anything ???
	
	'''
	# 3d mean ch1
	...
	# convert ch1 to mask
	selectWindow("20200420_distalHEAD__ch1.tif");
	setAutoThreshold("Default dark");
	//run("Threshold...");
	setAutoThreshold("Otsu dark");
	setOption("BlackBackground", false);
	run("Convert to Mask", "method=Otsu background=Dark calculate");
	run("Close");
	#
	# run 3d distance map, outputs two windows (EVF, EDT)
	#
	# v1, I thought this was working ???
	run("3D Distance Map", "map=Both image=20200420_distalHEAD__ch1 mask=20200420_distalHEAD__ch2_mask threshold=1 inverse");
	convert output evf to 8-bit
	output evf has (maybe don't convert to 8-bit???)
		-1: where there was no mask in ch1 (after 8-bit is 128)
		0: where there was a mask in ch2 (after 8-bit is 0)
		value: distance between point in ch1 mask and nearest point in ch2 mask
	#
	# v2, now this seems to be working (neither mask has inverted LUT)
	# here, 20200420_distalHEAD__ch1-1 is a mask of channel
	# run("3D Distance Map", "map=Both image=20200420_distalHEAD__ch2_mask mask=20200420_distalHEAD__ch1-1 threshold=1 inverse");
	'''

	#
	# 3d distance map (makes EDT window)
	print(' . === 3d euclidean distance map (EDM) ... please wait')
	paramStr = 'map=EDT image=' + impImage + ' mask=Same threshold=1 inverse' # inverse?
	#IJ.run("3D Distance Map", "map=EDT image=20200420_distalHEAD__ch2 mask=Same threshold=1 inverse")
	IJ.run("3D Distance Map", paramStr)
	
	edmImp = WindowManager.getCurrentImage()
	print(' .  edmImp:', edmImp)

	# convert 32-bit edm to 8-bit
	ic = ImageConverter(edmImp) # converts channelImp in place
	scaleConversions = True
	ic.setDoScaling(scaleConversions) # scales inensities to fill 0...255
	ic.convertToGray8()		
	print(' .  edmImp:', edmImp)
	
	#
	# save
	IJ.selectWindow(impWindowTitle)
	maskPath = filePathNoExtension + '_mask.tif'
	print(' .  === saving maskPath:', maskPath)
	IJ.saveAs("Tiff", maskPath)
	
	IJ.selectWindow("EDT");
	edmPath = filePathNoExtension + '_edm.tif'
	print(' .  === saving edmPath:', edmPath)
	IJ.saveAs("Tiff", edmPath)
	
	#
	# set both (mask and edm) changes=false (we save them)
	imp.changes = False
	edmImp.changes = False

	#
	# output, merge channels into composite
	# contrast adjust edmp
	print(' .  === contrast adjust edm')
	edmPath, edmFile = os.path.split(edmPath)
	IJ.selectWindow(edmFile);
	IJ.run("Enhance Contrast", "saturated=0.35"); # not sure how to calculate auto, 0.35 will be different !!!
	IJ.run("Apply LUT", "stack");
	# merge into composite
	print(' .  === merging into composite')
	#impOriginalWindowTitle was assigned right at start
	maskWindowTitle = imp.getTitle() # (mean, threshold) was done in place on copy
	edmWindowTitle = edmImp.getTitle()
	# run("Merge Channels...", "c1=20200420_distalHEAD__ch2.tif c2=20200420_distalHEAD__ch2_mask.tif c3=20200420_distalHEAD__ch2_edm.tif create keep ignore");
	paramStr = 'c1=' + impOriginalWindowTitle + ' c2=' + maskWindowTitle + ' c3=' + edmWindowTitle + ' create keep ignore'
	IJ.run("Merge Channels...", paramStr)
	
######################################################################
if __name__ in ['__main__', '__builtin__']:


	path = ''
	#path = '/Users/cudmore/box/data/nathan/20200420/20200420_distalHEAD__ch2.tif'

	#
	# open an image
	if path:
		if os.path.isfile(path):
			print('error: did not find file path:', path)
			
		imp = IJ.openImage(path)
		imp.show()

	imp = WindowManager.getCurrentImage()
	if imp is not None:
		impTitle = imp.getTitle()
		print('myMacro1() running on front most imp with impTitle:', impTitle)
		#
		runEDM(imp=imp)
		#
	else:
		print('error: please open an image')

	print('done with myMacro1')
