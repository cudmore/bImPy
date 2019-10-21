import numpy as np
from matplotlib.lines import Line2D
from matplotlib.artist import Artist
#from matplotlib.mlab import dist_point_to_segment



class PolygonInteractor(object):
	"""
	A polygon editor.

	Key-bindings

	  't' toggle vertex markers on and off.  When vertex markers are on,
		  you can move them, delete them

	  'd' delete the vertex under point

	  'i' insert a vertex at point.  You must be within epsilon of the
		  line connecting two existing vertices

	"""

	showverts = True
	epsilon = 5  # max pixel distance to count as a vertex hit

	def __init__(self, ax, poly):
		if poly.figure is None:
			raise RuntimeError('You must first add the polygon to a figure '
							   'or canvas before defining the interactor')
		self.ax = ax
		canvas = poly.figure.canvas
		self.poly = poly

		x, y = zip(*self.poly.xy)
		self.line = Line2D(x, y,
						   marker='o', markerfacecolor='r',
						   animated=True)
		self.ax.add_line(self.line)

		self.cid = self.poly.add_callback(self.poly_changed)
		self._ind = None  # the active vert

		canvas.mpl_connect('draw_event', self.draw_callback)
		canvas.mpl_connect('button_press_event', self.button_press_callback)
		canvas.mpl_connect('key_press_event', self.key_press_callback)
		canvas.mpl_connect('button_release_event', self.button_release_callback)
		canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
		self.canvas = canvas

	def draw_callback(self, event):
		self.background = self.canvas.copy_from_bbox(self.ax.bbox)
		self.ax.draw_artist(self.poly)
		self.ax.draw_artist(self.line)
		# do not need to blit here, this will fire before the screen is
		# updated

	def poly_changed(self, poly):
		'this method is called whenever the polygon object is called'
		# only copy the artist props to the line (except visibility)
		vis = self.line.get_visible()
		Artist.update_from(self.line, poly)
		self.line.set_visible(vis)  # don't use the poly visibility state

	def get_ind_under_point(self, event):
		'get the index of the vertex under point if within epsilon tolerance'

		# display coords
		xy = np.asarray(self.poly.xy)
		xyt = self.poly.get_transform().transform(xy)
		xt, yt = xyt[:, 0], xyt[:, 1]
		d = np.hypot(xt - event.x, yt - event.y)
		indseq, = np.nonzero(d == d.min())
		ind = indseq[0]

		if d[ind] >= self.epsilon:
			ind = None

		return ind

	def button_press_callback(self, event):
		'whenever a mouse button is pressed'
		if not self.showverts:
			return
		if event.inaxes is None:
			return
		if event.button != 1:
			return
		self._ind = self.get_ind_under_point(event)

	def button_release_callback(self, event):
		'whenever a mouse button is released'
		if not self.showverts:
			return
		if event.button != 1:
			return
		self._ind = None

	def key_press_callback(self, event):
		'whenever a key is pressed'
		needsUpdate = False
		if not event.inaxes:
			return
		if event.key == 't':
			self.showverts = not self.showverts
			self.line.set_visible(self.showverts)
			if not self.showverts:
				self._ind = None
			needsUpdate = True
		elif event.key == 'd':
			ind = self.get_ind_under_point(event)
			if ind is not None:
				self.poly.xy = np.delete(self.poly.xy,
										 ind, axis=0)
				self.line.set_data(zip(*self.poly.xy))
				needsUpdate = True
		elif event.key == 'i':
			xys = self.poly.get_transform().transform(self.poly.xy)
			p = event.x, event.y  # display coords
			for i in range(len(xys) - 1):
				s0 = xys[i]
				s1 = xys[i + 1]
				tmpLine = [s0, s1]
				d = self._point_to_line_dist(p, tmpLine)
				#d = dist_point_to_segment(p, s0, s1)
				if d <= self.epsilon:
					self.poly.xy = np.insert(
						self.poly.xy, i+1,
						[event.xdata, event.ydata],
						axis=0)
					self.line.set_data(zip(*self.poly.xy))
					needsUpdate = True
					break
		if needsUpdate or self.line.stale:
			self.canvas.draw_idle()

	def motion_notify_callback(self, event):
		'on mouse movement'
		if not self.showverts:
			return
		if self._ind is None:
			return
		if event.inaxes is None:
			return
		if event.button != 1:
			return
		x, y = event.xdata, event.ydata

		self.poly.xy[self._ind] = x, y
		if self._ind == 0:
			self.poly.xy[-1] = x, y
		elif self._ind == len(self.poly.xy) - 1:
			self.poly.xy[0] = x, y
		self.line.set_data(zip(*self.poly.xy))

		self.canvas.restore_region(self.background)
		self.ax.draw_artist(self.poly)
		self.ax.draw_artist(self.line)
		self.canvas.blit(self.ax.bbox)

	#dist_point_to_segment(p, s0, s1)
	def _point_to_line_dist(self, point, line):
		"""Calculate the distance between a point and a line segment.

		To calculate the closest distance to a line segment, we first need to check
		if the point projects onto the line segment.  If it does, then we calculate
		the orthogonal distance from the point to the line.
		If the point does not project to the line segment, we calculate the 
		distance to both endpoints and take the shortest distance.

		:param point: Numpy array of form [x,y], describing the point.
		:type point: numpy.core.multiarray.ndarray
		:param line: list of endpoint arrays of form [P1, P2]
		:type line: list of numpy.core.multiarray.ndarray
		:return: The minimum distance to a point.
		:rtype: float
		"""
		# unit vector
		unit_line = line[1] - line[0]
		norm_unit_line = unit_line / np.linalg.norm(unit_line)

		# compute the perpendicular distance to the theoretical infinite line
		segment_dist = (
			np.linalg.norm(np.cross(line[1] - line[0], line[0] - point)) /
			np.linalg.norm(unit_line)
		)

		diff = (
			(norm_unit_line[0] * (point[0] - line[0][0])) + 
			(norm_unit_line[1] * (point[1] - line[0][1]))
		)

		x_seg = (norm_unit_line[0] * diff) + line[0][0]
		y_seg = (norm_unit_line[1] * diff) + line[0][1]

		endpoint_dist = min(
			np.linalg.norm(line[0] - point),
			np.linalg.norm(line[1] - point)
		)

		# decide if the intersection point falls on the line segment
		lp1_x = line[0][0]  # line point 1 x
		lp1_y = line[0][1]  # line point 1 y
		lp2_x = line[1][0]  # line point 2 x
		lp2_y = line[1][1]  # line point 2 y
		is_betw_x = lp1_x <= x_seg <= lp2_x or lp2_x <= x_seg <= lp1_x
		is_betw_y = lp1_y <= y_seg <= lp2_y or lp2_y <= y_seg <= lp1_y
		if is_betw_x and is_betw_y:
			return segment_dist
		else:
			# if not, then return the minimum distance to the segment endpoints
			return endpoint_dist

if __name__ == '__main__':
	import matplotlib.pyplot as plt
	from matplotlib.patches import Polygon

	theta = np.arange(0, 2*np.pi, 0.1)
	r = 1.5

	xs = r * np.cos(theta)
	ys = r * np.sin(theta)

	poly = Polygon(np.column_stack([xs, ys]), animated=True)

	fig, ax = plt.subplots()
	ax.add_patch(poly)
	p = PolygonInteractor(ax, poly)

	ax.set_title('Click and drag a point to move it')
	ax.set_xlim((-2, 2))
	ax.set_ylim((-2, 2))
	plt.show()