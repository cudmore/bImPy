## bImPy

**bImPy**, pronounced bimpee, is a collection of tools to manipulate images in Python. A primary use is to convert folders of proprietary image files to Tiff while extracting acquisition parameters for each file.

Right now (As of June 2018) this is primarily for Olympus OIR files.

This makes heavy use of [Python bio-formats][python-bio-formats] which in itself is excellent and is used by [Fiji][fiji]. Regretably, bio-formats requires [javabridge][javabridge]. If you run into problems it is probably due to your Java installation.

[python-bio-formats]: https://pythonhosted.org/python-bioformats/
[javabridge]: https://pythonhosted.org/javabridge/
[fiji]: http://fiji.sc

## Usage

**bConvertFolder_Headers.py** : Given the full path to a folder, convert just the headers of all files in the folder.

**bConvertFolder** : Given the full path to a folder, convert all files in the folder to Tiff.

**bConvertOir.py** : Convert a single OIR file.

**bStack.py** : Back end code to open, manipulate, and save image stacks.

**bStackHeader** : Back end code to read and write both proprietary and Tiff file headers.

## Known bugs

 - Will fail to convert OIR files with more than 1,000 images. [See the work the good people at bio-formats are doing to fix this][maxFrames].
 - Will fail to convert line scans with more than 512 lines. [See the work the good people at bio-formats are doing to fix this][lineScans]

 
[maxFrames]: https://forum.image.sc/t/problems-opening-olympus-oir-files-using-bio-formats/24747
[lineScans]: https://forum.image.sc/t/problems-opening-olympus-oir-line-scan-files/24957/7

## Important:

    This will not work in an Anaconda/Conda environment.
    Please use a stock install of Python 3

## Install on macOS:

 1. Download and install java development kit (jdk).

```
https://www.oracle.com/technetwork/java/javase/downloads/jdk12-downloads-5295953.html
```

 2. Need to make sure JAVA_HOME is defined from terminal prompt

```
echo export "JAVA_HOME=\$(/usr/libexec/java_home)" >> ~/.bash_profile
```

The source code linked here was useful in figuring that out

```
https://github.com/LeeKamentsky/python-javabridge/blob/master/javabridge/locate.py
```

 3. install python packages

```
pip3 install javabridge
pip3 install python-bioformats
```

## To install on windows 7 (good luck)

#### Please note, I could not get javabridge to work on Windows 7 and gave up.

Download and install Windows SDK

    https://www.microsoft.com/en-us/download/details.aspx?id=8279

File is: winsdk_web.exe

If that does not work, then try this

    https://dotnet.microsoft.com/download/dotnet-framework?utm_source=getdotnet2&utm_medium=referral

file is: ndp48-devpack-enu

Sometimes it still does not work, on 'pip install javabridge' I am getting jre not found

trying to reinstall jre

    https://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html

new i get 'pip install javabridge' error 'error: Source option 6 is no longer supported. Use 7 or later.'

Download jre 6 (like i did in sierra), file is named 'jdk-6u45-windows-x64.exe'

    https://www.oracle.com/technetwork/java/javase/downloads/java-archive-downloads-javase6-419409.html

Now, my c:\Program File\Java has 4x versions of java

 - jdk1.6.0_45
 - jdk-12
 - jre1.8.0_211
 - jre6
 
Nope, still trying to use jdk-12 and getting error 'Source option 6 is no longer supported. Use 7 or later.'
 
Make a 'new system variable'
 
```
JDK_HOME = C:\Program Files\Java\jdk1.6.0_45\bin\javac.exe
```

That did not work

Now, progress, uninstall java se and jdk 12 (leaving 6)

'pip install javabridge' get past 'source option 6' error but now has

```
 error: Microsoft Visual C++ 14.0 is required. Get it with "Microsoft Visual C++ Build Tools": https://visualstudio.microsoft.com/downloads/
 ```
 
Then download 'microsoft visual studio build tools 2019' file is named: vs_buildtools__1853314971.1556229002.exe

This download takes for fucking ever !!!!!!!!!!!!!!!!!!!

Now 'pip install javabridge' works

But running code that uses python-bioformats results in

```
javabridge.jutil.JavaException: loci/common/RandomAccessInputStream : Unsupported major.minor version 51.0
```

Try installing jre 12 again (will then not be able to re-install javabridge!!!)


 


## To install on macOS Sierra

Had to uninstall java and downgrade to java 6

    https://support.apple.com/kb/dl1572?locale=en_US

    https://updates.cdn-apple.com/2018/macos/031-33898-20171026-7a797e9e-b8de-11e7-b1fe-c14fbda7e146/javaforosx.dmg

See this post: http://notesbyanerd.com/2018/11/02/pip-install-cant-find-numpy-header/

```
import numpy as np
np.get_include()
# yields: '/usr/local/lib/python3.7/site-packages/numpy/core/include'
```

At command prompt

```
export CFLAGS="-I/usr/local/lib/python3.7/site-packages/numpy/core/include"
```

In python virtual environment it is at

```
/Users/cudmore/Dropbox/olympus/myBioformats/bio_env/lib/python3.7/site-packages/numpy/core/include
```


##

see: https://github.com/LeeKamentsky/python-javabridge/issues/78

I am getting a similar error on macOS Sierra (10.12). Using Python 3 and javabridge==1.0.18

```
import os
import javabridge

javabridge.start_vm(run_headless=True)
try:
    print(javabridge.run_script('java.lang.String.format("Hello, %s!", greetee);',dict(greetee='world')))
finally:
    javabridge.kill_vm()
```

Gives me the error:

```
Failed to open libjvm.dylib.

Traceback (most recent call last):
  File "/usr/local/lib/python3.7/site-packages/javabridge/jutil.py", line 277, in start_thread
    vm.create_mac(args, RQCLS, library_path, libjli_path)
  File "_javabridge.pyx", line 708, in _javabridge.JB_VM.create_mac
RuntimeError: Failed to create Java VM. Return code = -1
Failed to create Java VM
Traceback (most recent call last):
  File "myTestJavaBridge.py", line 4, in <module>
    javabridge.start_vm(run_headless=True)
  File "/usr/local/lib/python3.7/site-packages/javabridge/jutil.py", line 314, in start_vm
    raise RuntimeError("Failed to start Java VM")
RuntimeError: Failed to start Java VM
```

