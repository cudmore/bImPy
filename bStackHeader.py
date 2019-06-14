# Author: Robert Cudmore
# Date: 20190424

import os
from collections import OrderedDict

#import javabridge
import bioformats

import xml

class bStackHeader:

	def __init__(self, path):

		self.path = path

		self.initHeader()

		if path.endswith('.oir'):
			self.readOirHeader()

	@property
	def stackType(self):
		return self.header['stackType']
	@property
	def numChannels(self):
		return self.header['numChannels']
	@property
	def numImages(self):
		return self.header['numImages']
	@property
	def numFrames(self):
		return self.header['numFrames']
	@property
	def pixelsPerLine(self):
		return self.header['xPixels']
	@property
	def linesPerFrame(self):
		return self.header['yPixels']
	@property
	def xVoxel(self):
		return self.header['xVoxel']
	@property
	def yVoxel(self):
		return self.header['yVoxel']

	def prettyPrint(self):
		print('   file:', os.path.split(self.path)[1],
			'channels:', self.numChannels, ',',
			'images:', self.numImages, ',',
			'x/y pixels:', self.pixelsPerLine, '/', self.linesPerFrame, ',',
			'x/y um/pixel:', self.xVoxel, '/', self.yVoxel,
			)

	def getMetaData(self):
		ijmetadataStr = ''
		for k, v in self.header.items():
			ijmetadataStr += k + '=' + str(v) + '\n'
		return ijmetadataStr

	def saveHeader(self, headerSavePath):
		""" Save the header as a .txt file to the path"""

		# check that the path exists

		#print('   bStackHeader.saveHeader:', headerSavePath)
		with open(headerSavePath, 'w') as f:
			#f.write(str(self.header))
			'''
			for k,v in self.header.items():
				f.write(k + '=' + str(v) + '\n')
			headerData = self.header.getMetaData()
			'''
			# todo: add bStackHeader.save(path)
			for k, v in self.header.items():
				f.write(k + '=' + str(v) + '\n')

	def initHeader(self):

		self.header = OrderedDict()

		self.header['path'] = self.path
		self.header['date'] = ''
		self.header['time'] = ''

		self.header['fileVersion'] = '' # Of the Olympus software
		self.header['programVersion'] = '' # Of the Olympus software

		self.header['laserWavelength'] = None #

		# 1
		self.header['pmtGain1'] = None #
		self.header['pmtOffset1'] = None #
		self.header['pmtVoltage1'] = None #
		# 2
		self.header['pmtGain2'] = None #
		self.header['pmtOffset2'] = None #
		self.header['pmtVoltage2'] = None #
		# 3
		self.header['pmtGain3'] = None #
		self.header['pmtOffset3'] = None #
		self.header['pmtVoltage3'] = None #

		self.header['scanner'] = None

		self.header['zoom'] = None # optical zoom of objective

		self.header['bitsPerPixel'] = None

		self.header['numChannels'] = None

		self.header['stackType'] = None

		self.header['xPixels'] = None
		self.header['yPixels'] = None
		self.header['numImages'] = None
		self.header['numFrames'] = None
		#
		self.header['xVoxel'] = None # um/pixel
		self.header['yVoxel'] = None
		self.header['zVoxel'] = None

		self.header['frameSpeed'] = None #
		self.header['lineSpeed'] = None # time of each line scan (ms)
		self.header['pixelSpeed'] = None #

		self.header['xMotor'] = None
		self.header['yMotor'] = None
		self.header['zMotor'] = None

	def readOirHeader(self):
		"""
		Read header information from xml. This is not pretty.
		"""
		#print('=== bStack.readOirHeader()')

		def _qn(namespace, tag_name):
			'''
			xml helper. Return the qualified name for a given namespace and tag name
			This is the ElementTree representation of a qualified name
			'''
			return "{%s}%s" % (namespace, tag_name)

		try:

			#print('=== bStackHeader.readOirHeader() log errors will be here')
			#
			metaData = bioformats.get_omexml_metadata(path=self.path)
			omeXml = bioformats.OMEXML(metaData)

			# this does not work, always gives us time as late in the PM?
			'''
			dateTime = omeXml.image().AcquisitionDate
			print('dateTime:', dateTime)
			date, time = dateTime.split('T')
			self.header['date'] = date
			self.header['time'] = time
			'''

			instrumentObject = omeXml.instrument()
			laserElement = instrumentObject.node.find(_qn(instrumentObject.ns['ome'], "Laser")) # laserElement is a 'xml.etree.ElementTree.Element'
			self.header['laserWavelength'] = laserElement.get("Wavelength")

			# todo: how do i get info from detector 1 and 2 ???
			'''
			self.header['pmt1_gain'] = omeXml.instrument().Detector.node.get("Gain") #
			self.header['pmt1_offset'] = omeXml.instrument().Detector.node.get("Offset") #
			self.header['pmt1_voltage'] = omeXml.instrument().Detector.node.get("Voltage") #
			'''

			numChannels = omeXml.image().Pixels.channel_count
			self.header['numChannels'] = numChannels

			self.header['xPixels'] = omeXml.image().Pixels.SizeX # pixels
			self.header['yPixels'] = omeXml.image().Pixels.SizeY # pixels

			# todo: this is NOT working
			#self.header['numImages'] = omeXml.image_count

			self.header['numImages'] = omeXml.image().Pixels.SizeZ # number of images
			self.header['numFrames'] = omeXml.image().Pixels.SizeT # number of images

			self.header['stackType'] = 'ZStack'

			# swap numFrames into numImages
			if self.header['numImages'] == 1 and self.header['numFrames'] > 1:
				self.header['numImages'] = self.header['numFrames']
				self.header['stackType'] = 'TSeries'

			self.header['xVoxel'] = omeXml.image().Pixels.PhysicalSizeX # um/pixel
			self.header['yVoxel'] = omeXml.image().Pixels.PhysicalSizeY
			self.header['zVoxel'] = omeXml.image().Pixels.PhysicalSizeZ

			root = xml.etree.ElementTree.fromstring(str(omeXml))
			i=0
			pixelSpeed2, pixelSpeed3 = None, None
			lineSpeed2, lineSpeed3 = None, None
			frameSpeed2, frameSpeed3 = None, None
			for child in root:
				if child.tag.endswith('StructuredAnnotations'):
					for grandchild in child:
						for greatgrandchild in grandchild:
							for greatgreatgrandchild in greatgrandchild:
								i+=1
								finalKey = greatgreatgrandchild[0].text
								finalValue = greatgreatgrandchild[1].text

								if 'general creationDateTime' in finalKey:
									theDate, theTime = finalValue.split('T')
									self.header['date'] = theDate
									self.header['time'] = theTime

								if 'fileInfomation version #1' in finalKey:
									self.header['fileVersion'] = finalValue
								if 'system systemVersion #1' in finalKey:
									self.header['programVersion'] = finalValue

								if 'area zoom' in finalKey:
									self.header['zoom'] = finalValue
								if 'configuration scannerType' in finalKey:
									self.header['scanner'] = finalValue # in ('Resonant', 'Galvano')
								if 'imageDefinition bitCounts' in finalKey:
									self.header['bitsPerPixel'] = finalValue

								# channel 1
								if 'pmt gain #1' in finalKey:
									self.header['pmtGain1'] = finalValue
								if 'pmt offset #1' in finalKey:
									self.header['pmtOffset1'] = finalValue
								if 'pmt voltage #1' in finalKey:
									self.header['pmtVoltage1'] = finalValue
								# channel 2
								if 'pmt gain #2' in finalKey:
									self.header['pmtGain2'] = finalValue
								if 'pmt offset #2' in finalKey:
									self.header['pmtOffset2'] = finalValue
								if 'pmt voltage #2' in finalKey:
									self.header['pmtVoltage2'] = finalValue
								# channel 3
								if 'pmt gain #3' in finalKey:
									self.header['pmtGain3'] = finalValue
								if 'pmt offset #3' in finalKey:
									self.header['pmtOffset3'] = finalValue
								if 'pmt voltage #3' in finalKey:
									self.header['pmtVoltage3'] = finalValue

								# use #2 for Galvano, and #3 for Resonant
								if 'speedInformation pixelSpeed #2' in finalKey:
									pixelSpeed2 = finalValue
								if 'speedInformation pixelSpeed #3' in finalKey:
									pixelSpeed3 = finalValue
								if 'speedInformation lineSpeed #2' in finalKey:
									lineSpeed2 = finalValue
								if 'speedInformation lineSpeed #3' in finalKey:
									lineSpeed3 = finalValue
								if 'speedInformation frameSpeed #2' in finalKey:
									frameSpeed2 = finalValue
								if 'speedInformation frameSpeed #3' in finalKey:
									frameSpeed3 = finalValue

			if self.header['scanner'] == 'Galvano':
				self.header['pixelSpeed'] = pixelSpeed2
				self.header['lineSpeed'] = lineSpeed2
				self.header['frameSpeed'] = frameSpeed2
			if self.header['scanner'] == 'Resonant':
				self.header['pixelSpeed'] = pixelSpeed3
				self.header['lineSpeed'] = lineSpeed3
				self.header['frameSpeed'] = frameSpeed3

		finally:
			pass
