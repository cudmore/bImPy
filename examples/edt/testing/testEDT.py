"""
using code from

https://github.com/seung-lab/euclidean-distance-transform-3d
"""

import os, sys, json

#import edt
import numpy as np
import tifffile

import scipy

#
# specify um/voxel dimension

# fractional numbers seem to cause segmentation fault
# these are real values in um/pixel
xVoxel = 0.3107403
yVoxel = 0.3107403
zVoxel = 0.5

# whole number run to completion
xVoxel = 3
yVoxel = 3
zVoxel = 5

# however you'll want to reverse the order of the anisotropic arguments for Fortran order
myAnisotropy = (xVoxel, yVoxel, zVoxel) # (x,y,z)
print('myAnisotropy:', myAnisotropy)

#
# load original mask and massage

myMaskPath = '/Users/cudmore/box/data/nathan/20200420/distanceAnalysis/20200420_distalHEAD__ch2_mask.tif'
myMaskPath = '/Users/cudmore/box/data/nathan/20200420/distanceAnalysis/20200420_HEAD__ch2_mask.tif'

myMask = tifffile.imread(myMaskPath)
print('1 myMask:', myMask.shape, myMask.dtype, 'min:', np.min(myMask), 'max:', np.max(myMask))

# make a copy to save and view original in Napari, 0:background, 255:mask
myMaskOriginal = myMask

# this works, converting mask to 0 and background to 1 ???
# original mask is 0==background and 255==mask
# again, original mask is 0:background, 255:mask
# convert to 0:mask, background:1
# 0==mask, 1==background
if 1:
	myMask[myMask==0] = 10 # 0 is original background
	myMask[myMask==255] = 0 # 255 is original mask
	myMask[myMask==10] = 1
	
print('2 myMask:', myMask.shape, myMask.dtype, 'min:', np.min(myMask), 'max:', np.max(myMask))
print(myMask.flags)

myMaskOutPath = '/Users/cudmore/Desktop/testedt_mask.tif'
print('saving oringinal mask myMaskOutPath:', myMaskOutPath)
tifffile.imsave(myMaskOutPath, myMaskOriginal)

#
# run edt

# order was confusing here, we are really using 'F' (z,x,y) but specify 'c' (x,y,z) ???? 
# 'F' (Fortran-order, ZYX, column major)
print('running edt ... please wait')
dt = edt.edt(
  myMask, anisotropy=myAnisotropy, 
  black_border=False, order='C',
  parallel=0 # number of threads, <= 0 sets to num cpu
) 

# cast dt results to uint16 to match myMask
#dt = dt.astype(np.uint16)

print('  dt:', type(dt), dt.shape, dt.dtype, 'min:', np.min(dt), 'max:', np.max(dt))

#
# save results

outpath = '/Users/cudmore/Desktop/testedt2.tif'
print('  saving dt', outpath)
tifffile.imsave(outpath, dt)

#
# napari
import napari
myScale = (myAnisotropy[2], myAnisotropy[0], myAnisotropy[1]) # (z,x,y)
with napari.gui_qt():
	viewer = napari.Viewer(ndisplay=3)
	viewer.add_image(dt, scale=myScale, name='dt')
	viewer.add_image(myMaskOriginal, scale=myScale, opacity=0.33, name='mask')

