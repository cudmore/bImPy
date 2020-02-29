# Robert Cudmore
# 20200228

import numpy as np
import tifffile

from raster_geometry import cylinder

def paste_slices(tup):
	pos, w, max_w = tup
	wall_min = max(pos, 0)
	wall_max = min(pos+w, max_w)
	block_min = -min(pos, 0)
	block_max = max_w-max(pos+w, max_w)
	block_max = block_max if block_max != 0 else None
	return slice(wall_min, wall_max), slice(block_min, block_max)

def paste(wall, block, loc):
	loc_zip = zip(loc, block.shape, wall.shape)
	wall_slices, block_slices = zip(*map(paste_slices, loc_zip))
	# was '=', use '+=' assuming we are using binary
	#print('   wall_slices:', wall_slices)
	#print('   block_slices:', block_slices)
	try:
		wall[wall_slices] += block[block_slices]
	except (ValueError) as e:
		print('paste() error in wall[wall_slices] ... fix this later')

def myRun():
	# put into bigger volume
	numSlices = 100
	pixelsPerLine = 256
	linesPerFrame = 256
	finalVolume = np.zeros([numSlices, pixelsPerLine, linesPerFrame])

	# because I am using axis=1, radius and height are swapped?
	axis = 1 # horizontal

	cylinderList = [
		{'height': 40, 'radius': 3, 'z': 10, 'x': 100, 'y': 100},
		{'height': 40, 'radius': 4, 'z': 50, 'x': 100, 'y': 100},
		{'height': 40, 'radius': 5, 'z': 75, 'x': 100, 'y': 100},
		{'height': 40, 'radius': 3, 'z': 90, 'x': 100, 'y': 100},
	]
	for aCylinder in cylinderList:
		'''
		height = 8
		radius = 40
		axis = 1 #-1
		'''
		height = aCylinder['radius'] #swapping
		radius = aCylinder['height']
		shape = (height,radius*2,radius*2)
		# position in larger volume
		z = aCylinder['z']
		x = aCylinder['x']
		y = aCylinder['y']

		# (shape, height, radius, axis, position)
		#c0 = cylinder(4, 2, 2, 0)
		theCylinder = cylinder(shape, height, radius, axis)#, position)
		#print(type(aCylinder), aCylinder.dtype, aCylinder.shape, np.min(aCylinder), np.max(aCylinder))

		'''
		z = 50
		x = 100
		y = 100
		'''
		paste(finalVolume, theCylinder, (z,x,y))

	# convert bool to int8
	#finalVolume = finalVolume > 0
	finalVolume = finalVolume.astype('uint8')
	finalVolume[finalVolume>0] = 200
	print('finalVolume.shape:', finalVolume.shape, 'finalVolume.dtype:', finalVolume.dtype, finalVolume.dtype.char)
	print('np.min(finalVolume):', np.min(finalVolume), np.max(finalVolume))

	print('saving cylinder0.tif...')
	tifffile.imwrite('cylinder0.tif', finalVolume, photometric='minisblack')
	tifffile.imwrite('cylinder0.tif', finalVolume,
		imagej=True, resolution=(1./2.6755, 1./2.6755),metadata={'spacing': 3.947368, 'unit': 'um'})
	
if __name__ == '__main__':
	myRun()
