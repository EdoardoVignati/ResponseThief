# ResponseThief
ResponseThief visits URLs from a list and returns the http response codes. 

     ___                            _____ _    _      __ 
    | _ \___ ____ __ ___ _ _  _____|_   _| |_ (_)___ / _|
    |   / -_(_-| '_ / _ | ' \(_-/ -_)| | | ' \| / -_|  _|
    |_|_\___/__| .__\___|_||_/__\___||_| |_||_|_\___|_|  
               |_|                                       	                               
                                       by @EdoardoVignati 

## Requirements for Python3
- from termcolor import colored, cprint
- import threading
- import requests
- import argparse
- import signal
- import time
- import sys
- import os
- import re

## Usage
Clone the repo and run 

```
$ ./response-thief.py inputfile.txt outputfile.txt
```

where ```inputfile.txt``` is a list of URLs without the protocol and ```outputfile.txt``` is a path to an empty file.

Example of input file:
```
www.github.com
github.com
foo.bar.gitlab.com
```


## Output
The output is built in this format:
```
[200] www.github.com
[301] foo.gitlab.com
...
```
Verbosity (--stdout) has 3 different levels:
- enabled (print everything)
- less (print important information)
- disable (do not print anything)

## Print on stdout
- Red URL: error retrieving URL
- White URL: ok, a response code has been registered 

## Errors
- [Timeout error] : cannot retrieve the webpage within 5 seconds
- [Connection error] : cannot open or find the domain
- [Unknown error] : don't know what's happening :)


![Demo](https://raw.githubusercontent.com/EdoardoVignati/ResponseThief/master/responsethief.png)
 
