	## open
	
		"""
	folderPath, filename = os.path.split(path)
	fileNameNoExtension, fileExtension = filename.split('.')
	baseFilePath = os.path.join(folderPath, fileNameNoExtension)
	
	print('=== === runVesselDistance() basFilePath:', baseFilePath)
	
	ch1Path = baseFilePath + '_ch1.tif'
	ch2Path = baseFilePath + '_ch2.tif'

	if not os.path.isfile(ch1Path):
		print('Error: runVesselDistance() did not find ch1Path:', ch1Path)
		return
	if not os.path.isfile(ch2Path):
		print('Error: runVesselDistance() did not find ch2Path:', ch2Path)
		return
		
	#
	# open images
	print(' . opening ch1Path', ch1Path)
	impCh1 = IJ.openImage(ch1Path)
	impCh1.show()
	myShrinkWindow()
	print(' . opening ch2Path', ch2Path)
	impCh2 = IJ.openImage(ch2Path)
	impCh2.show()
	myShrinkWindow()

	channel1_title = impCh1.getTitle() # bring to front with IJ.selectWindow(channel1_title)
	channel2_title = impCh2.getTitle() # bring to front with IJ.selectWindow(channel2_title)
	'''
	print(' . channel1_title:', channel1_title)
	print(' . channel2_title:', channel2_title)
	'''

	#
	#
	ch1_AnalysisOptions = getDefaultAnalysisDict('1')
	ch2_AnalysisOptions = getDefaultAnalysisDict('1')
	ch2_AnalysisOptions['removeBlobsSmallerThan'] = 100 # units ???
	
	#
	# remove slices based on filename (remove endocardium based on filename)
	first, last = myRemoveSlices(impCh1) # use ch1, both ch1/ch2 are the same
	if first is not None and last is not None:
		paramStr = 'first={0} last={1} increment=1'.format(first, last) #IJ.run(imp, "Slice Remover", "first=1 last=26 increment=1");
		# ch1
		print(' . removing slices from',channel1_title, first, last) 
		IJ.run(impCh1, "Slice Remover", paramStr);
		# ch2
		print(' . removing slices from',channel2_title, first, last) 
		IJ.run(impCh2, "Slice Remover", paramStr);

	#
	# make copies to work on (mean, threshold) are in place
	impCh1_copy = impCh1.duplicate() # window name is DUP_
	impCh2_copy = impCh2.duplicate()  # window name is DUP_

	impCh1_copy.show()
	myShrinkWindow()
	impCh2_copy.show()
	myShrinkWindow()

	channel1_copy_title = impCh1_copy.getTitle() # bring to front with IJ.selectWindow(channel1_copy_title)
	channel2_copy_title = impCh2_copy.getTitle() # bring to front with IJ.selectWindow(channel2_copy_title)
	print(' . channel1_copy_title:', channel1_copy_title)
	print(' . channel2_copy_title:', channel2_copy_title)
	
	# remember, we can get frontmost imp with
	# imp = IJ.getImage();
	"""

## end open
"""
	#
	# pre-process ch2
	IJ.selectWindow(channel2_copy_title) # bring to front
	
	# mean
	''' PUT BACK IN
	print('ch2 mean filter ... please wait')
	formatStr = 'x={0} y={1} z={2}'.format(3, 3, 2) #IJ.run("Mean 3D...", "x=3 y=3 z=2")
	IJ.run("Mean 3D...", formatStr)
	'''
	
	# threshold (makes binary)
	print('ch2 otsu threshold')
	IJ.run("Convert to Mask", "method=Otsu background=Dark calculate")
	IJ.run("Invert LUT") # puts it back to NOT inverted (normal)
	
	# fill holes, makes new window and appends to title '-Closing'
	print('ch2 fill holes')
	paramStr = 'operation=Closing element=Cube x-radius={0} y-radius={1} z-radius={2}'.format(4, 4, 2)
	#IJ.run("Morphological Filters (3D)", "operation=Closing element=Cube x-radius=4 y-radius=4 z-radius=2")
	IJ.run("Morphological Filters (3D)", paramStr)
	myShrinkWindow() # fluff
	#
	ch2_Final_Mask_Title = IJ.getImage().getTitle() # fucking complicated, used by EDT/EVF
	ch2_Final_Mask_Title = ch2_Final_Mask_Title.split('.')[0] # get title without .tif, used by 3D Distance Map
	print('ch2_Final_Mask_Title:', ch2_Final_Mask_Title)

	#
	# need for findAllLabels
	#IJ.run("Convert to Mask", "method=Default background=Dark list");
	"""
	
	#
	# remove small blobs
	# see: https://github.com/ijpb/MorphoLibJ/blob/master/src/main/java/inra/ijpb/binary/ConnectedComponents.java
	# todo: put this back in ... seems to be screwing up EDT/EVF ???
	"""
	print('ch2 connected components labelling, new window is -lbl')
	IJ.run("Connected Components Labeling", "connectivity=26 type=[16 bits]") # create new image with blobs labeled 1,2,3,...
	impLabels = IJ.getImage()
	'''
	labels = LabelImages.findAllLabels(impLabels) # get integer list of labels
	pixelCountArray = LabelImages.pixelCount(impLabels, labels) # pixel count of each label
	pixelCountArray = sorted(pixelCountArray)
	for labelIdx, pixelCount in enumerate(pixelCountArray):
		print('labelIdx:', labelIdx, 'pixelCount:', pixelCount)
	'''

	# see: https://javadoc.scijava.org/MorphoLibJ/inra/ijpb/label/LabelImages.html
	removeSmallerThanThis = 100
	myImageStack = impLabels.getImageStack()
	newImageStack = LabelImages.volumeOpening(myImageStack, removeSmallerThanThis) # expects an ij.ImageStack
	newImp = ImagePlus('xxx', newImageStack) # we are losing the scale !!!
	newImp.show()
	myShrinkWindow()
	# we now have a label stack witheach segmented object having intensity 1,2,3,...
	IJ.run(newImp, "Make Binary", "");

	ch2_Final_Mask_Title = IJ.getImage().getTitle() # fucking complicated, used by EDT/EVF
	ch2_Final_Mask_Title = ch2_Final_Mask_Title.split('.')[0] # get title without .tif, used by 3D Distance Map
	print('** after LabelImage.volumeOpening')
	print('  ch2_Final_Mask_Title:', ch2_Final_Mask_Title)
	"""
