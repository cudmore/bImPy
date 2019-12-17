import numpy as np
from skimage import data
import napari

import bimpy

myPointSize = 2

# this works
myPointColors = [[1.0, 0.1, 0.1], [0.1, 1.0, 0.1], [0.1, 0.1, 1.0]]
myPointColors = [0.0, 1.0, 1.0] #'cyan'

path = '/Users/cudmore/Sites/bImpy-Data/vesselucida/20191017__0001.tif'
myStack = bimpy.bStack(path=path)

print('myStack.stack.shape:', myStack.stack.shape) # [channels, slices, x, y]

#
# we are using reshape(-1,1) here because each of x/y/x are of shape (n,) and we want (n,1)
x = myStack.slabList.x.reshape((-1,1)) # to do, fix this (n,) shape converting to (n)
y = myStack.slabList.y.reshape((-1,1))
z = myStack.slabList.z.reshape((-1,1))

# swap x/y
xyzPoints = np.hstack((z, x, y))

#print('x.shape:', x.shape)
print('xyzPoints.shape', xyzPoints.shape)


# colorize each edge based on nan in x
myPointColors = []
'''
pointColorList = [
	[0.0, 1.0, 0.0], 
	[0.0, 0.0, 1.0],
	[0.0, 1.0, 1.0],
	[1.0, 0.0, 1.0],	
	]
'''
pointColorList = [
	[0.0, 1.0, 0.0], 
	[0.0, 0.0, 1.0],
	]

x0 = myStack.slabList.x
y0 = myStack.slabList.y
z0 = myStack.slabList.z
pointColorIdx = 0
currentEdgeIdx = 0
masterEdgeList = []
currentEdgeList = []
for idx, tmpx in enumerate(x):
	if np.isnan(tmpx):
		# next idx is new edge
		#print(idx, 'currentEdgeList:', currentEdgeList)
		masterEdgeList.append(currentEdgeList)
		# debug
		if currentEdgeIdx == 0:
			print('idx:', idx, 'currentEdgeIdx:', currentEdgeIdx, np.array(currentEdgeList))
		# reset
		currentEdgeIdx += 1
		currentEdgeList = []
			
		# colors
		pointColorIdx += 1
		if pointColorIdx > len(pointColorList) -1:
			pointColorIdx = 0
		#print('pointColorIdx:', pointColorIdx)
	else:
		# append to current edge
		currentEdgeList.append([z0[idx], x0[idx], y0[idx]])

	myPointColors.append(pointColorList[pointColorIdx])

print('masterEdgeList:', len(masterEdgeList))
print('masterEdgeList[0]:', len(masterEdgeList[0]))
arrayList  = [np.array(xx) for xx in masterEdgeList]
print('arrayList:', len(arrayList))
print('arrayList[0].shape:', arrayList[0].shape)
myPath0 = np.array(arrayList)
print('type(myPath0):', type(myPath0), 'myPath0.shape:', myPath0.shape)
print('myPath0[0]:', myPath0[0])

myPath0 = arrayList # always give napari a list where each[i] is a np.array ???

edge_width0 = 3
edge_color0 = 'red'

#
# dead ends in red
deadEndx = myStack.slabList.deadEndx.reshape((-1,1))
deadEndy = myStack.slabList.deadEndy.reshape((-1,1))
deadEndz = myStack.slabList.deadEndz.reshape((-1,1))

# swap x/y
xyzDeadEnds = np.hstack((deadEndz, deadEndx, deadEndy))

#
# using shapes path
myPath = np.array([
	np.array([[0, 0, 0], [0, 10, 10], [0, 5, 15], [20, 5, 15],
	[56, 70, 21], [127, 127, 127]]),
	np.array([[0, 0, 0], [0, 10, 10], [0, 5, 15], [0, 5, 15],
		[0, 70, 21], [0, 127, 127]])
	])
edge_width = [1,5]
print('myPath.shape:', myPath.shape)

with napari.gui_qt():
	# add the image
	scale = (0.2, 0.2, 1)
	scale = (1, 1, 1)
	viewer = napari.view_image(myStack.stack, name='vessellucida', scale=scale)
	
	# add the points
	#pointLayer = viewer.add_points(xyzPoints, size=myPointSize, edge_color=myPointColors, face_color=myPointColors)

	deadEndSize = 4
	deadEndColor = 'red'
	pointLayer = viewer.add_points(xyzDeadEnds, size=deadEndSize, edge_color=deadEndColor, face_color=deadEndColor)

	#print(pointLayer.face_colors)

	layer = viewer.add_shapes(
		myPath0, shape_type='path', edge_width=edge_width0, edge_color=edge_color0
	)	