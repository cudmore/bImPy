## Workflow

Starting with raw.tif

1) run alignment with caimanAlign.py, this outputs raw_aligned.tif
2) run detection on raw_aligned.tif with caimanDetect.py, this output raw_aligned.h5f
3) open results in bimpy and set traces isBad=True that are either
   not near an obvious cell membrane
   very noisy (still need interface for viewing traces)
4) view results in caimanResults.ipynb

20201016


## For Linux (and OSX) run these commands before launching Python:

```
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
```

See here to make these permanent, when conda environment is activated

https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#saving-environment-variables

## To run notebooks

```
jupyter notebook --NotebookApp.iopub_data_rate_limit=1.0e10
```

## caimanmanager

This creates a folder

```
python caimanmanager.py install --inplace
```

The folder is

```
/home/cudmore/caiman_data
```

## errors

on refit() was giving errors

see: https://github.com/flatironinstitute/CaImAn/issues/808
see: https://github.com/flatironinstitute/CaImAn/issues/754

I edited the following to fix it
file is '/home/cudmore/Sites/CaImAn/caiman/source_extraction/cnmf/spatial.py'
original line was 269
add in this 'if'

```
# abb was this
#f = np.delete(f, background_ff, 0)
if f.size>0:
	f = np.delete(f, background_ff, 0)
```

```
Traceback (most recent call last):
  File "bPipeline.py", line 241, in <module>
    runPipeline(pathList)
  File "bPipeline.py", line 114, in runPipeline
    cnm2 = cnm.refit(images, dview=dview)
  File "/home/cudmore/Sites/CaImAn/caiman/source_extraction/cnmf/cnmf.py", line 417, in refit
    return cnm.fit(images)
  File "/home/cudmore/Sites/CaImAn/caiman/source_extraction/cnmf/cnmf.py", line 543, in fit
    self.update_spatial(Yr, use_init=True)
  File "/home/cudmore/Sites/CaImAn/caiman/source_extraction/cnmf/cnmf.py", line 936, in update_spatial
    sn=self.estimates.sn, dims=self.dims, **self.params.get_group('spatial'))
  File "/home/cudmore/Sites/CaImAn/caiman/source_extraction/cnmf/spatial.py", line 269, in update_spatial_components
    f = np.delete(f, background_ff, 0)
  File "<__array_function__ internals>", line 6, in delete
  File "/home/cudmore/anaconda3/envs/caiman/lib/python3.7/site-packages/numpy/lib/function_base.py", line 4406, in delete
    keep[obj,] = False
```

That didn't work, now using the following
file is '/home/cudmore/Sites/CaImAn/caiman/source_extraction/cnmf/spatial.py'

```
if background_ff[0] < f.shape[0]:
	f = np.delete(f, background_ff, 0)
else:
	print('=== abb spatial skipped', 'f:', f.size, f.shape, background_ff)
```
