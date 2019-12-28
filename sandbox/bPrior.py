# Robert Cudmore
# 20191029

import serial, time

class bPrior:
	def __init__(self):
		self.eol = '\r\n'
		self.port = 'COM5'
		self.timeout = 1 # seconddef
		self.encoding = 'utf-8'
		
		self.ser = None
		
	def open(self):
		if self.ser is not None:
			print('port already opened')
		else:
			self.ser = serial.Serial(port=self.port, timeout=self.timeout)	
		return self.ser
		
	def close(self):
		if self.ser is None:
			print ('bPrior.close(), port not opened')
		else:
			self.ser.close()
			self.ser = None
		
	def writeLine(self, str):
		if self.ser is None:
			print('error in bPrior.write(), port not opened')
			return		
		outStr = str + self.eol # add end of line
		outStr = outStr.encode('utf-8') # encode as utf-8
		self.ser.write(outStr)
		
	def readLine(self):
		if self.ser is None:
			print('error in bPrior.read(), port not opened')
			return
		resp = self.ser.readline()
		resp = resp.decode(self.encoding)		
		return resp
		
	def priorReadPos(self):
		try:
			# open port
			self.open()

			self.writeLine('p') # write 'p' to ask for position
			resp = self.readLine() # read response

			xPos, yPos, zPos = resp.split(',')

			self.close()
		except Exception as e:
			print('exception in priorReadPos():', e)
			raise
		finally:
			self.close()
		
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
			self.writeLine(outStr)
			
			# wait for response of 'R'
			resp = self.readLine()
			while len(resp)>0:
				#print('resp:', resp)
				resp = self.readLine()
				
			stopTime = time.time()
			elapsedTime = stopTime - startTime
			print('priorMove() direction:', direction, 'umDistance:', umDistance, 'took', round(elapsedTime,2), 'seconds')
						
		except Exception as e:
			print('exception in priorMove():', e)
			raise
		finally:
			self.close()
			
if __name__ == '__main__':
	prior = bPrior()
	
	# test read position
	if 1:
		xPos, yPos = prior.priorReadPos()
		print('xPos:', xPos, 'yPos:', yPos)
	
	# test move
	if 1:
		prior.priorMove('right', 100000)
		