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

This is a complete rewrite of [Fredrik Valeur dmm_util](https://github.com/fvaleur/dmm_util)  
Previous one was written in Ruby. This one is written in Python 3.  
There are also some changes to the code.

**Prerequisites:**

Python 3.10+ and pyserial must have been installed before use.

many things have been added as we go along. So the code is not optimal.

**How to use it:**

./python3_dmm_util.py or python3 python3_dmm_util.py
This gives help.

**Easy install from PyPi**  
`pip install fluke-28x-dmm-util`  
pyserial will be automatically installed as well.  
Now you need to use it this way (for displaying help):  
`python3 -m fluke_28x_dmm_util`  
or  
`python -m fluke_28x_dmm_util`  

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
Copyright © 2017-2021 N0ury.  

