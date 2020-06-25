import numpy as np
from scipy.stats import norm # used by my_suggest_normalization_param

def my_suggest_normalization_param(structure_img0, verbose=False):
	"""
	clone of aics segmentation code. Just added return values.
	Used as intensity_scaling_param parameter for intensity_normalization()
	"""
	m, s = norm.fit(structure_img0.flat)
	if verbose:
		print(f'    mean intensity of the stack: {m}')
		print(f'    the standard deviation of intensity of the stack: {s}')

	p99 = np.percentile(structure_img0, 99.99)
	if verbose:
		print(f'    0.9999 percentile of the stack intensity is: {p99}')

	pmin = structure_img0.min()
	if verbose:
		print(f'    minimum intensity of the stack: {pmin}')

	pmax = structure_img0.max()
	if verbose:
		print(f'    maximum intensity of the stack: {pmax}')

	up_ratio = 0
	for up_i in np.arange(0.5, 1000, 0.5):
		if m+s * up_i > p99:
			if m+s * up_i > pmax:
				if verbose:
					print(f'    suggested upper range is {up_i-0.5}, which is {m+s*(up_i-0.5)}')
				up_ratio = up_i-0.5
			else:
				if verbose:
					print(f'    suggested upper range is {up_i}, which is {m+s*up_i}')
				up_ratio = up_i
			break

	low_ratio = 0
	for low_i in np.arange(0.5, 1000, 0.5):
		if m-s*low_i < pmin:
			if verbose:
				print(f'    suggested lower range is {low_i-0.5}, which is {m-s*(low_i-0.5)}')
			low_ratio = low_i-0.5
			break

	if verbose: print(f'    So ... suggested parameter for intensity_scaling_param normalization is [{low_ratio}, {up_ratio}]')
	if verbose:
		print('    To further enhance the contrast: You may increase the first value (may loss some dim parts), or decrease the second value' +
			  '    (may loss some texture in super bright regions)')
		print('    To slightly reduce the contrast: You may decrease the first value, or increase the second value')
	
	return low_ratio, up_ratio
	
