## pyserial

Sometimes 'pip install pyserial' is not enough? Need to use

```
python3 -m pip install pyserial
```

## Using Sphinx to generate API documentation

```
cd pimpy/docs
sphinx-apidoc -o . ..
make html

# remember to sometimes remake everything with -f options
sphinx-apidoc -f -o . ..
```

Added this to conf.py

```
# abb
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

on_rtd = os.environ.get('READTHEDOCS') == 'True'

# -- Project information -----------------------------------------------------

project = 'bImPy'
copyright = '2019, Robert H Cudmore'
author = 'Robert H Cudmore'

# The full version, including alpha/beta/rc tags
release = '0.1'


# requires `pip install mock` on the system i am running `make html`
#from mock import MagicMock
from mock import Mock as MagicMock

class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
            return MagicMock()

#matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

MOCK_MODULES = ['pygtk', 'gtk', 'gobject', 'argparse', 'numpy', 'sip',
    'cv2', 'PySpin', 'skimage', 'javabridge', 'bioformats', 'serial', 'matplotlib.backends.backend_qt5agg',
	'PyQt4', 'PyQt4.QtGui', 'PyQt4.QtCore', 'tifffile',
    'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends', 'matplotlib.backends.backend_qt4agg', 'matplotlib.figure',
    'pandas', 'pandas.tools', 'pandas.tools.plotting',
    'scipy', 'scipy.misc',
    'lapack', 'blas']
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

# remove duplicate modile name in every constructor
# e.g. mmMap.mmMap()
add_module_names = False

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
# abb sphinx.ext.napoleon
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx.ext.napoleon'
]
```
