"""
20200518
Robert Cudmore

	See:
		https://github.com/scipy/scipy/issues/9751#issuecomment-628878799

	This will only work with

		python3 -m venv myenv/
		source myenv/bin/activate
		pip install numpy==1.17.4
		pip install scipy==1.1.0
		pip install matplotlib scikit-image

"""

import os, argparse
import numpy as np
import scipy
import scipy.spatial

# can't use bimpy because of scipy requirements
#import bimpy

def _flood_fill_hull(image):	
	points = np.transpose(np.where(image))
	print('  flood_fill_hull.points:', points.shape, points.dtype)
	print('  calling ConvexHull')
	hull = scipy.spatial.ConvexHull(points)
	print('  calling Delaunay')
	deln = scipy.spatial.Delaunay(points[hull.vertices]) 
	print('  calling stack')
	idx = np.stack(np.indices(image.shape), axis = -1)
	out_idx = np.nonzero(deln.find_simplex(idx) + 1)
	out_img = np.zeros(image.shape)
	out_img[out_idx] = 1
	
	out_img = out_img.astype(np.uint8)
	
	return out_img, hull

def convexHull(stackMask):
	print('convexHull()')
	
	scipyVersion = scipy.__version__
	if scipyVersion > "1.4.1":
		print('CRITICAL ERROR: convexHull() requires scipy <= 1.4.1 but found', scipyVersion)
		return None
	
	points = np.transpose(np.where(stackMask))
	
	out_img, hull = _flood_fill_hull(stackMask)
		
	print('  out_img:', out_img.shape, out_img.dtype)
	print('  hull.volume:', hull.volume)
		
	return out_img

if __name__ == '__main__':

	import tifffile
	
	parser = argparse.ArgumentParser(description = 'Process 2 channel hcn1 and vascular files into edt')
	parser.add_argument('finalMask', nargs='*', default='', help='path to _finalMask.tif')
	args = parser.parse_args() # args is a list of command line arguments

	if len(args.finalMask)>0:
		path = args.tifPath[0]		
	else:

		# load mask
		path = '/Users/cudmore/box/data/nathan/20200116/analysis2/20190116__A01_G001_0007_ch1_finalMask.tif'
		path = '/Users/cudmore/box/data/nathan/20200116/analysis2/20190116__A01_G001_0010_ch1_finalMask.tif'
		path = '/Users/cudmore/box/data/nathan/20200116/analysis2/20190116__A01_G001_0011_ch1_finalMask.tif'
		#imageData, tiffHeader = bTiffFile.imread(path)

	imageData = tifffile.imread(path)
	print('loaded:', imageData.shape, imageData.dtype, 'from path:', path)

	#testHull()
	convexHullData = convexHull(imageData)

	#
	# save
	#savePath = '/Users/cudmore/Desktop/tstHull.tif'
	
	tmpPath, tmpFileName = os.path.split(path)
	tmpFileNameNoExtension, tmpExtension = tmpFileName.split('.')
	baseFilePath = os.path.join(tmpPath, tmpFileNameNoExtension)

	savePath = baseFilePath +'_hull.tif'
	
	print('saving to savePath:', savePath)
	tifffile.imsave(savePath, convexHullData)
	
