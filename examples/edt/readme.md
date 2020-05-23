# Install

### Make a directory to work in

```
mkdir myAnalysis
cd myAnalysis
```

Clone and install bImPy

```
git clone https://github.com/cudmore/bImPy.git
cd bImPy
pip install -e .
cd ..
```

### Make a virtual environment to run myConvex hull

This is called at the end of vascDen.py myRun(). Note, saved convex hull does not have proper x/y/z voxel size.

```
python3 -m venv my_hull_env/
source my_hull_env/bin/activate
pip install numpy==1.17.4
pip install scipy==1.1.0
pip install matplotlib scikit-image
```

# Workflow

Activate bImPy_env

```
source bImPy_env/bin/activate
```

Change into edt folder

```
cd examples/edt
```

### Edit examples/edt/master_cell_db.csv to specify (uFilename, uFirstSlice, uLastSLice)

