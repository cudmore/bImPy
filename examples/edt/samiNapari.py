import sys

import napari

def myNapari(path):
	print('myNapari()')
	#
	# napari
	#numLabels = np.max(labeledStack)
	#myScale = (5, 3, 3)
	myScale = (3, 1, 1)
	with napari.gui_qt():
		viewer = napari.Viewer(ndisplay=2)
		'''
		for k,v in results.items():
			minContrast = 0
			maxContrast = 1
			theMax = np.max(v)
			if theMax == 1:
				maxContrast = 1 # binary mask
			elif theMax>250:
				maxContrast = 60 # 8-bit image
			else:
				maxContrast = theMax + 1 # labeled stack
			colormap = 'gray'
			if k == 'distanceMap':
				colormap = 'inferno'
			elif k == 'imageStack':
				colormap = 'green'
			# colormap
			viewer.add_image(v, scale=myScale, contrast_limits=(minContrast,maxContrast), opacity=0.5, colormap=colormap, visible=False, name=k)
		'''
		
		'''
		# channel 2
		viewer.add_image(imageStack, scale=myScale, contrast_limits=(0, 60), visible=False, name='raw stack')
		viewer.add_image(thresholdStack, scale=myScale, contrast_limits=(0, 1), visible=False, name='thresholded')
		viewer.add_image(filledHolesStack, scale=myScale, contrast_limits=(0, 1), visible=False, name='filled holes')
		viewer.add_image(labeledStack, scale=myScale, contrast_limits=(0, numLabels+1), visible=False, name='labeled')
		viewer.add_image(finalMask, scale=myScale, contrast_limits=(0, 1), visible=False, name='final mask')
		viewer.add_image(erodedMask, scale=myScale, contrast_limits=(0, 1), visible=False, name='eroded mask')
		'''

if __name__ == '__main__':
	nArg = len(sys.argv)
	argList = str(sys.argv)
	for arg in argList:
		myNapari(arg)