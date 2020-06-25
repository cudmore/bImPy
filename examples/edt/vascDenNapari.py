"""
20200517
Robert Cudmore

Use napari to manually remove large vessels from mask.

Save results in _editLabels.tif

	Napari Keyboard:
		p: paint brush (draw around large vessel, removing small vessels befure mouse-click)
		z: zoom (e.g. PAN_ZOOM)
	
	My Mouse/Keyboard:
		mouse-click: set new label
		u: undo
		r: revert the selected label back to original label
		s: save labels as _editLabels.tif.tif
		
	todo:
		[fixed] We need a .csv to tell us the number of labels coming out of main analysis.
		This way we can make a new mask WITHOUT new labels created here
		
"""

import os, json
import argparse

import numpy as np
import scipy
import skimage
import napari
import tifffile

from contextlib import nullcontext # to have conditional 'with'

#from vascDen import myGetDefaultStackDict # vascDen.py needs to be in same folder
import vascDen

class myLabelEdit:

	def __init__(self, pathToRawTiff, withContext=True, verbose=True):
		"""
		pathToRawTiff: /Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0007_ch1.tif
		withContext: True if we need to build a 'with' context, alse context is already created like from in Jupyter notebook
		"""
		
		self.verbose = verbose
		
		tmpFolder, tmpFilename = os.path.split(pathToRawTiff)
		tmpFileNameNoExtension, tmpExtension = tmpFilename.split('.')
		
		if tmpFolder.endswith('analysis2'):
			# already in analysis folder
			self.analysisPath = tmpFolder
			if tmpFileNameNoExtension.endswith('_raw'):
				tmpFileNameNoExtension = tmpFileNameNoExtension.replace('_raw', '')
		else:
			self.analysisPath = os.path.join(tmpFolder, 'analysis2')
		self.baseFileName = tmpFileNameNoExtension
		self.baseFilePath = os.path.join(self.analysisPath, self.baseFileName )
		
		#
		# where we will save out edit
		self.editLabelPath = self.baseFilePath + '_labeled_edited.tif' # using _edited to match output of removeSmallVessels.py
		self.editLabelData = None
		self.editLabelName = 'edit labels' # the name of our edit labels in Napari
		self.myLabelsLayer = None # filled in by self.myNapari()
		
		#
		# to load analysis from vascDen.py
		self.stackDict = vascDen.myGetDefaultStackDict()
		#print('stackDict:', json.dumps(self.stackDict, indent=4))

		#
		# undo
		self.undoLabelNumber = []
		self.undoNewLabelNumber = []
		self.undoSliceNumber = []
		self.undoSliceData = []

		self.floodFillIterations = 0
		
		#
		# load raw analysis stacks
		self.loadTheseStacks = ['raw', 'filtered', 'threshold0', 'threshold1', 'threshold', 'labeled', 'finalMask', 'finalMask_hull', 'finalMask_edt']
		#self.loadTheseStacks = ['raw', 'labeled', 'finalMask', 'finalMask_hull', 'finalMask_edt']
		self.load() 
		
		origNumLabels = np.max(self.stackDict['labeled']['data'])
		self.origNumLabels = origNumLabels
		
		#
		# will not return
		self.myNapari(withContext=withContext)
		
		#
		# done
		print('Napari window closed ... myLabelEdit finished ...')
		
	def myPrint(self, message):
		if self.verbose:
			print(message)
		self.viewer.status = message
		
	def load(self):
		"""
		load stacks from analysis2/
		
		populate self.stackDict[stackName]['data']
		"""	
		
		print('vascDenNapari.load()')
		print('  analysis path:', self.analysisPath)
		
		for idx, (stackName,v) in enumerate(self.stackDict.items()):
			fileIdx = idx #+ 1
			if not stackName in self.loadTheseStacks:
				continue
			# v is a dist of keys (type, data)
			#idxStr = '_' + str(fileIdx) + '_'
			#fileName = self.baseFileName + idxStr + stackName + '.tif'
			fileName = self.baseFileName + '_' + stackName + '.tif'
			filePath = os.path.join(self.analysisPath, fileName)
			
			if not os.path.isfile(filePath):
				print('  Warning: did not find file', filePath)
				continue
				
			print('  loading:', fileName)
			#
			data = tifffile.imread(filePath)
			#
			self.stackDict[stackName]['data'] = data
			#print('   ', self.stackDict[stackName]['data'].shape)
			#

			# try and loaded edited labels
			if stackName == 'labeled':			
				if os.path.isfile(self.editLabelPath):
					tmpPath, tmpFilename = os.path.split(self.editLabelPath)
					print('  LOADING: editLabels from:', tmpFilename)
					self.editLabelData = tifffile.imread(self.editLabelPath)
				else:
					print('  CREATING: editLabels from original labeled')
					self.editLabelData = data.copy()
				print('    self.editLabelData.shape:', self.editLabelData.shape)
				
	def getEditLabelLayer(self, viewer):
		"""
		get layer named editLabelName
		"""
		for idx, layer in enumerate(viewer.layers):
			if layer.name == self.editLabelName:
				retIdx = idx
				break
		if viewer.layers is not None:
			return viewer.layers[retIdx]
		else:
			return None
		
	def setUndo(self, labelNumber, newLabelNumber, sliceNum, data):
		"""
		add to undo list
		"""
		self.undoLabelNumber.append(labelNumber)
		self.undoNewLabelNumber.append(newLabelNumber)
		self.undoSliceNumber.append(sliceNum)
		self.undoSliceData.append(data.copy())

	def undo(self, viewer):
		if self.undoSliceData:
			undoLabelNumber = self.undoLabelNumber.pop() # the label that was clicked on
			undoNewLabelNumber = self.undoNewLabelNumber.pop() # the label we originally created
			undoSliceNumber = self.undoSliceNumber.pop()
			undoSliceData = self.undoSliceData.pop()

			labelLayer = self.getEditLabelLayer(viewer)
			if labelLayer is not None:
				labelLayer.data[undoSliceNumber,:,:] = undoSliceData
				
				
				# set to the slice we just did uno on
				viewer.dims.set_point(0, undoSliceNumber) # set slice
				#
				labelLayer.refresh()

				statusStr = 'Did undo of label ' + str(undoNewLabelNumber) + ' back to original label ' + str(undoLabelNumber)
				self.myPrint(statusStr)

				print('    *** labelLayer.data.shape:', labelLayer.data.shape)
			
		else:
			statusStr = 'No undo data'
			self.myPrint(statusStr)
			#print(statusStr)
			#viewer.status = statusStr
			
	def save(self, viewer=None):
		"""
		save _v2 label layer
		"""	
		if viewer is None:
			viewer = self.viewer
		
		labelLayer = self.getEditLabelLayer(viewer)
		data = labelLayer.data # save this
		
		statusStr = 'Saving ' + self.editLabelPath
		self.myPrint(statusStr)
		labelLayer.refresh()
		
		print('  ', data.shape)
		
		tifffile.imsave(self.editLabelPath, data)

		statusStr = 'Done saving ' + self.editLabelPath
		self.myPrint(statusStr)
		#print(statusStr)
		#viewer.status = statusStr
		
	def revertLabel(self, viewer=None):
		"""
		set the current lavel in edit labl back to self.origNumLabels
		
		not optimal
		"""
		if viewer is None:
			viewer = self.viewer
		
		mySlice = self.viewer.dims.point[0] # get the slice
		
		layer = self.getEditLabelLayer(viewer)
		cords = np.round(layer.coordinates).astype(int) # [z,x,y], remember x is down, y is right
		myCoords = (cords[1], cords[2]) # tuple

		val = layer.get_value() # the label clicked on

		#
		# only revert if it is a label we modified
		if val <= self.origNumLabels:
			statusStr = "Can't revert an original label. Label number " + str(val)
			self.myPrint(statusStr)
			#print(statusStr)
			#viewer.status = statusStr
			return
			
		#
		# set the selected label back to self.origNumLabels
		originalLabelData = self.stackDict['labeled']['data'] 
		originalVal = originalLabelData[mySlice, myCoords[0], myCoords[1]]
		
		sliceData = layer.data[mySlice,:,:]
		sliceData[sliceData==val] = originalVal
		layer.data[mySlice,:,:] = sliceData
		
		layer.refresh()
		
		statusStr = 'Reverted label ' + str(val) + ' back to original label ' + str(originalVal)
		self.myPrint(statusStr)

		print('    *** layer.data.shape:', layer.data.shape)
		
	def editLabel(self, layer, event):
		"""
		Add a new label in the current slice, pixels under mouse pointer
		
		layer: has to be self.editLabelName
		"""

		if layer.name != self.editLabelName:
			# this never happens ???
			statusStr = 'mouse-click has to be in layer:' + self.editLabelName + ' ... NO ACTION TAKEN ...'
			self.myPrint(statusStr)
			return
		
		# mode can be (pan_zoom, pick, paint, fill)
		if layer.mode != 'pan_zoom':
			#print('can only edit in pan/zoom mode, select pan/zoom with "z" or click the magnifying glass icon')
			return
			
		# using member viewer in code !!! ???
		mySlice = self.viewer.dims.point[0] # get the slice

		#viewer.dims.set_point(axis, currentSlice) # set slice

		cords = np.round(layer.coordinates).astype(int) # [z,x,y], remember x is down, y is right
		myCoords = (cords[1], cords[2]) # tuple

		val = layer.get_value() # the label clicked on
		if val is None:
			statusStr = 'val was "None" ... not sure why'
			self.myPrint(statusStr)
			#print(statusStr)
			#layer.status = statusStr
			return
		
		if val > self.origNumLabels:
			statusStr = "Can't set a label again " + str(val)
			self.myPrint(statusStr)
			#print(statusStr)
			#layer.status = statusStr
			return
			
		currentNumberOfLabel = np.nanmax(layer.data)
		newLabel = currentNumberOfLabel + 1
	
		#
		#
		msg = ''
		if val > 0:
			sliceData = layer.data[mySlice,:,:]

			self.setUndo(val, newLabel, mySlice, sliceData)

			
			newValue = newLabel

			
			floodFillIterations = self.floodFillIterations
			if floodFillIterations == 0: # control with keyboard +/-
				# was this
				# flood_fill on JUST the label clicked on
				myRegion = skimage.morphology.flood_fill(sliceData, myCoords, newValue)		
			else:
				# dilate
				sliceDataBool = scipy.ndimage.binary_dilation(sliceData, iterations=floodFillIterations).astype(np.uint8)
				# flood_fill on (0/1) binary_dilation
				myRegion2 = skimage.morphology.flood_fill(sliceDataBool, myCoords, newValue)		
				# revert back to labels
				# create a region with original labels (sliceData) and new region (newValue)
				myRegion = np.where((sliceData>0) & (myRegion2==newValue), newValue, sliceData)
			
			layer.data[mySlice,:,:] = myRegion
						
			layer.refresh()

			#print('=== origNumLabels:', self.origNumLabels, 'currentNumberOfLabel:', currentNumberOfLabel, 'old label:', val, 'newLabel:', newLabel)
			msg = f'Clicked at {cords} on label {val} which is now label {newLabel}'
			self.myPrint(msg)

			print('    *** layer.data.shape:', layer.data.shape)
			
		else:
			msg = f'Clicked at {cords} on background which is ignored'
			self.myPrint(msg)
			

	def myNapari(self, withContext=True):
		if withContext:
		    cm = napari.gui_qt()
		else:
		    cm = nullcontext()

		#with napari.gui_qt():
		with cm:

			# this is super confusing, used from Jupyter notebooks
			self.viewer = napari.Viewer(title=self.baseFileName)
	
			for idx, (stackName,v) in enumerate(self.stackDict.items()):
				if not stackName in self.loadTheseStacks:
					continue

				type = v['type'] # (image, mask, label)
				data = v['data']
				
				if data is None:
					# not loaded
					print('  myNapari() stackName:', stackName, 'Warning: DID NOT FIND DATA')
					continue
				
				print('  myNapari() stackName:', stackName, data.shape)
				
				if type == 'image':
					minContrast= 0 
					maxContrast = np.nanmax(data)
					myImageLayer = self.viewer.add_image(data, contrast_limits=(minContrast, maxContrast), visible=False, name=stackName)
				if type == 'mask':
					minContrast= 0 
					maxContrast = 1
					myMaskLayer = self.viewer.add_image(data, contrast_limits=(minContrast, maxContrast), opacity=0.66, visible=False, name=stackName)
				elif type == 'label':
					myLabelsLayer = self.viewer.add_labels(data, opacity=0.7, visible=False, name=stackName)
					
					# switch this to _v2
					editLabelData = self.editLabelData #data.copy()
					self.myLabelsLayer = self.viewer.add_labels(editLabelData, opacity=0.7, visible=True, name=self.editLabelName)
				
				# myLabelsLayer = self.viewer.add_labels(myLabels, name=editLabelName)
				# myLabelsLayer.brush_size = 5
			
			if self.myLabelsLayer is None:
				fakeData = np.ndarray((1,1,1))
				self.myLabelsLayer = self.viewer.add_labels(fakeData, opacity=0.7, visible=False, name='x ' + self.editLabelName)
				
			'''
			@self.viewer.mouse_drag_callbacks.append
			def get_ndisplay(viewer, event):
				if 'Alt' in event.modifiers:
					print('viewer display ', viewer.dims.ndisplay)
			'''
			
			@self.viewer.bind_key('s')
			def mySave(viewer):
				self.save(viewer)

			@self.viewer.bind_key('r')
			def myRemove(viewer):
				self.revertLabel(viewer)
			
			@self.viewer.bind_key('u')
			def myUndo(viewer):
				self.undo(viewer)
			
			@self.viewer.bind_key('.')
			def myAdjustFloodFill_Plus(viewer):
				self.floodFillIterations += 1
				print('floodFillIterations:', self.floodFillIterations)
			@self.viewer.bind_key(',')
			def myAdjustFloodFill_Plus(viewer):
				self.floodFillIterations -= 1
				if self.floodFillIterations < 0:
					self.floodFillIterations = 0
				print('floodFillIterations:', self.floodFillIterations)
			
			
			@self.myLabelsLayer.mouse_drag_callbacks.append
			def get_connected_component_shape(layer, event):
				"""
				How can we get viewer in this callback???
				"""								
				self.editLabel(layer, event)
				
	def _printStackParams(self, name, myStack):
		print('  ', name, myStack.shape, myStack.dtype, 'dtype.char:', myStack.dtype.char,
			'min:', np.min(myStack),
			'max:', np.max(myStack),
			'mean:', np.mean(myStack),
			'std:', np.std(myStack),
			)
				
##############################################################################
if __name__ == '__main__':

	# todo: add argparse for command line
	
	parser = argparse.ArgumentParser(description = 'Process 2 channel hcn1 and vascular files into edt')
	parser.add_argument('tifPath', nargs='*', default='', help='path to original _ch1 .tif file')
	args = parser.parse_args() # args is a list of command line arguments

	if len(args.tifPath)>0:
		pathToRawTiff = args.tifPath[0]		
	else:
		#pathToRawTiff = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0007_ch1.tif'
		#pathToRawTiff = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0010_ch1.tif'
		#pathToRawTiff = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0011_ch1.tif'

		pathToRawTiff = '/Users/cudmore/box/data/nathan/20200116/20190116__A01_G001_0014_ch1.tif'
		pathToRawTiff = '/Users/cudmore/box/data/nathan/20200518/20200518__A01_G001_0003_ch2.tif'
		
	myLabelEdit(pathToRawTiff, withContext=True, verbose=True)
	
	
	
	