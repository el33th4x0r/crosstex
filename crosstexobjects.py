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
	self._citekey = None

    def _assign(self, key, value, condition={}):
	try:
            if not unassigned(getattr(self, key)):
	        raise ValueError, "field %s has already been assigned" % key
	except AttributeError:
            raise ValueError, "%s has no such field %s" % (self._name, key)
	meets = True
	for field in condition:
	    try:
		fieldvalue = getattr(self, field)
		if unassigned(fieldvalue):
		    meets = False
		elif fieldvalue != condition[field]:
		    raise ValueError, "condition on %s is false" % field
	    except AttributeError:
                raise ValueError, "%s has no such field %s" % (self._name, key)
	if meets:
	    setattr(self, key, value)
	elif (key, value, condition) not in self._conditionals:
	    self._conditionals += [(key, value, condition)]
	return meets

    def _applyconditions(self):
	changed = True
	while self._conditionals and changed:
            unmet = self._conditionals
	    self._conditionals = []
	    changed = False
	    for key, value, condition in unmet:
		try:
		    if self._assign(key, value, condition):
			changed = True
		except ValueError:
		    pass

    def _applyinheritance(self):
	for field in self._fields:
	    value = getattr(self, field)
	    if isinstance(value, bibobject):
		self._inherit(value)

    def _inherit(self, value):
	for field in value._fields:
	    valuefield = getattr(value, field)
	    if not unassigned(valuefield):
		try:
		    self._assign(field, valuefield)
		except ValueError:
		    pass
	for field, valuefield, condition in value._conditionals:
	    try:
		self._assign(field, valuefield, condition)
	    except ValueError:
		pass

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
        if self._options.convert == 'bib':
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

    def _assign(self, key, value, condition={}):
        # longname is an alias for name
        if key == 'longname':
            key = 'name'

        value = bibobject._assign(self, key, value, condition)
	if value:

            # With shortname, name is optional and vice versa
            if key == 'shortname' and self.name == REQUIRED:
                self.name = OPTIONAL
            if key == 'name' and self.shortname == REQUIRED:
                self.shortname = OPTIONAL

        return value

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

    def _names(self):
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
                value += charc
                if nesting == 0:
                    names.append(value)
                    value =""
                else:
                    nesting -= 1
            elif lastchar != '\\' and charc == "{":
                value += charc
                nesting += 1
            elif nesting == 0 and lastchar != '\\' and charc == ",":
                pass
            else:
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
	    return cmp(self._names()[2], other._names()[2])
	else:
	    return cmp(self._names()[2], other)

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

    def _assign(self, key, value, condition={}):
	value = bibobject._assign(self, key, value, condition)
	if value:
	
            # With author, editor is optional and vice versa
            if key == 'editor' and self.author == REQUIRED:
                self.author = OPTIONAL
            if key == 'author' and self.editor == REQUIRED:
                self.editor = OPTIONAL

            # With chapter, pages is optional and vice versa
            if key == 'chapter' and self.pages == REQUIRED:
                self.pages = OPTIONAL
            if key == 'pages' and self.chapter == REQUIRED:
                self.chapter = OPTIONAL

	return value

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
            value = str(self.author)
            if value != '':
                value += "."
        elif not unassigned(self.editor):
            value = str(self.editor)
            if value != '':
                value += ", ed."
        return value

    def _fulltitle(self):
        value = self._title()
        if value != '':
            value = "{%s}" % value
            if value[-2] != '.':
                value += '.'
        return value

    def _fullpublication(self):
        value = self._publication()
        if not unassigned(self.booktitle) and value == '':
            value += "In {\\em %s}" % str(self.booktitle)
        if not unassigned(self.journal):
            if value != '':
                value += ', '
            if self._options.in_str != '':
                value += self._options.in_str
            else:
                value += ' '
            value += "{\\em %s}" % str(self.journal)
	    if not unassigned(self.volume):
		if not unassigned(self.number) and not unassigned(self.pages):
		    if value != '':
			value += ' '
		    value += 'Volume'
		value += " %s" % str(self.volume)
	    if not unassigned(self.number):
		value += "(%s)" % str(self.number)
	    if not unassigned(self.pages):
		value += ":%s" % str(self.pages)
	else:
            if not unassigned(self.pages):
	        value += ", pages %s" % str(self.pages)
        if not unassigned(self.author) and not unassigned(self.editor):
            if value != '':
                value += ', '
            value += "%s, ed." % str(self.editor)
        if not unassigned(self.publisher):
            if value != '':
                value += ', '
            value += str(self.publisher)
        if not unassigned(self.address):
            if value != '':
                value += ', '
            value += str(self.address)
        if not unassigned(self.year):
            if value != '':
                value += ', '
            if not unassigned(self.month):
                value += str(self.month) + ' '
            value += str(self.year)
        if value != '':
            value = "{%s}." % value
        return value

    def __str__(self):
        if self._options.convert == 'bib':
            value = "@%s{%s" % (self._name, self._primarykey)
            for field in self._fields:
                fieldvalue = getattr(self, field)
		if not unassigned(fieldvalue):
                    value += ",\n\t%s = \"%s\"" % (field, str(fieldvalue))
            value += "}\n\n"
        else:
            value = ''
	    valueauthor = self._fullauthors()
	    valuetitle = self._fulltitle()
	    valuepublication = self._fullpublication()
	    if self._options.title_head:
		if valuetitle != '':
		    if value != '':
			value += "\n\\newblock "
		    value += "\\textbf{%s}" % self._fulltitle()
		if valueauthor != '':
		    if value != '':
			value += "\n\\newblock "
		    value += valueauthor
	    else:
		if valueauthor != '':
		    if value != '':
			value += "\n\\newblock "
		    value += valueauthor
		if valuetitle != '':
		    if value != '':
			value += "\n\\newblock "
		    value += valuetitle
	    if valuepublication != '':
		if value != '':
		    value += "\n\\newblock "
		value += valuepublication

            abstractlink = False
	    links = ''
	    for field in self._options.link:
		myfield = field.lower()
		if hasattr(self, myfield) and getattr(self, myfield) != '':
		    for m in linkre.finditer(str(getattr(self, myfield))):
			uri = m.group()
			linksub.sub(uri, "")
			if links != '':
			    links += ' '
			links += "\\href{%s}{\\small\\textsc{%s}}" % (uri, field)
			if myfield == 'abstract':
			    abstractlink = True
	    if links != '':
		if value != '':
		    value += "\n\\newblock "
		value += links

            if not unassigned(self.abstract) and self._options.abstract and not abstractlink:
                if value != '':
                    value += "\n"
                value += "\\begin{quotation}\\noindent\\begin{small}%s\\end{small}\\end{quotation}" % str(self.abstract)
            if not unassigned(self.keywords) and self._options.keywords:
                if value != '':
                    value += "\n"
                value += "\\begin{quote}\\begin{small}\\textsc{Keywords:} %s\\end{small}\\end{quote}" % str(self.keywords)

	    if not unassigned(self.note):
		if value != '':
		    value += "\n\\newblock "
		value += "%s." % str(self.note)

            label = self._label()
            if label != '':
                label = '[%s]' % label
	    if self._citekey == None:
		self._citekey = ''
            value = "\\bibitem%s{%s}\n%s\n\n" % (label, self._citekey, value)
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
        value = ' '.join(['In', self._options.proceedings_str])
        if value != '':
            value += ' '
        value += "{\\em %s}" % str(self.booktitle)
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
        value = self._thesistype
        if value != '':
            value += ' '
        value += 'Thesis'
        if not unassigned(self.school):
            value += ", %s" % str(self.school)
        return value

class mastersthesis(thesis):
    _thesistype = 'Masters'

class phdthesis(thesis):
    _thesistype = 'Ph.D.'

class patent(misc):
    author = REQUIRED
    title = REQUIRED
    number = REQUIRED
    month = REQUIRED
    year = REQUIRED

    def _publication(self):
        return "United States Patent %s", str(self.number)

class proceedings(misc):
    title = REQUIRED
    year = REQUIRED

class collection(proceedings):
    pass

class techreport(misc):
    author = REQUIRED
    title = REQUIRED
    institution = REQUIRED
    year = REQUIRED

    def _publication(self):
        value = 'Technical Report'
        if not unassigned(self.number):
            value += " %s" % str(self.number)
        if not unassigned(self.institution):
            value += ", %s" % str(self.institution)
        return value

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
            if value != '':
                value += ', Accessed '
            if not unassigned(self.accessmonth):
                value += str(self.accessmonth) + ' '
            value += str(self.accessyear)
	return value

class newspaperarticle(article):
    author = OPTIONAL

    def _assign(self, key, value, condition={}):
         # newspaper is an alias for journal
         if key == 'newspaper':
             key = 'journal'

         return article._assign(self, key, value, condition)

class newspaper(journal):
    pass
