# Author: Robert Cudmore
# Date: 20190701

"""
Manage a list of stack
"""

import os

from Stack import Stack

acceptableExtensions = ['tif', 'oir']

class StackList:
	def __init__(self, folderPath):
		self.folderPath = path
		self.stackList = []
		
	def loadFolder(self):
		for file in sorted(os.listdir(self.folderPath)):
			if file.startswith('.'):
				continue
			try:
				fileExtension = file.split('.')[1]
			except: #IndexError
				continue
			if fileExtension in acceptableExtensions:
				fullStackPath = os.path.join(self.folderPath, file)
				print('fullStackPath:', fullStackPath)
				
				newStack = Stack(fullStackPath)
				newStack.loadHeader()
				
				self.stackList.append(newStack)
				
				newStack.header.prettyPrint()
				
if __name__ == '__main__':
	path = '/Users/cudmore/box/data/testoir'
	path = '/Users/cudmore/box/data/testoir/testoir_tif'
	sl = StackList(path)
	sl.loadFolder()