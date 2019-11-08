# Robert Cudmore
# 20191108

import numpy as np

import bimpy
import napari

class bNapari:
	def __init__(self, path):

		self.myStack = bimpy.bStack(path)

		print('self.myStack.stack.shape:', self.myStack.stack.shape)

		self.myNapari = napari.view_image(self.myStack.stack[0,:,:,:])

		x = self.myStack.slabList.x
		y = self.myStack.slabList.y
		z = self.myStack.slabList.z

		points = np.column_stack((z,x,y,))
		#points = points[~np.isnan(points).any(axis=1)] # remove nan rows
		print('points.shape:', points.shape)

		size = 10

		#points = np.array([[100, 100], [200, 200], [333, 111]])
		#size = np.array([10, 20, 20])

		layer = self.myNapari.add_points(points, size=size, face_color='cyan', n_dimensional=False)

		#print(layer.edge_colors)
		#print(layer.face_colors)

if __name__ == '__main__':
	path = '/Users/cudmore/box/data/nathan/vesselucida/20191017__0001.tif'
	mn = bNapari(path)
