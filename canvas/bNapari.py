"""
20200917

I want this to be 'napari as a module'

see:
	https://github.com/napari/napari/issues/1110
"""

import numpy as np

import napari

import bimpy

class bNapari:
	def __init__(self, path, myCanvasWidget):
		"""
		path: path to tiff to open
		myCanvasWidget: bCanvasWidget

		todo: have canvas manage a list of bStack so we don't need to open every time

		"""
		self.path = path #myCanvasWidget.filePath
		self.mySimpleStack = bimpy.bStack(path, loadImages=True, loadTracing=False)

		self.myCanvasWidget = myCanvasWidget # bCanvasWidget

		#stackData = np.random.rand(10,512,512)

		#super(bNapari, self).__init__()#, stackData) #, stackData, ndisplay=3)

		ch1Data = self.mySimpleStack.getStack('raw', 1)

		self.viewer = napari.view_image(data=ch1Data)

		self.viewer.window._qt_window.closeEvent = self.cleanClose

		#v = self.viewer._qt_window
		'''
		c = self.viewer.close
		w = self.viewer.window.qt_viewer
		'''
		#wm = self.viewer.window.qt_viewer.window_menu

		#self.viewer.window.qt_viewer.close.connect(self.closeEvent)

	def cleanClose(self, event):
		print('bNapari.cleanClose()')

		# this works but does not sem right?
		self.viewer.close()

		#self.viewer.window._qt_window.hide()
		#return False

		# this gives
		"""
		ERROR:root:Unhandled exception:
		TypeError: invalid result from bNapari.cleanClose()
		"""
		#return self.viewer.window._qt_window.close()

	def close(self):
		print('bNapari.closeWindow()')
	def closeEvent(self, event):
		print('bNapari.closeWindow()')

if __name__ == '__main__':

	with napari.gui_qt():
		bn = bNapari()
