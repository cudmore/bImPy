import serial, time

from bMotor import bMotor

class mp285(bMotor):
	def __init__(self, isReal=True):
		bMotor.__init__(self, type='mp285')

		self.eol = '\r\n'
		self.port = 'COM5'
		self.timeout = 1 # seconddef
		self.encoding = 'utf-8'

		self.isReal = isReal
		self.fake_x = -4811.0 #-9811.7 #185
		self.fake_y = -10079.0 #-20079.0 #-83

		self.ser = None

		self.readPosition()

	def readPosition(self):
		try:
			if self.isReal:
				pass
			else:
				xPos = self.fake_x
				yPos = self.fake_y

		except Exception as e:
			print('exception in mp285.readPosition():', e)
			raise
		finally:
			self.close()

		xPos = float(xPos)
		yPos = float(yPos)
		print('mp285.readPosition() returning:', xPos, yPos)
		return xPos, yPos

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
				print('error: mp285.move() got bad direcion:', direction)
				return

			startTime = time.time()

			# send 'direction,distance', to move back 100 um, send 'B,100'
			umDistanceStr = str(umDistance)
			outStr = directionStr + ',' + umDistanceStr

			if self.isReal:
				#self.writeLine(outStr)
				pass
			else:
				if direction == 'left':
					self.fake_x -= float(umDistanceStr)
				elif direction == 'right':
					self.fake_x += float(umDistanceStr)
				elif direction == 'front':
					self.fake_y += float(umDistanceStr)
				elif direction == 'back':
					self.fake_y -= float(umDistanceStr)

			# wait for response of 'R'
			if self.isReal:
				pass
				'''
				resp = self.readLine()
				while len(resp)>0:
					#print('resp:', resp)
					resp = self.readLine()
				'''

			stopTime = time.time()
			elapsedTime = stopTime - startTime
			print('priorMove() direction:', direction, 'umDistance:', umDistance, 'took', round(elapsedTime,2), 'seconds')
			if self.isReal:
				#todo: print current motor coordinates
				pass
			else:
				print('  fake_x:', self.fake_x, 'fake_y:', self.fake_y)

		except Exception as e:
			print('exception in mp285.move():', e)
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
			if self.isReal:
				self.ser = serial.Serial(port=self.port, timeout=self.timeout)
			else:
				self.ser = 1
		return self.ser

	def close(self):
		if self.ser is None:
			if self.isReal:
				print ('mp285.close(), port not opened')
		else:
			if self.isReal:
				self.ser.close()
				self.ser = None
			else:
				pass
