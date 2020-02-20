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

logo=""" 
  ___                            _____ _    _      __ 
 | _ \___ ____ __ ___ _ _  _____|_   _| |_ (_)___ / _|
 |   / -_(_-| '_ / _ | ' \(_-/ -_)| | | ' \| / -_|  _|
 |_|_\___/__| .__\___|_||_/__\___||_| |_||_|_\___|_|  
            |_|
                                   by @EdoardoVignati                                  
	"""

# Arguments check
inputfile=None
outputfile=None

desc = "Given a list of URLs, tests the HTTP response codes and write them into a file. "
desc+="URLs must not begin with the protocol ('http://' or 'https://')\n"
parser = argparse.ArgumentParser(description=desc)
parser.add_argument('input', metavar='inputfile', help='path of input file. A list of URLs, each for row.')
parser.add_argument('output', metavar='outputfile', help='path of output file. An empty file to append output.')
parser.add_argument('--stdout', metavar='enabled/less/disabled', help='edit verbosity of stdout print.')
args = parser.parse_args()


# Global variables
inputfile = args.input
outputfile = args.output
stdout = "enabled"

if args.stdout!=None:
	stdout=args.stdout

# Logo
if(stdout != "disabled"):
	cprint(logo,"red")

if inputfile==None or outputfile==None:
	print(parser.print_help())
	exit(1)

responses=[]
launched_threads=[]
done=0
visit_timeout=5
total=0;
summary={}
maxUrl=0
sleeptime=0

# Manage CTRL+c
def signal_handler(sig, frame):
	sys.stdout.flush()
	print('\n\nAborted!')
	os._exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Check URL
def checkUrl(url):
	global total
	return re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url)[0]

# Done URLs
def visited(url, status):
	lock.acquire()
	responses.append((url,status))
	resp = str(status).split("[")[1].split("]")[0]
	if resp in summary.keys():
		summary[resp]=summary[resp]+1
	else:
		summary[resp]=1
	lock.release()

# Count done URLs
def counted(lock, url, error):
	lock.acquire()
	global done
	global maxUrl
	done+=1
	padding=(" " *(maxUrl-len(url)))
	if(error):
		print("Visited " + colored(str(done) + "/" + str(total),"green") + " -> " + colored(url,"red") + padding)
	else:
		print("Visited " + colored(str(done) + "/" + str(total),"green") + " -> " + url + padding)
	lock.release()	
	return done


# Visit thread
def visitThread(url, to, lock):
	try:
		# Test HTTP
		checkedUrl = checkUrl("http://"+url.strip());
		if(checkedUrl != ""):
			status = requests.head(checkedUrl, timeout=to)
			visited(url, status)

		# Test HTTPS
		checkedUrl = checkUrl("https://"+url.strip());
		if(checkedUrl != ""):
			status = requests.head(checkedUrl, timeout=to)
			visited(url, status)

		# Url done
		if(stdout=="enabled"):
			counted(lock, url, 0)

	except requests.ConnectionError:
		lock.acquire()
		responses.append((url,"[Connection error]"))
		lock.release()
		if(stdout=="enabled"):
			counted(lock, url, 1)
	except requests.exceptions.Timeout:
		lock.acquire()
		responses.append((url,"[Timeout error]"))
		lock.release()
		if(stdout=="enabled"):
			counted(lock, url, 1)
	except:
		lock.acquire()
		responses.append((url,"[Unknown error]"))
		lock.release()
		if(stdout=="enabled"):		
			counted(lock, url, 1)


# Count file length
if stdout!="disabled":
	output = open(inputfile, 'a')
	with open(inputfile) as fp:
		line = fp.readline()
		while line:
			if line.strip()!="":
				total+=1
				if(len(line.strip())>maxUrl):
					maxUrl=len(line.strip())
			line = fp.readline()
	print("Total URLs: " + str(total) + "\n")
	output.close()
	maxUrl+=len("Launching ")+(len(str(total))*2)+1


# Launch threads
lock = threading.Lock()
i=0
with open(inputfile) as fp:
	line = fp.readline()
	while line:
		i+=1
		if line.strip()!="":
			if(stdout=="enabled"):
				sys.stdout.write("Launching " + colored(str(i) + "/"+ str(total), "blue") +" -> " + line.strip() + "\r")
				sys.stdout.flush()
			elif(stdout=="less"):
				sys.stdout.write("Launching thread " + colored("#"+str(i), "blue") + "\r")
				sys.stdout.flush()
			t = threading.Thread(target=visitThread, args=(line.strip(), visit_timeout, lock))
			launched_threads.append(t)
			time.sleep(sleeptime)
			t.start()
		line = fp.readline()


# Wait for termination
for t in launched_threads:
	t.join()

# Write to output
j=0;
try:
	os.remove(outputfile)
except:
	pass

out = open(outputfile, 'a')
length = float(len(responses))
i=0.0
if stdout!="disabled":
	print("")
for u in responses:
	out.write("[" + str(u[1]).split("[")[1].split("]")[0] + "] " + u[0] + "\n")
	i+=1.0
	if(stdout=="enabled"):
		sys.stdout.write("Writing... " + str(format(round((i/length)*100,2))) + "%\r")
		sys.stdout.flush()
out.close()

if(stdout!="disabled"):
	# Print summary
	print("\n")
	for k in summary.keys():
		print("Response [" + str(k) + "] -> " + str(summary[k]) + " times")
	print("")
	print("Output in " + outputfile)
