import numpy as np
import imageio

from skimage.external import tifffile as tif

def sphere2(shape, radii, position):
	
	arr = np.zeros(shape, dtype=float)
	for myIdx, radius in enumerate(radii):
		# assume shape and position are both a 3-tuple of int or float
		# the units are pixels / voxels (px for short)
		# radius is a int or float in px
		semisizes = (radius,) * 3

	   	# genereate the grid for the support points
		# centered at the position indicated by position
		grid = [slice(-x0, dim - x0) for x0, dim in zip(position[myIdx], shape)]
		position2 = np.ogrid[grid]
		# calculate the distance of all points from `position` center
		# scaled by the radius
		#arr = np.zeros(shape, dtype=float)
		for x_i, semisize in zip(position2, semisizes):
			arr += (np.abs(x_i / semisize) ** 2)
		# the inner part of the sphere will have distance below 1
	
	return arr <= 1.0

def sphere(shape, radius, position):
	# assume shape and position are both a 3-tuple of int or float
	# the units are pixels / voxels (px for short)
	# radius is a int or float in px
	semisizes = (radius,) * 3

	# genereate the grid for the support points
	# centered at the position indicated by position
	grid = [slice(-x0, dim - x0) for x0, dim in zip(position, shape)]
	position = np.ogrid[grid]
	# calculate the distance of all points from `position` center
	# scaled by the radius
	arr = np.zeros(shape, dtype=float)
	for x_i, semisize in zip(position, semisizes):
		arr += (np.abs(x_i / semisize) ** 2)
	# the inner part of the sphere will have distance below 1
	return arr <= 1.0

arr = sphere((256, 256, 256), 10, (100, 100, 100))
print('arr.shape:', arr.shape, type(arr), arr.dtype)
#intArr = arr.astype('int8')

arr2 = sphere((256, 256, 256), 20, (50, 40, 50))
arr3 = sphere((256, 256, 256), 30, (150, 120, 150))
#intArr2 = arr2.astype('int8')

saveArr = arr + arr2 + arr3
saveArr = saveArr.astype('int8')
print('saveArr.shape:', saveArr.shape, type(saveArr), saveArr.dtype)
tif.imsave('a.tif', saveArr, bigtiff=True)

myShape = (256,1024,1024)
myRadii = [10,20,30,40,50,60]
myPositions = [
	(50, 40, 50),
	(100, 100, 100),
	(150, 120, 150),
	(100, 300, 300),
	(100, 500, 500),
	(120, 700, 700),
	]
#myArr = sphere2(myShape, myRadii, myPositions)
for idx, radius in enumerate(myRadii):
	print(idx)
	arr = sphere(myShape, myRadii[idx], myPositions[idx])
	if idx==0:
		saveArr = arr
	else:
		saveArr += arr
myArr = saveArr.astype('int8')
		
print('myArr.shape:', myArr.shape, type(myArr), myArr.dtype)
tif.imsave('b.tif', myArr, bigtiff=True)

#imageio.imwrite('sphere.tif', intArr)
# this will save a sphere in a boolean array
# the shape of the containing array is: (256, 256, 256)
# the position of the center is: (127, 127, 127)
# if you want is 0 and 1 just use .astype(int)
# for plotting it is likely that you want that

# just for fun you can check that the volume is matching what expected
mySum = np.sum(arr)
# gives: 4169
print('mySum:', mySum)

mySum2 = 4 / 3 * np.pi * 10 ** 3
print('mySum2:', mySum2)
# gives: 4188.790204786391
# (the two numbers do not match exactly because of the discretization error)
