from setuptools import setup, find_packages

setup(
    name='Canvas',
    version='0.1.0',
	description='',
	long_description='',
	author='Robert Cudmore',
	author_email='robert.cudmore@gmail.com',
	url='https://github.com/cudmore/bImPy',
    keywords=['in vivo', 'two photon', 'laser scanning microscopy'],
	packages=find_packages(),
    entry_points={
        'console_scripts': [
            'canvas=canvas.bCanvasApp:main',
        ]
    },
    install_requires=[
		'opencv-python-headless',
		'pyserial'
    ],
    extras_require={
        'bioformata': ['python-bioformats', 'javabridge'],
    }
)

'''
numpy
PyQt5
QtPy
napari
matplotlib
tifffile
scikit-image
h5py
skan # skeleton tracing (requires numba and pandas)
numba
pandas
PyQtGraph
qdarkstyle
'''
