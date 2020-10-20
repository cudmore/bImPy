def old_createParams(fnames):
	# dataset dependent parameters
	#fr = 30                             # imaging rate in frames per second
	fr = 20                             # imaging rate in frames per second
	decay_time = 1.2 #0.4                    # length of a typical transient in seconds

	myScaleFactor=5 # first run was 7

	# motion correction parameters
	strides = (48*myScaleFactor, 48*myScaleFactor) #(48, 48)          # start a new patch for pw-rigid motion correction every x pixels
	overlaps = (50, 50) #(24, 24)         # overlap between pathes (size of patch strides+overlaps)
	max_shifts = (6*myScaleFactor, 6*myScaleFactor) #(6,6)          # maximum allowed rigid shifts (in pixels)
	max_deviation_rigid = 3*myScaleFactor #3     # maximum shifts deviation allowed for patch with respect to rigid shifts
	pw_rigid = True             # flag for performing non-rigid motion correction

	# parameters for source extraction and deconvolution
	p = 1                       # order of the autoregressive system
	gnb = 2                     # number of global background components
	merge_thr = 0.85            # merging threshold, max correlation allowed
	rf = 15 * myScaleFactor #15                     # half-size of the patches in pixels. e.g., if rf=25, patches are 50x50
	stride_cnmf = 6*myScaleFactor #6             # amount of overlap between the patches in pixels
	K = 4                       # number of components per patch
	gSig = [4*myScaleFactor, 4*myScaleFactor] #[4, 4]               # expected half size of neurons in pixels
	method_init = 'greedy_roi'  # initialization method (if analyzing dendritic data using 'sparse_nmf')
	ssub = 1                    # spatial subsampling during initialization
	tsub = 1                    # temporal subsampling during intialization

	# parameters for component evaluation
	min_SNR = 1.15 #2.0               # signal to noise ratio for accepting a component
	rval_thr = 0.85              # space correlation threshold for accepting a component
	cnn_thr = 0.99              # threshold for CNN based classifier
	cnn_lowest = 0.1 # neurons with cnn probability lower than this value are rejected

	##
	##
	opts_dict = {'fnames': fnames,
	            'fr': fr,
	            'decay_time': decay_time,
	            'strides': strides,
	            'overlaps': overlaps,
	            'max_shifts': max_shifts,
	            'max_deviation_rigid': max_deviation_rigid,
	            'pw_rigid': pw_rigid,
	            'p': p,
	            'nb': gnb,
	            'rf': rf,
	            'K': K,
	            'stride': stride_cnmf,
	            'method_init': method_init,
	            'rolling_sum': True,
	            'only_init': True,
	            'ssub': ssub,
	            'tsub': tsub,
	            'merge_thr': merge_thr,
	            'min_SNR': min_SNR,
	            'rval_thr': rval_thr,
	            'use_cnn': True,
	            'min_cnn_thr': cnn_thr,
	            'cnn_lowest': cnn_lowest}

	opts = params.CNMFParams(params_dict=opts_dict)

	return opts
