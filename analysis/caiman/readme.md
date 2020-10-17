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
