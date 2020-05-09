"""
Author: Robert Cudmore
Date: 20200427
"""

from __future__ import print_function  # Only needed for Python 2, MUST be first import
import os, sys
import json

from ij import IJ, ImagePlus

from inra.ijpb.label import LabelImages
# try instead
from inra.ijpb.label.LabelImages import replaceLabels, sizeOpening, volumeOpening

def myRun():
	path = 'http://imagej.nih.gov/ij/images/blobs.gif'
	path = '/Users/cudmore/box/data/nathan/20200420/distanceAnalysis/20200420_HEAD__ch2.tif'
	
	imp = IJ.openImage(path)
	imp.show()
	print('  imp:', imp)
	
	# make mask, background is 0 and forground is 255
	IJ.run("Convert to Mask", "method=Otsu background=Dark calculate")
	#IJ.run("Invert LUT") # puts it back to NOT inverted (normal)

	# close some holes
	print('Morphological Filters (3D) operation=Closing')
	paramStr = 'operation=Closing element=Cube x-radius={0} y-radius={1} z-radius={2}'.format(4, 4, 2)
	IJ.run("Morphological Filters (3D)", paramStr)
	# see: https://javadoc.scijava.org/MorphoLibJ/inra/ijpb/morphology/Morphology.html
	# closing(ij.ImageStack image, Strel3D strel)
	# to make a strel
	# Strel strel = Strel.Shape.SQUARE.fromRadius(2);
	# cube strel
	# myStrel = inra.ijpb.morphology.strel.CubeStrel(int size)
	#
	# like this
	#myImageStack = imp.getImageStack()
	# there is no 3d rect strel? we need to pay attention to anisotropic scaling
	#myStrel = inra.ijpb.morphology.strel.CubeStrel(int size)
	
	# create new image '-lbl' with blobs labeled 1,2,3,...
	print('Connected Components Labeling')
	IJ.run("Connected Components Labeling", "connectivity=26 type=[16 bits]") 
	impLabels = IJ.getImage()
	print('  impLabels:', impLabels)
	
	# get integer list of labels
	labels = LabelImages.findAllLabels(impLabels) 
	print(' . num labels:', len(labels))
	
	# pixel count of each label
	# in MorphoLibJ_-1.4.1, this is expecint 'ij.process.ImageProcessor'
	ip = impLabels.getChannelProcessor()
	#pixelCountArray = LabelImages.pixelCount(impLabels, labels) 
	pixelCountArray = LabelImages.pixelCount(ip, labels) 
	pixelCountArray = sorted(pixelCountArray)
	
	# build a list of labels to remove
	removeLabelListStr = ''
	removeLabelList = []
	for labelIdx, pixelCount in enumerate(pixelCountArray):
		print('labelIdx:', labelIdx, 'pixelCount:', pixelCount)
		if pixelCount < 100:
			removeLabelListStr += str(labelIdx) + ','
			removeLabelList.append(labelIdx)
			
	if removeLabelListStr.endswith(','):
		# remove trailing ','
		removeLabelListStr = removeLabelListStr[:-1]
	
	print('removeLabelListStr:', removeLabelListStr)
	
	# remove a list of labels
	# this seems to corrupt -lbl stack ??? It appears to be an all 0 intensity stack?
	# corruptions occurs in version 1.41 and 1.42
	'''
	paramStr = 'label(s)={0} final={1}'.format(removeLabelListStr, 0)
	IJ.run(impLabels, "Replace/Remove Label(s)", paramStr)
	'''
	#replaceLabels(ip, removeLabelList, 0)
	
	# remove one label, this works
	'''
	thisLabelNumber = 56
	IJ.run(impLabels, "Replace/Remove Label(s)", "label(s)=56 final=0");
	'''
	
	# this does not work, does not corrupt stack but seems there is no change
	# requires version 1.4.2
	#IJ.run(impLabels, "Label Size Filtering", "operation=Greater_Than size=100");
	#IJ.run(impLabels, "Label Size Filtering", "operation=Less_Than size=100");

	# try instead
	# Applies size opening on a label image: creates a new label image that contains only particles
	# with at least the specified number of pixels or voxels.
	
	# see: https://javadoc.scijava.org/MorphoLibJ/inra/ijpb/label/LabelImages.html
	# this might be for 2d?
	#newImp = sizeOpening(impLabels, 100)
	# 3d
	myImageStack = impLabels.getImageStack()
	newImageStack = volumeOpening(myImageStack, 100) # expects an ij.ImageStack
	newImp = ImagePlus('xxx', newImageStack)
	newImp.show()
	
	IJ.run('Tile', '')
	
if __name__ in ['__main__', '__builtin__']:

	myRun()

	print('testLabels done')
	