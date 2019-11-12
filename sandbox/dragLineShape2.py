import sys
import numpy as np

import napari

print(napari.__version__)

class bNapari:
	def __init__(self, title):

		self.viewer = napari.Viewer(title=title)

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

		# this is a callback for when the data of the line shape changes
		self.shapeLayer.events.set_data.connect(self.lineShapeChange_callback)

	def lineShapeChange_callback(self, event):
		print('=== lineShapeChange_callback()')
		print('   type(event)', type(event))
		print('   event.source:', event.source)
		print('   event.type:', event.type)

		print('   self.shapeLayer.selected_data:', self.shapeLayer.selected_data)
		
		# self.shapeLayer.selected_data is a list of int tell us index into self.shapeLayer.data of all selected shapes
		selected_data = self.shapeLayer.selected_data
		if len(selected_data) > 0:
			index = selected_data[0] # just the first selected shape
			print('   shape at index', index, 'in self.shapeLayer.data changed and is now:', self.shapeLayer.data[index])
		
if __name__ == '__main__':
	from PyQt5 import QtGui, QtCore, QtWidgets
	app = QtWidgets.QApplication(sys.argv)
	mn = bNapari('drag line shape and get mouse drag position')
	sys.exit(app.exec_())

