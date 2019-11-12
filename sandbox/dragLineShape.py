import sys
import numpy as np

import napari

print(napari.__version__)

class bNapari:
	def __init__(self, title):

		self.viewer = napari.Viewer(title=title)

		#
		# shapes layer with 2x lines
		line1 = np.array([[11, 13], [111, 113]])
		line2 = np.array([[200, 200], [400, 300]])
		lines = [line1, line2]
		self.shapeLayer = self.viewer.add_shapes(lines,
			shape_type='line',
			edge_width = 5,
			edge_color = 'coral',
			face_color = 'royalblue')
		self.shapeLayer.mode = 'select'
		print('type(self.shapeLayer.data):', type(self.shapeLayer.data))
		print('self.shapeLayer.data:', self.shapeLayer.data)

		# see:
		# https://github.com/napari/napari/pull/544# make a callback for all mouse moves

		self.shapeLayer.events.set_data.connect(self.my_update_slider)

		"""
		# this works fine but as discussed does not get called durnig dragging
		@self.shapeLayer.mouse_move_callbacks.append
		def shape_mouse_move_callback(viewer, event):
			self.myMouseMove_Shape(viewer, event)
		"""

		'''
		@self.shapeLayer.mouse_drag_callbacks.append
		def shape_mouse_drag_callback(layer, event):
			self.myMouseDrag_Shape(layer, event)
		'''
		
	def my_update_slider(self, event):
		print('=== my_update_slider()')
		print('   type(event)', type(event))
		print('   event:', event)
		print('   event.source:', event.source)
		print('   event.type:', event.type)

		for idx, item in enumerate(self.shapeLayer.data):
			print('item', idx, 'is:', item)

	'''
	# this works fine but as discussed does not get called durnig dragging
	def myMouseMove_Shape(self, layer, event):
		"""
		event is type vispy.app.canvas.MouseEvent
		see: http://api.vispy.org/en/v0.1.0-0/event.html
		"""
		print('myMouseMove_Shape() layer:', layer, 'event:', event, type(event), 'type:', event.type, 'button', event.button)
		ind_x, ind_y = np.round(layer.coordinates).astype('int')
		print('   myMouseMove_Shape()', ind_x, ind_y)
	'''
	
	def myMouseDrag_Shape(self, layer, event):
		"""
		event is type napari.util.misc.ReadOnlyWrapper
		"""

		ind_x, ind_y = np.round(layer.coordinates).astype('int')
		print('******',
			'myMouseDrag_Shape() layer:', layer,
			'event:', event, 'type(event):', type(event), 'event.type:', event.type, 'event.button', event.button)
		print('   x:', ind_x, 'y:', ind_y)

		# This is from the docstring and the discussion
		# see: https://github.com/napari/napari/pull/544
		# I don't understand the sytax where you have a string sitting along on a line, e.g. "dragging"
		'''
		"dragging"
		yield

		# on move
		while event.type == 'mouse_move':
			print(event.pos)
			yield

		# on release
		print('goodbye world ;(')
		'''
		
if __name__ == '__main__':
	from PyQt5 import QtGui, QtCore, QtWidgets
	app = QtWidgets.QApplication(sys.argv)
	mn = bNapari('drag line shape and get mouse drag position')
	sys.exit(app.exec_())

