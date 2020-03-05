#20200303

"""
Use Skan to analyze a skeleton as a graph.

see: https://jni.github.io/skan/getting_started.html

skan requires (pandas, numba)

pip install pandas
pip install numba
"""

import numpy as np

import tifffile
import napari
from skimage import morphology

import skan
from skan import draw # for plotting

def myMaxProect(data):
	maxProject = np.max(data, axis=0)
	return maxProject

# load the raw image
path = '/Users/cudmore/box/Sites/DeepVess/data/20191017/20191017__0001_z.tif'
print('=== path:', path)
rawStack = tifffile.imread(path)
print('    rawStack:', rawStack.shape)

# load binary 3d mask, the output of deepvess
path = '/Users/cudmore/box/Sites/DeepVess/data/20191017/20191017__0001_z_dvMask.tif'
dvMask = tifffile.imread(path)
print('    dvMask:', dvMask.shape)

# load deepves skel (the saved output of postprocess)
path = '/Users/cudmore/box/Sites/DeepVess/data/20191017/20191017__0001_z_dvSkel.tif'
dvSkel = tifffile.imread(path)
print('    dvSkel:', dvSkel.shape)

# convert the deepvess mask to a skeleton (same as deepves postprocess)
print('    making skeleton from binary stack dvMask ...')
skeleton0 = morphology.skeletonize(dvMask)
print('    skeleton0:', type(skeleton0), skeleton0.dtype, skeleton0.shape, np.min(skeleton0), np.max(skeleton0))

#
# analysis of skeleton
pixel_graph, coordinates, degrees = skan.skeleton_to_csgraph(skeleton0)
print('    pixel_graph:', type(pixel_graph))#, pixel_graph)
print('    coordinates:', type(pixel_graph))#, coordinates)
print('    degrees:', type(pixel_graph))#, degrees)

#
# alternate way to use skan (todo: look into this)
skanSkel = skan.Skeleton(skeleton0)
branch_data = skan.summarize(skanSkel)
#print(branch_data.head())
print(branch_data)

#
# plot the results
# this does not work because we are using 3D, would be nice !!!
print('plotting with skan and matplotlib')
import matplotlib.pyplot as plt
oneImage = skeleton0[59,:,:]
pixel_graph0, coordinates0, degrees0 = skan.skeleton_to_csgraph(oneImage) # just one image
fig, axes = plt.subplots(1, 2)
draw.overlay_skeleton_networkx(pixel_graph0, coordinates0, image=oneImage, axis=axes[0])
plt.show() # this needs to be added to the Skel documentation !!!

# visualize in napari
doNapari = False
if doNapari:
	with napari.gui_qt():
		viewer = napari.view_image(data=dvMask, contrast_limits=[0,1], colormap='cyan', name='dvMask')
		viewer.add_image(data=skeleton0, contrast_limits=[0,1], opacity=0.8, colormap='gray', name='skeleton0')
		viewer.add_image(data=dvSkel, contrast_limits=[0,1], opacity=0.8, colormap='red', name='dvSkel')
		viewer.add_image(data=rawStack, opacity=0.5, colormap='green', name='rawStack')

# todo: compare the skeleton from deepvess postprocess to the skeleton from skimage.morphology.skeletonize
