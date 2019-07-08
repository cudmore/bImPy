# Author:
# Date: 20190704

import os

class bFileUtil:
	def __init__(self):
		pass
	def getConvertedFolder(self, rawFilePath):
		"""
		Given a raw scope file (like an oir)
		Return the full path to the converted _tif folder
		"""
		
		# full path to the folder it is in
		folderPath = os.path.dirname(rawFilePath) 
		#print('getConvertedFolder() folderPath:', folderPath)
		
		# the name of the enclosing folder
		enclosingFolder = os.path.basename(os.path.normpath(folderPath)) 
		#print('getConvertedFolder() enclosingFolder:', enclosingFolder)
		
		# full path to converted _tif folder
		convertedFolder = os.path.join(folderPath, enclosingFolder + '_tif')
		#print('getConvertedFolder() convertedFolder:', convertedFolder)


		return convertedFolder
	
	def getMaxConvertedFolder(self, rawFilePath):
		"""
		Given a raw scope file (like an oir)
		Return the full path to the converted _tif/max folder
		"""
		convertedFolder = self.getConvertedFolder(rawFilePath)
		maxPath = os.path.join(convertedFolder, 'max')
		return maxPath
		
	'''
	def removeChannel(self, fileName):
		fileName = fileName.replace('_ch1', '')
		fileName = fileName.replace('_ch2', '')
		fileName = fileName.replace('_ch3', '')
		fileName = fileName.replace('_ch4', '')
		return fileName
	'''
			
	def getMaxFileFromRaw(self, rawFilePath, theChannel=1):
		"""
		Given a raw scope file (like an oir)
		Return the full path to the converted _tif/max file
		Return None if it does not exist
		"""
	
		# full path to converted _tif folder
		convertedMaxFolder = self.getMaxConvertedFolder(rawFilePath)
		
		#print('getMaxFileFromRaw convertedMaxFolder:', convertedMaxFolder)
		
		fullFileName = os.path.basename(rawFilePath)
		baseFileName, extension = os.path.splitext(fullFileName)

		maxFileName = 'max_' + baseFileName + '_ch' + str(theChannel) + '.tif'
		
		#print('maxFileName:', maxFileName)
		
		convertedMaxPath = os.path.join(convertedMaxFolder, maxFileName)

		#print('convertedMaxPath:', convertedMaxPath)
		
		if os.path.isfile(convertedMaxPath):
			return convertedMaxPath
		else:
			return None
		
	def getHeaderFileFromRaw(self, rawFilePath):
		"""
		Given a raw file off the scope (like an oir)
		Return full path to converted header .txt file
		Return None if it does not exist
		"""
		
		# full path to converted _tif folder
		convertedFolder = self.getConvertedFolder(rawFilePath)
		
		fullFileName = os.path.basename(rawFilePath)
		baseFileName, extension = os.path.splitext(fullFileName)
		
		headerTextFile = baseFileName + '.txt'
				
		convertedHeaderPath = os.path.join(convertedFolder, headerTextFile)
				
		if os.path.isfile(convertedHeaderPath):
			return convertedHeaderPath
		else:
			return None

	'''
	def getMaxProjectFromRaw(self, rawFilePath):
		# full path to converted _tif folder
		convertedFolder = self.getConvertedFolder(rawFilePath)
	'''
		
if __name__ == '__main__':
	rawOir = '/Users/cudmore/Dropbox/data/20190429/20190429_tst2/20190429_tst2_0014.oir'
	fu = bFileUtil()
	
	# works
	#print(fu.getHeaderFileFromRaw(rawOir))
	
	maxFile = fu.getMaxFileFromRaw(rawOir, 1)
	print('maxFile:', maxFile)
	
	
	
	
	
	