# ResponseThief
ResponseThief visits URLs from a list and returns the http responses. 

     ____                                     _____ _     _       __ 
    |  _ \ ___  ___ _ __   ___  _ __  ___  __|_   _| |__ (_) ___ / _|
    | |_) / _ \/ __| '_ \ / _ \| '_ \/ __|/ _ \| | | '_ \| |/ _ \ |_ 
    |  _ \  __/\__ \ |_) | (_) | | | \__ \  __/| | | | | | |  __/  _|
    |_| \_\___||___/  __/ \___/|_| |_|___/\___||_| |_| |_|_|\___|_|  
                   |_|             
                                                   by @EdoardoVignati     

## Requirements for Python3
- import requests
- import threading
- import time
- import os
- import sys
- from termcolor import colored, cprint
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
 
