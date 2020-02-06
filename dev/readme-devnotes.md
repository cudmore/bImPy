## website to convert files, in particular .mov to .gif

https://convertio.co/

## hdf5 viewer

https://www.hdfgroup.org/downloads/hdfview/#download

## Using multiprocessing to process measurements on many image slices

line intensity profile

2624 images
serial took 32 seconds
parallel (at home) with 7 processes took 15 seconds

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

Get this opengl error when having >2000 line segments (some individual segments might have ~200 vertices)

```
WARNING: Error drawing visual <Volume at 0x1a8028dd8>
WARNING: Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/OpenGL/latebind.py", line 41, in __call__
    return self._finalCall( *args, **named )
TypeError: 'NoneType' object is not callable

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/app/backends/_qt.py", line 818, in paintGL
    self._vispy_canvas.events.draw(region=None)
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/util/event.py", line 455, in __call__
    self._invoke_callback(cb, event)
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/util/event.py", line 475, in _invoke_callback
    self, cb_event=(cb, event))
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/util/event.py", line 471, in _invoke_callback
    cb(event)
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/scene/canvas.py", line 217, in on_draw
    self._draw_scene()
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/scene/canvas.py", line 266, in _draw_scene
    self.draw_visual(self.scene)
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/scene/canvas.py", line 304, in draw_visual
    node.draw()
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/scene/visuals.py", line 99, in draw
    self._visual_superclass.draw(self)
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/visuals/visual.py", line 443, in draw
    self._vshare.index_buffer)
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/visuals/shaders/program.py", line 101, in draw
    Program.draw(self, *args, **kwargs)
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/gloo/program.py", line 533, in draw
    canvas.context.flush_commands()
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/gloo/context.py", line 176, in flush_commands
    self.glir.flush(self.shared.parser)
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/gloo/glir.py", line 572, in flush
    self._shared.flush(parser)
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/gloo/glir.py", line 494, in flush
    parser.parse(self._filter(self.clear(), parser))
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/gloo/glir.py", line 819, in parse
    self._parse(command)
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/gloo/glir.py", line 789, in _parse
    ob.set_size(*args)  # Texture[1D, 2D, 3D], RenderBuffer
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/gloo/glir.py", line 1624, in set_size
    gl.GL_BYTE, shape[:3])
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/vispy/gloo/glir.py", line 1573, in glTexImage3D
    width, height, depth, border, format, type, None)
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/OpenGL/latebind.py", line 45, in __call__
    return self._finalCall( *args, **named )
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/OpenGL/wrapper.py", line 875, in wrapperCall
    raise err
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/OpenGL/wrapper.py", line 868, in wrapperCall
    result = wrappedOperation( *cArguments )
  File "/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/OpenGL/error.py", line 232, in glCheckError
    baseOperation = baseOperation,
OpenGL.error.GLError: GLError(
	err = 1281,
	description = b'invalid value',
	baseOperation = glTexImage3D,
	pyArgs = (
		GL_TEXTURE_3D,
		0,
		GL_LUMINANCE,
		1981,
		5783,
		134,
		0,
		GL_LUMINANCE,
		GL_BYTE,
		None,
	),
	cArgs = (
		GL_TEXTURE_3D,
		0,
		GL_LUMINANCE,
		1981,
		5783,
		134,
		0,
		GL_LUMINANCE,
		GL_BYTE,
		None,
	),
	cArguments = (
		GL_TEXTURE_3D,
		0,
		GL_LUMINANCE,
		1981,
		5783,
		134,
		0,
		GL_LUMINANCE,
		GL_BYTE,
		None,
	)
)
Abort trap: 6
```