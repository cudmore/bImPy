"""
This (17,7) grid is SUPER SLOW on my home machine, thus I tweaked it to (12,7)
"""

import myDaskNapari

myGridParams = myDaskNapari.getDaskGridDict()
myGridParams['path'] = '/Users/cudmore/box/data/nathan/20200519'
myGridParams['prefixStr'] = '20200519__A01_G001_'
myGridParams['channelList'] = [1, 2]
myGridParams['commonShape'] = (62,512,512)
myGridParams['commonVoxelSize'] = (1, 0.621480865, 0.621480865)
myGridParams['trimPercent'] = 15
myGridParams['trimPixels'] = None # calculated
myGridParams['nRow'] = 12 #17
myGridParams['nCol'] = 7

myDaskNapari.openDaskNapari(myGridParams)
