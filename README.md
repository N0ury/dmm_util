# dmm_util
dmm_util is a utility for interacting with Fluke 289 and 287 Series multimeters.
You can:
- download saved measurements
- download saved recordings
- download saved min-max
- download peaks
- set date and time
- set internal data such as company,contact,operator,or site
- display realtime measurements
- set available record names list
- display configuration informations

This is a complete rewrite of [Fredrik Valeur dmm_util](https://github.com/fvaleur/dmm_util)  
Previous one was written in Ruby. This one is written in Python 3.  
There are also some changes to the code.

**Prerequisites:**

**Python 3.10+** and pyserial must have been installed before use.

many things have been added as we go along. So the code is not optimal.

**Important**  
All the data displayed are those returned by the multimeter.  
None is calculated or processed


**How to install it:**

1. - Using PyPi (the simplest way)  
Latest **release** can be installed by typing:  
`python -m pip install fluke_28x_dmm_util`  
[![PyPI version](https://badge.fury.io/py/fluke-28x-dmm-util.svg)](https://badge.fury.io/py/fluke-28x-dmm-util)  
[![Downloads](https://pepy.tech/badge/fluke-28x-dmm-util)](https://pepy.tech/project/fluke-28x-dmm-util)


2. - From github (newest version):  
Latest **commit** can be used by typing:  
`git clone https://github.com/N0ury/dmm_util.git`  



3. -  From Github [release](https://github.com/N0ury/dmm_util/releases)  
![GitHub release (latest by date)](https://img.shields.io/github/v/release/N0ury/dmm_util)  
Get the latest release and unzip (or gunzip) it  
cd to the folder that has been created and run the utility as shown above.


**How to run the utility**  
Main command is:  
`python -m fluke_28x_dmm_util -p PORT ...`  

**If you have installed the release (.zip or /tgz), you need to change directory to the one of installation. The directory before running the utility MUST be dmm_util.**

If you have installed the PyPi version this is not necessary, and you can run the utility anywhere.  

Syntax:  

`python -m fluke_28x_dmm_util options command`  

**options**  

{-p|--port} PORT  
This is mandatory, it's the port to which the DMM is connected (eg: COM3)   

{-s|--separator} SEPARATOR  
Separator is optional. Default is TAB  

{-t|--timeout} TIMEOUT  
Timeout is optional. Default is 0.09 (in seconds)  
You need to change this only if timeouts occur.

**command**  
This depends on what you want to do  
- get:  
get recordings {name | index} [, {name | index}...]  
get minmax {name | index} [, {name | index}...]  
get peak {name | index} [, {name | index}...]  
get measurements {name | index} [, {name | index}...]  
get current: get current measured values  
get config: get DMM configuration  
get names: get DMM names prefix used for storing data  

'name' is the name used for a recording, 'index' is a number  
These data can be displayed with 'list' command,  
'name' can be surrounded by quotes in case it contains spaces.  
If this parameter contains only digits, value is assumed to be an index.  
Otherwise, it will be taken as a name. Multiple names or indexes are permitted, they must be comma separated.  

Example:  
get recordings 1,"Record 2",5  
get recordings 3  

This command displays detailed recordings informations

- set:  
set company <value>: set DMM company name  
set operator <value>: set DMM operator name  
set site <value>: set DMM site name  
set contact <value>: set DMM contact name  
set datetime: set DMM date and time to the PC current date/time  
set names <index> <name>: set the name of recording at given index  

'index' is a value between 1 and 8. List can be obtained using 'get names'.  

Example:  
set operator N0ury  
set name 2 Min_Max  

- list  
list recordings: list recording type recordings  
list minmax: list min/max type recordings  
list peak: list peak type recordings  
list measurements: list all the measurements  
list all: list all the memory stored values  

This command displays general informations about recordings  

**Common issues**
```
  File "python3_dmm_util.py", line nn
    match len(name):
            ^
SyntaxError: invalid syntax
```

You are using Python version less than 3.10, consider upgrading.

```
Traceback (most recent call last):
  File "python3_dmm_util.py", line 4, in <module>
    import serial
ModuleNotFoundError: No module named 'serial'
```

pyserial module is needed.
Install it this way  
`python -m pip install pyserial`


**Copyright**

Copyright © 2011 Fredrik Valeur.  
Copyright © 2017-2022 N0ury.

