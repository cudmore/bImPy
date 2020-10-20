"""
(load_dict_from_hdf5, recursively_load_dict_contents_from_group)
taken from:
	CaImAn/caiman/utils/utils.py
"""
from collections import OrderedDict

import numpy as np
import scipy
import scipy.sparse # not sufficient to just import scipy? why?
import h5py
from typing import Any, Dict, List, Tuple, Union, Iterable

def readCaiman(path, verbose=False):
	'''
	with h5py.File(path, "r") as f:
		estimates = f['estimates']
		print(estimates)
	'''

	print('readCaiman() path:', path)

	estimatesArrayDict = OrderedDict()

	for key, val in load_dict_from_hdf5(path).items():
		#print('key:', key, 'type(val)', type(val))

		if key == 'dims':
			originalShape = val

		#if key == 'estimates':
		if isinstance(val, dict):
			if verbose:
				print('key:', key, 'type(val)', type(val))
			# print the dict
			if verbose:
				for k2, v2 in val.items():
					if v2 is None:
						print('  ', k2, ':', v2)
					else:
						print('  ', k2, ':', type(v2))

			if key == 'estimates':
				for k2, v2 in val.items():
					if isinstance(v2, np.ndarray) or isinstance(v2, scipy.sparse.csc.csc_matrix):
						estimatesArrayDict[k2] = v2

			# not that informative
			'''
			if key == 'params':
				# trying to figure out what is in here
				data = val['data']
				print('    params data:', data)
			'''

		else:
			# print the value (of a non dict)
			if verbose:
				print('key:', key, '=', val)

	numROI = estimatesArrayDict['A'].shape[1]

	# add original image shape
	estimatesArrayDict['originalShape'] = originalShape
	estimatesArrayDict['numROI'] = numROI

	print('  originalShape:', originalShape)
	print('  numROI:', numROI)

	return estimatesArrayDict

def load_dict_from_hdf5(filename:str) -> Dict:
    ''' Load dictionary from hdf5 file
    Args:
        filename: str
            input file to load
    Returns:
        dictionary
    '''

    with h5py.File(filename, 'r') as h5file:
        return recursively_load_dict_contents_from_group(h5file, '/')

def recursively_load_dict_contents_from_group(h5file:h5py.File, path:str) -> Dict:
    '''load dictionary from hdf5 object
    Args:
        h5file: hdf5 object
            object where dictionary is stored
        path: str
            path within the hdf5 file
    '''

    ans:Dict = {}
    for key, item in h5file[path].items():

        if isinstance(item, h5py._hl.dataset.Dataset):
            val_set = np.nan
            if isinstance(item[()], str):
                if item[()] == 'NoneType':
                    ans[key] = None
                else:
                    ans[key] = item[()]

            elif key in ['dims', 'medw', 'sigma_smooth_snmf', 'dxy', 'max_shifts', 'strides', 'overlaps']:

                if type(item[()]) == np.ndarray:
                    ans[key] = tuple(item[()])
                else:
                    ans[key] = item[()]
            else:
                if type(item[()]) == np.bool_:
                    ans[key] = bool(item[()])
                else:
                    ans[key] = item[()]

        elif isinstance(item, h5py._hl.group.Group):
            if key in ('A', 'W', 'Ab', 'downscale_matrix', 'upscale_matrix'):
                data =  item[path + key + '/data']
                indices = item[path + key + '/indices']
                indptr = item[path + key + '/indptr']
                shape = item[path + key + '/shape']
                ans[key] = scipy.sparse.csc_matrix((data[:], indices[:],
                    indptr[:]), shape[:])
                if key in ('W', 'upscale_matrix'):
                    ans[key] = ans[key].tocsr()
            else:
                ans[key] = recursively_load_dict_contents_from_group(h5file, path + key + '/')
    return ans

if __name__ == '__main__':
	# _v0 is before I ran demo_pipeline notebook again with different detection prams
	path = '/media/cudmore/data/20201014/inferior/2_nif_inferior_cropped_results_v0.hdf5'

	path = '/media/cudmore/data/20201014/inferior/2_nif_inferior_cropped_results.hdf5'
	# this _v0 had no reject bad (accept good), had 109 components
	path = '/media/cudmore/data/20201014/inferior/3_nif_inferior_cropped_results_v0.hdf5'
	path = '/media/cudmore/data/20201014/inferior/3_nif_inferior_cropped_results.hdf5' # cnm2
	#path = '/media/cudmore/data/20201014/inferior/3_nif_inferior_cropped_results_0.hdf5' # cnm

	caimanDict = readCaiman(path, verbose=True)
