	"""
	# add gaussian and median
	if doMedian:
		thresholdStack = np.add(gaussianThresholdStack, medianThresholdStack)
		thresholdStack[thresholdStack==2] = 1
	else:
		thresholdStack = gaussianThresholdStack
	#thresholdStack[thresholdStack==1] = 0
	#thresholdStack[thresholdStack==10] = 1
	_printStackParams('thresholdStack', thresholdStack)
	results['thresholdStack'] = thresholdStack

	if doSave:
		tmpOutPath = baseSavePath + '_threshold.tif'
		tifffile.imsave(tmpOutPath, thresholdStack)

	# distance map was here
	
	#
	# fill holes
	#filledHolesStack = myClosing(thresholdStack, structure = (4,10,10))
	filledHolesStack = myFillHoles(thresholdStack) # does stack then per image slice
	results['filledHolesStack'] = filledHolesStack

	if doSave:
		tmpOutPath = baseSavePath + '_filled.tif'
		tifffile.imsave(tmpOutPath, filledHolesStack)
	
	#
	# label connected component 1, 2, 3, ...
	labeledStack = myLabel(filledHolesStack, structure=(3,3,3))
	results['labeledStack'] = labeledStack

	if doSave:
		tmpOutPath = baseSavePath + '_labeled.tif'
		tifffile.imsave(tmpOutPath, labeledStack)
	
	#
	# calculate volume of largest connected component

	loc = ndimage.find_objects(labeledStack) # label 0 is background and not included
	print('  ', len(loc), 'labels') # labeled object 103 is at index 103 (0/background is not in labels)
	retStack = labeledStack.copy()
	numLabels = len(loc)
	largestLabelPixelCount = 0
	largestLabel = np.nan
	for i in range(numLabels+1):
		if i == 0:
			# background
			continue
					
		# this does not work
		'''
		tmpLoc = loc[i]		
		# this is probably slow, how do i count number of pixels in label i?
		tmpStack = labeledStack[tmpLoc]
		print('  tmpStack.shape:', tmpStack.shape)
		numPixelsInLabel = np.count_nonzero(tmpStack)
		'''
		
		numPixelsInLabel = np.count_nonzero(labeledStack[labeledStack==i])
		
		if numPixelsInLabel > largestLabelPixelCount:
			print('  largets is label', i, 'numPixelsInLabel:', numPixelsInLabel, 'largestLabelPixelCount', largestLabelPixelCount)
			largestLabelPixelCount = numPixelsInLabel
			largestLabel = i

	print('largestLabel:', largestLabel, 'largestLabelPixelCount:', largestLabelPixelCount)
	
	#
	# convert labeled stack back to binary mask
	finalMask = labeledStack.copy()
	finalMask[:] = 0
	finalMask[labeledStack == largestLabel] = 1
	results['finalMask'] = finalMask
	

	#
	# erode mask by um distance
	erodedMask = morphology.binary_erosion(finalMask, iterations=3) # returns a true/false mask?
	erodedMask = erodedMask.astype(np.uint8)
	results['erodedMask'] = erodedMask
	#print('erodedMask:', erodedMask.shape, type(erodedMask), erodedMask.dtype, np.min(erodedMask), np.max(erodedMask))
	
	#
	# subtract eroded from finalMask (to get ring)
	
	#
	# save mask
	if doSave:
		maskSavePath = '/Users/cudmore/Desktop/finalMask.tif'
		tifffile.imsave(maskSavePath, finalMask)
	"""
	
	#myNapari(results)
