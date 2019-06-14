import sys
import bioformats
import javabridge

import bStack

#print('bioformats.JARS:', bioformats.JARS)

path = sys.argv[1]
print('path:', path)

files = bioformats.JARS
for file in files:
	print(file)
	
with javabridge.vm(
		run_headless=True,
		class_path=bioformats.JARS
		):
	print(1)
