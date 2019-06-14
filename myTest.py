"""
Important:
    This will not work in an Anaconda/Conda environment.
    Please use a stock install of Python 3

Install:

Download and install java development kit (jdk).

    https://www.oracle.com/technetwork/java/javase/downloads/jdk12-downloads-5295953.html

Need to make sure JAVA_HOME is defined from terminal prompt

    echo export "JAVA_HOME=\$(/usr/libexec/java_home)" >> ~/.bash_profile

The source code linked here was useful in figuring that out

    https://github.com/LeeKamentsky/python-javabridge/blob/master/javabridge/locate.py


    pip3 install javabridge
    pip3 install python-bioformats

"""


javabridge.start_vm(class_path=bioformats.JARS)

myPath = '/Volumes/fourt0/Dropbox/data/arsalan/20190416/20190416_b_0021.oir'
myPath = '/Users/cudmore/Dropbox/data/arsalan/20190416/20190416_b_0021.oir'

metaData = bioformats.get_omexml_metadata(path=myPath)
#print('metaData:', metaData)

myOmeXml = bioformats.OMEXML(metaData)

'''
print(myOmeXml)
import xml.dom.minidom
dom = xml.dom.minidom.parseString(str(myOmeXml))
print(dom.toprettyxml())
'''

print('Date/Time', myOmeXml.image().AcquisitionDate)
print('image_count:', myOmeXml.image_count)
print('channel_count:', myOmeXml.image().Pixels.channel_count)
print('channel name', myOmeXml.image().Pixels.Channel(0).Name)
print('pixel type:', myOmeXml.image().Pixels.get_PixelType()) # not real, default to 16 bit
print('units', myOmeXml.image().Pixels.PhysicalSizeXUnit) # string like 'um'
print('x um/pixel:', myOmeXml.image().Pixels.PhysicalSizeX) # um/pixel
print('y um/pixel:', myOmeXml.image().Pixels.PhysicalSizeY) # um/pixel
print('z um/pixel:', myOmeXml.image().Pixels.PhysicalSizeZ) # um/pixel
print('x pixels:', myOmeXml.image().Pixels.SizeX) # um/pixel
print('y pixels:', myOmeXml.image().Pixels.SizeY) # um/pixel
print('z pixels:', myOmeXml.image().Pixels.SizeZ) # um/pixel

print('Objective LensNA:', myOmeXml.instrument().Objective.LensNA) # um/pixel
# i want to get detector gain???
print('Detector Gain:', myOmeXml.instrument().Detector.node.get("Gain")) # um/pixel
print('Detector Voltage:', myOmeXml.instrument().Detector.node.get("Voltage")) # um/pixel

def qn(namespace, tag_name):
    '''Return the qualified name for a given namespace and tag name
    This is the ElementTree representation of a qualified name
    '''
    return "{%s}%s" % (namespace, tag_name)

try:
    instrumentObject = myOmeXml.instrument()
    print('instrumentObject:', instrumentObject)
    # laserElement is a 'xml.etree.ElementTree.Element'
    laserElement = instrumentObject.node.find(qn(instrumentObject.ns['ome'], "Laser"))
    print('laser:', laserElement.get("Wavelength"))

    significantbits = myOmeXml.image().Pixels.node.get("SignificantBits")
    print('significantbits:', significantbits)

except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

# now, how do i get something like this
#zoom = myOmeXml.StructuredAnnotations.get_original_metadata_value(key='20190416_b_0001.oir area zoom #1')
#print('zoom:', zoom)
'''
print('structured_annotations:', myOmeXml.structured_annotations)
myKey = '20190416_b_0001.oir speedInformation lineSpeed #3'
print(myOmeXml.structured_annotations.get_original_metadata_value(myKey))
print(myOmeXml.structured_annotations.OriginalMetadata)
'''

import xml.etree.ElementTree as ET
root = ET.fromstring(str(myOmeXml))
i=0
for child in root:
    if child.tag.endswith('StructuredAnnotations'):
        #print('child:', child) #child.attr
        for grandchild in child:
            #print('   grandchild:', grandchild.attrib)
            for greatgrandchild in grandchild:
                #print('      greatgrandchild:', greatgrandchild)
                #print(greatgrandchild.keys())
                for greatgreatgrandchild in greatgrandchild:
                    i+=1
                    #print(i, 'greatgreatgrandchild:', greatgreatgrandchild[0].text)
                    finalKey = greatgreatgrandchild[0].text
                    finalValue = greatgreatgrandchild[1].text
                    if 'area zoom' in finalKey:
                        print(finalKey, finalValue)
                    if 'speedInformation lineSpeed' in finalKey:
                        print(finalKey, finalValue)
                    if 'speedInformation seriesInterval' in finalKey:
                        print(finalKey, finalValue)
                    if 'imageDefinition bitCounts' in finalKey:
                        print(finalKey, finalValue)
                    if 'speedInformation pixelSpeed' in finalKey:
                        print(finalKey, finalValue)
                    if 'speedInformation frameSpeed' in finalKey:
                        print(finalKey, finalValue)
                    if 'configuration scannerType' in finalKey:
                        print(finalKey, finalValue)


'''
		<ome:XMLAnnotation ID="Annotation:482" Namespace="openmicroscopy.org/OriginalMetadata">
			<ome:Value>
				<ome:OriginalMetadata>
					<ome:Key>20190416_b_0001.oir speedInformation lineSpeed #3</ome:Key>
					<ome:Value>0.06337135614702154</ome:Value>
				</ome:OriginalMetadata>
			</ome:Value>
		</ome:XMLAnnotation>
'''

javabridge.kill_vm()
