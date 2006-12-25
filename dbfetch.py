#! /usr/bin/env python
#
# Fetch content from DBLP 
#
# Author: Emin Gun Sirer

import thread
import socket 
import time
import urllib
import re

def getbibtex(str):
    url = urllib.urlopen(str)
    contents = url.read()
    url.close()
    match = re.compile("<pre>(.*)</pre>", re.S).search(contents)
    bibtex = match.group(1)
    return re.sub(r'<([^>]*)>', '', bibtex)
    
#name = "sosp"
#years = range(71,100,2) + range(2001,2006,2)
#name = "osdi"
#years = [94, 96, 99] + range(2000,2007,2)
#name = "sigcomm"
#years = range(1985,2007,1)
#name = "nsdi"
#years = [2004]
name = "podc"
years = range(82,100,1) + range(2000,2007,1)
for i in years:
    print "%%\n%% %s %d\n%%" % (name, i)
    str = "http://www.informatik.uni-trier.de/~ley/db/conf/%s/%s%s.html" % (name,name,i)
    url = urllib.urlopen(str)
    contents = url.read()
    url.close()

    iter = re.compile("<a href=\"([^\"]+)\">BibTeX</a>", re.M).finditer(contents)
    try:
        match = iter.next()
	while match:
	      str = match.group(1)
	      match = iter.next()
	      #	  fetch the URL
              print getbibtex(str)
    except:
	pass

	
