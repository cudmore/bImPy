# Author: Robert Cudmore
# Date: 20190424

"""
Load converted headers with bStackHeader._loadHeaderFromConverted(scopeFIlePath)

Converted header .txt file is in json format and looks like this

{
    "path": "/Users/cudmore/box/data/testoir/20190514_0001.oir",
    "date": "2019-05-14",
    "time": "15:43:24.544-07:00",
    "olympusFileVersion": "2.1.2.3",
    "olympusProgramVersion": "2.3.1.163",
    "laserWavelength": "920.0",
    "laserPercent": "7.7",
    "pmtGain1": "1.0",
    "pmtOffset1": "0",
    "pmtVoltage1": "557",
    "pmtGain2": "1.0",
    "pmtOffset2": "0",
    "pmtVoltage2": "569",
    "pmtGain3": "1.0",
    "pmtOffset3": "0",
    "pmtVoltage3": "557",
    "scanner": "Galvano",
    "zoom": "2.0",
    "bitDepth": 16,
    "numChannels": 1,
    "stackType": "TSeries",
    "xPixels": 218,
    "yPixels": 148,
    "numImages": 200,
    "numFrames": 200,
    "xVoxel": 0.497184455521791,
    "yVoxel": 0.497184455521791,
    "zVoxel": 1.0,
    "umWidth": 73.58329941722508,
    "umHeight": 108.38621130375044,
    "frameSpeed": "307.19",
    "lineSpeed": "1.39",
    "pixelSpeed": "0.002",
    "xMotor": null,
    "yMotor": null,
    "zMotor": null
}
"""

import os, sys, json
from collections import OrderedDict
from pprint import pprint

import tifffile

#import javabridge
try:
    import bioformats
except (ImportError) as e:
    #print('bImPy bStackHeader Exception: bStackHeader failed to import bioformats e:', e)
    bioformats = None

import xml
import xml.dom.minidom # to pretty print

import bimpy
#from bimpy import bFileUtil

import logging
logger = logging.getLogger('bStackHeader')

class bStackHeader:

    def __init__(self, path=''):

        logger.info('constructor')

        self.path = path

        self.initHeader()

        fu = bimpy.bFileUtil()
        convertedStackHeaderPath = fu.getHeaderFileFromRaw(self.path)
        if convertedStackHeaderPath is not None:
            # read from converted stack header .txt file
            self._loadHeaderFromConverted(convertedStackHeaderPath)
        elif path.endswith('.oir'):
            if bioformats is None:
                print('error: bioformats was not imported, will not open .oir file')
            else:
                self.readOirHeader()
        else:
            #print('warning: bStackHeader.__init__() did not load header')
            self.loadHeader()

    def print(self):
        print('  bStackHeader.print()', self.path)
        printTheseKeys = ['path', 'type', 'numChannels', 'numImages', 'xVoxel', 'yVoxel', 'zVoxel', 'xMotor', 'yMotor', 'zMotor']
        allKeys = True
        for k,v in self.header.items():
            if allKeys or k in printTheseKeys:
                print('  ', k, ':', v)
    '''
    def getHeaderFromDict(self, igorImportDict):
        """
        Used to import video from Igor canvas
        theDict: created in bCanvas.importIgorCanvas()
        """
        fullFileName = os.path.basename(self.path)
        baseFileName, extension = os.path.splitext(fullFileName)
        if baseFileName in igorImportDict.keys():
            self._header = igorImportDict[baseFileName] # may fail
        else:
            print('bStack.getHeaderFromDict() did not find imported header information for file:', self.path)
    '''

    def importVideoHeaderFromIgor(self, igorImportDict):
        print('importVideoHeaderFromIgor()')
        fullFileName = os.path.basename(self.path)
        baseFileName, extension = os.path.splitext(fullFileName)
        if baseFileName in igorImportDict.keys():
            self.header = igorImportDict[baseFileName].header # may fail
            print('   self.header:', self.header)
        else:
            print('bStackHeader.importVideoHeaderFromIgor() did not find imported header information for file:', self.path)

    @property
    def fileName(self):
        return os.path.basename(self.header['path'])
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
    @property
    def zVoxel(self):
        return self.header['zVoxel']
    @property
    def zoom(self):
        return self.header['zoom']
    @property
    def umWidth(self):
        return self.header['umWidth']
    @property
    def umHeight(self):
        return self.header['umHeight']
    @property
    def xMotor(self):
        return self.header['xMotor']
    @property
    def yMotor(self):
        return self.header['yMotor']
    @property
    def bitDepth(self):
        # get rid of this 'if', I am switching everything to use 'bitDepth'
        if 'bitDepth' in self.header.keys():
            bitDepth = self.header['bitDepth']
        elif 'bitsPerPixel' in self.header.keys():
            bitDepth = self.header['bitsPerPixel']
        if type(bitDepth) == str:
            # todo: put this back in
            #print('   error: bStackHeader.bitDepth @property found str bitDepth/bitsperpixel: ""', bitDepth, '"', self.path)
            bitDepth = int(bitDepth)
        if bitDepth is None or bitDepth=='':
            # todo: put this back in
            #print('   error: bStackHeader.bitDepth @property got bad (None or "") bitDepth:', bitDepth, 'returning 8, path:', self.path)
            bitDepth = 8
        #print('type(bitDepth):', type(bitDepth), bitDepth, self.path)
        return bitDepth
        #print('bStackHeader.bitDepth NEVER WORKS, RETURNING 8')
        #return 8

    def loadHeader(self):
        self.initHeader()

        verbose = False
        debug = False

        if debug:
            print('\nbStackHeader.loadHeader()', self.path)

        # make sure this works, if not, then bail
        try:
            with tifffile.TiffFile(self.path) as tif:
                pass
        except(tifffile.TiffFileError) as e:
            print('\n\n EXCEPTION: bStackHeader.loadHeader() e:', e)
            print('  self.path:', self.path, '\n\n')
            return

        with tifffile.TiffFile(self.path) as tif:
            isScanImage = tif.is_scanimage

            xVoxel = 1
            yVoxel = 1
            zVoxel = 1
            numChannels = 1

            try:
                tag = tif.pages[0].tags['XResolution']
                if tag.value[0]>0 and tag.value[1]>0:
                    xTag_value_1 = tag.value[1] # debug
                    xTag_value_0 = tag.value[0]
                    xVoxel = tag.value[1] / tag.value[0]
                    if isScanImage:
                        xVoxel *= 1e4
                else:
                    print('   bStackHeader.loadHeader() error, got zero tag value?')
                if verbose: print('   bStackHeader.loadStack() xVoxel from TIFF XResolutions:', xVoxel)
            except (KeyError) as e:
                print('warning: bStackHeader.loadHeader() did not find XResolution')

            try:
                tag = tif.pages[0].tags['YResolution']
                if tag.value[0]>0 and tag.value[1]>0:
                    yTag_value_1 = tag.value[1] # debug
                    yTag_value_0 = tag.value[0]
                    yVoxel = tag.value[1] / tag.value[0]
                    if isScanImage:
                        yVoxel *= 1e4
                else:
                    print('   bStackHeader.loadHeader() error, got zero tag value?')
                if verbose: print('   bStackHeader.loadStack() yVoxel from TIFF YResolutions:', yVoxel)
            except (KeyError) as e:
                print('warning: bStackHeader.loadHeader() did not find YResolution')

            # HOLY CRAP, FOUND IT QUICK
            imagej_metadata = tif.imagej_metadata
            
            # print('=== loadheader() imagej_metadata:')
            # pprint(imagej_metadata)
            
            if imagej_metadata is not None:
                #print('bStackHeader.imread() xxx yyy imagej_metadata:', imagej_metadata)
                try:
                    #print('    imagej_metadata["spacing"]:', imagej_metadata['spacing'], type(imagej_metadata['spacing']))
                    zVoxel = imagej_metadata['spacing']
                except (KeyError) as e:
                    logger.error('warning: bStackHeader.loadHeader() did not find "spacing" key')

            '''
            tag = tif.pages[0].tags['ResolutionUnit']
            print('ResolutionUnit:', tag.value)
            '''

            numImages = len(tif.pages)

            tag = tif.pages[0].tags['ImageWidth']
            xPixels = tag.value
            tag = tif.pages[0].tags['ImageLength']
            yPixels = tag.value

            umWidth = yPixels * yVoxel
            umHeight = xPixels * xVoxel

            # in fiji is voxel 0.0790972
            # here 7.909722626209259e-06
            if debug:
                print(f'  isScanImage {isScanImage}')
                print(f'  xVoxel {xVoxel} xTag_value_1 {xTag_value_1}  / xTag_value_0 {xTag_value_0}')
                print(f'  yVoxel {yVoxel} yTag_value_1 {yTag_value_1}  / yTag_value_0 {yTag_value_0}')
                print(f'  xPixels {xPixels} yPixels {yPixels}')
                print(f'  umWidth {umWidth} umHeight {umHeight}')
                print(f'  numImages {numImages}')
                print('\n')

        self.header['stackType'] = 'Tiff'

        self.header['xPixels'] = xPixels
        self.header['yPixels'] = yPixels
        self.header['numChannels'] = numChannels
        self.header['numImages'] = numImages
        self.header['numFrames'] = None
        #
        print('    bStackHeader.loadHeader() got xVoxel:', xVoxel, 'yVoxel:', yVoxel)
        self.header['xVoxel'] = xVoxel # um/pixel
        self.header['yVoxel'] = yVoxel
        self.header['zVoxel'] = zVoxel

        # 20200915, this will both OVERWRITE and CONTAMINATE (with ImageJ info)
        # 20220805, tifffile.imsave with met_dataseems to lowercase all keys in the dict
        '''
        if imagej_metadata is not None:
            for k,v in imagej_metadata.items():
                self.header[k] = v
        '''
        if 'xmotor' in imagej_metadata.keys():
            self.header['xMotor'] = imagej_metadata['xmotor']
        if 'ymotor' in imagej_metadata.keys():
            self.header['yMotor'] = imagej_metadata['ymotor']
        if 'zmotor' in imagej_metadata.keys():
            self.header['zMotor'] = imagej_metadata['zmotor']
            
        if 'seconds' in imagej_metadata.keys():
            self.header['seconds'] = imagej_metadata['seconds']

        if isScanImage:
            # sets numChannels
            self.loadScanImageHeader()

        if yPixels is not None and yVoxel is not None:
            self.header['umWidth'] = yPixels * yVoxel
        else:
            self.header['umWidth'] = None

        if xPixels is not None and xVoxel is not None:
            self.header['umHeight'] = xPixels * xVoxel
        else:
            self.header['umHeight'] = None

        # print('    FINAL HEADER IS:')
        # pprint(self.header)


    def loadScanImageHeader(self):
        with tifffile.TiffFile(self.path) as f:
            isScanImage = f.is_scanimage
            if not isScanImage:
                print('error: bStackHeader.xxx() is not a ScanImage file:', self.path)
            else:
                self.header['stackType'] = 'ScanImage'

                scanimage_metadata = f.scanimage_metadata

                k2 = 'SI.VERSION_MAJOR'
                VERSION_MAJOR = scanimage_metadata['FrameData'][k2]
                self.header['si_VERSION_MAJOR'] = VERSION_MAJOR

                k2 = 'SI.VERSION_MINOR'
                VERSION_MINOR = scanimage_metadata['FrameData'][k2]
                self.header['si_VERSION_MINOR'] = VERSION_MINOR

                k2 = 'SI.hChannels.channelSave' # like [[1], [2]]
                channelSave = scanimage_metadata['FrameData'][k2]
                numChannels = len(channelSave)
                self.header['numChannels'] = numChannels

                '''
                k2 = 'SI.hStackManager.numSlices'
                numSlices = scanimage_metadata['FrameData'][k2]
                self.header['numImages'] = numChannels
                '''

                k2 = 'SI.hChannels.channelAdcResolution'
                bitDepth = scanimage_metadata['FrameData'][k2]
                bitDepth = bitDepth[0] # assuming all channels the same
                self.header['bitDepth'] = bitDepth

                #k2 = 'SI.hRoiManager.linesPerFrame'
                #linesPerFrame = scanimage_metadata['FrameData'][k2]

                #k2 = 'SI.hRoiManager.pixelsPerLine'
                #pixelsPerLine = scanimage_metadata['FrameData'][k2]

                k2 = 'SI.hRoiManager.scanZoomFactor'
                zoom = scanimage_metadata['FrameData'][k2]
                self.header['zoom'] = zoom

                # SI.hMotors.motorPosition: [-186541, -180967, -651565]
                k2 = 'SI.hMotors.motorPosition'
                motorPosition = scanimage_metadata['FrameData'][k2]
                self.header['xMotor'] = motorPosition[0]
                self.header['yMotor'] = motorPosition[1]
                self.header['zMotor'] = motorPosition[2]

    def _loadHeaderFromConverted(self, convertedStackHeaderPath):
        """Load header from coverted header .txt file"""

        #print('bStackHeader._loadHeaderFromConverted() convertedStackHeaderPath:', convertedStackHeaderPath)
        # clear our existing header
        self.initHeader()

        with open(convertedStackHeaderPath, 'r') as f:
            self.header = json.load(f)

        '''
        print('bStackHeader._loadHeaderFromConverted() is loading header information from .txt file:', convertedStackHeaderPath)
        with open(convertedStackHeaderPath, 'r') as file:
            lines = file.readlines()
        # remove whitespace characters like `\n` at the end of each line
        lines = [x.strip() for x in lines]

        # clear our existing header
        self.initHeader()

        # parse what we just read
        for line in lines:
            lhs, rhs = line.split('=')
            self.header[lhs] = rhs

        ######
        ## FIX THIS
        ######
        #print('bStackHeader._loadHeaderFromConverted() *** TODO *** add umWidth and umHeight to original conversion !!!!!')
        #print('   also need to figure out str versus int versus float !!!!')
        # todo: add this to original python/fiji scripts that convert header
        # add (umWidth, umHeight)
        # x
        #if 'umWidth' not in self.header.keys():
        if 1:
            xPixels = int(self.header['xPixels'])
            xVoxel = float(self.header['xVoxel'])
            umWidth = xPixels * xVoxel
            self.header['umWidth'] = umWidth
        # y
        #if 'umHeight' not in self.header.keys():
        if 1:
            yPixels = int(self.header['yPixels'])
            yVoxel = float(self.header['yVoxel'])
            umHeight = yPixels * yVoxel
            self.header['umHeight'] = umHeight
        '''

    def prettyPrint(self):
        print('   file:', os.path.split(self.path)[1],
            'stackType:', self.stackType, ',', 'bitDepth:', self.bitDepth,
            'channels:', self.numChannels, ',',
            'images:', self.numImages, ',',
            'x/y pixels:', self.pixelsPerLine, '/', self.linesPerFrame, ',',
            'x/y um/pixel:', self.xVoxel, '/', self.yVoxel,
            'umWidth:', self.umWidth, 'umHeight:', self.umHeight,
            )

    def getMetaData(self):
        """Get all header items as text in a single line"""
        ijmetadataStr = ''
        for k, v in self.header.items():
            ijmetadataStr += k + '=' + str(v) + '\n'
        return ijmetadataStr

    def saveHeader(self, headerSavePath):
        """ Save the header as a .txt file to the path"""
        # todo: check that the path exists
        with open(headerSavePath, 'w') as fp:
            json.dump(self.header, fp, indent=4)

    def initHeader(self):

        self.header = OrderedDict()

        self.header['path'] = self.path # full path to the file
        self.header['filename'] = '' #added 20191115
        self.header['date'] = ''
        self.header['time'] = ''
        self.header['seconds'] = ''

        self.header['stackType'] = None
        self.header['numChannels'] = None
        self.header['bitDepth'] = None

        self.header['xPixels'] = None
        self.header['yPixels'] = None
        self.header['numImages'] = None
        self.header['numFrames'] = None
        #
        self.header['xVoxel'] = 1 # um/pixel
        self.header['yVoxel'] = 1
        self.header['zVoxel'] = 1

        self.header['umWidth'] = None
        self.header['umHeight'] = None

        self.header['zoom'] = None # optical zoom of objective

        # abb removed 20200915 working on canvas in Baltimore
        # maybe tiff headers should be dynamic based on file type?
        # with some key elements ['xVoxel', 'yVoxel', 'xMotor', 'yMotor', ...]
        '''
        self.header['laserWavelength'] = None #
        self.header['laserPercent'] = None #

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

        self.header['frameSpeed'] = None #
        self.header['lineSpeed'] = None # time of each line scan (ms)
        self.header['pixelSpeed'] = None #

        self.header['olympusFileVersion'] = '' # Of the Olympus software
        self.header['olympusProgramVersion'] = '' # Of the Olympus software
        '''

        self.header['xMotor'] = None
        self.header['yMotor'] = None
        self.header['zMotor'] = None


    def old_assignToShape(self, stack):
        """shape is (channels, slices, x, y)"""
        #print('=== === bStackHeader.assignToShape()')
        shape = stack.shape
        if len(shape)==3:
            # single plane image
            self.header['numChannels'] = shape[0]
            self.header['numImages'] = 1
            self.header['xPixels'] = shape[1]
            self.header['yPixels'] = shape[2]
        elif len(shape)==4:
            # 3d image volume
            self.header['numChannels'] = shape[0]
            self.header['numImages'] = shape[1]
            self.header['xPixels'] = shape[2]
            self.header['yPixels'] = shape[3]
        else:
            print('   error: bStackHeader.assignToShape() got bad shape:', shape)
        #print('self.header:', self.header)
        #bitDepth = self.header['bitDepth']
        bitDepth = self.bitDepth # this will trigger warning if not already assigned
        #if bitDepth is not None:
        if type(self.bitDepth) is not 'NoneType':
            #print('bStackHeader.assignToShape() bitDepth is already', self.bitDepth, type(self.bitDepth))
            pass
        else:
            dtype = stack.dtype
            if dtype == 'uint8':
                bitDepth = 8
            else:
                bitDepth = 16
            self.header['bitDepth'] = bitDepth

    def assignToShape2(self, stack):
        """shape is (channels, slices, x, y)"""
        #print('=== === bStackHeader.assignToShape()')
        shape = stack.shape
        if len(shape)==2:
            # single plane image
            #self.header['numChannels'] = shape[0]
            self.header['numImages'] = 1
            self.header['xPixels'] = shape[0]
            self.header['yPixels'] = shape[1]
        elif len(shape)==3:
            # 3d image volume
            #self.header['numChannels'] = shape[0]
            self.header['numImages'] = shape[0]
            self.header['xPixels'] = shape[1]
            self.header['yPixels'] = shape[2]
        else:
            print('   error: bStackHeader.assignToShape() got bad shape:', shape)
        #print('self.header:', self.header)
        #bitDepth = self.header['bitDepth']
        bitDepth = self.bitDepth # this will trigger warning if not already assigned
        #if bitDepth is not None:
        if type(self.bitDepth) is not 'NoneType':
            #print('bStackHeader.assignToShape() bitDepth is already', self.bitDepth, type(self.bitDepth))
            pass
        else:
            dtype = stack.dtype
            if dtype == 'uint8':
                bitDepth = 8
            else:
                bitDepth = 16
            self.header['bitDepth'] = bitDepth

    def readOirHeader(self):
        """
        Read header information from xml. This is not pretty.
        """
        print('    bStackHeader.readOirHeader() self.path:', self.path)

        def _qn(namespace, tag_name):
            '''
            xml helper. Return the qualified name for a given namespace and tag name
            This is the ElementTree representation of a qualified name
            '''
            return "{%s}%s" % (namespace, tag_name)

        try:

            #print('=== StackHeader.readOirHeader() log errors will be here')
            #
            #print('readOirHeader() self.path:', self.path)

            '''
            mjb = bimpy.bJavaBridge()
            mjb.start()
            '''

            if bioformats is None:
                print('ERROR: bStackHeader.readOirHeader() did not find package bioformats. Is it installed?')
                return

            metaData = bioformats.get_omexml_metadata(path=self.path)
            omeXml = bioformats.OMEXML(metaData)

            '''
            mjb.stop()
            '''

            # leave this here, will extract ome-xml as pretty printed string
            #print('omeXml:', omeXml.prettyprintxml())
            '''
            pretty_xml = xml.dom.minidom.parseString(str(omeXml))
            print(pretty_xml.toprettyxml())
            sys.exit()
            '''

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
            #print('    laserElement:',type(laserElement))
            if laserElement is not None:
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

            if self.header['numImages'] > 1:
                #print('--------- tmp setting -------- self.header["stackType"] = "ZStack"')
                self.header['stackType'] = 'ZStack' #'ZStack'

            # swap numFrames into numImages
            if self.header['numImages'] == 1 and self.header['numFrames'] > 1:
                self.header['numImages'] = self.header['numFrames']
                #print('--------- tmp setting -------- self.header["stackType"] = "TSeries"')
                self.header['stackType'] = 'TSeries'

            self.header['xVoxel'] = omeXml.image().Pixels.PhysicalSizeX # um/pixel
            self.header['yVoxel'] = omeXml.image().Pixels.PhysicalSizeY
            self.header['zVoxel'] = omeXml.image().Pixels.PhysicalSizeZ

            self.header['umWidth'] = self.header['xPixels'] * self.header['xVoxel']
            self.header['umHeight'] = self.header['yPixels'] * self.header['yVoxel']

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

                                # 20190617
                                """
                                <ome:OriginalMetadata>
                                    <ome:Key>20190613__0028.oir method sequentialType #1</ome:Key>
                                    <ome:Value>Line</ome:Value>
                                </ome:OriginalMetadata>
                                """
                                # removed 20191029, was not working
                                """
                                if 'method sequentialType' in finalKey:
                                    print(finalKey)
                                    print('   ', finalValue)
                                    print('--------- tmp setting -------- self.header["stackType"] = ', finalValue)
                                    self.header['stackType'] = finalValue
                                """

                                # 20190617, very specific for our scope
                                """
                                <ome:OriginalMetadata>
                                    <ome:Key>- Laser Chameleon Vision II transmissivity</ome:Key>
                                    <ome:Value>[9.3]</ome:Value>
                                </ome:OriginalMetadata>
                                """
                                if '- Laser Chameleon Vision II transmissivity' in finalKey:
                                    finalValue = finalValue.strip('[')
                                    finalValue = finalValue.strip(']')
                                    self.header['laserPercent'] = finalValue

                                if 'general creationDateTime' in finalKey:
                                    theDate, theTime = finalValue.split('T')
                                    self.header['date'] = theDate
                                    self.header['time'] = theTime

                                if 'fileInfomation version #1' in finalKey:
                                    self.header['olympusFileVersion'] = finalValue
                                if 'system systemVersion #1' in finalKey:
                                    self.header['olympusProgramVersion'] = finalValue

                                if 'area zoom' in finalKey:
                                    self.header['zoom'] = finalValue
                                if 'configuration scannerType' in finalKey:
                                    self.header['scanner'] = finalValue # in ('Resonant', 'Galvano')
                                if 'imageDefinition bitCounts' in finalKey:
                                    self.header['bitDepth'] = int(finalValue)

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

        except Exception as e:
            print('EXCEPTION in bStackHeader.readOirHeader()', e)
            raise
        finally:
            pass

if __name__ == '__main__':
    print('tifffile.__version__', tifffile.__version__)

    path = '/Users/cudmore/data/canvas/20200911/20200911_aaa/xy512z1zoom5bi_00001_00010.tif'
    path = '/Users/cudmore/data/canvas/20200914/20200914_ssslllaaa/20200914_ssslllaaa_video/v20200914_ssslllaaa_000.tif'
    sh = bStackHeader(path=path)
    for k,v in sh.header.items():
        print(k,':',v)
