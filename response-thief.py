#!/usr/bin/env python3
from termcolor import colored, cprint
import threading
import requests
import argparse
import signal
import time
import sys
import os
import re

logo = """ 
  ___                            _____ _    _      __ 
 | _ \___ ____ __ ___ _ _  _____|_   _| |_ (_)___ / _|
 |   / -_(_-| '_ / _ | ' \(_-/ -_)| | | ' \| / -_|  _|
 |_|_\___/__| .__\___|_||_/__\___||_| |_||_|_\___|_|  
            |_|
                                   by @EdoardoVignati                                  
"""

# Global variables
stdout = "enabled"
errors = True
responses = []
done = 0
total = 0
summary = {}
maxUrl = 0
lock = threading.Lock()
print_lock = threading.Lock()
filter_status = None


def is_error(s):
    error_status = ["Connection_error", "Timeout_error", "Unknown_error"]
    return s in error_status


def signal_handler(sig, frame):
    sys.stdout.flush()
    print('\n\nAborted!')
    exit(130)


def check_url(url):
    try:
        checked = re.findall("(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", url)
        # checked = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url)
    except:
        return False

    return len(checked) == 1


def visited(url, status):
    global lock
    lock.acquire()

    global summary
    global responses
    if (url, status.status_code) not in responses:
        responses.append((url, status.status_code))
        if status.status_code in summary.keys():
            summary[status.status_code] = summary[status.status_code] + 1
        else:
            summary[status.status_code] = 1
    lock.release()


def counter(url, status):
    if stdout == "disabled":
        return

    global lock
    global done
    global maxUrl
    global total
    global errors
    global filter_status

    lock.acquire()
    done += 1
    padding = (" " * (maxUrl - len(url) + 27))

    print_lock.acquire()

    if stdout == "enabled" or stdout == "minimal":
        if not is_error(str(status)):
            code = status.status_code
        else:
            code = status
        if (filter_status is not None and str(code) == filter_status) or filter_status is None:
            green = "Visited {} -> [{}] {}{}".format(colored(str(done) + "/" + str(total), "green"),
                                                     code, url, padding)
            red = "Visited {} -> [{}] {}{}".format(colored(str(done) + "/" + str(total), "green"),
                                                  code, colored(url, "red"), padding)
            if not errors:
                if not is_error(str(status)):
                    print(green)
            elif errors:
                if is_error(str(status)):
                    print(red)
                else:
                    print(green)
        if stdout == "enabled":
            sys.stdout.write("Visited... {}%{}\r".format(str("{:.2f}".format(round((done / total) * 100, 2))), padding))
            sys.stdout.flush()

    print_lock.release()
    lock.release()

    return done


def visit_thread(raw_url, to):
    global lock
    global responses
    global stdout

    url = raw_url.replace("http://", "").replace("https://", "")

    try:
        # Test HTTPS
        status = requests.head("https://" + url.strip(), timeout=to, allow_redirects=True)
        # Test HTTP
        status = requests.get("http://" + url.strip(), timeout=to, allow_redirects=True)

        # Url done
        visited(url, status)
        counter(url, status)

    except requests.ConnectionError:
        lock.acquire()
        responses.append((url, "Connection_error"))
        lock.release()
        counter(url, "Connection_error")
    except requests.exceptions.Timeout:
        lock.acquire()
        responses.append((url, "Timeout_error"))
        lock.release()
        counter(url, "Timeout_error")
    except:
        lock.acquire()
        responses.append((url, "Unknown_error"))
        lock.release()
        counter(url, "Unknown_error")


def read_file(file_input):
    global urlList
    global total
    global maxUrl

    urlList = []
    with open(file_input) as fp:
        l = fp.readline().strip()
        while l:
            if (l != "") and (l != "\n") and check_url(l) and (l not in urlList):
                urlList.append(l)
                total += 1
                if len(l.strip()) > maxUrl:
                    maxUrl = len(l.strip())
            l = fp.readline().strip()
    if stdout == "enabled":
        print("Total URLs: " + str(total) + "\n")
    maxUrl += len("Launching ") + (len(str(total)) * 2) + 1
    return urlList


def write_output(file_output):
    global responses
    global stdout
    global errors
    global filter_status

    try:
        os.remove(file_output)
    except:
        pass
    out = open(file_output, "a")
    length = float(len(responses))
    write_count = 0.0

    for u in responses:
        if (filter_status is not None and str(u[1]) == filter_status) or filter_status is None:
            if not errors:
                if not is_error(u[1]):
                    out.write("[" + str(u[1]) + "] " + u[0] + "\n")
            else:
                out.write("[" + str(u[1]) + "] " + u[0] + "\n")

        write_count += 1.0
        if stdout == "enabled":
            padding = (" " * (maxUrl + 27))
            sys.stdout.write("Writing... {}%{}\r".format(round((write_count / length) * 100, 2), padding))
            sys.stdout.flush()
    out.close()


def print_summary():
    if stdout != "disabled":
        print("\n")
        for k in summary.keys():
            print("Response [{}] -> {} times".format(str(k), str(summary[k])))
        if stdout == "enabled":
            print("")
            print("Output saved in '" + os.path.abspath(file_output) + "'")


if __name__ == "__main__":

    desc = "Given a list of URLs, tests the HTTP response codes and write them into a file. "
    desc += "URLs must not begin with the protocol ('http://' or 'https://')\n"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('input', metavar='file_input', help='path of input file. A list of URLs, each for row.')
    parser.add_argument('output', metavar='file_output',
                        help='path of output file. An empty file to append output. Should be different from file_input')
    parser.add_argument('--stdout', metavar='[enabled, minimal, disabled]', help='edit verbosity of stdout print.')
    parser.add_argument('--errors', metavar='[yes, no]', help='save or not errors')
    parser.add_argument('--filter', metavar='[200, 301, ..]', help='a status code to filter')
    args = parser.parse_args()

    file_input = args.input
    file_output = args.output
    filter_status = args.filter

    if args.stdout is not None:
        stdout = args.stdout

    if args.errors is not None:
        if args.errors == "no":
            errors = False

    if stdout == "enabled":
        cprint(logo, "red")

    if file_input is None or file_output is None:
        print(parser.print_help())
        exit(1)

    if file_input == file_output:
        print(parser.print_help())
        exit(1)

    try:
        f = open(file_input)
        f.close()
    except IOError:
        print("File not found: " + file_input)
        exit(1)

    signal.signal(signal.SIGINT, signal_handler)

    urlList = read_file(file_input)

    # Launch threads
    launched_threads = []
    visit_timeout = 5
    sleep_time = 0
    i = 0
    for line in urlList:
        i += 1
        if line.strip() != "":
            if stdout == "enabled":
                sys.stdout.write(
                    "Launching " + colored(str(i) + "/" + str(total), "blue") + " -> " + line.strip() + "\r")
                sys.stdout.flush()
            t = threading.Thread(target=visit_thread, args=(line.strip(), visit_timeout))
            launched_threads.append(t)
            time.sleep(sleep_time)
            t.start()

    # Wait for termination
    for t in launched_threads:
        t.join()

    write_output(file_output)

    print_summary()
