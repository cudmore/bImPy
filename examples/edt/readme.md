# Install

## Install aics and bImPy togethere

## Install aics and bImPy togethere

Need to use conda

```
conda create -n segmentation2 python=3.6
conda activate segmentation

conda install nb_conda

# see: https://github.com/AllenInstitute/aics-segmentation/blob/master/docs/installation_mac.md
git clone https://github.com/AllenInstitute/aics-segmentation.git

pip install numpy
pip install itkwidgets==0.14.0
pip install -e segmentation.git/.[all]

# install bimpy
pip install -e /Users/Sites/bImPy/.

# downgrade tifffile (for aics)
pip install tifffile==0.15.1
```

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

This is called at the end of vascDen.py myRun(). Note, saved convex hull will not have a header with x/y/z voxel size. This is ok.

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

'uFilename' must be the raw data filename without _ch1.tif or _ch2.tif

For example, for original file '20200518__A01_G001_0016_ch1', 'uFilename' is '20200518__A01_G001_0016'


### One File

Run vascDen and/or cellDen on one raw file.

 - Make sure calling cellDen.py on HCN4 channel 1
 - Make sure calling vascDen.py on vascular channel 2

```
python cellDen.py /Users/cudmore/box/data/nathan/20200518/20200518__A01_G001_0016_ch1.tif 
python vascDen.py /Users/cudmore/box/data/nathan/20200518/20200518__A01_G001_0016_ch2.tif 
```

#### [OR] Entire folder

Run vascDen and/or cellDen on an entire raw folder

```
# python denAnalysisFolder.p <channel>, <type>, <percent overlap> <folder>
python denAnalysisFolder.py 1 cellDen 15 /Users/cudmore/box/data/nathan/20200518
python denAnalysisFolder.py 2 vascDen 15 /Users/cudmore/box/data/nathan/20200518
```

### Generate cross channel edt

Here, need to specify stack in analysis folder analysis2/

This is beacuse edt is calculated from output of main cellDen.py and vascDen.py which is in analysis2/ folder.

```
# see below
#python crossChannelEDT.py /Users/cudmore/box/data/nathan/20200518/analysis2/20200518__A01_G001_0002_ch1_raw.tif
```

**UPDATE, WRITE A script**

```
from crossChannelEDT import crossChannelEDTFolder

path = '/Users/cudmore/box/data/nathan/20200518/analysis_full'
crossChannelEDTFolder(path)
```

# Notes

See this Python package for deconvolution

https://github.com/tlambert03/pycudadecon

See https://osf.io/dashboard for file sharing

```
test-osf.py
```

