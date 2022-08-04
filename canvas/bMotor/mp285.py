import serial, time, struct
import traceback

from bMotor import bMotor

import logging
logger = logging.getLogger('canvasApp')

class mp285(bMotor):
	def __init__(self, port='COM4'):
		"""
		port: serial port, on windows like 'COM5'

		linen sutter is COM4
		"""
		bMotor.__init__(self, type='mp285')
		self.swapxy = True
		
		self.verbose = True

		self.eol = '\r'
		self.port = port
		self.baud = 9600
		self.timeout = 5 # second

		self.stepSize = 0.04
		#self.stepSize = 0.2

		self.ser = None

		#todo: make interface so user can set this
		ok = self.setVelocity('medium')

		'''
		self.open()
		print('reading 1')
		r1 = self.ser.read(1)
		print('  r1:', r1)
		print('reading 2')
		r2 = self.ser.read(1)
		print('  r2:', r2)
		print('mp285.__init__() done')
		self.close()
		'''

	def open(self):
		if self.ser is not None:
			print('mp285.open(), port already opened')
		else:
			try:
				self.ser = serial.Serial(port=self.port, baudrate=self.baud,
					bytesize=serial.EIGHTBITS,
					parity=serial.PARITY_NONE,
					stopbits=serial.STOPBITS_ONE,
					timeout=self.timeout)
			#except (FileNotFoundError) as e:
			#	print('\nexception: mp285.open() FileNotFoundError')
			#	print('  e:', e)
			#	print(traceback.format_exc())
			#	raise
			except (serial.SerialException) as e:
				print('\nexception: mp285.open() serial.SerialException')
				print('  e:', e)
				return False
				#print(traceback.format_exc())
				#raise
			except:
				print('\nexception: mp285.open() UNKNOWN')
				print(traceback.format_exc())
				return False
				#raise

		return True

	def close(self):
		if self.ser is None:
			print ('mp285.close(), port not opened')
		else:
			self.ser.close()
			self.ser = None

	def setVelocity(self, fastSlow, openPort=True):
		"""
		fastSlow: in ('fast', 'medium', 'slow')

		Returns:
			true/false

		Note: The lower 15 bits (Bit 14 through 0) contain
		the velocity value. The high-order bit (Bit 15) is
		used to indicate the microstep-to-step resolution:
			0= 10, 1 = 50 uSteps/step

		Constant kFastVelocity = 30000
		Constant kSlowVelocity = 1500

		theVel = kFastVelocity
		//set bit 15 to 0
		theVel = theVel & ~(2^15)
		//set bit 15 to 1
		theVel = theVel | (2^15)

		Variable outType = 0 //unsigned short (16-bit) integer
		outType = outType | (2^4) //16-bit integer
		outType = outType | (2^6) //unsigned

		velocity: u-steps/second from 1000-10000
			(1000 is accurate, 7000 is not)
		"""
		def set_bit(value, bit):
			return value | (1<<bit)

		if fastSlow == 'fast':
			theVelocity = 30000
		elif fastSlow == 'medium':
			theVelocity = 6000 #3000
		elif fastSlow == 'slow':
			theVelocity = 1500
		else:
			logger.info(f'mp285.setVelocity() did not understand fastSlow: {fastSlow}')
			return False

		print('mp285.setVelocity() fastSlow:', fastSlow, 'theVelocity:', theVelocity)

		bVelocity = '{:b}'.format(theVelocity)
		#print('before set bit 15 bVelocity:', bVelocity)

		#velb = struct.pack('H',int(theVelocity))
		theVelocity = set_bit(theVelocity, 15)

		bVelocity = '{:b}'.format(theVelocity)
		#print(' after set bit 15 bVelocity:', bVelocity)

		# > is big-endian
		# < is little endian
		# H: unsigned short
		binaryVelocity = struct.pack('<H', theVelocity)

		if openPort and not self.open():
			return False

		try:
			self.ser.write(b'V' + binaryVelocity + b'\r')
			self.ser.read(1)
		except:
			print('exception: mp285.setVelocity() UNKNOWN')
			print(traceback.format_exc())
			return False
		finally:
			if openPort:
				self.close()

		return True

	def readPosition(self, openPort=True, verbose=True):
		if verbose:
			print ('mp285.readPosition() openPort:', openPort, 'verbose:', verbose)

		theRet = (None, None, None)

		if openPort and not self.open():
			return theRet

		try:
			self.ser.write(b'c\r')

			resp = self.ser.read(13) # 12 +1 (3 4-byte signed long numbers + CR)
			resp = resp.rstrip() # strip of trailing '\r'

			if len(resp) == 0:
				print('  warning: mp285.readPosition() did not get resp')
			elif b'\t' in resp:
				# occasional error
				print('  error: mp285.readPosition()  resp contained "\\t" resp:', resp)
			elif b'%' in resp:
				# occasional error
				print('  error: mp285.readPosition()  resp contained "%" resp:', resp)
			else:
				# > is big-endian
				# < is little endian
				stepTuple = struct.unpack('<lll', resp) # < is little-endian
				micronList = [x*self.stepSize for x in stepTuple]
				theRet = (micronList[0], micronList[1], micronList[2])
		except:
			print('exceptiopn: mp285.readPosition() UNKNOWN')
		finally:
			if openPort: self.close()

		if verbose:
			print('  mp285.readPosition() returning:', theRet)
		return theRet

	def moveto(self, direction, umDistance):
		return self.move(direction, umDistance)

	def move(self, direction, umDistance, openPort=True):
		"""
		direction: str:  in ['left', 'right', 'front', 'back']
		umDistance: int: Not sure on units yet
		"""

		print('=== mp285.moveto() direction:', direction, 'umDistance:', umDistance)

		theRet = (None, None, None)

		if openPort and not self.open():
			return theRet

		try:

			(x,y,z) = self.readPosition(openPort=False)
			print('  mp285.move() original position:', x, y, z)

			if x is None or y is None or z is None:
				print('  error: mp285.move() did not get good original position')
				return theRet

			# todo: these need to map to correct direction when looking at video
			if direction == 'left':
				y -= umDistance
			elif direction == 'right':
				y += umDistance
			elif direction == 'front':
				x += umDistance
			elif direction == 'back':
				x -= umDistance
			elif direction == 'up':
				# polarity is correct?
				z -= umDistance
			elif direction == 'down':
				# polarity is correct
				z += umDistance

			print('  moving to new position:', x, y, z)

			# convert um to step
			x = int(x / self.stepSize)
			y = int(y / self.stepSize)
			z = int(z / self.stepSize)

			xyzb = struct.pack('lll',x,y,z) # convert integer values into bytes
			startt = time.time() # start timer
			self.ser.write(b'm' + xyzb + b'\r') # send position to controller; add the "m" and the CR to create the move command

			cr = []
			cr = self.ser.read(1) # read carriage return and ignore
			endt = time.time() # stop timer

			if len(cr)== 0:
				print('  mp285.moveto() did not finish moving before timeout (%d sec).' % self.timeout)
			else:
				print('  mp285.moveto(): move completed in (%.2f sec)' % (endt-startt))

			print('  after move, reading again')
			theRet = self.readPosition(openPort=False)
			print('  final position:', x, y, z)

		except:
			print('exception: mp285.moveto() UNKNOWN')

		finally:
			if openPort: self.close()

		return theRet

if __name__ == '__main__':
	m = mp285()

	#m.setVelocity('fast')

	(x,y,z) = m.readPosition()
	print('  __main__ readPosition() x:', x, 'y:', y, 'z:', z)

	(x,y,z) = m.moveto('left', 500)
	print('  __main__ after moveto() x:', x, 'y:', y, 'z:', z)
