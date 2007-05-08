# (c) August 2006, Emin Gun Sirer
# Distributed under the GNU Public License, v2
# See the file COPYING for copyright info
#
#
# This file describes the object hierarchy in the bibliography itself
# 

import re
import sys

# Matching URIs
linkre = re.compile("[a-zA-Z][-+.a-zA-Z0-9]*://([:/?#[\]@!$&'()*+,;=a-zA-Z0-9_\-.~]|%[0-9a-fA-F][0-9a-fA-F]|\\-|\s)*")
linksub = re.compile("\\-\s")

# Co-ordination so as not to re-use citation keys
usedlabels = []

# Piece an entry together.
def punctuate(bib, string, punctuation, tail=' ', braces=False):
    value = str.strip(string)
    if value == '':
	return value
    addpunct = True
    if bib.punctuation.match(string):
	addpunct = False
    if braces:
        value = '{' + value + '}'
    if addpunct:
	value += punctuation
    value += tail
    return value

# Glue for object references.
class objref:

    def __init__(self, key, bib):
	self.key = key
	self.bib = bib

    def value(self):
	return self.bib[self.key]

    def __str__(self):
	return str(self.value())

    def __eq__(self, other):
	return isinstance(other, objref) and self.bib == other.bib and self.key == other.key

    def __ne__(self, other):
	return not self.__eq__(other)

# Formatter for field = value strings
def fieldval(field, value):
    if isinstance(value, objref):
	return "%s = %s" % (field, value.key)
    else:
	try:
	    return "%s = %d" % (field, int(str(value)))
	except ValueError:
	    return "%s = \"%s\"" % (field, str(value))

# Some sugar to make extension really easy.
class requirement:
    def __str__(self):
	return ''

def unassigned(field):
    return isinstance(field, requirement) or str(field) == ''

REQUIRED = requirement()
OPTIONAL = requirement()

# Base class of bibliography objects
class bibobject(object):

    def __init__(self, file, line, bib):
        self._bib = bib
        self._line = line
        self._file = file
        self._name = type(self).__name__
        self._name = self._name[self._name.find('.') + 1:]
        self._options = self._bib.options
	self._fields = [key for key in dir(self) if key[0] != '_']
	self._conditionals = []
	self._defaults = []
	self._citekey = None
	self._requirements = {}
	for field in self._fields:
	    self._requirements[field] = getattr(self, field)

    def _assign(self, key, value, condition={}, default=False):
	if not hasattr(self, key):
            raise ValueError, "%s has no such field %s" % (self._name, key)
	for field in condition:
	    if not hasattr(self, field):
                raise ValueError, "%s has no such field %s" % (self._name, field)
	if default:
	    if (key, value, condition) not in self._defaults:
	        self._defaults += [(key, value, condition)]
	else:
	    if (key, value, condition) not in self._conditionals:
	        self._conditionals += [(key, value, condition)]

    def _resolve(self):
	for field in self._fields:
	    setattr(self, field, self._requirements[field])
	next = self._conditionals[:]
	changed = True
	usedefaults = True
	if not self._defaults:
	    usedefaults = False
	while changed:
	    changed = False
	    conditionals = next
	    inherit = []
	    next = []
	    for key, value, condition in conditionals:
		if not hasattr(self, key) or not unassigned(getattr(self, key)):
		    continue
		meets = 1
		for field in condition:
		    fieldvalue = getattr(self, field)
		    if unassigned(fieldvalue):
			meets = 0
		    elif fieldvalue != condition[field]:
			meets = -1
		if meets == 1:
		    setattr(self, key, value)
		    if isinstance(value, objref):
			inherit += self._inherit(value.value())
		    changed = True
		elif meets == 0:
		    next += [(key, value, condition)]
	    next += inherit
	    if not changed and usedefaults:
		next += self._defaults
		usedefaults = False
		changed = True

    def _inherit(self, value):
	fields = []
	for key, value, condition in value._conditionals:
	    possible = True
	    if not hasattr(self, key):
		possible = False
	    for field in condition:
		if not hasattr(self, key):
		    possible = False
	    if possible:
		fields += [(key, value, condition)]
	return fields

    def _check(self):
        for field in self._fields:
            if getattr(self, field) == REQUIRED:
                raise ValueError, "field %s, required by %s, is missing" % (field, self._name)

    def _tobibtex(self):
        pass

class authorlist(list):
    def __init__(self, options):
        self._options = options

    def __str__(self):
        if self._options.convert == 'bib' or self._options.convert == 'xtx':
            return ' and '.join([ str(author) for author in self ])
        value = ''
        for i in range(0, len(self)):
            if value != '':
                if i == len(self) - 1:
                    value += ' and '
                else:
                    value += ', '
            if i == 0 and self._options.last_first:
                value += self[i]._last_first()
            else:
                value += str(self[i])
        return value
            
    def _bibpromote(self, other):
        for obj in self:
            if hasattr(obj, '_bibpromote'):
                obj._bibpromote(other)
            
class string(bibobject):
    name = REQUIRED
    shortname = REQUIRED

    def _assign(self, key, value, condition={}, default=False):
        # longname is an alias for name
        if key == 'longname':
            key = 'name'

	bibobject._assign(self, key, value, condition, default)

	try:
            # With shortname, name is optional and vice versa
            if key == 'shortname':
		self._requirements['name'] = OPTIONAL
            if key == 'name':
		self._requirements['shortname'] = OPTIONAL
	except ValueError:
	    pass

    def __str__(self):
	value = REQUIRED
	if self._name in self._options.short:
	    value = self.shortname
	if unassigned(value):
	    value = self.name
	if unassigned(value):
	    value = self.shortname
	value = str(value)
	if self._name in self._options.capitalize:
	    value = self._bib.titlecase(value, 'upper', False)
	return value

class author(string):
    address = OPTIONAL
    affiliation = OPTIONAL
    email = OPTIONAL
    institution = OPTIONAL
    organization = OPTIONAL
    phone = OPTIONAL
    school = OPTIONAL
    url = OPTIONAL

    def _names(self, plain=False):
        name = string.__str__(self)
        value = ""
        lastchar = ' '
        names = []
        nesting = 0
        for i in range(0,len(name)):
            charc = name[i]
            if nesting == 0 and lastchar != '\\' and lastchar != ' ' and charc == " ":
                names.append(value)
                value = ""
            elif lastchar != '\\' and charc == "}":
		if not plain:
                    value += charc
                if nesting == 0:
                    names.append(value)
                    value =""
                else:
                    nesting -= 1
            elif lastchar != '\\' and charc == "{":
		if not plain:
                    value += charc
                nesting += 1
            elif nesting == 0 and lastchar != '\\' and charc == ",":
                pass
            else:
		if not plain or (charc != '\\' and lastchar != '\\'):
                    value += charc
            lastchar = charc
        names.append(value)

        # extract lastname, check suffixes and last name modifiers
        # extract also a list of first names
        snames = ["Jr.", "Sr.", "Jr", "Sr", "III", "IV"]
	mnames = ["van", "von", "de", "bin", "ibn"]
        sname = ""
        snameoffset = len(names)
        while snameoffset > 0 and names[snameoffset - 1] in snames:
	    snameoffset -= 1
        mnameoffset = 0
        while mnameoffset < snameoffset and names[mnameoffset] not in mnames:
	    mnameoffset += 1
	lnameoffset = snameoffset
        while lnameoffset > 0 and names[lnameoffset - 1] not in mnames:
	    lnameoffset -= 1
	if lnameoffset <= mnameoffset:
	    lnameoffset = mnameoffset = snameoffset - 1
	    
        # return the person info as a 3-tuple
        return (names[:mnameoffset], names[mnameoffset:lnameoffset], names[lnameoffset:snameoffset], names[snameoffset:])

    def _last_initials(self, size):
	(fnames, mnames, lnames, snames) = self._names()
	namestr = ""
	for lname in mnames + lnames:
	    if len(namestr) >= len(mnames) + size:
		break
	    first = 0
	    while first < len(lname):
	        if lname[first] not in "{}\\":
		    namestr += lname[first]
		    if len(namestr) >= size:
		        break
		    first += 1
	        elif lname[first] == "\\":
		    first += 2
	        else:
		    first += 1
	return namestr

    def __cmp__(self, other):
	if isinstance(other, author):
	    return cmp(self._names(True)[2], other._names(True)[2])
	else:
	    return cmp(self._names(True)[2], other)

    def _last_first(self):
        if self._name in self._options.short and not unassigned(self.shortname):
            return str(self.shortname)
        else:
            (fnames, mnames, lnames, snames) = self._names()
            namestr = ""
            for n in mnames:
                if namestr != "":
                    namestr += " "
                namestr += n
            for n in lnames:
                if namestr != "":
                    namestr += " "
                namestr += n
            if len(fnames) > 0:
                namestr += ', '
            for n in fnames:
                if self._name in self._options.short:
                    first = 0
                    while first < len(n):
                        if n[first] not in "{}\\":
                            if namestr != "":
                                namestr += "~"
                            namestr += n[first] + "."
                            break
                        elif n[first] == "\\":
                            first += 2
                        else:
                            first += 1
                else:
                    if namestr != "":
                        namestr += " "
                    namestr += n
	    for n in snames:
                if namestr != "":
                    namestr += ", "
		namestr += n
            return namestr

    def __str__(self):
        if self._name in self._options.short and not unassigned(self.shortname):
            return str(self.shortname)
        else:
            (fnames, mnames, lnames, snames) = self._names()
            namestr = ""
            for n in fnames:
                if self._name in self._options.short:
                    first = 0
                    while first < len(n):
                        if n[first] not in "{}\\":
                            if namestr != "":
                                namestr += "~"
                            namestr += n[first] + "."
                            break
                        elif n[first] == "\\":
                            first += 2
                        else:
                            first += 1
                else:
                    if namestr != "":
                        namestr += " "
                    namestr += n
            for n in mnames:
                if namestr != "":
                    namestr += " "
                namestr += n
            for n in lnames:
                if namestr != "":
                    namestr += " "
                namestr += n
	    for n in snames:
                if namestr != "":
                    namestr += ", "
		namestr += n
            return namestr

class state(string):
    country = OPTIONAL

class country(string):
    pass

class location(bibobject):
    city = OPTIONAL
    state = OPTIONAL
    country = OPTIONAL

    def __str__(self):
        value = ''
        if not unassigned(self.city):
            if value != '':
                value += ', '
            value += str(self.city)
        if not unassigned(self.state):
            if value != '':
                value += ', '
            value += str(self.state)
        if not unassigned(self.country):
            if value != '':
                value += ', '
            value += str(self.country)
        return value

class month(string):
    monthno = REQUIRED

    def __cmp__(self, other):
	if isinstance(other, month):
	    return cmp(int(self.monthno), int(other.monthno))
	else:
	    return cmp(int(self.monthno), other)

class journal(string):
    pass

# Base for all publications, everything optional.
class misc(bibobject):
    abstract = OPTIONAL
    address = OPTIONAL
    affiliation = OPTIONAL
    annote = OPTIONAL
    author = OPTIONAL
    bib = OPTIONAL
    bibsource = OPTIONAL
    booktitle = OPTIONAL
    category = OPTIONAL
    subcategory = OPTIONAL
    chapter = OPTIONAL
    contents = OPTIONAL
    copyright = OPTIONAL
    crossref = OPTIONAL
    doi = OPTIONAL
    dvi = OPTIONAL
    edition = OPTIONAL
    editor = OPTIONAL
    ee = OPTIONAL
    ftp = OPTIONAL
    howpublished = OPTIONAL
    html = OPTIONAL
    http = OPTIONAL
    institution = OPTIONAL
    isbn = OPTIONAL
    issn = OPTIONAL
    journal = OPTIONAL
    key = OPTIONAL
    keywords = OPTIONAL
    language = OPTIONAL
    lccn = OPTIONAL
    location = OPTIONAL
    month = OPTIONAL
    monthno = OPTIONAL
    mrnumber = OPTIONAL
    note = OPTIONAL
    number = OPTIONAL
    organization = OPTIONAL
    pages = OPTIONAL
    pdf = OPTIONAL
    price = OPTIONAL
    ps = OPTIONAL
    publisher = OPTIONAL
    rtf = OPTIONAL
    school = OPTIONAL
    series = OPTIONAL
    size = OPTIONAL
    title = OPTIONAL
    type = OPTIONAL
    url = OPTIONAL
    volume = OPTIONAL
    year = OPTIONAL

    _numbertype = ''

    def _assign(self, key, value, condition={}, default=False):
	bibobject._assign(self, key, value, condition, default)
	try:

            # With author, editor is optional and vice versa
            if key == 'editor':
		self._requirements['author'] = OPTIONAL
            if key == 'author':
		self._requirements['editor'] = OPTIONAL

            # With chapter, pages is optional and vice versa
            if key == 'pages':
		self._requirements['chapter'] = OPTIONAL
            if key == 'chapter':
		self._requirements['pages'] = OPTIONAL

	except ValueError:
	    pass

    def _label(self):
        # Compute a new label
        global usedlabels
        if hasattr(self, '_citelabel'):
            return self._citelabel
        label = ''
        authors = self.author
	if unassigned(authors):
	    authors = self.editor
        if unassigned(authors) or len(authors) == 0:
	    if self._options.cite_by != 'number' and not unassigned(self.key):
	        label = str(self.key)
        elif self._options.cite_by == 'initials':
            if len(authors) == 1:
                label += authors[0]._last_initials(3)
            elif len(authors) <= 4:
                for i in range(0, min(len(authors), 4)):
                    label += authors[i]._last_initials(1)
            else:
                for i in range(0, min(len(authors), 3)):
                    label += authors[i]._last_initials(1)
                label += "{\etalchar{+}}"
            if not unassigned(self.year):
                   label += "%02d" % (int(str(self.year)) % 100)
        elif self._options.cite_by == 'fullname':
            if len(authors) == 2:
                (fnames1, mnames1, lnames1, snames1) = authors[0]._names()
                (fnames2, mnames1, lnames2, snames2) = authors[1]._names()
                label += ' '.join(lnames1) + " \& " + ' '.join(lnames2)
            else:
                (fnames1, mnames1, lnames1, snames1) = authors[0]._names()
                label += ' '.join(lnames1)
                if len(authors) > 2:
                    label += " et al."
            if not unassigned(self.year):
                label += str(self.year)
        # Ensure the label is unique
        if label in usedlabels:
            for char in list("abcdefghijklmnopqrstuvwxyz"):
                if label + char not in usedlabels:
                    label += char
                    break
            else:
                sys.stderr.write("crosstex: too many citations with key %s" % label)
        if label != '':
            usedlabels.append(label)
        self._citelabel = label
        return self._citelabel

    def _title(self):
        value = ''
	if not unassigned(self.title):
	    value = str(self.title)
            if self._options.titlecase != 'as-is':
                value = self._bib.titlecase(value, self._options.titlecase)
        return value

    def _publication(self):
	value = ''
	if not unassigned(self.howpublished):
	    value = str(self.howpublished)
	return value

    def _fullauthors(self):
	value = ''
	if not unassigned(self.author):
	    value = punctuate(self._bib, str(self.author), '.', '')
        elif not unassigned(self.editor):
	    value = punctuate(self._bib, str(self.editor), ',', ' ed.')
        return value

    def _fulltitle(self):
        return punctuate(self._bib, self._title(), '.', '', braces=True)

    def _fullpublication(self):
        value = self._publication()
        if not unassigned(self.booktitle) and value == '':
	    value = punctuate(self._bib, value, '.')
            value += "In \emph{%s}" % str(self.booktitle)
	    if not unassigned(self.volume):
	        value += ", volume %s" % str(self.volume)
		if not unassigned(self.series):
		    value += " of \em{%s}" % str(self.series)
	    if not unassigned(self.chapter):
	        value += ", chapter %s" % str(self.chapter)
	    if not unassigned(self.pages):
	        value += ", pages %s" % str(self.pages)
        elif not unassigned(self.journal):
	    value = punctuate(self._bib, value, ',')
            value += self._options.in_str
	    value = punctuate(self._bib, value, '')
            value += "\emph{%s}" % str(self.journal)
	    if not unassigned(self.number) or not unassigned(self.pages) or not unassigned(self.volume):
		value = punctuate(self._bib, value, ',')
	    if not unassigned(self.volume):
		value += str(self.volume)
	    if not unassigned(self.number):
		value += "(%s)" % str(self.number)
	    if not unassigned(self.pages):
		if not unassigned(self.volume) or not unassigned(self.number):
		    value += ":%s" % str(self.pages)
		else:
		    value += "pages %s" % str(self.pages)
        if not unassigned(self.institution):
	    value = punctuate(self._bib, value, ',')
            value += str(self.institution)
        if not unassigned(self.school):
	    value = punctuate(self._bib, value, ',')
            value += str(self.school)
	if unassigned(self.journal):
	    if not unassigned(self.number):
	        value = punctuate(self._bib, value, ',')
		value += self._numbertype
	        value = punctuate(self._bib, value, '')
		value += str(self.number)
            if not unassigned(self.pages):
	        value = punctuate(self._bib, value, ',')
	        value += "pages %s" % str(self.pages)
        if not unassigned(self.author) and not unassigned(self.editor):
	    value = punctuate(self._bib, value, ',')
            value += "%s, ed." % str(self.editor)
        if not unassigned(self.publisher):
	    value = punctuate(self._bib, value, ',')
            value += str(self.publisher)
        if not unassigned(self.address):
	    value = punctuate(self._bib, value, ',')
            value += str(self.address)
        if not unassigned(self.year):
	    value = punctuate(self._bib, value, ',')
            if not unassigned(self.month):
                value += str(self.month)
	        value = punctuate(self._bib, value, '')
            value += str(self.year)
	value = punctuate(self._bib, value, '.', braces=True)
        return value

    def __str__(self):
        if self._options.convert == 'bib':
            value = "@%s{%s" % (self._name, self._primarykey)
            for field in self._fields:
                fieldvalue = getattr(self, field)
		if not unassigned(fieldvalue):
		    value += ",\n\t" + fieldval(field, fieldvalue)
            value += "}\n\n"
        elif self._options.convert == 'xtx':
            value = "@%s{%s" % (self._name, self._primarykey)
            for field, fieldvalue, condition in self._conditionals:
		if self._bib.options.heading and field in [x[1] for x in self._bib.options.heading[-self._bib.options.headingdepth-1:]]:
		    continue
		value += ",\n\t"
		if condition:
		    value += '['
		    for k, v in condition:
			if value[-1] != '[':
			    value += ', '
			value += fieldval(k, v)
		    value += '] '
		value += fieldval(field, fieldvalue)
            value += "}\n\n"
        else:
            value = ''
	    valueauthor = self._fullauthors()
	    valuetitle = self._fulltitle()
	    valuepublication = self._fullpublication()
	    if valuetitle != '':
		valuetitle = "\\textbf{%s}" % valuetitle
	    if self._options.title_head:
		if valuetitle != '':
		    value = punctuate(self._bib, value, "\n\\newblock")
		    value += valuetitle
		if valueauthor != '':
		    value = punctuate(self._bib, value, "\n\\newblock")
		    value += valueauthor
	    else:
		if valueauthor != '':
		    value = punctuate(self._bib, value, "\n\\newblock")
		    value += valueauthor
		if valuetitle != '':
		    value = punctuate(self._bib, value, "\n\\newblock")
		    value += valuetitle
	    if valuepublication != '':
		value = punctuate(self._bib, value, "\n\\newblock")
		value += valuepublication

            abstractlink = False
	    links = ''
	    for field in self._options.link:
		myfield = field.lower()
		if hasattr(self, myfield) and getattr(self, myfield) != '':
		    for m in linkre.finditer(str(getattr(self, myfield))):
			uri = m.group()
			linksub.sub(uri, "")
			links = punctuate(self._bib, links, '')
			links += "\\href{%s}{\\small\\textsc{%s}}" % (uri, field)
			if myfield == 'abstract':
			    abstractlink = True
	    if links != '':
		value = punctuate(self._bib, value, "\n\\newblock")
		value += links

            if not unassigned(self.abstract) and self._options.abstract and not abstractlink:
		value = punctuate(self._bib, value, "\n")
                value += "\\begin{quotation}\\noindent\\begin{small}%s\\end{small}\\end{quotation}" % str(self.abstract)
            if not unassigned(self.keywords) and self._options.keywords:
		value = punctuate(self._bib, value, "\n")
                value += "\\begin{quote}\\begin{small}\\textsc{Keywords:} %s\\end{small}\\end{quote}" % str(self.keywords)

	    if not unassigned(self.url) and self._name != 'url':
		value = punctuate(self._bib, value, "\n\\newblock")
		value += punctuate(self._bib, str(self.url), '.')

	    if not unassigned(self.note):
		value = punctuate(self._bib, value, "\n\\newblock")
		value += punctuate(self._bib, str(self.note), '.')

            label = self._label()
            if label != '':
                label = '[%s]' % label
	    if self._citekey == None:
                value = "\\bibitem%s{}\n%s\n\n" % (label, str.strip(value))
	    else:
                value = "\\bibitem%s{%s}\n%s\n\n" % (label, self._citekey, str.strip(value))
        return value

class article(misc):
    author = REQUIRED
    title = REQUIRED
    journal = REQUIRED
    year = REQUIRED

class book(misc):
    author = REQUIRED
    editor = REQUIRED
    title = REQUIRED
    publisher = REQUIRED
    year = REQUIRED

class booklet(misc):
    title = REQUIRED

class inbook(misc):
    author = REQUIRED
    editor = REQUIRED
    title = REQUIRED
    chapter = REQUIRED
    pages = REQUIRED
    publisher = REQUIRED
    year = REQUIRED

class incollection(misc):
    author = REQUIRED
    title = REQUIRED
    booktitle = REQUIRED
    publisher = REQUIRED
    year = REQUIRED

class inproceedings(misc):
    author = REQUIRED
    title = REQUIRED
    booktitle = REQUIRED
    year = REQUIRED

    def _publication(self):
        value = 'In ' + self._options.proceedings_str
	value = punctuate(self._bib, value, '')
        value += "\emph{%s}" % str(self.booktitle)
        return value

class manual(misc):
    title = REQUIRED

class thesis(misc):
    author = REQUIRED
    title = REQUIRED
    school = REQUIRED
    year = REQUIRED

    _thesistype = ''

    def _publication(self):
	value = self.type
	if unassigned(value):
            value = self._thesistype
	    value = punctuate(self._bib, value, '')
            value += 'Thesis'
        return value

class mastersthesis(thesis):
    _thesistype = "Master's"

class phdthesis(thesis):
    _thesistype = "Ph.D."

class proceedings(misc):
    title = REQUIRED
    year = REQUIRED

class collection(proceedings):
    pass

class patent(misc):
    author = REQUIRED
    title = REQUIRED
    number = REQUIRED
    month = REQUIRED
    year = REQUIRED

    _numbertype = 'United States Patent'

class techreport(misc):
    author = REQUIRED
    title = REQUIRED
    institution = REQUIRED
    year = REQUIRED

    _numbertype = 'Technical Report'

class unpublished(misc):
    author = REQUIRED
    title = REQUIRED
    note = REQUIRED

# New objects in CrossTeX:

# In BibTeX, conference was the same as inproceedings.
# This one's a string instead, and is closer to proceedings.
class conference(string):
    address = OPTIONAL
    crossref = OPTIONAL
    editor = OPTIONAL
    institution = OPTIONAL
    isbn = OPTIONAL
    key = OPTIONAL
    keywords = OPTIONAL
    language = OPTIONAL
    location = OPTIONAL
    month = OPTIONAL
    publisher = OPTIONAL
    url = OPTIONAL
    year = OPTIONAL

class conferencetrack(conference):
    conference = OPTIONAL

    def __str__(self):
        if not unassigned(self.conference):
            return str(self.conference) + ", " + string.__str__(self)
        else:
            return string.__str__(self)

class workshop(conferencetrack):
    pass

class rfc(misc):
    author = REQUIRED
    title = REQUIRED
    number = REQUIRED
    month = REQUIRED
    year = REQUIRED

    def _publication(self):
        return "IETF Request For Comments %s" % str(self.number)

class url(misc):
    url = REQUIRED
    accessmonth = OPTIONAL
    accessyear = OPTIONAL

    def _publication(self):
	value = str(self.url)
        if not unassigned(self.accessyear):
	    value = punctuate(self._bib, value, ',')
	    value += 'Accessed'
	    value = punctuate(self._bib, value, '')
            if not unassigned(self.accessmonth):
                value += str(self.accessmonth)
	        value = punctuate(self._bib, value, '')
            value += str(self.accessyear)
	return value

class newspaperarticle(article):
    author = OPTIONAL

    def _assign(self, key, value, condition={}, default=False):
         # newspaper is an alias for journal
         if key == 'newspaper':
             key = 'journal'

         article._assign(self, key, value, condition, default)

class newspaper(journal):
    pass
