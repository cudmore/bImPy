
## download and install python 3.8

see 'python-3.8.5-amd64.exe'

https://www.python.org/downloads/

## download and install visual studio 2019

required to 'pip install napari' (for example)

requires reboot/restart

installation of visual studio only requires C/C++ development, things like cpp, clang, etc

see 'vs_community__1339317600.1600197547.exe'

https://visualstudio.microsoft.com/downloads/

## download and uncompress bImpy

### Either clone with git

```
cd Desktop
cd cudmore
git clone https://github.com/cudmore/bImPy.git
```

### Or clone with git

https://github.com/cudmore/bImPy

see: bImPy-master.zip

make sure you rename folder to bImPy

c:\Users\LindenLab\Desktop\cudmore\bImPy

## make a virtual environment in folder bimpy_env

```
cd bImPy
python3 -m venv bimpy_env
```

## activate bimpy_env virtual env (can't copy/paste this into terminal? Type it directly)

```
cd bImPy
.\bimpy_venv\Scripts\activate
```

## start installing bImPy

```
cd bImPy
pip3 install -e .
```

## install canvas

```
cd canvas
#pip install -r requirements.txt
pip3 install -e .
```

## manually install PyQt5

```
pip install PyQt5
```

may need 

does not seem to be needed 
```
pip install PyQt5==5.13.0
```

## Troubleshooting

```
pip install PyQt5==5.13.0
```

```
pip install napari
```

gives error:

error: Microsoft Visual C++ 14.0 is required. Get it with "Build Tools for Visual Studio": https://visualstudio.microsoft.com/downloads/

## todo:

1) update canvas requirements.txt to include 'opencv-python-headless'

2) in bCanvasApp.py need to show() on windows

```
		myCanvasApp = bCanvasApp(parent=app)
		myCanvasApp.show()
```

3) quit is broken, does not return?

### list ports

```
python -m serial.tools.list_ports -v

```

```
COM1
    desc: Communications Port (COM1)
    hwid: ACPI\PNP0501\1
COM3
    desc: NI USB-232/1 SN:BBEDCE, Communications Port (COM3)
    hwid: NISERU\USB232X1_1\6&22F65707&3&1
COM4
    desc: NI USB-232/1 SN:000BBF, Communications Port (COM4)
    hwid: NISERU\USB232X1_1\6&27027774&3&1
3 ports found
```

### powrshell

```
powershell
[System.IO.Ports.SerialPort]::getportnames()

$port= new-Object System.IO.Ports.SerialPort COM4,9600,None,8,one

```



