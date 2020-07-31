import myDaskNapari

myGridParams = myDaskNapari.getDaskGridDict()
myGridParams['path'] = '/Users/cudmore/box/data/nathan/20200518'
myGridParams['prefixStr'] = '20200518__A01_G001_'
myGridParams['channelList'] = [1, 2]
myGridParams['commonShape'] = (64,512,512)
myGridParams['commonVoxelSize'] = (1, 0.621480865, 0.621480865)
myGridParams['trimPercent'] = 15
myGridParams['trimPixels'] = None # calculated
myGridParams['nRow'] = 8
myGridParams['nCol'] = 6

myDaskNapari.openDaskNapari(myGridParams)
