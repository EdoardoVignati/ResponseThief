#!/usr/bin/env python3
import http

from termcolor import colored, cprint
import threading
import requests
import argparse
import signal
import time
import sys
import os
from urllib.parse import urlparse

logo = """ 
  ___                            _____ _    _      __ 
 | _ \___ ____ __ ___ _ _  _____|_   _| |_ (_)___ / _|
 |   / -_(_-| '_ / _ | ' \(_-/ -_)| | | ' \| / -_|  _|
 |_|_\___/__| .__\___|_||_/__\___||_| |_||_|_\___|_|  
            |_|
                                   by @EdoardoVignati                                  
"""


def check_url(url):
    try:
        urlparse(url)
    except ValueError:
        return False
    return True


def visited(url, status, visited_protocol):
    global lock
    global summary
    global responses

    lock.acquire()
    responses[available_protocols.index(visited_protocol)].append((url, status.status_code))
    if status.status_code in summary.keys():
        summary[status.status_code] = summary[status.status_code] + 1
    else:
        summary[status.status_code] = 1
    lock.release()


def counter(url, status):
    global lock
    global done
    global max_url
    global total
    global filter_status

    if stdout == "disabled":
        return

    lock.acquire()
    done += 1
    padding = (" " * (max_url - len(url) + 27))

    print_lock.acquire()

    if stdout == "enabled" or stdout == "minimal":
        if not str(status) in errors_status_list:
            code = status.status_code
        else:
            code = status
        if (filter_status is not None and str(code) == filter_status) or filter_status is None:
            count_visited = colored(str(done) + "/" + str(total * len(available_protocols)), "blue")
            color_code = code
            if code in errors_status_list:
                color_code = colored(code, "red")
            print("Visited {} -> [{}] {}{}".format(count_visited, color_code, url, "red", padding))

        if stdout == "enabled":
            round_value = str("{:.2f}".format(round((done / total) * 100, 2)))
            sys.stdout.write("Visited... {}%{}\r".format(round_value, padding))
            sys.stdout.flush()

    print_lock.release()
    lock.release()

    return done


def remove_protocols(url_with_protocol):
    url_without_protocols = url_with_protocol
    for protocol_to_remove in available_protocols:
        if url_without_protocols.startswith(protocol_to_remove):
            url_without_protocols = url_with_protocol.replace(protocol_to_remove, "")
    return url_without_protocols


def visit_thread(raw_url, to):
    global lock
    global responses
    global stdout

    for current_protocol in available_protocols:
        current_responses_list = responses[available_protocols.index(current_protocol)]
        url = current_protocol + remove_protocols(urlparse(raw_url).geturl())
        try:
            if request_method == http.HTTPMethod.GET:
                status = requests.get(url, timeout=to, allow_redirects=True)
            else:
                status = requests.head(url, timeout=to, allow_redirects=True)

            visited(url, status, current_protocol)
            counter(url, status)

        except requests.ConnectionError:
            lock.acquire()
            current_responses_list.append((url, "Connection_error",))
            lock.release()
            counter(url, "Connection_error")
        except requests.exceptions.Timeout:
            lock.acquire()
            current_responses_list.append((url, "Timeout_error"))
            lock.release()
            counter(url, "Timeout_error")
        except:
            lock.acquire()
            current_responses_list.append((url, "Unknown_error"))
            lock.release()
            counter(url, "Unknown_error")


def read_file():
    global url_list
    global total
    global max_url
    global file_input

    url_list = []
    with open(file_input, encoding="utf8") as fp:
        current_line = fp.readline().strip()
        while current_line:
            if (current_line != "") and (current_line != "\n") and check_url(current_line) and (current_line not in url_list):
                url_list.append(current_line)
                total += 1
                if len(current_line.strip()) > max_url:
                    max_url = len(current_line.strip())
            current_line = fp.readline().strip()
    if stdout == "enabled":
        print("Total URLs: " + str(total))
        print("Tested protocols: " + " ".join(available_protocols) + "\n")
    max_url += len("Launching ") + (len(str(total)) * 2) + 1


def write_output(current_file_output):
    global responses
    global stdout
    global filter_status

    try:
        os.remove(current_file_output)
    except OSError:
        pass
    out = open(current_file_output, "a", encoding="utf8")

    if stdout == "enabled":
        print("Writing output...\n")

    for response_protocol in responses:
        for current_response in response_protocol:
            if (filter_status is not None and str(current_response[1]) == filter_status) or filter_status is None:
                out_str = "[{}] {}\n".format(current_response[1], current_response[0])
                if errors or (not errors and not current_response[1] in errors_status_list):
                    out.write(out_str)

    out.close()


def print_summary():
    if stdout != "disabled":
        for k in summary.keys():
            print("Response [{}] -> {} times".format(str(k), str(summary[k])))
        if stdout == "enabled":
            print("")
            print("Output saved at: " + os.path.abspath(file_output) + "")


def launch_threads():
    # Launch threads
    launched_threads = []
    visit_timeout = 5
    sleep_time = 0
    i = 0
    for line in url_list:
        if check_url(line):
            i += 1
            if stdout == "enabled":
                count_color = colored(str(i) + "/" + str(total), "blue")
                launching_str = "Launching {} -> {}\r".format(count_color, remove_protocols(line))
                print(launching_str)
            t = threading.Thread(target=visit_thread, args=(line, visit_timeout))
            launched_threads.append(t)
            time.sleep(sleep_time)
            t.start()

    # Wait for termination
    for t in launched_threads:
        t.join()


if __name__ == "__main__":

    # Global variables
    stdout = "enabled"
    url_list = []
    done, total, max_url = 0, 0, 0
    summary = {}
    lock, print_lock = threading.Lock(), threading.Lock()
    filter_status = None
    request_method = http.HTTPMethod.GET
    errors_status_list = ["Connection_error", "Timeout_error", "Unknown_error"]
    available_protocols = ["http://", "https://"]
    responses = [[], []]
    errors = True

    # Manual
    desc = "Given a list of URLs, tests the HTTP/HTTPS response codes (GET) and write them into a file. "
    desc += "URLs will be validated and will be tested http and https\n"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("input", metavar='file_input', help="Path of input file. A list of URLs, each for row.")
    parser.add_argument("output", metavar='file_output', help="Path of output file. An empty file to append output. Should be different from file_input.")
    parser.add_argument("--stdout", metavar='[enabled, minimal, disabled]', help="Edit verbosity of stdout print.")
    parser.add_argument("--errors", metavar='[yes, no]', help="save or not errors.")
    parser.add_argument("--filter", metavar='[200, 301, ..]', help="A status code to filter.")
    args = parser.parse_args()

    file_input = args.input
    file_output = args.output

    if args.filter is not None:
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
        f = open(file_input, encoding="utf8")
        f.close()
    except IOError:
        print("File not found: " + file_input)
        exit(1)

    signal.signal(signal.SIGINT, lambda: exit(130))

    read_file()
    launch_threads()
    write_output(file_output)
    print_summary()
