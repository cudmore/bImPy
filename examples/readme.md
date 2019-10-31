## Examples

**bConvertFolder_Headers.py** : Given the full path to a folder, convert just the headers of all files in the folder.

**bConvertFolder** : Given the full path to a folder, convert all files in the folder to Tiff.

**bConvertOir.py** : Convert a single OIR file.

Use bConvertFolder_Headers.py to save a comma-seperated text file containing the header information for each file in a folder

The command

```
python3 bConvertFolder_Headers.py /Users/cudmore/box/data/testoir/
```

Will output two different text files, one will be a .csv file with one row per original file in the folder.

|path                                             |date      |time              |fileVersion|programVersion|laserWavelength|pmtGain1|pmtOffset1|pmtVoltage1|pmtGain2|pmtOffset2|pmtVoltage2|pmtGain3|pmtOffset3|pmtVoltage3|scanner|zoom|bitsPerPixel|numChannels|stackType|xPixels|yPixels|numImages|numFrames|xVoxel           |yVoxel           |zVoxel|frameSpeed       |lineSpeed|pixelSpeed|xMotor|yMotor|zMotor|
|-------------------------------------------------|----------|------------------|-----------|--------------|---------------|--------|----------|-----------|--------|----------|-----------|--------|----------|-----------|-------|----|------------|-----------|---------|-------|-------|---------|---------|-----------------|-----------------|------|-----------------|---------|----------|------|------|------|
|/Users/cudmore/box/data/testoir/20190514_0004.oir|2019-05-14|16:52:02.879-07:00|2.1.2.3    |2.3.1.163     |920.0          |1.0     |0         |453        |1.0     |0         |596        |1.0     |0         |453        |Galvano|2.0 |12          |1          |TSeries  |242    |453    |200      |200      |0.497184455521791|0.497184455521791|1.0   |721.146          |1.578    |0.002     |None  |None  |None  |
|/Users/cudmore/box/data/testoir/20190514_0005.oir|2019-05-14|17:10:32.520-07:00|2.1.2.3    |2.3.1.163     |920.0          |1.0     |0         |453        |1.0     |0         |596        |1.0     |0         |453        |Galvano|2.0 |12          |1          |TSeries  |242    |453    |200      |200      |0.497184455521791|0.497184455521791|1.0   |721.146          |1.578    |0.002     |None  |None  |None  |
|/Users/cudmore/box/data/testoir/20190514_0006.oir|2019-05-14|17:13:53.682-07:00|2.1.2.3    |2.3.1.163     |920.0          |1.0     |0         |453        |1.0     |0         |596        |1.0     |0         |453        |Galvano|2.0 |12          |1          |TSeries  |242    |453    |200      |200      |0.497184455521791|0.497184455521791|1.0   |721.146          |1.578    |0.002     |None  |None  |None  |
|/Users/cudmore/box/data/testoir/20190514_0002.oir|2019-05-14|16:24:05.214-07:00|2.1.2.3    |2.3.1.163     |920.0          |1.0     |0         |550        |1.0     |0         |596        |1.0     |0         |550        |Galvano|2.0 |12          |1          |TSeries  |128    |233    |200      |200      |0.497184455521791|0.497184455521791|1.0   |319.9500000000001|1.35     |0.002     |None  |None  |None  |
|/Users/cudmore/box/data/testoir/20190514_0003.oir|2019-05-14|16:27:07.287-07:00|2.1.2.3    |2.3.1.163     |920.0          |1.0     |0         |550        |1.0     |0         |596        |1.0     |0         |550        |Galvano|2.0 |12          |1          |TSeries  |128    |233    |200      |200      |0.497184455521791|0.497184455521791|1.0   |319.9500000000001|1.35     |0.002     |None  |None  |None  |
|/Users/cudmore/box/data/testoir/20190514_0001.oir|2019-05-14|15:43:24.544-07:00|2.1.2.3    |2.3.1.163     |920.0          |1.0     |0         |557        |1.0     |0         |569        |1.0     |0         |557        |Galvano|2.0 |12          |1          |TSeries  |148    |218    |200      |200      |0.497184455521791|0.497184455521791|1.0   |307.19           |1.39     |0.002     |None  |None  |None  |

The second will be a .txt file for each original file in the folder in the [JSON][json] format.

```
{
    "path": "/Users/cudmore/Sites/bImpy-Data/ca-smooth-muscle-oir/20190514_0003.oir",
    "date": "2019-05-14",
    "time": "16:27:07.287-07:00",
    "fileVersion": "2.1.2.3",
    "programVersion": "2.3.1.163",
    "laserWavelength": "920.0",
    "laserPercent": "10.5",
    "pmtGain1": "1.0",
    "pmtOffset1": "0",
    "pmtVoltage1": "550",
    "pmtGain2": "1.0",
    "pmtOffset2": "0",
    "pmtVoltage2": "596",
    "pmtGain3": "1.0",
    "pmtOffset3": "0",
    "pmtVoltage3": "550",
    "scanner": "Galvano",
    "zoom": "2.0",
    "bitsPerPixel": "12",
    "numChannels": 1,
    "stackType": "TSeries",
    "xPixels": 128,
    "yPixels": 233,
    "numImages": 200,
    "numFrames": 200,
    "xVoxel": 0.497184455521791,
    "yVoxel": 0.497184455521791,
    "zVoxel": 1.0,
    "umWidth": 63.63961030678925,
    "umHeight": 115.8439781365773,
    "frameSpeed": "319.9500000000001",
    "lineSpeed": "1.35",
    "pixelSpeed": "0.002",
    "xMotor": null,
    "yMotor": null,
    "zMotor": null
}
```

[json]: https://www.json.org/
