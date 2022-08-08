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
	def __init__(self, bStackObject, myCanvasWidget):
		"""
		path: path to tiff to open
		myCanvasWidget: bCanvasWidget

		todo: have canvas manage a list of bStack so we don't need to open every time

		"""
		print('bNapari.__init__() bStackObject:', bStackObject.print)

		self.path = bStackObject.path

		# assuming already loaded
		#self.mySimpleStack = bimpy.bStack(path, loadImages=True, loadTracing=False)

		# todo: don't make a reference?
		self.mySimpleStack = bStackObject

		self.myCanvasWidget = myCanvasWidget # bCanvasWidget


		self.viewer = napari.Viewer(title=self.path)
		self.viewer.window._qt_window.closeEvent = self.cleanClose

		numChannels = self.mySimpleStack.numChannels

		colorList = ['green', 'red', 'blue']
		if numChannels == 1:
			colorList = ['gray']

		channelList = list(range(numChannels))
		channelList.reverse() # reverse is in place
		for i in channelList:
			channelNumber = i + 1

			# may be nan if not loaded
			channelData = self.mySimpleStack.getStack('raw', channelNumber)
			if channelData is None:
				continue

			name = 'Channel ' + str(channelNumber)
			self.viewer.add_image(data=channelData,
							name=name,
							blending='additive',
							colormap=colorList[i])

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
		# nope, now it does not workk???
		#self.viewer.close()

		#self.viewer.window._qt_window.hide()
		self.viewer.window._qt_window.close()
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
