import serial, time

from bMotor import bMotor

class fakeMotor(bMotor):
	def __init__(self, port):
		bMotor.__init__(self, type='fakeMotor')

		self.fake_x = -186541.0 #-9811.7 #185 # [-186541 -180967 -651565]
		self.fake_y = -180967.0 #-20079.0 #-83

		self.port = port
		self.ser = None

		self.readPosition()

	def readPosition(self):
		try:
			self.open()

			xPos = self.fake_x
			yPos = self.fake_y

		except Exception as e:
			print('exception in fakeMotor.readPosition():', e)
			raise
		finally:
			self.close()

			xPos = float(xPos)
			yPos = float(yPos)
			print('fakeMotor.readPosition() returning:', xPos, yPos)
			return xPos, yPos, None

	def move(self, direction, umDistance):
		"""
		direction: str:  in ['left', 'right', 'front', 'back']
		umDistance: int: Not sure on units yet
		"""

		try:
			self.open()

			directionStr = ''
			if direction == 'left':
				directionStr = 'L'
			if direction == 'right':
				directionStr = 'R'
			if direction == 'front':
				directionStr = 'F'
			if direction == 'back':
				directionStr = 'B'
			if len(directionStr)==0:
				# error
				print('error: fakeMotor.move() got bad direcion:', direction)
				return

			startTime = time.time()

			# send 'direction,distance', to move back 100 um, send 'B,100'
			umDistanceStr = str(umDistance)
			outStr = directionStr + ',' + umDistanceStr

			if direction == 'left':
				self.fake_x -= float(umDistanceStr)
			elif direction == 'right':
				self.fake_x += float(umDistanceStr)
			elif direction == 'front':
				self.fake_y += float(umDistanceStr)
			elif direction == 'back':
				self.fake_y -= float(umDistanceStr)

			# wait for response of 'R'

			stopTime = time.time()
			elapsedTime = stopTime - startTime
			print('fakeMotor.move() direction:', direction, 'umDistance:', umDistance, 'took', round(elapsedTime,2), 'seconds')

			print('  fake_x:', self.fake_x, 'fake_y:', self.fake_y)

		except Exception as e:
			print('exception in fakeMotor.move():', e)
			raise
		finally:
			self.close()

		# not sure if timing with real motor will report correct position???
		theRet = self.readPosition()
		return theRet

	def open(self):
		if self.ser is not None:
			print('mp285.open(), port already opened')
		else:
			self.ser = True
		return self.ser

	def close(self):
		if self.ser is None:
			print ('fakeMotor.close(), port not opened')
		else:
			self.ser = None
