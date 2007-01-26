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
import sys

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
#name = "podc"
#years = range(82,100,1) + range(2000,2007,1)
#name = "mobicom"
#years = range(1995,2006,1)
#name = "soda"
#years = range(90, 100, 1) + range(2000, 2007, 1)
#name = "icdcs"
#years = [82] + range(84, 91, 1) + range(92, 100, 1) + range(2000, 2007, 1) + ["w2000", "w2002", "w2003", "w2004", "w2005", "w2006"]
#name = "usenix"
#years = ["_su86", "_su87", "_wi88", "_su90", "_wi91", "_su91", "_wi93", "_su93", "_wi94", "_su94", "_wi95", "96", "1999f", "1999g", "2000f", "2000g", "2001f", "2001g", "2002f", "2002g", "2003f", "2003g", "2004f", "2004g"]

base = 'http://www.informatik.uni-trier.de/~ley/db/conf/'

for name in sys.argv[1:]:
    file = open(name + '.bib', 'w')

    print name
    confurl = urllib.urlopen(base + name + '/index.html')
    confcontents = confurl.read()
    confurl.close()

    confiter = re.compile("<a href=\"([^\"]+)\">Contents</a>", re.M).finditer(confcontents)

    for confmatch in confiter:
        year = confmatch.group(1)

        print year
	yearurl = urllib.urlopen(base + name + '/' + year)
	contents = yearurl.read()
	yearurl.close()

	iter = re.compile("<a href=\"([^\"]+)\">BibTeX</a>", re.M).finditer(contents)

	for match in iter:
	    str = match.group(1)
	    file.write(getbibtex(str))
