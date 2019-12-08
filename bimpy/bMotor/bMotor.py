# Author: RObert Cudmore
# Date: 20191208

"""
An abstract class to define a motor interface

This needs to be derived for each type of motor, e.g. (prior, mp285, bruker)

See bPrior for an example
"""

class bMotor(object):
	def __init__(self, type=None):
		self._type = type

	def readPosition(self):
		pass

	def move(direction, umDistance):
		pass
