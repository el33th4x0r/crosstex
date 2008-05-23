#! /usr/bin/env python
#
# Fetch content from DBLP 
#
# Author: Emin Gun Sirer
# Updated by Robert Burgess January 2007

import thread
import socket 
import time
import urllib
import re
import sys

base = 'http://www.informatik.uni-trier.de/~ley/db/conf/'
contentre = "<a href=\"([^\"]+)\">Contents</a>"
bibtexre = "<a href=\"([^\"]+)\">BibTeX</a>"

def getbibtex(str):
    url = urllib.urlopen(str)
    contents = url.read()
    url.close()
    match = re.compile("<pre>(.*)</pre>", re.S).search(contents)
    bibtex = match.group(1)
    return re.sub(r'<([^>]*)>', '', bibtex)

for name in sys.argv[1:]:
    file = open(name + '.bib', 'w')

    print name, base + name + '/index.html'
    confurl = urllib.urlopen(base + name + '/index.html')
    confcontents = confurl.read()
    confurl.close()

    linkre = re.compile("<a href=\"([^/]+[^\"/]*.html)\">")

    for confmatch in linkre.finditer(confcontents):
	year = confmatch.group(1)

        print '  ' + year
	yearurl = urllib.urlopen(base + name + '/' + year)
	contents = yearurl.read()
	yearurl.close()

	for match in re.compile(bibtexre, re.M).finditer(contents): 
	    str = match.group(1)
	    file.write(getbibtex(str))
