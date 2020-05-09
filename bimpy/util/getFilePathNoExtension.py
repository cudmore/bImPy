"""
given full file path, return file path without extension
"""
import os

def getFilePathNoExtension(path):

	baseFilePath = ''
	tmpPath, tmpFileName = os.path.split(path)
	tmpFileNameNoExtension, tmpExtension = tmpFileName.split('.')
	baseFilePath = os.path.join(tmpPath, tmpFileNameNoExtension)

	return baseFilePath
	
if __name__ == '__main__':
	
	path = '/a/b/c/file.txt'
	ret = getFilePathNoExtension(path)
	print(path, ret)