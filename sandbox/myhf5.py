# 20191120, trying to figure out how to save/load h5py
# will use this to save napari shapes and associated anaysis in line profile plugin

import numpy as np
import h5py
import json

# some data
table1 = np.array([(1,4), (2,5), (3,6)], dtype=[('x', float), ('y', float)])
table2 = np.ones(shape=(3,3))

# save to data to file
print('\ncreate')
with h5py.File("test.h5", "w") as f:
	'''
	f.create_dataset("Table1", data=table1)

	f.create_dataset("Table2", data=table2, compression=True)
	# add attributes
	f["Table2"].attrs["attribute1"] = "some info"

	myDict = {'a':10, 'b':20}
	myDict_json = json.dumps(myDict)
	f["Table2"].attrs["attribute2"] = myDict_json
	#h5file.close()
	'''

	myShapeDict = {
		'shape_types': 'line',
		'edge_colors':'r',
		'face_colors': 'g',
		'edge_widths': 3,
		'opacities': 1,
		'z_indices': 99,
	}
	myDict_json = json.dumps(myShapeDict)

	# each shape will have a group
	grp = f.create_group("shape1")
	# each shape group will have a shape dict with all parameters to draw ()
	grp.attrs['shapeDict'] = myDict_json
	# each shape group will have 'data' with coordinates of polygon
	grp.create_dataset("data", (50,40,30,20,10), dtype='f')
	#
	# each group will have analysis
	# line shape diameter analysis
	grp.create_dataset("lineProfileDiameter", (1,3,5,7,9), dtype='f')

	exampleImage = np.ones(shape=(60,133))
	grp.create_dataset("lineProfileImage", data=exampleImage, dtype='f')

	#f["shape1/data"].attrs["attribute1"] = "some info"

# load
print('\nload')
with h5py.File("test.h5", "r") as f:
	#print('f.name:', f.name)
	# iterate through groups, each group is a shape
	for name in f:
		print('name:', name)

		print(f[name + '/data']) #numpy array of polygon vertices

		# attribues of the shape
		'''
		for key, value in f[name].attrs.items():
			# value is ALWAYS <class 'str'>
			print('type(key):', type(key), 'type(value):', type(value))
			print('key:', key, 'value:', value)
		'''

		# convert f[name].attrs to dict
		json_str = f[name].attrs['shapeDict']
		json_dict = json.loads(json_str)
		print(json_dict)
		print(type(json_dict))

		# my analysis done in plugin
		print(f[name + '/lineProfileDiameter'])
		print(f[name + '/lineProfileImage'])
		#print(f[name + '/data'].attrs['attribute1'])
		#print(f[name].attrs.keys())

		# convert to numpy ndarray
		print(type(f[name + '/lineProfileDiameter']))
		# .value is depreciated, use [()] instead. This is completely fucked up syntax!!!
		#myarray = f[name + '/lineProfileDiameter'].value
		#print(type(myarray))
		myarray = f[name + '/lineProfileDiameter'][()]
		print(type(myarray))

	'''
	# read from file (numpy-like behavior)
	#print(f["Table1"]["x"])
	#print(f["Table1"]["y"])
	print(f["Table1"][:])
	# read everything into memory (real numpy array)
	print(np.array(f["Table2"]))
	# read attributes
	print(f["Table2"].attrs["attribute1"])

	json_str = f["Table2"].attrs["attribute2"]
	json_dict = json.loads(json_str)
	print(json_dict)
	print(type(json_dict))
	print(type(f["Table2"].attrs["attribute2"]))
	'''
