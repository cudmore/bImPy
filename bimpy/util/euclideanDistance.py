import math

def euclideanDistance(x1, y1, z1, x2, y2, z2):
	if z1 is None and z2 is None:
		return math.sqrt((x2-x1)**2 + (y2-y1)**2)
	else:
		return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
