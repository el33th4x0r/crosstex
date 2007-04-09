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

# Base class of bibliography objects
class bibobject(object):
    _line = 0
    _file = ''
    _name = ''
    _assigned = []
    _conditionals = []
    _citekey = ''

    def __init__(self, conditionals, defaults, file, line, bib):
        self._bib = bib
        self._line = line
        self._file = file
        self._name = type(self).__name__
        self._name = self._name[self._name.find('.') + 1:]
        self._options = self._bib.options
        self._assigned = []
        self._conditionals = conditionals

        while self._applyconditions():
            pass

	for key in defaults:
	    if hasattr(self, key):
	        self._assign(key, defaults[key])

        while self._applyconditions():
            pass

    def _check(self):
        for field in self._fields():
            if getattr(self, field) == None:
                raise ValueError, "field %s, required by %s, is missing" % (field, self._name)

    def _fields(self):
        return [key for key in dir(self) if key[0] != '_']

    def _meets(self, condition):
        if condition == None:
            return True
        for field in condition:
            if not hasattr(self, field) or getattr(self, field) != condition[field]:
                return False
        return True

    def _assign(self, key, value):
        if not hasattr(self, key):
            raise ValueError, "%s has no such field %s" % (self._name, key)
        else:
            if hasattr(value, '_bibpromote'):
                value._bibpromote(self)
            if key not in self._assigned:
                self._assigned.append(key)
                setattr(self, key, value)

    def _applyconditions(self):
        unmet = []
        valid = []
        for condition, fields in self._conditionals:
            if self._meets(condition):
                valid += [fields]
            else:
                unmet += [(condition, fields)]
        self._conditionals = unmet
        for fields in valid:
            for key in fields:
                self._assign(key, fields[key])
        return len(valid) > 0

    def _filter(self, other, fields):
        filtered = {}
        for name in other._fields():
            if name in fields:
                filtered[name] = fields[name]
        return filtered

    def _bibpromote(self, other):
        attrs = {}
        for field in self._fields():
            attrs[field] = getattr(self, field)
        for condition, fields in self._conditionals + [(None, attrs)]:
            other._conditionals += [(condition, self._filter(other, fields))]

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
    name = None
    shortname = None

    def _assign(self, key, value):
        # longname is an alias for name
        if key == 'longname':
            key = 'name'

        # With shortname, name is optional and vice versa
        if key == 'shortname' and self.name == None:
            self.__dict__['name'] = value
        if key == 'name' and self.shortname == None:
            self.__dict__['shortname'] = value
        bibobject._assign(self, key, value)

    def __str__(self):
	value = self.name
	if self._name in self._options.short:
	    value = self.shortname
	if self._name in self._options.capitalize:
	    value = self._bib.titlecase(value, 'upper', False)
	return value

class author(string):
    address = ''
    affiliation = ''
    email = ''
    institution = ''
    organization = ''
    phone = ''
    school = ''
    url = ''

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
        if self._name in self._options.short and 'shortname' in self._assigned:
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
        if self._name in self._options.short and 'shortname' in self._assigned:
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
    country = ''

class country(string):
    pass

class location(bibobject):
    city = ''
    state = ''
    country = ''

    def __str__(self):
        value = ''
        state = str(self.state)
        country = str(self.country)
        if 'city' in self._assigned:
            value += str(self.city)
        if state != '':
            if value != '':
                value += ', '
            value += state
        if country != '':
            if value != '':
                value += ', '
            value += country
        return value

class month(string):
    monthno = None

    def __cmp__(self, other):
	if isinstance(other, month):
	    return cmp(int(self.monthno), int(other.monthno))
	else:
	    return cmp(int(self.monthno), other)

class journal(string):
    pass

# Base for all publications, everything optional.
class misc(bibobject):
    abstract = ''
    address = ''
    affiliation = ''
    annote = ''
    author = ''
    bib = ''
    bibsource = ''
    booktitle = ''
    category = ''
    subcategory = ''
    chapter = ''
    contents = ''
    copyright = ''
    crossref = ''
    doi = ''
    dvi = ''
    edition = ''
    editor = ''
    ee = ''
    ftp = ''
    howpublished = ''
    html = ''
    http = ''
    institution = ''
    isbn = ''
    issn = ''
    journal = ''
    key = ''
    keywords = ''
    language = ''
    lccn = ''
    location = ''
    month = ''
    monthno = ''
    mrnumber = ''
    note = ''
    number = ''
    organization = ''
    pages = ''
    pdf = ''
    price = ''
    ps = ''
    publisher = ''
    rtf = ''
    school = ''
    series = ''
    size = ''
    title = ''
    type = ''
    url = ''
    volume = ''
    year = ''

    def _assign(self, key, value):
        # With author, editor is optional and vice versa
        if key == 'editor' and self.editor == None and self.author == None:
            self.__dict__['author'] = ''
        if key == 'author' and self.editor == None and self.author == None:
            self.__dict__['editor'] = ''

        # With chapter, pages is optional and vice versa
        if key == 'chapter' and self.chapter == None and self.pages == None:
            self.__dict__['pages'] = ''
        if key == 'pages' and self.chapter == None and self.pages == None:
            self.__dict__['chapter'] = ''

        bibobject._assign(self, key, value)

    def _label(self):
        # Compute a new label
        global usedlabels
        if hasattr(self, '_citelabel'):
            return self._citelabel
        label = ''
        authors = self.author
	if len(authors) == 0 and len(self.editor) != 0:
	    authors = self.editor
        if len(authors) == 0:
	    if self._options.cite_by != 'number':
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
            if self.year != '':
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
            if self.year != '':
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
        value = str(self.title)
        if value != '':
            if self._options.titlecase != 'as-is':
                value = self._bib.titlecase(value, self._options.titlecase)
        return value

    def _publication(self):
        return str(self.howpublished)

    def _fullauthors(self):
        value = str(self.author)
        if value != '':
            value += "."
        else:
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
        if self.booktitle != '' and value == '':
            value += "In {\\em %s}" % str(self.booktitle)
        if self.journal != '':
            if value != '':
                value += ', '
            if self._options.in_str != '':
                value += self._options.in_str
            else:
                value += ' '
            value += "{\\em %s}" % str(self.journal)
	    if self.volume != '':
		if self.number == '' and self.pages == '':
		    if value != '':
			value += ' '
		    value += 'Volume'
		value += " %s" % str(self.volume)
	    if self.number != '':
		value += "(%s)" % str(self.number)
	    if self.pages != '':
		value += ":%s" % str(self.pages)
        if str(self.author) != '' and str(self.editor) != '':
            if value != '':
                value += ', '
            value += "%s, ed." % str(self.editor)
        if self.publisher != '':
            if value != '':
                value += ', '
            value += str(self.publisher)
        if self.address != '':
            if value != '':
                value += ', '
            value += str(self.address)
        if self.year != '':
            if value != '':
                value += ', '
            if self.month != '':
                value += str(self.month) + ' '
            value += str(self.year)
        if value != '':
            value = "{%s}." % value
        return value

    def __str__(self):
        if self._options.convert == 'bib':
            value = "@%s{%s" % (self._name, self._citekey)
            for field in self._assigned:
                fieldvalue = str(getattr(self, field))
                if len(fieldvalue) != 0:
                    value += ",\n\t%s = \"%s\"" % (field, getattr(self, field))
            value += "}\n\n"
        else:
            value = ''
	    valueauthor = self._fullauthors()
	    valuetitle = self._fulltitle()
	    valuepublication = self._fullpublication()
	    if self._options.title_head:
		if valuetitle != None and valuetitle != '':
		    if value != '':
			value += "\n\\newblock "
		    value += "\\textbf{%s}" % self._fulltitle()
		if valueauthor != None and valueauthor != '':
		    if value != '':
			value += "\n\\newblock "
		    value += valueauthor
	    else:
		if valueauthor != None and valueauthor != '':
		    if value != '':
			value += "\n\\newblock "
		    value += valueauthor
		if valuetitle != None and valuetitle != '':
		    if value != '':
			value += "\n\\newblock "
		    value += valuetitle
	    if valuepublication != None and valuepublication != '':
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

            if self.abstract != '' and self._options.abstract and not abstractlink:
                if value != '':
                    value += "\n"
                value += "\\begin{quotation}\\noindent\\begin{small}%s\\end{small}\\end{quotation}" % str(self.abstract)
            if self.keywords != '' and self._options.keywords:
                if value != '':
                    value += "\n"
                value += "\\begin{quote}\\begin{small}\\textsc{Keywords:} %s\\end{small}\\end{quote}" % str(self.keywords)

            label = self._label()
            if label != '':
                label = '[%s]' % label
            value = "\\bibitem%s{%s}\n%s\n\n" % (label, self._citekey, value)
        return value

class article(misc):
    author = None
    title = None
    journal = None
    year = None

class book(misc):
    author = None
    editor = None
    title = None
    publisher = None
    year = None

class booklet(misc):
    title = None

class inbook(misc):
    author = None
    editor = None
    title = None
    chapter = None
    pages = None
    publisher = None
    year = None

class incollection(misc):
    author = None
    title = None
    booktitle = None
    publisher = None
    year = None

class inproceedings(misc):
    author = None
    title = None
    booktitle = None
    year = None

    def _publication(self):
        value = ' '.join(['In', self._options.proceedings_str])
        if value != '':
            value += ' '
        value += "{\\em %s}" % str(self.booktitle)
        return value

class manual(misc):
    title = None

class thesis(misc):
    author = None
    title = None
    school = None
    year = None

    _thesistype = ''

    def _publication(self):
        value = self._thesistype
        if value != '':
            value += ' '
        value += 'Thesis'
        if self.school != '':
            value += ", %s" % str(self.school)
        return value

class mastersthesis(thesis):
    _thesistype = 'Masters'

class phdthesis(thesis):
    _thesistype = 'Ph.D.'

class patent(misc):
    author = None
    title = None
    number = None
    month = None
    year = None

    def _publication(self):
        return "United States Patent %s", str(self.number)

class proceedings(misc):
    title = None
    year = None

class collection(proceedings):
    pass

class techreport(misc):
    author = None
    title = None
    institution = None
    year = None

    def _publication(self):
        value = 'Technical Report'
        if self.number != '':
            value += " %s" % str(self.number)
        if self.institution != '':
            value += ", %s" % str(self.institution)
        return value

class unpublished(misc):
    author = None
    title = None
    note = None

# New objects in CrossTeX:

# In BibTeX, conference was the same as inproceedings.
# This one's a string instead, and is closer to proceedings.
class conference(string):
    address = ''
    crossref = ''
    editor = ''
    institution = ''
    isbn = ''
    key = ''
    keywords = ''
    language = ''
    location = ''
    month = ''
    publisher = ''
    url = ''
    year = ''

class conferencetrack(conference):
    conference = ''

    def __str__(self):
        if self.conference != '':
            return str(self.conference) + ", " + string.__str__(self)
        else:
            return string.__str__(self)

class workshop(conferencetrack):
    pass

class rfc(misc):
    author = None
    title = None
    number = None
    month = None
    year = None

    def _publication(self):
        return "IETF Request For Comments %s" % str(self.number)

class url(misc):
    url = None
    accessmonth = ''
    accessyear = ''

    def _publication(self):
	value = self.url
        if self.accessyear != '':
            if value != '':
                value += ', Accessed '
            if self.accessmonth != '':
                value += str(self.accessmonth) + ' '
            value += str(self.accessyear)
	return value

class newspaperarticle(article):
    author = ''
    def _assign(self, key, value):
         # newspaper is an alias for journal
         if key == 'newspaper':
             key = 'journal'

class newspaper(journal):
    pass
