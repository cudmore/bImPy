from PIL import Image
from PIL.TiffTags import TAGS

path = '/Users/cudmore/box/data/nathan/vesselucida/20191017__0001.tif'

with Image.open(path) as img:
	print(img.tag)
	meta_dict = {TAGS[key] : img.tag[key] for key in img.tag.iterkeys()}
print(meta_dict)
