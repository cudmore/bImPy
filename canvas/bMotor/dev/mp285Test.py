"""
at hopkins 20200916

test mp285 serial
"""

import os, sys, time

# used pip install pyserial, but import is serial?
import serial 
import struct

def moveTo(x,y,z):
	stepMult = 0.04
	
	x = int(x /= stepMult
	y = int(y /= stepMult
	z = int(z /= stepMult
	
	xyzb = struct.pack('lll',x, y, z) # convert integer values into bytes
	startt = time.time() # start timer
	self.ser.write('m'+xyzb+'\r') # send position to controller; add the "m" and the CR to create the move command
	cr = []
	cr = self.ser.read(1) # read carriage return and ignore
	endt = time.time() # stop timer
	if len(cr)== 0:
		print('Sutter did not finish moving before timeout (%d sec).' % self.timeOut)
	else:
		print('sutterMP285: Sutter move completed in (%.2f sec)' % (endt-startt))

def mp285Test():
	print('mp285Test()')
	
	#port = 'COM3'
	port = 'COM4' # seems to be correct?
	baud = 9600 #1200 #9600 #19200
	eolStr = '\r'
	timeOut = 3 # timeout in sec
	
	#ser = serial.Serial(port, baud, timeout=2)  # open serial port
	
	print('  opening serial with serial.Serial')
	try:
		#ser = serial.Serial(port='COM4',baudrate=baud,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=timeOut)
		ser = serial.Serial(port=port, baudrate=baud, bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=timeOut)
	except:
		print('Exception: mp285Test() serial.Serial')
	finally:
		pass
	
	print('  ser:', ser)
	
	#time.sleep(1)
	
	
	# this works
	#ser.write(b'r') # r: Reset Controller, returns nothing
	
	# c: Get Current Position
	# returns: xxxxyyyyzzzzCR three signed long (32-bit) integers + 0Dh
	print('  writing: c')
	ser.write(b'c') 
	 
	'''
	print('flush')
	ser.flush() # Flush of file like objects. In this case, wait until all data is written.
	'''
	
	# x/y/z, 4 bytes for each
	# units are 'steps', convert to um by * 0.04
	#resp = ser.read(4)
	print('  reading resp')
	#resp = ser.readline()
	resp = ser.read(13) # 12 +1 (3 4-byte signed long numbers + CR)
	resp = resp.rstrip() # strip of trailing '\r'

	print('    resp:', resp) #  b'\xff\xdb\xb9\xff\xfa+\xba\xffW\x98\t\xff\r'
	
	if resp:
		pass
	else:
		print('  did not get resp')
		sys.exit()
	
	if b'\t' in resp:
		# occasional error
		print('error: resp contained "\t" resp:', resp)
		sys.exit()
	if b'%' in resp:
		# occasional error
		print('error: resp contained "\t" resp:', resp)
		sys.exit()
		
	nBytes = len(resp)
	print('  nBytes:', nBytes)
	
	'''
	xBin = resp[0:4]
	xStep = struct.unpack('l', xBin)[0]
	xUm = xStep * 0.04
	xUm2 = xStep / 0.04
	
	print('just x')
	print('  xBin:', xBin)
	print('  xStep:', xStep)
	print('  xUm:', xUm)
	print('  xUm2:', xUm2)
	'''
	
	# > is big-endian
	# < is little endian
	# mp285 responds with little endian
	print('little-endian')	
	stepTuple = struct.unpack('<lll', resp)
	micronList = [x*0.04 for x in stepTuple]
	
	print('  stepTuple:', stepTuple)
	print('  micronList:', micronList)
	
			
	'''
	i = int.from_bytes(resp, byteorder='big', signed=True)
	print('  i:', i)
	i *= 0.04
	print('  i*0.04', i)
	'''
	
	ser.close()
	
def mp285Reset():
	ser.write(b'r') # r: Reset Controller, returns nothing

if __name__ == '__main__':
	mp285Test()