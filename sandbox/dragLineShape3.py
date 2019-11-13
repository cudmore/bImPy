"""
Display a 2D image and do complex processing based on mouse drags on a
shapes layer.
"""

from skimage import data
from skimage import measure
import numpy as np
import napari


def profile_lines(image, shape_layer):
	profile_data = []
	for line in shape_layer.data:
		profile_data.append(
			measure.profile_line(image, line[0], line[1]).mean()
		)
	msg = ('profile means: ['
			+ ', '.join([f'{d:.2f}' for d in profile_data])
			+ ']')
	shape_layer.status = msg



with napari.gui_qt():
	np.random.seed(1)
	viewer = napari.Viewer()
	blobs = data.binary_blobs(length=512, volume_fraction=0.1, n_dim=2)
	viewer.add_image(blobs, name='blobs')
	line1 = np.array([[11, 13], [111, 113]])
	line2 = np.array([[200, 200], [400, 300]])
	lines = [line1, line2]
	shapes_layer = viewer.add_shapes(lines, shape_type='line',
			edge_width=5, edge_color='coral', face_color='royalblue')
	shapes_layer.mode = 'select'

	@shapes_layer.mouse_move_callbacks.append
	def profile_lines_move(layer, event):
		print('profile_lines_move() event.type:', event.type)

	@shapes_layer.mouse_drag_callbacks.append
	def profile_lines_drag(layer, event):
		profile_lines(blobs, layer)
		print('1)', event.pos)
		yield
		while event.type == 'mouse_move':
			profile_lines(blobs, layer)
			print('2)', event.pos)
			yield
