# (c) August 2006, Emin Gun Sirer
# Distributed under the GNU Public License, v2
# See the file COPYING for copyright info
#
#
# This file describes the object hierarchy in the bibliography itself
# 

from crosstexutils import authorstring, authornames, citationcase

# Co-ordination so as not to re-use citation keys
usedlabels = set()

# Base class of bibliography objects
class bibobject(object):
    _line = 0
    _file = ''
    _name = ''
    _options = {}
    _assigned = set()
    _conditionals = []
    _citekey = ''

    def __init__(self, conditionals, file, line, options = {}):
	self._line = line
	self._file = file
	self._name = type(self).__name__
	self._name = self._name[self._name.find('.') + 1:]
	self._options = options
	self._assigned = set()
	self._conditionals = conditionals

	while self._applyconditions():
	    pass

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
	key = key.lower()
	if not hasattr(self, key):
	    raise ValueError, "%s has no such field %s" % (self._name, key)
	else:
	    if hasattr(value, '_bibpromote'):
		value._bibpromote(self)
	    if key not in self._assigned:
		self._assigned.add(key)
	        setattr(self, key, value)

    def _applyconditions(self):
	unmet = []
	apply = []
	for condition, fields in self._conditionals:
	    if self._meets(condition):
		apply += [fields]
	    else:
		unmet += [(condition, fields)]
	self._conditionals = unmet
	for fields in apply:
	    for key in fields:
		self._assign(key, fields[key])
	return len(apply) > 0

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
	if 'xtx2bib' in self._options and self._options['xtx2bib']:
	    return ' and '.join([ str(author) for author in self ])
	value = ''
	for i in range(0, len(self)):
	    if value != '':
		if i == len(self) - 1:
		    value += ' and '
		else:
		    value += ', '
	    (fnames, lname, sname) = authornames(str(self[i]))
	    value += authorstring(fnames, lname, sname, self._options)
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
        optname = 'use-short-' + self._name + 'names'
	if optname in self._options and self._options[optname]:
	    return str(self.shortname)
	else:
	    return str(self.name)

class author(string):
    address = ''
    affiliation = ''
    email = ''
    institution = ''
    organization = ''
    phone = ''
    school = ''
    url = ''

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

class journal(string):
    pass

# Base for all publications, everything optional.
class misc(bibobject):
    abstract = ''
    address = ''
    affiliation = ''
    annote = ''
    author = []
    bibsource = ''
    booktitle = ''
    chapter = ''
    contents = ''
    copyright = ''
    crossref = ''
    edition = ''
    editor = ''
    ee = ''
    howpublished = ''
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
    price = ''
    publisher = ''
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
	    self.__dict__['author'] = []
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
	authors = [ str(name) for name in self.author ]
	if len(authors) == 0 and self.editor != '':
	    authors = [ str(self.editor) ]
	if len(authors) == 0:
	    label = str(self.key)
	elif 'cite-by' in self._options and self._options['cite-by'] == 'initials':
	    if len(authors) == 1:
		(fnames, lname, sname) = authornames(authors[0])
		label += lname[0:3]
	    elif len(authors) <= 4:
		for i in range(0, min(len(authors), 4)):
		    (fnames, lname, sname) = authornames(authors[i])
		    label += lname[0]
	    else:
		for i in range(0, min(len(authors), 3)):
		    (fnames, lname, sname) = authornames(authors[i])
		    label += lname[0]
		label += "{\etalchar{+}}"
	    if self.year != '':
   	        label += "%02d" % (int(str(self.year)) % 100)
	elif 'cite-by' in self._options and self._options['cite-by'] == 'fullname':
	    if len(authors) == 2:
		(fnames1, lname1, sname1) = authornames(authors[0])
		(fnames2, lname2, sname2) = authornames(authors[1])
		label += lname1 + " \& " + lname2
	    else:
		(fnames, lname, sname) = authornames(authors[0])
		label += lname
		if len(authors) > 2:
		    label += " et al."
	    if self.year != '':
   	        label += " %02d" % (int(str(self.year)) % 100)
	else:
	    label = ''
        # Ensure the label is unique
	if label in usedlabels:
	    for char in "abcdefghijklmnopqrstuvwxyz":
		if label + char not in usedlabels:
		    label += char
		    break
	    else:
		sys.stderr.write("crosstex: too many citations with key %s" % label)
	if label != '':
	    usedlabels.add(label)
	self._citelabel = label
	return self._citelabel

    def _sortkey(self):
	if self._label() != '':
	    return self._label()
	authors = [ str(name) for name in self.author ]
	if len(authors) == 0 and self.editor != '':
	    authors = [ str(self.editor) ]
	return [ [ authornames(name)[1] for name in authors ], self.year, self.monthno ]

    def _title(self):
	value = str(self.title)
	if value != '':
	    if 'title-uppercase' in self._options and self._options['title-uppercase']:
		value = citationcase(value, "upper")
	    elif 'title-lowercase' in self._options and self._options['title-lowercase']:
		value = citationcase(value, "lower")
	    elif 'title-titlecase' in self._options and self._options['title-titlecase']:
		value = citationcase(value, "title")
	    if self.booktitle != '':
		value += ". In {\\em %s}" % str(self.booktitle)
	    if self.editor != '':
		value += ", %s, ed." % str(self.editor)
	return value

    def _publication(self):
	return str(self.howpublished)

    def _fulltitle(self):
	value = self._title()
	if value != '':
	    value = "\\newblock {%s}" % value
	    if value[-2] != '.':
		value += '.'
	    value += "\n"
	return value

    def _fullpublication(self):
	value = self._publication()
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
	    value = "\\newblock {%s}.\n" % value
	return value

    def __str__(self):
	if 'xtx2bib' in self._options and self._options['xtx2bib']:
	    value = "@%s{%s" % (self._name, self._citekey)
	    for field in self._assigned:
		fieldvalue = str(getattr(self, field))
		if len(fieldvalue) != 0:
		    value += ",\n\t%s = \"%s\"" % (field, getattr(self, field))
	    value += "}\n\n"
	else:
	    label = self._label()
	    if label != '':
		label = '[%s]' % label
	    value = "\\bibitem%s{%s}\n" % (label, self._citekey)
	    value += str(self.author) + ".\n"
	    value += self._fulltitle()
	    value += self._fullpublication()
	    value += "\n"
	return value

class article(misc):
    author = None
    title = None
    journal = None
    year = None

    def _publication(self):
	value = ''
	if 'use-inforarticles' in self._options and self._options['use-inforarticles']:
	    value = 'In '
	value += "{\\em %s}" % str(self.journal)
	if self.volume != '':
	    if self.number == '' and self.pages == '':
		value += ' Volume'
	    value += " %s" % str(self.volume)
	if self.number != '':
	    value += "(%s)" % str(self.number)
	if self.pages != '':
	    value += ":%s" % str(self.pages)
	return value

class book(misc):
    author = None
    editor = None
    title = None
    publisher = None
    year = None

    def _publication(self):
	return str(self.publisher)

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

    def _title(self):
	value = str(self.title)
	if value != '':
	    if 'title-uppercase' in self._options and self._options['title-uppercase']:
		value = citationcase(value, "upper")
	    elif 'title-lowercase' in self._options and self._options['title-lowercase']:
		value = citationcase(value, "lower")
	    elif 'title-titlecase' in self._options and self._options['title-titlecase']:
		value = citationcase(value, "title")
	    procof = ''
	    if 'add-proceedingsof' in self._options and self._options['add-proceedingsof']:
		procof = 'Proceedings of the '
	    elif 'add-procof' in self._options and self._options['add-procof']:
		procof = 'Proc. of '
	    if self.booktitle != '':
		value += ". In {\\em %s}" % (procof + str(self.booktitle))
	    if self.editor != '':
		value += ", %s, ed." % str(self.editor)
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
    pass

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
