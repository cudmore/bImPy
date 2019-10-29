
## Python video viewer

python camera viewer is in `c:\Users\cudmore\Desktop\bCamera\bCamera2.py`

When running, files are saved every 1 sec into c:\\Users\\cudmore\\Desktop\\bCamera\\tmp.tif'

Control that from within `bCamera2.py` with

```
mySaveInterval = 1
myFilename = 'c:\\Users\\cudmore\\Desktop\\bCamera\\tmp.tif'
```

## Igor Canvas

Files are in C:\Users\cudmore\Dropbox\bJHU

### 1) Run the Canvas in Igor Pro

Run in Igor from desktop with `bOlympus.ipf` alias

### 2) Initialize canvas

Use main menu `Canvas - Load User` and select `scope\nathan_olympus.txt`. This will open the `mp285 Panel`, set the save path to `e:\Nathan\data`, and set video to '2.67 um/pixel'. This size is assuming the 0.63 c-mount, 1x magnification turret

In mp285_panel Save/Session section

 - Specify a 'Session ID', something short like san1, san2, san3, etc
 - Click green 'Initialize Session' button. This will open a canvas a mp285 canvas window.

The folder you save .oir files to is critical, if not in the right place, the Igor canvas will not be able to find them.

On 20191028, for a canvas (session id) named 'tst1', the folder is

```
E:\Nathan\data\20191028\20191028_tst1
```

You can always get to the hard-drive folder for the current canvas by clicking the `hdd` button.

### 4) Interacting with the canvas

Use the left/right and front/back arrow buttons to move the stage a pre-defined amount. See below for setting step size.

If you move the stage with the Prior joystick, you need to refresh the Igor canvas with green 'read position' button. If this results in an error with speaking to the Prior controller, the button will turn red.

The **Zoom Square** checkbox will show you the size of either the video image and/or the size of a 2p image at different magnifications. This is useful if you are manually moving the stage with the joystick and you need to align something into an approximate tile.

**Capture video** will load the most recent bCapture2.py file from 'c:\Users\cudmore\Desktop\bCamera\tmp.tif'.

**Import From Scope** will look for new .oir files in your hdd folder. 
You can always get to the hard-drive folder for the current canvas by clicking the 'hdd' button.


### Setting and saving left/right and front/back step sizes.

When clicking left/right, front/back arrows, the canvas software will move the stage a specified amount. This can be controlled in two ways.

 1. To set the x/y step size temporarily, in the 'mp285_panel' window, set the values in the 'X Step (um)' and 'Y Step (um)' fields

 2. To set the x/y step size permanently. (i) Open the canvas options panel with main menu 'canvas - mp285 Options', (ii) In the 'Objectives' section, find the objective you are using. **Should be named 'oly'**. (iii) set desired step size in the 'stepx' and 'stepy' columns. (iv) click save.

### Watch Folder

### Read Motor

In mp285_2p:mp285_InitSession()

```
	elseif (gUseOlympusMotor)
		if (!DataFolderExists("root:bOlympus"))
			bOlympus_Init()
		endif
		SVAR olympusWatchFolder = root:bOlympus:olympusWatchFolder
		olympusWatchFolder = animalFolder
		Olympus_WatchTask_Start()
	endif
```

In bOlympus.ipf



```
//////////////////////////////////////////////////////////////////////////
Function bOlympus_Init()
	NewDataFolder/O root:bOlympus
	
	Variable/G root:bOlympus:xOlympus = NaN
	Variable/G root:bOlympus:yOlympus = NaN
	
	Variable/G root:bOlympus:writeTimeout = 0.1
	Variable/G root:bOlympus:readTimeout = 0.1
	
	String/G root:bOlympus:eol = "\r\n"
	
	// watch a folder for new .oir files
	String/G root:bOlympus:olympusWatchFolder = ""
	Make/O/T/N=(1,4) root:bOlympus:watchFolderFound = ""
	Wave/T watchFolderFound = root:bOlympus:watchFolderFound
		SetDimLabel 1,0,path watchFolderFound
		SetDimLabel 1,1,fileName watchFolderFound
		SetDimLabel 1,2,xmotor watchFolderFound
		SetDimLabel 1,3,ymotor watchFolderFound
		
	print "bOlympus_Init() initializing Prior  stage controller to serial COM5"
	VDTOperationsPort2 COM5
	// changes as of OCt 2019, after Olympus installed new hardware
	//VDTOperationsPort2 COM1
	
End
```

```
//////////////////////////////////////////////////////////////////////////
Function OlympusWatchTask(s)		// This is the function that will be called periodically
	STRUCT WMBackgroundStruct &s
	
	SVAR olympusWatchFolder = root:bOlympus:olympusWatchFolder
	//Printf "Task %s called OlympusWatchTask(), ticks=%d wathing folder %s\r", s.name, s.curRunTicks, olympusWatchFolder
	//olympusWatchFolder = "E:Arsalan:03202019"
	// check that watch folder exists
	if (!bFolderExists(olympusWatchFolder))
		print "OlympusWatchTask() did not find folder:", olympusWatchFolder
		return 0	// Continue background task
	endif
	String fileList = bGetFileList(olympusWatchFolder, ".oir", quiet=1)
	Variable mFile = ItemsInList(fileList)
	//print "fileList:", fileList
	
	Variable numAdded = 0
	
	// for each file in fileList, check if it is our already found list root:bOlympus:watchFolderFound
	Wave/T watchFolderFound = root:bOlympus:watchFolderFound
	Variable mFound = DimSize(watchFolderFound,0)
	Variable i, j
	for (i=0; i<mFile; i+=1) 
		String currFile = StringFromList(i, fileList)
		//print "looking for currFile:", currFile
		Variable foundIdx = -1
		for (j=0; j<mFound; j+=1)
			String currentPath = watchFolderFound[j][%path]
			String currFound = watchFolderFound[j][%fileName]
			//print "currentPath:", currentPath
			if (bIsSame(currentPath, olympusWatchFolder))
				if (bISSame(currFile, currFound))
					//print "found", currFile, "in found list, idx:", j
					foundIdx = j
				endif
			endif
		endfor // j files in found list
		if (foundIdx == -1)
			Variable serialReadOk = bOlympus_Serial_ReadPos(verbose=0)
			//if (serialReadOk == 1)
				NVAR moveToX = root:MapManager3:options:mp285:moveToX
				NVAR moveToY = root:MapManager3:options:mp285:moveToY
				watchFolderFound[mFound][] = {""} // append a row
				watchFolderFound[mFound][%path] = olympusWatchFolder // append a row
				watchFolderFound[mFound][%fileName] = currFile // append a row
				watchFolderFound[mFound][%xmotor] = num2str(moveToX)
				watchFolderFound[mFound][%ymotor] = num2str(moveToY)
				mFound = DimSize(watchFolderFound,0)
				numAdded += 1
				print "=== OlympusWatchTask() added new file:", currFile, "X:", moveToX, "Y:", moveToY
			//else
			//	print "=== OlympusWatchTask() failed to add file, could not rwad from serial PRior motor controller???"
			//endif
		endif
	endfor // i files in folder list
	
	//if (numAdded > 0)
	//	print "   OlympusWatchTask() added", numAdded, "oir files"
	//endif
	return 0	// Continue background task
End

Function Olympus_WatchTask_Start()
	print "Olympus_WatchTask_Start()"

	// always stop before we start
	Olympus_WatchTask_Stop()
	
	if (!DataFolderExists("root:bOlympus"))
		bOlympus_Init()
	endif

	Variable numTicks = 2 * 60		// Run every two seconds (120 ticks)
	CtrlNamedBackground OlympusWatch, period=numTicks, proc=OlympusWatchTask
	CtrlNamedBackground OlympusWatch, start
	CtrlNamedBackground OlympusWatch, status
	print S_Info
End

Function Olympus_WatchTask_Stop()
	print "Olympus_WatchTask_Stop()"
	CtrlNamedBackground OlympusWatch, stop
	CtrlNamedBackground OlympusWatch, status
	print S_Info
End
```

###Load OIR

This is a mess but works. 

```
Function bOlympus_execute2(oirFilePath)
String oirFilePath

	print "bOlympus_execute2() oirFilePath:", oirFilePath
	
	String oirFileName = bGetName(oirFilePath)
	
	Variable isMac = 0
	Variable isWindows = bIsWindows()
	if (!isWindows)
		isMac = 1
	endif
	
	if (isMac)
		oirFilePath = "/Volumes/" + ReplaceString(":", oirFilePath, "/")
	elseif (isWindows)
		// convert
		// e:cudmore:data:20190326:20190326_tst1:030119_HCN4-GCaMP8_SAN__0001.oir
		// to
		//
		oirFilePath = ReplaceString(":", oirFilePath, "\\\\")
		oirFilePath = oirFilePath[0] + ":" + oirFilePath[1,strlen(oirFilePath)-1]
	endif
	print "   final oirFilePath:", oirFilePath
	
	String pythonFolderPath = bNV_GetDefaultPath(getThisPath="python")
	
	if (isMac)
		pythonFolderPath = ":Volumes:" + pythonFolderPath
	endif
	
	// assuming everything is install in python3 (javabridge, numpy, bStack, etc)
	String pythonPath = ""
	if (isWindows)
		pythonPath = "python" + " " + pythonFolderPath + "myBioFormats\\bConvertOir.py"
	elseif (isMac)
		pythonPath = "/usr/local/bin/python3" + " " + pythonFolderPath + "myBioFormats:bConvertOir.py"
		//pythonPath = "/usr/local/bin/python3" + " " + pythonFolderPath + "myBioFormats:test1.py"
	endif
	
	print "pythonPath:", pythonPath
	
	String unixCmd = ""
	unixCmd = pythonPath + " " + oirFilePath

	String igorCmd = ""
	if (isWindows)
		igorCmd = unixCmd //+ " > c:\\tmp.txt"
	elseif (isMac)
		unixCmd = ReplaceString(":", unixCmd, "/")
		//unixCmd = "pwd; echo $PATH; source /Users/cudmore/jhu/bJHU/python/myBioformats/bStack_env/bin/activate; " + unixCmd
		String exportJavaHome = "export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-12.0.1.jdk/Contents/Home; "
		unixCmd = exportJavaHome + unixCmd
		sprintf igorCmd, "do shell script \"%s\"", unixCmd
	endif
	
	//print "unixCmd:", unixCmd
	print "   igorCmd:", igorCmd

	//if (isMac)
	//	//String javaHome = "echo export \"JAVA_HOME=\$(/usr/libexec/java_home)\""
	//	String javaHome = "export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-12.0.1.jdk/Contents/Home"
	//	ExecuteScriptText/B "do shell script \"" + javaHome + "\""
	//	print "   S_value:", S_value
	//endif
	
	String progressWinStr = mm3_Progress_Open("", "", mapTitle="Converting " + oirFileName + "...")
	
	// on windows, /B runs in background
	ExecuteScriptText/B igorCmd // creates S_value
	// S_value will have stdout from fiji
	print "   S_value:", S_value
	
	mm3_ProgressClose(progressWinStr)
End
```

## Olympus software

"C:\Program Files\OlympusMicro\FV30S-SW\eclipse\FV31S-SW.exe"

"C:\Program Files\OlympusMicro\FV30S-SW\eclipse\FV31S-SW.exe" -dt

FV31S-SW

Version: 2.3.1.163 ( Powered by H-PF Version 1.23.2.205 )

Installed plugins:

```
FV20-3D
FV20-ACQ
FV20-CELLSENS
FV20-MATL
FV20-MPELASER
FV20-PROCESSING
FV20-PSEQM
FV20-SEQM
FV20-STITCH
FV20-XYSTAGE
```

## x/y translation stage

x/y stage: Prior Z-Deck
Controller box: Prior Proscan III

See: d:\Users\cudmore\stage-prior


## Mouse heating pad

Rodent Warmer x1

pad is: 53810A - 7x7 cm for 53801/53851

https://www.stoeltingco.com/rodent-warmer.html

## scope video camera is

ptgrey / flir / grasshopper3 GS3-U3-23S6M / firmware 2.30.3.0 / 1/1.2" sensor

See: d:\Users\cudmore\install\video-camera-ptgrey

