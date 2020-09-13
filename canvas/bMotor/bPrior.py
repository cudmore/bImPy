# Robert Cudmore
# 20191029

import serial, time

from bMotor import bMotor

class bPrior(bMotor):
	def __init__(self, isReal=True):
		bMotor.__init__(self, type='bPrior')

		self.eol = '\r\n'
		self.port = 'COM5'
		self.timeout = 1 # seconddef
		self.encoding = 'utf-8'

		self.isReal = isReal
		self.fake_x = -4811.0 #-9811.7 #185
		self.fake_y = -10079.0 #-20079.0 #-83

		self.ser = None

		self.readPosition()

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
			if self.isReal:
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

	def readPosition(self):
		try:
			if self.isReal:
				# open port
				self.open()

				self.writeLine('p') # write 'p' to ask for position
				resp = self.readLine() # read response

				print('   bPrior.readPosition() resp:', resp)
				try:
					xPos, yPos, zPos = resp.split(',')

					print(xPos)
					# when prior is at -18937.0 um we get -189370
					xPos = float(xPos)
					yPos = float(yPos)
					xPos /= 10
					yPos /= 10

					# step by 500 moves ~50 um
					# need to *10 the microns we specify in canvas interface

				except:
					print('   bPrior.readPosition() exception')
					xPos = 'Nan'
					yPos = 'Nan'
				'''
				if len(resp) == 3:
					xPos, yPos, zPos = resp.split(',')
				else:
					print('error reading Prior motor position')
					xPos = 'Nan'
					yPos = 'Nan'
				'''
				#self.close()
			else:
				xPos = self.fake_x
				yPos = self.fake_y

		except Exception as e:
			print('exception in bPrior.readPosition():', e)
			raise
		finally:
			self.close()

		xPos = float(xPos)
		yPos = float(yPos)
		print('bPrior.readPosition() returning:', xPos, yPos)
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
					self.fake_x -= float(umDistanceStr)
				elif direction == 'right':
					self.fake_x += float(umDistanceStr)
				elif direction == 'front':
					self.fake_y += float(umDistanceStr)
				elif direction == 'back':
					self.fake_y -= float(umDistanceStr)

			# wait for response of 'R'
			if self.isReal:
				resp = self.readLine()
				while len(resp)>0:
					#print('resp:', resp)
					resp = self.readLine()

			stopTime = time.time()
			elapsedTime = stopTime - startTime
			print('prior.move() direction:', direction, 'umDistance:', umDistance, 'took', round(elapsedTime,2), 'seconds')
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
		theRet = self.readPosition()
		return theRet

if __name__ == '__main__':
	isReal = False

	prior = bPrior(isReal=isReal)

	# test read position
	if 0:
		xPos, yPos = prior.readPosition()
		print('xPos:', xPos, 'yPos:', yPos)

	# test move
	if 1:
		print('start posiiton:', prior.readPosition())
		prior.priorMove('left', 100000)
		print('end posiiton:', prior.readPosition())
