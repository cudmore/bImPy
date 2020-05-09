import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

def myOpenFileDialog(initialdir=None, filetypes=None):
	"""
	return a str with a file path, will return empty str '' on user cancel
	"""
	filePath = filedialog.askopenfilename(initialdir=initialdir, filetypes=filetypes)
	if filePath:
		print('filePath:', filePath)
	else:
		print('no file selected')
	return filePath
	
def myOpenFolderDialog(initialdir=None):
	"""
	return a str with a folder path, will return empty str '' on user cancel
	"""
	# get a folder path
	folderPath = filedialog.askdirectory(initialdir=initialdir)
	if folderPath:
		print('folderPath:', folderPath)
	else:
		print('no folder selected')
	return folderPath
	
if __name__ == '__main__':

	# if you know where the dialog should default to
	initialdir = '' #'/Users/cudmore/Desktop'
	# you can specify allowed file types in askopenfilename
	filetypes = (("tiff file","*.tif"),("all files","*.*"))

	userSelectedFilePath = myOpenFileDialog(initialdir=initialdir, filetypes=filetypes)
	
	userSelectedFolderPath = myOpenFolderDialog(initialdir=initialdir)