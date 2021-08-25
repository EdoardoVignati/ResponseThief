# ResponseThief

ResponseThief visits URLs from a list and returns the http response codes.

     ___                            _____ _    _      __ 
    | _ \___ ____ __ ___ _ _  _____|_   _| |_ (_)___ / _|
    |   / -_(_-| '_ / _ | ' \(_-/ -_)| | | ' \| / -_|  _|
    |_|_\___/__| .__\___|_||_/__\___||_| |_||_|_\___|_|  
               |_|                                       	                               
                                       by @EdoardoVignati 

## Installation

```$ pip install -r requirements.txt```

## Usage

Use Python3.

Clone the repo and run:

```bash
$ ./response-thief.py url_sample.txt result.txt
```

where `url_sample.txt` is a list of URLs without the protocol and `result.txt` is a path to an empty file.

Test it with:
```bash
$ ./response-thief.py ./url_sample.txt result.txt 
```

Example of input file:

```
www.github.com
github.com
foo.bar.gitlab.com
```

## Filter

You can filter a specific http status code by adding:

```
--filter 404
```

The output file will contain only the filtered url.

## Output

The output is built in this format:

```
[200] www.github.com
[301] foo.gitlab.com
[...] ...
```

Verbosity (`--stdout`) has 3 different levels:

- `enabled` (print everything)
- `minimal` (print important information)
- `disable` (do not print anything)

## Print on stdout

- Red URL: error retrieving URL
- White URL: ok, a response code has been registered

## Errors

- `Timeout error` : cannot retrieve the webpage within 5 seconds
- `Connection error` : cannot open or find the domain
- `Unknown error` : don't know what's happening :)

![Demo](https://raw.githubusercontent.com/EdoardoVignati/ResponseThief/master/responsethief.png)

