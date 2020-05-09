import os, sys

def getFileListFromFile(filePath):

	"""
	given a .txt file with one path per line, return a list paths
	"""
	with open(filePath) as f:
		content = f.readlines()
	# remove whitespace characters like `\n` at the end of each line
	content = [x.strip() for x in content] 
	# remove lines starting with '#'
	retList = []
	for line in content:
		if line.startswith('#'):
			pass
		else:
			retList.append(line)
	return retList
