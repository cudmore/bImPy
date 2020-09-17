
"""

r: reset display

s: status

"""

"""
status
"""
VDTWrite2("s\r") //ask for Status, return (32 bytes)CR, remember, 32 bytes is 8 long integers

VDTReadBinary2/O=1.0/Q /B /TYPE=(0x20) statusVar
VDTReadBinary2/O=1.0/Q /TYPE=(0x20) CarrRetVar

"""
this returns a constant scale
"""
Variable currScale = mp285_GetScale()

"""
move to x/y/z
"""

String portStr = mp285_GetPort()
Variable currScale = mp285_GetScale() // 0.04

Variable moveToXustep = moveToX / currScale //um to ustep
Variable moveToYustep = moveToY / currScale //um to ustep
Variable moveToZustep = moveToZ / currScale //um to ustep

// 06Dh + three signed long (32-bit) integers + 0Dh
VDTWrite2("m")

VDTWriteBinary2 /O=1.0/B /TYPE=(0x20) moveToYustep,moveToXustep,moveToZustep
VDTWriteBinary2/O=1.0/TYPE=(0x08) constCR

VDTReadBinary2/O=1.0/Q /TYPE=(0x08) gLastCarrRetVar	 //read off final CR, it is a byte which is an 8-bit integer

"""
read pos
"""
VDTWrite2("c\r") //ask for position, return xxxxyyyyzzzzCR

Variable returnType = 0
returnType = returnType | (2^5) //signed long integer (32-bit), see wavetype

Variable posXustep, posYustep, posZustep

#my x is left/right --->>> corresponds to Y on controller
#my y is front/back --->>> corresponds to X on controller

#X and Y are swapped
VDTReadBinary2/O=1.0/Q /B /TYPE=(returnType) posYustep, posXustep, posZustep
VDTReadBinary2/O=1.0/Q /TYPE=(0x08) gLastCarrRetVar	 //read off final CR, it is a byte which is an 8-bit integer

if (gLastCarrRetVar != 13) //we got a CR
	if (mp285_Verbose())
		print "ERROR: mp285_ReadPosition() got badreturn character =", gLastCarrRetVar
	endif
	ok = 0
else
	//multiply by 0.04 to convert from usteps to um (currScale=0.04)
	posXum = posYustep * currScale //ustep to um
	posYum = posXustep * currScale
	posZum = posZustep * currScale
