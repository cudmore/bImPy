# Author: 
# Date: 20190707

# see
# https://stackoverflow.com/questions/14464449/using-numpy-to-efficiently-convert-16-bit-image-data-to-8-bit-for-display-with

import tifffile
import numpy as np
import timeit
import time

path = '/Users/cudmore/Dropbox/data/20190429/20190429_tst2/20190429_tst2_video/v20190429_tst2_1.tif'

startTime = time.time()
image = tifffile.TiffFile(path).asarray()
stopTime = time.time()
print('load took', stopTime - startTime)

rows,cols = image.shape
print(rows,cols)

#rows, cols = 768, 1024
#image = np.random.randint(100, 14000,
#                             size=(1, rows, cols)).astype(np.uint16)
display_min = 1000
display_max = 10000

def display(image, display_min, display_max): # copied from Bi Rico
    # Here I set copy=True in order to ensure the original image is not
    # modified. If you don't mind modifying the original image, you can
    # set copy=False or skip this step.
    image = np.array(image, copy=True)
    image.clip(display_min, display_max, out=image)
    image -= display_min
    np.floor_divide(image, (display_max - display_min + 1) / 256,
                    out=image, casting='unsafe')
    return image.astype(np.uint8)

def lut_display(image, display_min, display_max) :
    #lut = np.arange(2**16, dtype='uint16')
    lut = np.arange(2**8, dtype='uint8')
    lut = display(lut, display_min, display_max)
    return np.take(lut, image)


print(
    np.all(display(image, display_min, display_max) ==
            lut_display(image, display_min, display_max))
    )
    
print(
    timeit.timeit('display(image, display_min, display_max)',
            'from __main__ import display, image, display_min, display_max',
            number=10)
    )
    
print(
    timeit.timeit('lut_display(image, display_min, display_max)',
            'from __main__ import lut_display, image, display_min, display_max',
            number=10)
    )