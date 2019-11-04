# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

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

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
