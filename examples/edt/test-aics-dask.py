"""

1) sometimes I get this exception

  File "/Users/cudmore/Sites/bImPy/examples/edt/aics-segmentation/aicssegmentation/core/pre_processing_utils.py", line 67, in edge_preserving_smoothing_3d
    itk_img = itk.GetImageFromArray(struct_img.astype(np.float32))
AttributeError: module 'itk' has no attribute 'GetImageFromArray'


2) in general, aicssegmentation.core.vessel.filament_3d_wrapper
	(i) does not run on multiple cores
	(ii) never returns or takes a SUPER long time

	when i ctrl+c out of stalled code, I see

	```
	KeyboardInterrupt
	^CError in atexit._run_exitfuncs:
	Traceback (most recent call last):
	  File "/Users/cudmore/Sites/bImPy/bImPy_env/lib/python3.7/site-packages/matplotlib/_pylab_helpers.py", line 77, in destroy_all
		gc.collect(1)
	KeyboardInterrupt
	^C
	```
	
"""

import time
import numpy as np
import scipy

import dask
import dask.array as da

from aicssegmentation.core.vessel import filament_3d_wrapper

@dask.delayed
def myRun(path, commonShape, common_dtype):

	# create fake data
	stackData = np.random.normal(loc=100, scale=10, size=commonShape)
	#stackData = stackData.astype(common_dtype)
	
	# takes about 9 seconds if we have 1x in dask array and still 9 seconds if we have 4x in dask array
	medianKernelSize = (3,4,4)
	print('  median filter', path)
	startTime = time.time()
	#
	smoothData = scipy.ndimage.median_filter(stackData, size=medianKernelSize)
	#
	stopTime = time.time()
	print('    median filter done in', round(stopTime-startTime,2), 'seconds', path)
	
	# takes about 19 seconds if we have 1x in dask array but 500+ seconds if we have 4x in dask array
	print('  filament_3d_wrapper', path)
	startTime = time.time()
	#
	f3_param=[[1, 0.01]]
	filamentData = filament_3d_wrapper(smoothData, f3_param)
	filamentData = filamentData.astype(np.uint8)
	#
	stopTime = time.time()
	print('    filament_3d_wrapper done in', round(stopTime-startTime,2), 'seconds', path)
	
if __name__ == '__main__':

	# if I feed dask 1x stacks
	# filament_3d_wrapper returns in about 19 seconds (per stack)
	filenames = ['1']

	# if I feed dask 4x stacks
	# filament_3d_wrapper will run all 4 in parallel but CPU usage does not increase by 4x, looks like I am running just 1x
	# filament_3d_wrapper returns in about 550-650 seconds (per stack)
	filenames = ['1', '2', '3', '4']
	
	# da.from_delayed() needs to know the shape and dtype it will work with?
	commonShape = (64, 512, 512)
	common_dtype = np.float #np.uint8

	# wrap myRun() function as a dask.delayed()
	#myRun_Dask = dask.delayed(myRun)
	
	#lazy_arrays = [dask.delayed(myRun_Dask)(filename, commonShape, common_dtype) for filename in filenames]
	lazy_arrays = [myRun(filename, commonShape, common_dtype) for filename in filenames]

	#lazy_arrays = [da.from_delayed(x, shape=commonShape, dtype=common_dtype) for x in lazy_arrays]
	lazy_arrays = [da.from_delayed(x, shape=commonShape, dtype=common_dtype) for x in lazy_arrays]

	x = da.block(lazy_arrays)
	
	x.compute()
