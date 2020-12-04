from setuptools import setup, find_packages

exec (open('bimpy/version.py').read())

setup(
    name='bimpy',
    version=__version__,
    description='Image volume and time series analysis',
    url='http://github.com/cudmore/bImPy',
    author='Robert H Cudmore',
    author_email='robert.cudmore@gmail.com',
    license='GNU GPLv3',
    #packages = find_packages(),
    #packages = find_packages(exclude=['version']),
    #packages=[
    #    'pymapmanager',
    #    'pymapmanager.mmio'
    #],
    setup_requires=[
        "numpy>1.18",
    ],
    install_requires=[
        'napari',
        'PyQt5',
        'qtpy',
        'numpy>1.18',
        'matplotlib',
        'tifffile',
        'scikit-image',
        'h5py',
        'skan',
        'numba',
        'pandas',
        'chart_studio',
        'plotly',
        'pyqtgraph',
        'qdarkstyle',
		'opencv-python',
        #'javabridge',
        #'python-bioformats',
    ],
    entry_points={
        'console_scripts': [
            'bimpy=bimpy.interface.bStackBrowser:main',
        ]
    },

)
