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
# Global variables
stdout = "enabled"
errors = True
responses=[]
done=0
total=0;
summary={}
maxUrl=0
lock = threading.Lock()
filter_status=None


def isError(s):
	error_status=["Connection_error", "Timeout_error", "Unknown_error"]
	return s in error_status


def signal_handler(sig, frame):
	sys.stdout.flush()
	print('\n\nAborted!')
	os._exit(130)


def checkUrl(url):
	try:
		checked = re.findall('(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url)
		#checked = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url)
	except:
		return False
	
	return len(checked)==1

def visited(url, status):
	global lock	
	lock.acquire()

	global summary
	global responses
	if (url,status.status_code) not in responses: 
		responses.append((url,status.status_code))
		if status.status_code in summary.keys():
			summary[status.status_code]=summary[status.status_code]+1
		else:
			summary[status.status_code]=1
	lock.release()


def counted(url, status):
	if(stdout=="disabled"):
		return

	global lock
	lock.acquire()

	global done
	global maxUrl
	global total
	global errors
	global filter_status

	done+=1
	padding=(" " *(maxUrl-len(url)+27))

	sys.stdout.write("Visited... " + str(("{:.2f}").format(round((done/total)*100,2))) + "%" + padding + "\r")
	sys.stdout.flush()
	
	if stdout=="enabled":

		if not isError(str(status)):
			code=status.status_code
		else:
			code=status

		if(filter_status!=None and str(code)==filter_status) or  filter_status==None: 
			if not errors:
				if not isError(str(status)):
					print("Visited " + colored(str(done) + "/" + str(total),"green") + " -> " + url + padding)
			elif errors:
				if isError(str(status)):
					print("Visited " + colored(str(done) + "/" + str(total),"green") + " -> " + colored(url,"red") + padding)
				else:
					print("Visited " + colored(str(done) + "/" + str(total),"green") + " -> " + url + padding)
	lock.release()
	return done


def visitThread(url, to):
	global lock
	global responses
	global stdout
		
	try:

		# Test HTTPS
		status = requests.head("https://"+url.strip(), timeout=to, allow_redirects=True)
		# Test HTTP
		status = requests.get("http://"+url.strip(), timeout=to, allow_redirects=True)

		# Url done
		visited(url, status)
		counted(url, status)

	except requests.ConnectionError:
		lock.acquire()
		responses.append((url,"Connection_error"))
		lock.release()
		counted(url, "Connection_error")
	except requests.exceptions.Timeout:
		lock.acquire()
		responses.append((url,"Timeout_error"))
		lock.release()
		counted(url, "Timeout_error")
	except:
		lock.acquire()
		responses.append((url,"Unknown_error"))
		lock.release()
		counted(url, "Unknown_error")


def readFile(inputfile):
	global urlList
	global total
	global maxUrl

	urlList = []
	with open(inputfile) as fp:
		line = fp.readline().strip()
		while line:
			if (line!="") and (line!="\n") and checkUrl(line) and (line not in urlList):
				urlList.append(line)
				total+=1
				if(len(line.strip())>maxUrl):
					maxUrl=len(line.strip())
			line = fp.readline().strip()
	if stdout!="disabled":
		print("Total URLs: " + str(total) + "\n")
	maxUrl+=len("Launching ")+(len(str(total))*2)+1
	return urlList


def writeOutput(outputfile):

	global responses
	global stdout
	global errors
	global filter_status

	try:
		os.remove(outputfile)
	except:
		pass
	out = open(outputfile, 'a')
	length = float(len(responses))
	i=0.0

	for u in responses:
		if(filter_status!=None and str(u[1])==filter_status) or  filter_status==None: 
			if not errors:		
				if not isError(u[1]):				
					out.write("[" + str(u[1]) + "] " + u[0] + "\n")
			else:
				out.write("[" + str(u[1]) + "] " + u[0] + "\n")
		
		i+=1.0
		if(stdout=="enabled"):
			padding=(" " *(maxUrl+27))
			sys.stdout.write("Writing... " + str(format(round((i/length)*100,2))) + "%" + padding + "\r")
			sys.stdout.flush()
	out.close()


def printSummary():
	if(stdout!="disabled"):
		print("\n")
		for k in summary.keys():
			print("Response [" + str(k) + "] -> " + str(summary[k]) + " times")
		print("")
		print("Output saved in '" + os.path.abspath(outputfile) + "'")


if __name__ == "__main__":

	inputfile=None
	outputfile=None

	desc = "Given a list of URLs, tests the HTTP response codes and write them into a file. "
	desc+="URLs must not begin with the protocol ('http://' or 'https://')\n"
	parser = argparse.ArgumentParser(description=desc)
	parser.add_argument('input', metavar='inputfile', help='path of input file. A list of URLs, each for row.')
	parser.add_argument('output', metavar='outputfile', help='path of output file. An empty file to append output.')
	parser.add_argument('--stdout', metavar='[enabled, less, disabled]', help='edit verbosity of stdout print.')
	parser.add_argument('--errors', metavar='[yes, no]', help='save or not errors')
	parser.add_argument('--filter', metavar='[200, 301, ..]', help='a status code to filter')
	args = parser.parse_args()


	inputfile = args.input
	outputfile = args.output
	filter_status = args.filter

	if args.stdout!=None:
		stdout=args.stdout

	if args.errors!=None:
		if args.errors=="no":	
			errors=False	

	if(stdout != "disabled"):
		cprint(logo,"red")

	if inputfile==None or outputfile==None:
		print(parser.print_help())
		exit(1)

	try:
		f = open(inputfile)
	except IOError:
		print("File not found: " + inputfile)
		exit(1)
	finally:
		try:
			f.close()
		except Exception:
			pass

	signal.signal(signal.SIGINT, signal_handler)

	urlList = readFile(inputfile)

	# Launch threads
	launched_threads=[]
	visit_timeout=5
	sleeptime=0
	i=0
	for line in urlList:
		i+=1
		if line.strip()!="":
			if(stdout=="enabled"):
				sys.stdout.write("Launching " + colored(str(i) + "/"+ str(total), "blue") +" -> " + line.strip() + "\r")
				sys.stdout.flush()
			t = threading.Thread(target=visitThread, args=(line.strip(), visit_timeout))
			launched_threads.append(t)
			time.sleep(sleeptime)
			t.start()

	# Wait for termination
	for t in launched_threads:
		t.join()

	writeOutput(outputfile)

	printSummary()
