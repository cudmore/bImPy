
## Canvas

Canvas is a pure python application allowing images from two different light paths on a microscope to be visual/spatially displayed in an interactive canvas

## Install

1) nistall bImPy

pip install -e ../.

2) install canvas

pip install -r requirements.txt

## Javabridge (mac)

1) Download JDK (and maybe JRE)

2) Set JAVA_HOME to the correct path

see: https://github.com/LeeKamentsky/python-javabridge/issues/168?email_token=AAFBH5O4WSHTLYHZLG73SRDQJKEHTA5CNFSM4IWIFORKYY3PNVWWK3TUL52HS4DFUVEXG43VMWVGG33NNVSW45C7NFSM4HLCCG2A

```
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-11.0.8.jdk/Contents/Home
```

3) install

```
pip install javabridge
```
```
To use the "javac" command-line tool you need to install a JDK

see: https://www.oracle.com/java/technologies/javase-downloads.html

Java SE 11 (LTS)
Java SE 11.0.8 is the latest release for the Java SE 11 Platform

https://www.oracle.com/java/technologies/javase-jdk11-downloads.html

Java SE Development Kit 11.0.8

https://www.oracle.com/java/technologies/javase-jdk11-downloads.html

https://www.oracle.com/java/technologies/javase-jdk11-downloads.html#license-lightbox


```

```
java -version

# return
java version "11.0.8" 2020-07-14 LTS
Java(TM) SE Runtime Environment 18.9 (build 11.0.8+10-LTS)
Java HotSpot(TM) 64-Bit Server VM 18.9 (build 11.0.8+10-LTS, mixed mode)

```
## Screenshots

Example Canvas interface. This is another bad example, keep in tune as it will get better.

<!-- <IMG SRC="https://github.com/cudmore/bImPy/blob/master/docs/img/canvas-example.png"> -->
<IMG WIDTH=600 SRC="../docs/img/canvas-example.png">

## To Do

Write code to properly save tiff tags in video so we can then read them (use tifffile)
 
see here for code to do proper contrast adjustment

```
https://stackoverflow.com/questions/14464449/using-numpy-to-efficiently-convert-16-bit-image-data-to-8-bit-for-display-with
```

only available in Qt>=5.13, QtGui.QImage.Format_Grayscale16

this generally works, need to check bit depth of video images
```
image_stack = skimage.img_as_ubyte(image_stack, force_copy=False)
```

### todo notes

1) load as qimage (keep copy),
2) adjust brightness, second copy,
3) insert brightness adjusted into QPixmap/myGraphicsPixMapItem

