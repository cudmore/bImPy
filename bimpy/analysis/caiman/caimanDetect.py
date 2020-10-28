"""
20201016

run the entire pipeline for one source tiff file

- open file
- motion correct
- detect Ca++ transients
- prune good/bad transients
- save h5f
- !!!

Once this is done, use bReadCaiman.py to visualize the results !!!

"""

import sys, os, time

import cv2
import glob
import logging
import numpy as np

try:
    cv2.setNumThreads(0)
except():
    pass

import tifffile

import caiman as cm
from caiman.motion_correction import MotionCorrect
from caiman.source_extraction.cnmf import cnmf as cnmf
from caiman.source_extraction.cnmf import params as params
from caiman.utils.utils import download_demo

# to turn off sklearn decomposition ConvergenceWarning
from sklearn.utils.testing import ignore_warnings
from sklearn.exceptions import ConvergenceWarning

#import shutil # to copy .mmap file to a sane name
import caimanOptions # my file, set motion correction (and caimanDetect) parameters here

logFile = __file__ + '.log'
logFormat = "%(relativeCreated)12d [%(filename)s:%(funcName)20s():%(lineno)s] [%(process)d] %(message)s"
logging.basicConfig(format = logFormat,
                    filename = logFile,
                    level = logging.WARNING)

@ignore_warnings(category=ConvergenceWarning)
def caimanDetect(fnames):
	"""
	following demo_pipline jupyter notebook

	parameters:
		fnames: list of path to multiple files (should in theory work in parallel)
	"""

	print('=== caimanDetect.caimanDetect() make sure your CPU is cooled properly :)')
	print('  fnames:', fnames)

	startSeconds = time.time()

	opts = caimanOptions.createParams(fnames)

	#start a cluster for parallel processing (if a cluster already exists it will be closed and a new session will be opened)
	if 'dview' in locals():
		cm.stop_server(dview=dview)
	c, dview, n_processes = cm.cluster.setup_cluster(backend='local', n_processes=None, single_thread=False)

	# if no motion correction just memory map the file
	# trying to just use _aligned.tif
	print('  creating mmap file from original fnames:',fnames)
	fname_new = cm.save_memmap(fnames, base_name='memmap_', order='C', border_to_0=0, dview=dview)

	'''
	myMemMapFile, tmpExt = os.path.splitext(fnames[0])
	myMemMapFile += '.mmap'
	myMemMapFile = '/media/cudmore/data/20201014/inferior_2p/memmap__d1_512_d2_512_d3_1_order_C_frames_900_.mmap'
	'''
	#Yr, dims, T = cm.load_memmap(myMemMapFile)
	print('  loading mmap file we just created fname_new:', fname_new)
	Yr, dims, T = cm.load_memmap(fname_new)
	images = np.reshape(Yr.T, [T] + list(dims), order='F')

	#
	# restart the cluster to clear memory
	print('  restarting cluster to clear memory')
	if 'dview' in locals():
	    cm.stop_server(dview=dview)
	c, dview, n_processes = cm.cluster.setup_cluster(backend='local', n_processes=None, single_thread=False)

	'''
	Run CNMF on patches in parallel
	The FOV is split is different overlapping patches that are subsequently processed in parallel by the CNMF algorithm.
	The results from all the patches are merged with special attention to idendtified components on the border.
	The results are then refined by additional CNMF iterations.
	'''
	print('  Run CNMF on patches in parallel ... please wait ...')
	cnm = cnmf.CNMF(n_processes, params=opts, dview=dview)
	cnm = cnm.fit(images)

	#
	# Re-run (seeded) CNMF on the full Field of View
	# RE-RUN seeded CNMF on accepted patches to refine and perform deconvolution
	# todo: i do not understand this step???
	# components rejected on the previous step will not be recovered here.
	##
	# getting error when I run on the full image, not cropped ???
	# IndexError: index 41 is out of bounds for axis 0 with size 2
	##
	reRun = True
	if reRun:
		print('  Re-run (seeded) CNMF on the full Field of View')
		cnm2 = cnm.refit(images, dview=dview)
	else:
		print('  NOT Re-run (seeded) CNMF on the full Field of View')
		cnm2 = cnm

	'''
	The processing in patches creates several spurious components.
	These are filtered out by evaluating each component using three different criteria:
	- the shape of each component must be correlated with the data at the corresponding location within the FOV
	- a minimum peak SNR is required over the length of a transient
	- each shape passes a CNN based classifier
	'''
	print('  filter out spurious patches')
	cnm2.estimates.evaluate_components(images, cnm2.params, dview=dview)

	#
	# Extract DF/F values
	'''
	quantileMin: quantile used to estimate the baseline (values in [0,100])
	frames_window: number of frames for computing running quantile
	'''
	print('  Extract DF/F values')
	cnm2.estimates.detrend_df_f(quantileMin=8, frames_window=250)

	#
	# Select only high quality components¶
	print('  Select only high quality components¶')
	cnm2.estimates.select_components(use_object=True)

	#
	# save the results
	# fnames is like ['/home/cudmore/data/20201014/inferior/2_nif_inferior_cropped.tif']
	# h5FilePath='/home/cudmore/data/20201014/inferior/2_nif_inferior_cropped_results.hdf5'
	oneName = fnames[0]
	# save cnm2
	savePath, tmpExt = os.path.splitext(oneName)
	savePath += '_results.hdf5'
	print('  saving results in savePath:', savePath)
	cnm2.save(savePath)
	# save cnm
	'''
	savePath, tmpExt = os.path.splitext(oneName)
	savePath += '_results_0.hdf5'
	print('  saving results in savePath:', savePath)
	cnm.save(savePath)
	'''

	# remove mmap file fname_new
	if os.path.isfile(fname_new):
		print('  removing mmap file fname_new:', fname_new)
		os.remove(fname_new)

	#
	# done

	# debug my timing
	stopSeconds = time.time()
	elapsedSeconds = round(stopSeconds-startSeconds,3)
	elapsedMinutes = round(elapsedSeconds/60,3)
	#
	print(f'  caimanDetect() done in {elapsedMinutes} minutes')

if __name__ == '__main__':

	#path = '/media/cudmore/data/20201014/inferior/2_nif_inferior_cropped_aligned.tif'

	#path = '/media/cudmore/data/20201014/inferior/3_nif_inferior_cropped.tif'
	#path = '/media/cudmore/data/20201014/inferior/4_nif_inferior_cropped_aligned.tif'

	#path = '/media/cudmore/data/20201014/inferior_2p/20201014__0001_ch1_aligned.tif'

	path = '/media/cudmore/data/20201014/inferior/3_nif_inferior_cropped_aligned.tif'

	path = '/media/cudmore/data/20201014/superior_2p/tiff/preprocess/v2/v2_Median_MAX_20201014__0001_aligned_ch1.tif'

	pathList = [path]
	caimanDetect(pathList)
