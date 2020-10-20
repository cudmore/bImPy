# THIS DOES NOT WORK
# IT IS MIXING CAIMAN AND BIMPY !!!!!

import os, time

#import bimpy
import caimanAlign
import caimanDetect

pathList = [
			# superior
			'/media/cudmore/data/20201014/slow/superior/2_nif_superior_cropped.tif',
			'/media/cudmore/data/20201014/slow/superior/3_nif_superior_cropped.tif',
			'/media/cudmore/data/20201014/slow/superior/4_nif_superior_cropped.tif',
			# inferior
			'/media/cudmore/data/20201014/slow/inferior/2_nif_inferior_cropped.tif',
			'/media/cudmore/data/20201014/slow/inferior/3_nif_inferior_cropped.tif',
			'/media/cudmore/data/20201014/slow/inferior/4_nif_inferior_cropped.tif',
			]

startSeconds = time.time()

# align
if 0:
	for path in pathList:
		if os.path.isfile(path):
			print('  align:', path)
			path = [path]
			caimanAlign.caimanAlign(path)
		else:
			print('file not found:', path)

# detect
if 1:
	for path in pathList:
		alignedPath, tmpExtension = os.path.splitext(path)
		alignedPath += '_aligned.tif'
		if os.path.isfile(alignedPath):
			print('  detect:', alignedPath)
			path = [alignedPath]
			caimanDetect.caimanDetect(path)
		else:
			print('file not found:', alignedPath)

# done
stopSeconds = time.time()
elapsedSeconds = round(stopSeconds-startSeconds,3)
elapsedMinutes = round(elapsedSeconds/60,3)
print(f'  caimanBatch() done in {elapsedMinutes} minutes')
