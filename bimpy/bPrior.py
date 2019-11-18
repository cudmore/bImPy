# Robert Cudmore
# 20191029

import serial, time

class bPrior:
	def __init__(self, isReal=True):
		self.eol = '\r\n'
		self.port = 'COM5'
		self.timeout = 1 # seconddef
		self.encoding = 'utf-8'

		self.isReal = isReal
		self.fake_x = -4811.0 #-9811.7 #185
		self.fake_y = -10079.0 #-20079.0 #-83

		self.ser = None

	def open(self):
		if self.ser is not None:
			print('port already opened')
		else:
			if self.isReal:
				self.ser = serial.Serial(port=self.port, timeout=self.timeout)
			else:
				self.ser = 1
		return self.ser

	def close(self):
		if self.ser is None:
			print ('bPrior.close(), port not opened')
		else:
			if self.isReal:
				self.ser.close()
				self.ser = None
			else:
				pass

	def writeLine(self, str):
		if self.ser is None:
			print('error in bPrior.write(), port not opened')
			return
		outStr = str + self.eol # add end of line
		outStr = outStr.encode('utf-8') # encode as utf-8
		if self.isReal:
			self.ser.write(outStr)
		else:
			pass

	def readLine(self):
		if self.ser is None:
			print('error in bPrior.read(), port not opened')
			return
		if self.isReal:
			resp = self.ser.readline()
			resp = resp.decode(self.encoding)
		else:
			resp = "111,222,333"
		return resp

	def priorReadPos(self):
		try:
			if self.isReal:
				# open port
				self.open()

				self.writeLine('p') # write 'p' to ask for position
				resp = self.readLine() # read response

				xPos, yPos, zPos = resp.split(',')

				self.close()
			else:
				xPos = self.fake_x
				yPos = self.fake_y

		except Exception as e:
			print('exception in priorReadPos():', e)
			raise
		finally:
			self.close()

		print('priorReadPos() returning:', xPos, yPos)
		return xPos, yPos

	def priorMove(self, direction, umDistance):
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
				print('error: bPrior.move() got bad direcion:', direction)
				return

			startTime = time.time()

			# send 'direction,distance', to move back 100 um, send 'B,100'
			umDistanceStr = str(umDistance)
			outStr = directionStr + ',' + umDistanceStr

			if self.isReal:
				self.writeLine(outStr)
			else:
				if direction == 'left':
					self.fake_x -= int(umDistanceStr)
				elif direction == 'right':
					self.fake_x += int(umDistanceStr)
				elif direction == 'front':
					self.fake_y += int(umDistanceStr)
				elif direction == 'back':
					self.fake_y -= int(umDistanceStr)

			# wait for response of 'R'
			if self.isReal:
				resp = self.readLine()
				while len(resp)>0:
					#print('resp:', resp)
					resp = self.readLine()

			stopTime = time.time()
			elapsedTime = stopTime - startTime
			print('priorMove() direction:', direction, 'umDistance:', umDistance, 'took', round(elapsedTime,2), 'seconds')
			if self.isReal:
				#todo: print current motor coordinates
				pass
			else:
				print('  fake_x:', self.fake_x, 'fake_y:', self.fake_y)

		except Exception as e:
			print('exception in priorMove():', e)
			raise
		finally:
			self.close()

		# not sure if timing with real motor will report correct position???
		theRet = self.priorReadPos()
		return theRet

if __name__ == '__main__':
	isReal = False

	prior = bPrior(isReal=isReal)

	# test read position
	if 0:
		xPos, yPos = prior.priorReadPos()
		print('xPos:', xPos, 'yPos:', yPos)

	# test move
	if 1:
		print('start posiiton:', prior.priorReadPos())
		prior.priorMove('left', 100000)
		print('end posiiton:', prior.priorReadPos())
