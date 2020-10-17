"""
20201016

read in a caiman h5f file

see:
	https://github.com/flatironinstitute/CaImAn/wiki/Interpreting-Results

estimates.F_dff: Set of DF/F normalized temporal components.
					Saved as a numpy array with dimensions (# of components X # of timesteps).
					Each row corresponds to the DF/F fluorescence for the corresponding component.

"""

import numpy as np
import h5py
import matplotlib.pyplot as plt

from bUtil import load_dict_from_hdf5

def readCaiman(path):
	'''
	with h5py.File(path, "r") as f:
		estimates = f['estimates']
		print(estimates)
	'''

	print('readCaiman() path:', path)

	for key, val in load_dict_from_hdf5(path).items():
		#print('key:', key, 'type(val)', type(val))

		#if key == 'estimates':
		if isinstance(val, dict):
			print('key:', key, 'type(val)', type(val))
			# print the dict
			for k2, v2 in val.items():
				print('  ', k2)

			if key == 'estimates':
				#
				idx_components = val['idx_components']
				idx_components_bad = val['idx_components_bad']

				estimates_A = val['A']
				#estimates_S = val['S'] # this works, not sure what it is
				#estimates_V = val['V'] # this does not work
				F_dff = val['F_dff'] # this works

			# not that informative
			'''
			if key == 'params':
				# trying to figure out what is in here
				data = val['data']
				print('    params data:', data)
			'''

		else:
			# print the value (of a non dict)
			print('key:', key, '=', val)

	# these do not work
	# it seems the components in the h5py file are only the ACCEPTED components (fine)
	print('accepted components are in idx_components:', idx_components)
	print('rejected components are in idx_components_bad:', idx_components_bad)

	numROI = estimates_A.shape[1]
	print('numROI:', numROI)

	#
	# view the i-th component
	if 1:
		# this works
		dims = (1200, 456) # original image size
		tmpImage = np.zeros(dims, dtype=np.float64)
		for roiIdx in range(numROI):
			# each component is shape of original image (dims)
			oneComponent = np.reshape(estimates_A[:,roiIdx].toarray(), dims, order='F')
			tmpImage += oneComponent
		#
		plt.figure()
		plt.imshow(tmpImage)
		plt.show()

	# plot the final f/f_0 (?)  for the i-th component
	if 1:
		# this works
		# todo: make this plot with each component at an offset

		# plotting a subset
		# 33 is really large event
		plotTheseComponents = [0, 1, 2, 3, 12, 18 ,19, 21, 31, 32, 33, 35, 36, 37, 41, 43]

		plt.figure()
		#for roiIdx in range(numROI):
		numPlotted = 0
		for roiIdx in plotTheseComponents:
			finalPlot = F_dff[roiIdx]
			#print(finalPlot.shape) # (1000,)
			finalPlot += numPlotted * 0.5 # plot each trace at an offset (max y for dataset is 0.5)
			plt.plot(finalPlot)

			# increment
			numPlotted += 1
		plt.show()

	# plot estimates_S, not sure what this is?
	if 0:
		plt.figure()
		for roiIdx in range(numROI):
			finalPlot = estimates_S[roiIdx]
			#print(finalPlot.shape) # (1000,)
			finalPlot += roiIdx * 0.5 # plot each trace at an offset (max y for dataset is 0.5)
			plt.plot(finalPlot)
		plt.show()


if __name__ == '__main__':
	# _v0 is before I ran demo_pipeline notebook again with different detection prams
	path = '/home/cudmore/data/20201014/inferior/2_nif_inferior_cropped_results_v0.hdf5'

	path = '/home/cudmore/data/20201014/inferior/2_nif_inferior_cropped_results.hdf5'

	readCaiman(path)
