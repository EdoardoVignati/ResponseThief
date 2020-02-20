#!/usr/bin/env python3
import requests
import threading
import time
import os
import sys
from termcolor import colored, cprint
import re

# Logo
cprint(""" 
 ____                                     _____ _     _       __ 
|  _ \ ___  ___ _ __   ___  _ __  ___  __|_   _| |__ (_) ___ / _|
| |_) / _ \/ __| '_ \ / _ \| '_ \/ __|/ _ \| | | '_ \| |/ _ \ |_ 
|  _ \  __/\__ \ |_) | (_) | | | \__ \  __/| | | | | | |  __/  _|
|_| \_\___||___/  __/ \___/|_| |_|___/\___||_| |_| |_|_|\___|_|  
               |_|             
                                               by @EdoardoVignati                                  
""","red")

# Arguments check
if len(sys.argv)!=3:
	print("Given a list of URLs, tests the response codes and write them into a file")
	print("URLs must not contain the protocol ('http://' or 'https://')\n")
	print("Usage:\n\t$ ./response-thief.py </path/to/inputfile.txt> </path/to/outputfile.txt>\n")
	exit()

# Global variables
inputfile = sys.argv[1]
outputfile = sys.argv[2]
responses=[]
launched_threads=[]
done=0
visit_timeout=5
total=0;
summary={}
maxUrl=0

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
		counted(lock, url, 0)

	except requests.ConnectionError:
		lock.acquire()
		responses.append((url,"[Connection error]"))
		lock.release()
		counted(lock, url, 1)
	except requests.exceptions.Timeout:
		lock.acquire()
		responses.append((url,"[Timeout error]"))
		lock.release()
		counted(lock, url, 1)
	except:
		lock.acquire()
		responses.append((url,"[Unknown error]"))
		lock.release()
		counted(lock, url, 1)



#Count file length
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
			sys.stdout.write("Launching " + colored(str(i) + "/"+ str(total), "blue") +" -> " + line.strip() + "\r")
			sys.stdout.flush()
			t = threading.Thread(target=visitThread, args=(line.strip(), visit_timeout, lock))
			launched_threads.append(t)
			time.sleep(0.1)
			t.start()
		line = fp.readline()
output.close()

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
print("")
for u in responses:
	out.write("[" + str(u[1]).split("[")[1].split("]")[0] + "] " + u[0] + "\n")
	i+=1.0
	sys.stdout.write("Writing... " + str(format(round((i/length)*100,2))) + "%\r")
	sys.stdout.flush()
out.close()

# Print summary
print("\n")
for k in summary.keys():
	print("Response [" + str(k) + "] -> " + str(summary[k]) + " times")
print("")
