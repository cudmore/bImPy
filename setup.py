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
    packages = find_packages(),
    #packages = find_packages(exclude=['version']),
    #packages=[
    #    'pymapmanager',
    #    'pymapmanager.mmio'
    #],
    install_requires=[
        'napari',
        'numpy',
        'matplotlib',
        'tifffile',
        #'PyQt5',
        #'PyQtChart',
        'pyside2',
        'qtpy',
        'scikit-image',
        'javabridge',
        'python-bioformats',
    ]
)
