"""
# Robert Cudmore
# 20200426

Important
	We are using MorphoLibJ for most 3d operations
		https://imagej.net/MorphoLibJ
		https://github.com/ijpb/MorphoLibJ
	3D Distance map is from:
		https://imagejdocu.tudor.lu/doku.php?id=plugin:stacks:3d_ij_suite:start
	
To install MorphoLibJ

	- In ImageJ2 (including Fiji), you just need to add the IJPB-plugins site to your list of update sites:
	- Select Help  › Update... from the menu to start the updater.
	- Click on Manage update sites. This brings up a dialog where you can activate additional update sites.
	- Activate the IJPB-plugins update site and close the dialog. Now you should see an additional jar file for download.
	- Click Apply changes and restart ImageJ.

Given a path to original .oir file
	path = ''
	
	General Algorithm:
	1) remove some slices, usually endocardium (See myRemoveSlices())
	2) pre process each original channel (see myPreProcess)
		2.1) Mean
		2.2) Otsu Threshold (makes a binary mask)
		2.3) 3D fill holes
		2.4) for vessel channel, remove small segmented objects
	3) 3d euclidean distance map
		convert edm from 32-bit to 8-bit
	4) save
		original ch1/ch2 (potentially with removed slices)
		final mask for ch1/ch2 (output of step 2)
		euclidean distance images (EDT,EVF)
"""

from __future__ import print_function  # Only needed for Python 2, MUST be first import
import os, sys
import json
from collections import OrderedDict

from ij import IJ, ImagePlus, WindowManager
from ij.io import DirectoryChooser, OpenDialog
from ij.process import ImageConverter

from loci.plugins import BF

# see: https://javadoc.scijava.org/MorphoLibJ/index.html?inra/ijpb/label/LabelImages.html
from inra.ijpb.label import LabelImages
#from inra.ijpb.label.LabelImages import volumeOpening #replaceLabels, sizeOpening, volumeOpening

# allows us to import our own .py files, e.g. 'import simpleFileInfo
import inspect
thisFilePath = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0)))
print(' .  thisFilePath:', thisFilePath)
sys.path.append(thisFilePath)

import simpleFileInfo

def mySliceKeeper(imp):
	"""
	keep slices based on file name
	"""
	title = imp.getTitle()

	first = None
	last = None
	
	if title.find('20200420_distalHEAD_') != -1:
		first = 27
		last = 52 #26
	elif title.find('20200420_Mid_') != -1:
		first = 17 #1
		last = 39 #16
	elif title.find('20200420_HEAD_') != -1:
		first = 23 #1
		last = 58 #22

	return first, last

def myShrinkWindow():
	"""shrink frontmost window"""
	IJ.run("Out [-]", "")
	IJ.run("Out [-]", "")
	
def myPreProcess(path, analysisParams):
	"""
	return:
		analysisParams: modified with channel stack parameters
		finalMaskTitle:
		impCh1: 

	todo: I am not modifying xxx, I want to add detection parameters for stack like
		(filename, path, xVoxel, yVoxel, zVoxel)
	"""
	
	channel = analysisParams['channel']
	doMeanFilter = analysisParams['doMeanFilter']
	
	print('=== preProcess() channel:', channel, 'path:', path)


	folderPath, filename = os.path.split(path)
	fileNameNoExtension, fileExtension = filename.split('.')
	baseFilePath = os.path.join(folderPath, fileNameNoExtension)
	print(' . basFilePath:', baseFilePath)
	
	if channel == 1:
		chPath = baseFilePath + '_ch1.tif'
	elif channel ==2:
		chPath = baseFilePath + '_ch2.tif'	

	if not os.path.isfile(chPath):
		print(' . Error: runVesselDistance() did not find chPath:', chPath)
		return None, None, None
		
	#
	# open images
	print(' . opening chPath', chPath)
	impCh1 = IJ.openImage(chPath)
	impCh1.show()
	myShrinkWindow()

	channel1_title = impCh1.getTitle() # bring to front with IJ.selectWindow(channel1_title)
	
	#
	# remove slices based on filename (remove endocardium based on filename)
	first, last = mySliceKeeper(impCh1) # use ch1, both ch1/ch2 are the same
	if first is not None and last is not None:
		paramStr = 'first={0} last={1} increment=1'.format(first, last) #IJ.run(imp, "Slice Remover", "first=1 last=26 increment=1");
		print(' . keeping slices from',channel1_title, first, last) 
		IJ.run(impCh1, "Slice Keeper", paramStr) # makes new window, appending 'kept stack' to title
		impCh1.close() # close original
		impCh1 = IJ.getImage() # swap in kep slices
	#
	# make copies to work on (mean, threshold) are in place
	impCh1_copy = impCh1.duplicate() # window name is DUP_

	impCh1_copy.show()
	myShrinkWindow()

	channel1_copy_title = impCh1_copy.getTitle() # bring to front with IJ.selectWindow(channel1_copy_title)
	print(' . channel1_copy_title:', channel1_copy_title)

	
	###
	### Working on copy
	###
	
	# mean
	if doMeanFilter:
		xVoxel_mean = analysisParams['xVoxel_mean']
		yVoxel_mean = analysisParams['yVoxel_mean']
		zVoxel_mean = analysisParams['zVoxel_mean']
		print(' . mean filter', xVoxel_mean, xVoxel_mean, xVoxel_mean, ' ... please wait')
		formatStr = 'x={0} y={1} z={2}'.format(3, 3, 2) #IJ.run("Mean 3D...", "x=3 y=3 z=2")
		IJ.run("Mean 3D...", formatStr)
	
	
	# threshold (makes binary)
	print(' . otsu threshold')
	IJ.run(impCh1_copy, "Convert to Mask", "method=Otsu background=Dark calculate")
	IJ.run("Invert LUT") # puts it back to NOT inverted (normal)
	
	# fill holes, makes new window and appends to title '-Closing'
	xRadius_fillHoles = analysisParams['xRadius_fillHoles']
	yRadius_fillHoles = analysisParams['yRadius_fillHoles']
	zRadius_fillHoles = analysisParams['zRadius_fillHoles']
	print(' . fill holes', xRadius_fillHoles, yRadius_fillHoles, zRadius_fillHoles)
	paramStr = 'operation=Closing element=Cube x-radius={0} y-radius={1} z-radius={2}'.format(xRadius_fillHoles, yRadius_fillHoles, zRadius_fillHoles)
	#IJ.run("Morphological Filters (3D)", "operation=Closing element=Cube x-radius=4 y-radius=4 z-radius=2")
	IJ.run(impCh1_copy, "Morphological Filters (3D)", paramStr)
	myShrinkWindow() # fluff
	#
	impCh1_filledHoles = IJ.getImage()
	finalMaskTitle = IJ.getImage().getTitle() # fucking complicated, used by EDT/EVF
	finalMaskTitle = finalMaskTitle.split('.')[0] # get title without .tif, used by 3D Distance Map
	#print('ch1_Final_Mask_Title:', ch1_Final_Mask_Title)

	if analysisParams['removeBlobsSmallerThan'] is not None:
		removeBlobsSmallerThan = analysisParams['removeBlobsSmallerThan']

		print('channel:', 2, 'connected components labelling, new window is -lbl')
		IJ.run(impCh1_filledHoles, "Connected Components Labeling", "connectivity=26 type=[16 bits]") # create new image with blobs labeled 1,2,3,...
		myShrinkWindow() # fluff
		impLabels = IJ.getImage()
		impLabels.setDisplayRange(0, 10) # this is a wierd stack/image, labels are intensity 1,2,3,...
		'''
		# count the number of pixels in each label 1,2,3,...
		labels = LabelImages.findAllLabels(impLabels) # get integer list of labels
		pixelCountArray = LabelImages.pixelCount(impLabels, labels) # pixel count of each label
		pixelCountArray = sorted(pixelCountArray)
		for labelIdx, pixelCount in enumerate(pixelCountArray):
			print('labelIdx:', labelIdx, 'pixelCount:', pixelCount)
		'''
	
		# see: https://javadoc.scijava.org/MorphoLibJ/inra/ijpb/label/LabelImages.html
		# Applies area opening on a 3D label image: creates a new label image that contains only particle with
		# at least the specified number of voxels.
		myImageStack = impLabels.getImageStack()
		newImageStack = LabelImages.volumeOpening(myImageStack, removeBlobsSmallerThan) # expects an ij.ImageStack
		#
		myCalibration = impCh1.getCalibration() # get calibration from original imp
		newImp = ImagePlus('xxx_yyy', newImageStack) # we are losing the scale !!!
		newImp.setCalibration(myCalibration)
		newImp.show()
		myShrinkWindow()
		# we now have a label stack with each segmented object having intensity 1,2,3,...
		#
		# todo: not sure if this will remove some of the pixels (like a thrshold) ???
		#IJ.run(newImp, "Make Binary", "method=Default background=Default calculate");
		# instead ... step through each label and set its label index to 255, effectively making a mask ????
		labels = LabelImages.findAllLabels(newImp) # get integer list of labels
		'''
		pixelCountArray = LabelImages.pixelCount(newImp, labels) # pixel count of each label
		pixelCountArray = sorted(pixelCountArray)
		for labelIdx, pixelCount in enumerate(pixelCountArray):
			print('labelIdx:', labelIdx, 'pixelCount:', pixelCount)
		'''
		LabelImages.replaceLabels(newImp, labels, 255)
		
		finalMaskTitle = IJ.getImage().getTitle() # fucking complicated, used by EDT/EVF
		finalMaskTitle = finalMaskTitle.split('.')[0] # get title without .tif, used by 3D Distance Map

	return analysisParams, finalMaskTitle, impCh1

def runVesselDistance(path):
	"""
	path: full path to original oir file
	"""
	
	#
	# PREPROCESS (mean, threshold, closing)

	# pre-process ch1
	ch1_AnalysisOptions = getDefaultAnalysisDict(1)
	ch1_AnalysisOptions, ch1_Final_Mask_Title, impCh1 = myPreProcess(path, ch1_AnalysisOptions)
	if ch1_AnalysisOptions is None:
		# there was an error in myPreProcess
		return None
		
	# pre-process ch1
	ch2_AnalysisOptions = getDefaultAnalysisDict(2)
	ch2_AnalysisOptions['removeBlobsSmallerThan'] = 100 # units ???
	ch2_AnalysisOptions, ch2_Final_Mask_Title, impCh2 = myPreProcess(path, ch2_AnalysisOptions)
	if ch2_AnalysisOptions is None:
		# there was an error in myPreProcess
		return None

	
	##
	## Calculate (EDT, EVF)
	## 	in general, we want pixel values from EDT but only for pixels in EVF in range [0.0, 1.0]
	## 	todo: I am not going to get to this right now
	##

	doDistanceMap = False
	if doDistanceMap:
		# this is using '#D ImageJ Suite
		# see: https://imagejdocu.tudor.lu/doku.php?id=plugin:stacks:3d_ij_suite:start
		#myThreshold = 1
		#paramStr = 'map=Both image=' + ch2_Final_Mask_Title + ' mask=' + ch1_Final_Mask_Title + ' threshold=' + str(myThreshold) + ' inverse'
		paramStr = 'map=Both image={0} mask={1} threshold={2} inverse'.format(ch2_Final_Mask_Title, ch1_Final_Mask_Title, myThreshold)
		print('3D Distance Map paramStr:', paramStr)
		print(' . calculating (EDT, EVF) ... this will make new windows (EDT, EVF) ...please wait')
		IJ.run("3D Distance Map", paramStr);
		IJ.run("Fire", "") # set last window, evf, to fire
		
		# shrink (EDT, EVF) windows
		
		'''
			Both (EDT, EVF) are 32-bit images
			EDT has:
				pixel values set to the micrometer distance to the vascular mask
			EVF has pixel values:
				-1: pixels that were in the ch2 vascular mask
				0: pixels outside the ch1 HCN1 mask
				[0..1]: distance between pixels in HCN1 mask and vascular map (these are normalized)
	
			todo:
				for each value in SVF between [0..1], grab value in EDT (in microns)
		'''

	##
	# save results
	##
	
	#
	# make output folder
	folderPath, filename = os.path.split(path)
	fileNameNoExtension, fileExtension = filename.split('.')
	
	outputPath = os.path.join(folderPath, 'distanceAnalysis')
	if not os.path.exists(outputPath):
		os.makedirs(outputPath)
    
	# append to this to get final output fil path ('_ch1.tif', '_ch2.tif', '_ch1_mask.tif', ...)
	outBasePath = os.path.join(outputPath,fileNameNoExtension)
    
	# ch1
	ch1SavePath = outBasePath + '_ch1.tif'
	print(' . saving ch1:', ch1SavePath)
	IJ.save(impCh1, ch1SavePath)

	# ch2
	ch2SavePath = outBasePath + '_ch2.tif'
	print(' . saving ch2:', ch2SavePath)
	IJ.save(impCh2, ch2SavePath)
	
	# ch1 mask
	impCh1Mask = WindowManager.getImage(ch1_Final_Mask_Title)
	ch1MaskSavePath = outBasePath + '_ch1_mask.tif'
	print(' . saving ch1 mask:', ch1MaskSavePath)
	IJ.save(impCh1Mask, ch1MaskSavePath)
	
	# ch2 mask
	impCh2Mask = WindowManager.getImage(ch2_Final_Mask_Title)
	ch2MaskSavePath = outBasePath + '_ch2_mask.tif'
	print(' . saving ch2 mask:', ch2MaskSavePath)
	IJ.save(impCh2Mask, ch2MaskSavePath)
	
	if doDistanceMap:
		impEDT = WindowManager.getImage('EDT')
		edtSavePath = outBasePath + '_edt.tif'
		print(' . saving EDT:', edtSavePath)
		IJ.save(impEDT, edtSavePath)
	
		impEVF = WindowManager.getImage('EVF')
		evfSavePath = outBasePath + '_evf.tif'
		print(' . saving EVF:', evfSavePath)
		IJ.save(impEVF, evfSavePath)

	##
	# merge results into composite (merge EVF and vessel mask)
	##
	
	'''
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
	'''
	
	# tile all the windows
	IJ.run('Tile', '')
	
	#
	print('closing all windows')
	#closeWorked = WindowManager.closeAllWindows()

	return True
	
######################################################################
def getDefaultAnalysisDict(channel):
	
	theRet = OrderedDict()
	theRet['channel'] = channel
	theRet['doMeanFilter'] = False # makes debugging faster
	theRet['xVoxel_mean'] = 3
	theRet['yVoxel_mean'] = 3
	theRet['zVoxel_mean'] = 2
	theRet['xRadius_fillHoles'] = 4
	theRet['yRadius_fillHoles'] = 4
	theRet['zRadius_fillHoles'] = 2
	theRet['removeBlobsSmallerThan'] = None # units???

	return theRet
	
######################################################################
if __name__ in ['__main__', '__builtin__']:

	path = ''
	
	# run one one of three images ('HEAD', 'distalHead', )
	oirPath = '/Users/cudmore/box/data/nathan/20200420/20200420_MID_.oir'
	oirPath = '/Users/cudmore/box/data/nathan/20200420/20200420_HEAD_.oir'
	# works well but thin
	#oirPath = '/Users/cudmore/box/data/nathan/20200420/20200420_distalHEAD_.oir'
	
	myReturn = runVesselDistance(oirPath)

	print('done with vesselDistance1')
