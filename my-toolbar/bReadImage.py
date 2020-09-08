#from scipy import misc
import os
import imageio
import glob

for filepath in glob.glob("/Users/cudmore/Sites/bImPy/my-toolbar/icons/*.png"):
	if '-inv' in filepath:
		continue
	image = imageio.imread(filepath)
	print(filepath, image.shape, image.dtype)

	image_invert = image.copy()
	#image_invert[image_invert[:,:,0]==255] = 0
	#image_invert[image_invert[:,:,1]==255] = 0
	image_invert[:,:,0] = 0
	image_invert[:,:,1] = 0

	savePath = os.path.splitext(filepath)[0]
	savePath += '-inv.png'
	print('  savePath:', savePath)
	imageio.imwrite(savePath, image_invert)
	for i in range(image.shape[2]):
		print(i, image_invert[:,:,i])
