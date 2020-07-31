"""
Given a raw folder, generate list of file basename without _ch1.tif, _ch2.tif
"""

import os, argparse

def gateBasename(path):
	chStr = '_ch1.tif'
	
	for file in os.listdir(path):
		if file.startswith('.'):
			continue
		if not file.endswith('.tif'):
			continue

		if not file.endswith(chStr):
			continue
	
		baseFile = file
		baseFile = baseFile.replace('_ch1.tif', '')
		baseFile = baseFile.replace('_ch2.tif', '')
		baseFile = baseFile.replace('_ch3.tif', '')
		
		print(baseFile)

################################################################################
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = 'Process a vascular stack')
	parser.add_argument('rawPath', nargs=1, default='', help='path to raw folder with _ch1.tif and _ch2.tif')
	args = parser.parse_args() # args is a list of command line arguments

	if len(args.rawPath)>0:
		path = args.rawPath[0]
	
	# for 20200519
	thesIndices = [3,4,5,9,10,15,16,21,22,23,26,27,28,33,34,35,38,39,46,47]
	
	gateBasename(path)
	
