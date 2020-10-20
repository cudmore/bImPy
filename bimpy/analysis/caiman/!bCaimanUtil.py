"""
20201016

taken from:
	CaImAn/caiman/utils/utils.py

"""

import numpy as np
import scipy.sparse # not sufficient to just import scipy? why?
import h5py
from typing import Any, Dict, List, Tuple, Union, Iterable

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
	pass
	
