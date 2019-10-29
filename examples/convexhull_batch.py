"""
# Robert Cudmore
# 20191029

Run this script and point the folder dialog to a folder with correspong .tif and .xml files.

The output will be one line of text for each .tif/.xls pair including
 - the full path to the .tif file
 - the 3D convex hull enclosing all points
 - the total tracing length
"""

import os
import numpy as np
from scipy.spatial import ConvexHull

from tkinter import filedialog
from tkinter import *

from bimpy import bSimpleStack

def convelHullVolume(path):
	"""
	given original .tif, return 3d convex hull from xml file

	args:
		path: full path to .tif file
	return:
		3d convex hull
	"""

	# load stack by parsing vascular graph in corresponding .xml file
	bss = bSimpleStack.bSimpleStack(path, loadImages=False)

	# check if we found corresponding .xml file
	if len(bss.slabList.x) == 0:
		print('did not load xml for tiff file', path)
		return None

	# get list of all (x,y,z) points in tracing
	points = bss.slabMatrix_original()
	points = points[~np.isnan(points).any(axis=1)] # remove nan rows

	# calculate convex hull
	hull = ConvexHull(points)
	volume = hull.volume

	totalTracingLength = 0
	for edge in bss.slabList.edgeDictList:
		totalTracingLength += edge['Len 3D Nathan']

	return volume, totalTracingLength

if __name__ == '__main__':
	#path = '/Users/cudmore/box/data/nathan/vesselucida'
	path = ''
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
				volume, totalTracingLength = convelHullVolume(fullpath)
				print(fullpath, round(volume,2), round(totalTracingLength,2))
