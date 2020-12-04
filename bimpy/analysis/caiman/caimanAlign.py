"""
use caiman to align a .tif file of frames (not slices)

this requires options (like frame rate) to be set via
	caimanOptions.createParams(fnames)

output:
	2x mmap files
	_aligned.tif: the results after the alignment

"""

import sys, os, time

'''
import cv2
import glob
import logging
'''
import numpy as np

'''
try:
    cv2.setNumThreads(0)
except():
    pass
'''

import tifffile

import caiman as cm
from caiman.motion_correction import MotionCorrect
#from caiman.source_extraction.cnmf import cnmf as cnmf
#from caiman.source_extraction.cnmf import params as params
#from caiman.utils.utils import download_demo

import caimanOptions # my file, set motion correction (and caimanDetect) parameters here

def caimanAlign(fnames, frameRate=20):
	"""
	fnames: list of file path
	"""

	startSeconds = time.time()

	opts = caimanOptions.createParams(fnames, frameRate=frameRate)

	#start a cluster for parallel processing (if a cluster already exists it will be closed and a new session will be opened)
	if 'dview' in locals():
		cm.stop_server(dview=dview)
	c, dview, n_processes = cm.cluster.setup_cluster(backend='local', n_processes=None, single_thread=False)

	#
	# create a motion correction object with the parameters specified.
	#Note that the file is not loaded in memory
	mc = MotionCorrect(fnames, dview=dview, **opts.get_group('motion'))

	# set mmap_file
	'''
	tmpPath, tmpExt = os.path.splitext(fnames[0])
	tmpPath += '.mmap'
	print('setting mc.mmap_file to tmpPath:', tmpPath)
	mc.mmap_file = tmpPath
	'''
	#print('mc.mmap_file:', mc.mmap_file)
	#
	# perform motion correction
	# We will perform piecewise rigid motion correction using the NoRMCorre algorithm.
	# This has already been selected by setting pw_rigid=True when defining the parameters object.
	print('  performing motion correction ... please wait ...', fnames[0])
	mc.motion_correct(save_movie=True)
	m_els = cm.load(mc.fname_tot_els)
	border_to_0 = 0 if mc.border_nan is 'copy' else mc.border_to_0
	print('  border_to_0:', border_to_0)
	# maximum shift to be used for trimming against NaNs

	#
	# memory mapping
	print('  memory mapping')
	print('    save_memmap mc.mmap_file:', mc.mmap_file)
	fname_new = cm.save_memmap(mc.mmap_file, base_name='memmap_', order='C',
	                           border_to_0=border_to_0, dview=dview) # exclude borders
	print('    mc.mmap_file:', mc.mmap_file)
	print('    fname_new:', fname_new)

	# make a copy of mmap file with a sane name
	# does not work, seems you can not 'copy' a mmap file like a normal file
	'''
	tmpSavePath, tmpExt = os.path.splitext(fnames[0])
	tmpSavePath += '.mmap' # need to be _aligned_ch1.tif
	shutil.copyfile(fname_new, tmpSavePath)
	'''

	# save a _mmap.txt file with the name of the memory map file
	'''
	tmpFile, tmpFilename = os.path.splitext(fnames[0])
	tmpFile += '_mmap.txt'
	with open(tmpFile, 'w') as myTmpFile:
		myTmpFile.write(fname_new)
	'''

	# now load the file
	Yr, dims, T = cm.load_memmap(fname_new)
	images = np.reshape(Yr.T, [T] + list(dims), order='F')
    #load frames in python format (T x X x Y)

	# save as .tif
	images_8bit = ((images - images.min()) / (images.ptp() / 255.0)).astype(np.uint8) # map the data range to 0 - 255
	tmpSavePath, tmpExt = os.path.splitext(fnames[0])
	tmpSavePath += '_aligned.tif' # need to be _aligned_ch1.tif
	print('    saving aligned .tif', images_8bit.shape, images_8bit.dtype, 'tmpSavePath:', tmpSavePath)
	tifffile.imsave(tmpSavePath, images_8bit, bigtiff=True)

	# shut down the cluster
	if 'dview' in locals():
	    cm.stop_server(dview=dview)

	# remove mmap file fname_new
	if os.path.isfile(fname_new):
		print('  removing mmap file:', fname_new)
		os.remove(fname_new)
	oneFile = mc.mmap_file[0]
	if os.path.isfile(oneFile):
		print('  removing mmap file mc.mmap_file[0]:', oneFile)
		os.remove(oneFile)

	# done
	stopSeconds = time.time()
	elapsedSeconds = round(stopSeconds-startSeconds,3)
	elapsedMinutes = round(elapsedSeconds/60,3)
	print(f'  caimanAlign() done in {elapsedMinutes} minutes')

if __name__ == '__main__':

	#path = '/media/cudmore/data/20201014/inferior/2_nif_inferior_cropped.tif'
	path = '/media/cudmore/data/20201014/inferior/3_nif_inferior_cropped.tif'
	#path = '/media/cudmore/data/20201014/inferior/4_nif_inferior_cropped.tif'

	#path = '/media/cudmore/data/20201014/inferior_2p/20201014__0001_ch1.tif'

	# I need to crop first !!!!!!!!!
	path = '/media/cudmore/data/20201014/superior/2_nif_superior_cropped.tif'
	path = '/media/cudmore/data/20201014/superior_2p/tiff/preprocess/MAX_20201014__0001_ch1.tif'

	path = '/media/cudmore/data/20201111/tif1d.tif'

	path = '/media/cudmore/data/20201124/9.tif'
	frameRate = 18

	#pathList = [path]
	#caimanAlign(pathList, frameRate=frameRate)

	# process all video files from one day. Each file takes 25 min * 15 = 375 min
	# this is 6 1/4 hours, maybe 8 because some files are bigger
	frameRate = 18
	masterPathList = [
		#'/media/cudmore/data/20201124/1.tif',
		#'/media/cudmore/data/20201124/2.tif',
		#'/media/cudmore/data/20201124/3.tif',
		#'/media/cudmore/data/20201124/4.tif',
		#'/media/cudmore/data/20201124/5.tif',
		#'/media/cudmore/data/20201124/6.tif',
		#'/media/cudmore/data/20201124/7.tif',
		#'/media/cudmore/data/20201124/8.tif',
		#'/media/cudmore/data/20201124/9.tif',
		#'/media/cudmore/data/20201124/10.tif',
		'/media/cudmore/data/20201124/11.tif',
		'/media/cudmore/data/20201124/12.tif',
		'/media/cudmore/data/20201124/13.tif',
		'/media/cudmore/data/20201124/14.tif',
		'/media/cudmore/data/20201124/15.tif',
	]
	for path in masterPathList:
		if os.path.isfile(path):
			pass
			onePathList = [path]
			print('\n\n=== caimanAlign starting on path:', path)
			caimanAlign(onePathList, frameRate=frameRate)
		else:
			print('error: did not find path:', path)
