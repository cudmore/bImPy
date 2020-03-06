#20200303

"""
Use Skan to analyze a skeleton as a graph.

see: https://jni.github.io/skan/getting_started.html

skan requires (pandas, numba)

pip install skan
pip install pandas
pip install numba
"""

fileRoot = '/Users/cudmore' # macOS
fileRoot = 'C:/Users/cudmorelab' # windows

import time
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
path = fileRoot + '/box/Sites/DeepVess/data/20191017/20191017__0001_z.tif'
path = fileRoot + '/box/Sites/DeepVess/data/20200228/20200228__0001_z.tif'
print('=== path:', path)
rawStack = tifffile.imread(path)
print('    rawStack:', rawStack.shape)

# load binary 3d mask, the output of deepvess
path = fileRoot + '/box/Sites/DeepVess/data/20191017/20191017__0001_z_dvMask.tif'
path = fileRoot + '/box/Sites/DeepVess/data/20200228/20200228__0001_z_dvMask.tif'
dvMask = tifffile.imread(path)
print('    dvMask:', dvMask.shape)

# load deepves skel (the saved output of postprocess)
path = fileRoot + '/box/Sites/DeepVess/data/20191017/20191017__0001_z_dvSkel.tif'
path = fileRoot + '/box/Sites/DeepVess/data/20200228/20200228__0001_z_dvSkel.tif'
dvSkel = tifffile.imread(path)
print('    dvSkel:', dvSkel.shape)

# convert the deepvess mask to a skeleton (same as deepves postprocess)
print('    making skeleton from binary stack dvMask ...')
# todo: fix this, older version need to use max_pool3d
#skeleton0 = morphology.skeletonize(dvMask)
startSeconds = time.time()
skeleton0 = morphology.skeletonize_3d(dvMask)
print('    skeleton0:', type(skeleton0), skeleton0.dtype, skeleton0.shape, np.min(skeleton0), np.max(skeleton0))
print('        took:', round(time.time()-startSeconds,2), 'seconds')
#
# analysis of skeleton
pixel_graph, coordinates, degrees = skan.skeleton_to_csgraph(skeleton0)
print('    pixel_graph:', type(pixel_graph))
print('    coordinates:', type(coordinates), coordinates.shape) # (n,3) each row is a point in skel
print('    degrees:', type(degrees), degrees.shape)

# make a list of coordinate[i] that are segment endpoints_src
nCoordinates = coordinates.shape[0]
slabs = coordinates.copy() #np.full((nCoordinates,3), np.nan)
nodes = np.full((nCoordinates), np.nan)
nodeEdgeList = [[] for tmp in range(nCoordinates)]
edges = np.full((nCoordinates), np.nan)

print('degrees==0:', degrees[degrees==0].shape)
print('degrees==1:', degrees[degrees==1].shape)
print('degrees==2:', degrees[degrees==2].shape)
print('degrees>=3:', degrees[degrees>=3].shape)

'''
degrees is an image of the skeleton, with each skeleton pixel containing the
number of neighbouring pixels. This enables us to distinguish between
junctions (where three or more skeleton branches meet),
endpoints (where a skeleton ends),
and paths (pixels on the inside of a skeleton branch).
'''

#
# alternate way to use skan (todo: look into this)
print('    === running skan.Skeleton(skeleton0)')
skanSkel = skan.Skeleton(skeleton0, source_image=rawStack)

pathIdx = 2
print('skanSkel.paths_list():', len(skanSkel.paths_list()))
thisPath = skanSkel.paths_list()[pathIdx] # list of indices into coordinates[i,3]
print('    pathIdx:', pathIdx, 'thisPath:', thisPath)
# works
#print('    coordinates[thisPath]:', coordinates[thisPath])
if 1:
	for idx, path in enumerate(skanSkel.paths_list()):
		srcPnt = path[0]
		dstPnt = path[-1]
		'''
		slabs[srcPnt] = coordinates[srcPnt]
		slabs[dstPnt] = coordinates[dstPnt]
		'''
		nodes[srcPnt] = idx
		nodes[dstPnt] = idx
		nodeEdgeList[srcPnt].append(idx)
		nodeEdgeList[dstPnt].append(idx)
		if len(path)>2:
			for idx2 in path[1:-2]:
				edges[idx2] = idx
		#print(idx, 'path:', path)
		#print('path', path, skanSkel.path(path)) # Return the pixel indices of path number index.

# works fine
if 1:
	'''
	    branch_data['branch-type'] is as follows
		kind[(deg_src == 1) & (deg_dst == 1)] = 0  # tip-tip
	    kind[(deg_src == 1) | (deg_dst == 1)] = 1  # tip-junction
	    2: junction-to-junction
		kind[endpoints_src == endpoints_dst] = 3  # cycle
	'''
	branch_data = skan.summarize(skanSkel)
	print('branch_data.shape:', branch_data.shape)
	print(branch_data.head())
	# works fine
	#branch_data.to_excel('C:/Users/cudmorelab/Box/Sites/summary.xlsx')

#
# plot the results
# this does not work because we are using 3D, would be nice !!!
if 0:
	print('plotting with skan and matplotlib')
	import matplotlib.pyplot as plt
	oneImage = skeleton0[59,:,:]
	pixel_graph0, coordinates0, degrees0 = skan.skeleton_to_csgraph(oneImage) # just one image
	fig, axes = plt.subplots(1, 2)
	draw.overlay_skeleton_networkx(pixel_graph0, coordinates0, image=oneImage, axis=axes[0])
	plt.show() # this needs to be added to the Skel documentation !!!

# visualize in napari
if 1:
	with napari.gui_qt():
		viewer = napari.view_image(data=dvMask, contrast_limits=[0,1], colormap='cyan', name='dvMask')
		viewer.add_image(data=skeleton0, contrast_limits=[0,1], opacity=0.8, colormap='gray', name='skeleton0')
		viewer.add_image(data=dvSkel, contrast_limits=[0,1], opacity=0.8, colormap='red', name='dvSkel')
		viewer.add_image(data=rawStack, opacity=0.5, colormap='green', name='rawStack')
		viewer.add_points(slabs[nodes>=0,:], edge_color ='red', face_color='red', size=5)
		viewer.add_points(slabs[edges>=0,:], edge_color ='cyan', face_color='cyan', size=3)

# todo: compare the skeleton from deepvess postprocess to the skeleton from skimage.morphology.skeletonize
