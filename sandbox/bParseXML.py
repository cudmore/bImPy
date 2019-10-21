import numpy as np
from xml.dom import minidom

path = '/Volumes/t3/Nathan/vesselucida/20191017_0001-all.xml'
mydoc = minidom.parse(path)

vessels = mydoc.getElementsByTagName('vessel')
print('found', len(vessels), 'vessels')

outPointList = [] #np.array((0,3))
diamList = []
outEdgeList = [] #np.array(0) # just keep track of each points edge index

masterEdgeIdx = 0
for i, vessel in enumerate(vessels):
		print('vessel i:', i, 'name:', vessel.attributes['name'].value)

		edges = vessel.getElementsByTagName('edges')
		print('   found', len(edges), 'edges')
		for j, edge in enumerate(edges):
			edgeList = vessel.getElementsByTagName('edge')
			print('      found', len(edgeList), 'edges')
			for k in range(len(edgeList)):
				edge_id = edgeList[k].attributes['id'].value
				points = edgeList[k].getElementsByTagName('point')
				# this is my 'edge' list, the tubes between branch points ???
				print('         for edge id', edge_id, 'found', len(points), 'points')
				for point in points:
					x = point.attributes['x'].value
					y = point.attributes['y'].value
					z = point.attributes['z'].value
					diam = point.attributes['d'].value
					# append to master lists
					outPointList.append([x,y,z])
					diamList.append(diam)
					outEdgeList.append(masterEdgeIdx)
				masterEdgeIdx += 1

# convert lists to 2d numpy array
outPoints = np.array(outPointList, dtype='float32')
outDiameters = np.array(diamList, dtype='float32')
outDiameters *= 5
outEdgeIndx = np.array(outEdgeList, dtype='float32')

# plot
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

#Axes3D.scatter(xs, ys, zs=0, zdir='z', s=20, c=None, depthshade=True, *args, **kwargs)¶
ax.scatter(outPoints[:,0].tolist(), outPoints[:,1].tolist(), outPoints[:,2].tolist(),
	c='k', marker='o', s=outDiameters.tolist())

fig.show()
plt.show()
