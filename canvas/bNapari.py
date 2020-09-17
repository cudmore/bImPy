"""
20200917

I want this to be 'napari as a module'

see:
	https://github.com/napari/napari/issues/1110
"""

import numpy as np

import napari

class bNapari:
	def __init__(self):
		stackData = np.random.rand(10,512,512)

		#super(bNapari, self).__init__()#, stackData) #, stackData, ndisplay=3)

		self.viewer = napari.view_image(data=stackData)

		self.viewer.window._qt_window.closeEvent = self.cleanClose

		#v = self.viewer._qt_window
		'''
		c = self.viewer.close
		w = self.viewer.window.qt_viewer
		'''
		#wm = self.viewer.window.qt_viewer.window_menu

		#self.viewer.window.qt_viewer.close.connect(self.closeEvent)

	def cleanClose(self, event):
		print('cleanClose()')

		# this works but does not sem right?
		self.viewer.close()

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
