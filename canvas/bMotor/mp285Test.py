"""
at hopkins 20200916

test mp285 serial
"""

import os, sys

# used pip install pyserial, but import is serial?
import serial 
import struct

def mp285Test():
	print('mp285Test()')
	
	port = 'COM4'
	baud = 9600 #19200
	eolStr = '\r'
	
	#ser = serial.Serial(port, baud, timeout=2)  # open serial port
	
	verbose = 1. # level of messages
	timeOut = 30 # timeout in sec
	try:
		ser = serial.Serial(port='COM4',baudrate=9600,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=timeOut)
	except:
		print('xxx eception')
		
	# this works
	#ser.write(b'r') # r: Reset Controller, returns nothing
	
	# c: Get Current Position
	# returns: xxxxyyyyzzzzCR three signed long (32-bit) integers + 0Dh
	ser.write(b'c') 
	 
	ser.flush() # Flush of file like objects. In this case, wait until all data is written.
	 
	# x/y/z, 4 bytes for each
	# units are 'steps', convert to um by * 0.04
	#resp = ser.read(4)
	resp = ser.readline()
	resp = resp.rstrip() # strip of trailing '\r'

	print('  resp:', resp) #  b'\xff\xdb\xb9\xff\xfa+\xba\xffW\x98\t\xff\r'
	
	nBytes = len(resp)
	print('  nBytes:', nBytes)
	
	b1 = resp[0:4]
	b2 = resp[5:8]
	b3 = resp[9:12]
	
	print(b1,b2,b3)
	
	# > is big-endian
	# < is little endian
	stepTuple = struct.unpack('>lll', resp)
	micronList = [x/0.04 for x in stepTuple]
	micronList2 = [x*0.04 for x in stepTuple]
	print('stepTuple:', stepTuple)
	print('micronList:', micronList)
	print('micronList2:', micronList2)
	
	
			
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