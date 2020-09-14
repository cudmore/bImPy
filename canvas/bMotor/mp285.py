import serial, time

from bMotor import bMotor

class mp285(bMotor):
	def __init__(self, port):
		"""
		port: serial port, on windows like 'COM5'
		"""
		bMotor.__init__(self, type='mp285')

		self.eol = '\r\n'
		self.port = port
		self.timeout = 1 # seconddef
		self.encoding = 'utf-8'

		self.ser = None

		self.readPosition()

	def readPosition(self):
		try:
			self.open()

			'''
			self.writeLine('p') # write 'p' to ask for position
			resp = self.readLine() # read response

			print('   mp285.readPosition() resp:', resp)
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
				print('   mp285.readPosition() exception')
				xPos = 'Nan'
				yPos = 'Nan'
			'''

			'''
			if len(resp) == 3:
				xPos, yPos, zPos = resp.split(',')
			else:
				print('error reading mp285 motor position')
				xPos = 'Nan'
				yPos = 'Nan'
			'''
			#self.close()

		except Exception as e:
			print('exception in mp285.readPosition():', e)
			self.close()
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

			'''
			self.writeLine(outStr)
			'''

			# wait for response of 'R'
			'''
			resp = self.readLine()
			while len(resp)>0:
				#print('resp:', resp)
				resp = self.readLine()
			'''

			stopTime = time.time()
			elapsedTime = stopTime - startTime
			print('mp285.move() direction:', direction, 'umDistance:', umDistance, 'took', round(elapsedTime,2), 'seconds')

		except Exception as e:
			print('exception in mp285.move():', e)
			self.close()
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
			self.ser = serial.Serial(port=self.port, timeout=self.timeout)
		return self.ser

	def close(self):
		if self.ser is None:
			print ('mp285.close(), port not opened')
		else:
			self.ser.close()
			self.ser = None
