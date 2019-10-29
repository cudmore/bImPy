# Robert Cudmore
# 20191029

import os
import numpy as np
from scipy.spatial import ConvexHull

from tkinter import filedialog
from tkinter import *

from bimpy import bSimpleStack

def convelHullVolume(path):
	"""
	return convex hull from xml file, given original tiff

	args:
		path: full path to tiff file
	"""
	bss = bSimpleStack.bSimpleStack(path, loadImages=False)

	# check if we found xml file
	if len(bss.slabList.x) == 0:
		print('did not load xml for tiff file', path)
		return None

	'''
	x = bss.slabList.orig_x
	y = bss.slabList.orig_y
	z = bss.slabList.orig_z
	# put 1d arrays of (x,y,z) into 2d matrix
	points = np.column_stack((x,y,z))
	'''
	points = bss.slabMatrix_original()

	hull = ConvexHull(points)

	return hull.volume

if __name__ == '__main__':
	path = '/Users/cudmore/box/data/nathan/vesselucida'
	if len(path) == 0:
		root = Tk()
		root.withdraw()
		path = filedialog.askdirectory()
	if len(path) == 0:
		pass
	else:
		for file in os.listdir(path):
			if file.endswith('.tif'):
				fullpath = os.path.join(path, file)
				volume = convelHullVolume(fullpath)
				print(fullpath, volume)
