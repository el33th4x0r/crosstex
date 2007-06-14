import copy
import re

#
# Handling requirement levels and detecting assignment.
# Like an enum with two values, REQUIRED and OPTIONAL.
#

class requirement:
    pass

REQUIRED = requirement()
OPTIONAL = requirement()


#
# Entries in a bibliography.
#

def cmpclasses(a, b):
    if issubclass(a, b):
        return -1
    elif issubclass(b, a):
        return 1
    else:
        return cmp(a.__name__, b.__name__)

class formatter(object):

    _filters = {}
    _listformatters = {}
    _listfilters = {}
    _producers = {}
    _updated = 0

    def __init__(self, *kargs, **kwargs):
        self._cached = {}
        self._updated = self.__class__._updated
        super(formatter, self).__init__(*kargs, **kwargs)

    def _addproducer(cls, filter, *context):
        if not context:
            raise ValueError, "must have non-empty context"
        if isinstance(filter, str):
            def producer(obj, context):
                return filter
            cls._producers.setdefault(context, {}).setdefault(cls, []).insert(0, producer)
        else:
            cls._producers.setdefault(context, {}).setdefault(cls, []).insert(0, filter)
        cls._updated += 1
    _addproducer = classmethod(_addproducer)

    def _addlistfilter(cls, filter, *context):
        if not context:
            raise ValueError, "must have non-empty context"
        cls._listfilters.setdefault(context, {}).setdefault(cls, []).insert(0, filter)
        cls._updated += 1
    _addlistfilter = classmethod(_addlistfilter)

    def _addlistformatter(cls, filter, *context):
        if not context:
            raise ValueError, "must have non-empty context"
        cls._listformatters.setdefault(context, {}).setdefault(cls, []).insert(0, filter)
        cls._updated += 1
    _addlistformatter = classmethod(_addlistformatter)

    def _addfilter(cls, filter, *context):
        if not context:
            raise ValueError, "must have non-empty context"
        cls._filters.setdefault(context, {}).setdefault(cls, []).insert(0, filter)
        cls._updated += 1
    _addfilter = classmethod(_addfilter)

    def _produce(self, context):
        objvalue = None
        for trycontext in range(len(context))[::-1]:
            if context[trycontext:] in self._producers:
                objtypes = [objtype for objtype in self._producers[context[trycontext:]] if issubclass(type(self), objtype)]
                objtypes.sort(cmpclasses)
                for objtype in objtypes:
                    for producer in self._producers[context[trycontext:]][objtype]:
                        objvalue = producer(self, context)
                        if objvalue != None:
                            return objvalue
        return objvalue

    def _listfilter(self, objvalue, context):
        for trycontext in range(len(context))[::-1]:
            if not isinstance(objvalue, list):
                return objvalue
            if context[trycontext:] in self._listfilters:
                objtypes = [objtype for objtype in self._listfilters[context[trycontext:]] if issubclass(type(self), objtype)]
                objtypes.sort(cmpclasses)
                for objtype in objtypes:
                    for listfilter in self._listfilters[context[trycontext:]][objtype]:
                        objvalue = listfilter(self, objvalue, context)
        return objvalue

    def _listformat(self, objvalue, context):
        for trycontext in range(len(context))[::-1]:
            if not isinstance(objvalue, list):
                return objvalue
            if context[trycontext:] in self._listformatters:
                objtypes = [objtype for objtype in self._listformatters[context[trycontext:]] if issubclass(type(self), objtype)]
                objtypes.sort(cmpclasses)
                for objtype in objtypes:
                    for listformatter in self._listformatters[context[trycontext:]][objtype]:
                        objvalue = listformatter(self, objvalue, context)
        return objvalue

    def _filter(self, objvalue, context):
        if objvalue == None:
            return objvalue
        if isinstance(objvalue, entry) and isinstance(self, entry):
            objvalue = copy.deepcopy(objvalue)
            for field, value, condition in self._conditionals[0]:
                try:
                    objvalue._addfield(field, value, condition)
                except ValueError:
                    pass
        objvalue = str(objvalue)
        for trycontext in range(len(context))[::-1]:
            if context[trycontext:] in self._filters:
                objtypes = [objtype for objtype in self._filters[context[trycontext:]] if issubclass(type(self), objtype)]
                objtypes.sort(cmpclasses)
                for objtype in objtypes:
                    for filter in self._filters[context[trycontext:]][objtype]:
                        objvalue = filter(self, objvalue, context)
        return objvalue

    def _format(self, *context):
        if self._updated != self.__class__._updated:
            self._cached = {}
            self._updated = self.__class__._updated
        if not context:
            raise ValueError, "empty context"
        if context[0] == 'value' and len(context) > 1:
            context = context[1:]
        if context in self._cached:
            return self._cached[context]
        objvalue = self._produce(context)
        objvalue = self._listfilter(objvalue, context)
        objvalue = self._listformat(objvalue, context)
        objvalue = self._filter(objvalue, context)
        self._cached[context] = objvalue
        return objvalue

    def __str__(self):
        value = self._format('value')
        if value == None:
            raise ValueError, "no value for formatter of type %s" % type(self).__name__
        return str(value)

class entrylist(formatter, list):

    def __init__(self, *kargs, **kwargs):
        super(entrylist, self).__init__(*kargs, **kwargs)

class entry(formatter):

    def __init__(self, file, line, *kargs, **kwargs):
        self._file = file
        self._line = line

        self._name = type(self).__name__
        self._name = self._name[self._name.find('.')+1:]

        self._conditionals = []
        self._fields = None
        self._citekey = None

        super(entry, self).__init__(*kargs, **kwargs)

    def __getattribute__(self, field):
        if field.startswith('_'):
            return super(entry, self).__getattribute__(field)
        else:
            return self._format(field)

    def __eq__(self, other):
        return isinstance(other, entry) and self._conditionals == other._conditionals

    def __ne__(self, other):
        return not (self == other)

    def _addfield(self, field, value, condition={}, layer=0, extend=False):
        for condfield in condition.keys() + [field]:
            if not hasattr(type(self), condfield):
                raise ValueError, "%s has no such field %s" % (self._name, condfield)
        if len(self._conditionals) <= layer or (field, value, condition) not in self._conditionals[layer]:
            self._fields = None
            self._cached = {}
            while len(self._conditionals) <= layer:
                self._conditionals.append([])
            if extend:
                self._conditionals[layer].insert(0, (field, value, condition) )
            else:
                self._conditionals[layer].append( (field, value, condition) )

    def _resolve(self):
        self._fields = {}
        next = []
        for layer in self._conditionals:
            next.extend(layer)
            changed = True
            while changed:
                changed = False
                conditionals = next
                inherit = []
                next = []
                for field, value, condition in conditionals:
                    if not hasattr(type(self), field) or field in self._fields:
                        continue
                    for condfield in condition:
                        if condfield not in self._fields:
                            next.append( (field, value, condition) )
                            break
                        elif condition[condfield] != self._fields[condfield]:
                            break
                    else:
                        self._fields[field] = value
                        if isinstance(value, entry):
                            for inheritfield, inheritvalue, inheritcondition in value._conditionals[0]:
                                for condfield in inheritcondition.keys() + [inheritfield]:
                                    if not hasattr(type(self), field):
                                        break
                                else:
                                    inherit.append( (inheritfield, inheritvalue, inheritcondition) )
                        elif isinstance(value, list):
                            for element in value:
                                    if isinstance(element, entry):
                                        for inheritfield, inheritvalue, inheritcondition in element._conditionals[0]:
                                            for condfield in inheritcondition.keys() + [inheritfield]:
                                                if not hasattr(type(self), field):
                                                    break
                                            else:
                                                inherit.append( (inheritfield, inheritvalue, inheritcondition) )
                        changed = True
                next.extend(inherit)

    def _check(self):
        for field in self._required:
            if self._produce((field,)) == None:
                raise ValueError, "field %s, required by %s, is missing" % (field, self._name)


#
# The actual objects.
#

class string(entry):
    name = OPTIONAL
    shortname = [REQUIRED, 'name', 'longname']
    longname = [REQUIRED, 'name', 'shortname']

class author(string):
    address = OPTIONAL
    affiliation = OPTIONAL
    email = OPTIONAL
    institution = OPTIONAL
    organization = OPTIONAL
    phone = OPTIONAL
    school = OPTIONAL
    url = OPTIONAL

class state(string):
    country = OPTIONAL

class country(string):
    pass

class location(string):
    city = OPTIONAL
    state = OPTIONAL
    country = OPTIONAL

class month(string):
    monthno = REQUIRED

class journal(string):
    pass

class misc(entry):
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
    journal = [OPTIONAL, 'newspaper']
    newspaper = [OPTIONAL, 'journal']
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

class manual(misc):
    title = REQUIRED

class thesis(misc):
    author = REQUIRED
    title = REQUIRED
    school = REQUIRED
    year = REQUIRED

class mastersthesis(thesis):
    pass

class phdthesis(thesis):
    pass

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

class techreport(misc):
    author = REQUIRED
    title = REQUIRED
    institution = REQUIRED
    year = REQUIRED

class unpublished(misc):
    author = REQUIRED
    title = REQUIRED
    note = REQUIRED

class conference(string):
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
    journal = [OPTIONAL, 'newspaper']
    newspaper = [OPTIONAL, 'journal']
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

class conferencetrack(conference):
    conference = OPTIONAL

class workshop(conferencetrack):
    pass

class rfc(misc):
    author = REQUIRED
    title = REQUIRED
    number = REQUIRED
    month = REQUIRED
    year = REQUIRED

class url(misc):
    url = REQUIRED
    accessmonth = OPTIONAL
    accessyear = OPTIONAL

class newspaperarticle(article):
    author = OPTIONAL

class newspaper(journal):
    pass


#
# Common, important style functions.
#

_wordre = re.compile('(-+|\s+|\\\w+|\\\W+|\$[^\$]*\$|[{}])', re.IGNORECASE)
_spacere = re.compile(r'^\s*$')
_specialre = re.compile(r'^(\\.*|\$[^\$]*\$)$')
_punctuationre = re.compile('.*([:!.?]|-{2,})$')
_linkre = re.compile("[a-zA-Z][-+.a-zA-Z0-9]*://([:/?#[\]@!$&'()*+,;=a-zA-Z0-9_\-.~]|%[0-9a-fA-F][0-9a-fA-F]|\\-|\s)*")
_linksub = re.compile("\\-\s")

# Piece an entry together.
def _punctuate(string, punctuation='', tail=' '):
    if string == None:
        string = ''
    else:
        string = str.strip(str(string))
    if string == '':
        return string
    if not _punctuationre.match(string):
        string += punctuation
    return string + tail

def _names(name, short=False, plain=False):
    value = ""
    lastchar = ' '
    names = []
    nesting = 0
    if isinstance(name, formatter):
        name = name._format('value')
    for i in range(0, len(name)):
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
            
    # return the person info as a tuple
    (fnames, mnames, lnames, snames) = (names[:mnameoffset], names[mnameoffset:lnameoffset], names[lnameoffset:snameoffset], names[snameoffset:])
    if short:
        fnamesabbr = []
        for n in fnames:
            abbr = ''
            first = 0
            while first < len(n):
                if n[first] not in "{}\\":
                    if abbr != "":
                        abbr += "~"
                    abbr += n[first] + "."
                    break
                elif n[first] == "\\":
                    abbr += 2
                else:
                    abbr += 1
            fnamesabbr.append(abbr)
        return (fnamesabbr, mnames, lnames, snames)
    else:
        return (fnames, mnames, lnames, snames)

def _last_initials(name, size):
    (fnames, mnames, lnames, snames) = _names(name)
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

def _fieldval(field, value):
    if isinstance(value, entry):
        return "%s = %s" % (field, value._primarykey)
    else:
        value = str(value)
        try:
            return "%s = %d" % (field, int(value))
        except:
            if '{' in value or '}' in value:
                return "%s = {%s}" % (field, value)
            else:
                return "%s = \"%s\"" % (field, value)

def makegetterproducer(field):
    def getterproducer(obj, context):
        try:
            return getattr(obj, field)
        except AttributeError:
            return None
    return getterproducer

def bibtexproducer(obj, context):
    value = "@%s{%s" % (obj._name, obj._primarykey)
    if obj._fields == None:
        obj._resolve()
    for field in obj._fields:
        fieldvalue = obj._format(*(context + (field,)))
        if fieldvalue:
            value += ",\n\t" + _fieldval(field, fieldvalue)
    value += "}\n\n"
    return value

def crosstexproducer(obj, context):
    if re.search('\s', obj._primarykey):
        return ''
    value = "@%s{%s" % (obj._name, obj._primarykey)
    for field, fieldvalue, condition in obj._conditionals[0]:
        if len(obj._conditionals) > 1 and (field, fieldvalue) in [x[:2] for x in obj._conditionals[-1]]: # Don't waste time on defaults.
            continue
        value += ",\n\t"
        if condition:
            value += '['
            for condfield in condition:
                if value[-1] != '[':
                    value += ', '
                value += _fieldval(condfield, condition[condfield])
            value += '] '
        value += _fieldval(field, fieldvalue)
    value += "}\n\n"
    return value

def authortitlepublicationproducer(obj, context):
    authorvalue = obj._format(*(context + ('fullauthor',)))
    titlevalue = obj._format(*(context + ('fulltitle',)))
    publicationvalue = obj._format(*(context + ('fullpublication',)))
    linksvalue = obj._format(*(context + ('links',)))
    extrasvalue = obj._format(*(context + ('extras',)))
    objvalue = ''
    if authorvalue:
        objvalue = _punctuate(objvalue, "\n\\newblock") + str(authorvalue)
    if titlevalue:
        objvalue = _punctuate(objvalue, "\n\\newblock") + str(titlevalue)
    if publicationvalue:
        objvalue = _punctuate(objvalue, "\n\\newblock") + str(publicationvalue)
    if linksvalue:
        objvalue = _punctuate(objvalue, "\n\\newblock") + str(linksvalue)
    if extrasvalue:
        objvalue = _punctuate(objvalue, "\n", tail='') + str(extrasvalue)
    if objvalue:
        label = obj._format(*(context + ('label',)))
        if label:
            label = '[%s]' % label
        objvalue = "\\bibitem%s{%s}\n%s\n\n" % (label, obj._citekey, str.strip(objvalue))
    return objvalue

def titleauthorpublicationproducer(obj, context):
    authorvalue = obj._format(*(context + ('fullauthor',)))
    titlevalue = obj._format(*(context + ('fulltitle',)))
    publicationvalue = obj._format(*(context + ('fullpublication',)))
    linksvalue = obj._format(*(context + ('links',)))
    extrasvalue = obj._format(*(context + ('extras',)))
    objvalue = ''
    if titlevalue:
        objvalue = _punctuate(objvalue, "\n\\newblock") + str(titlevalue)
    if authorvalue:
        objvalue = _punctuate(objvalue, "\n\\newblock") + str(authorvalue)
    if publicationvalue:
        objvalue = _punctuate(objvalue, "\n\\newblock") + str(publicationvalue)
    if linksvalue:
        objvalue = _punctuate(objvalue, "\n\\newblock") + str(linksvalue)
    if extrasvalue:
        objvalue = _punctuate(objvalue, "\n", tail='') + str(extrasvalue)
    if objvalue:
        label = obj._format(*(context + ('label',)))
        if label:
            label = '[%s]' % label
        objvalue = "\\bibitem%s{%s}\n%s\n\n" % (label, obj._citekey, str.strip(objvalue))
    return objvalue

def makelinksproducer(fields):
    def linksproducer(obj, context):
        links = ''
        for field in fields:
            myfield = field.lower()
            fieldvalue = obj._format(*(context + (myfield,)))
            if fieldvalue:
                for m in _linkre.finditer(str(fieldvalue)):
                    uri = m.group()
                    _linksub.sub(uri, '')
                    links = _punctuate(links) + "\\href{%s}{\\small\\textsc{%s}}" % (uri, field)
        return links
    return linksproducer

def extrasproducer(obj, context):
    extras = ''
    abstractvalue = obj._format(*(context + ('abstract',)))
    keywordsvalue = obj._format(*(context + ('keywords',)))
    if abstractvalue:
        extras = _punctuate(extras, "\n") + "\\begin{quotation}\\noindent\\begin{small}%s\\end{small}\\end{quotation}" % abstractvalue
    if keywordsvalue:
        extras = _punctuate(extras, "\n") + "\\begin{quotation}\\noindent\\begin{small}\\textsc{Keywords:} %s\\end{small}\\end{quotation}" % keywordsvalue
    return extras

def authoryearproducer(obj, context):
    authorvalue = obj._format(*(context + ('author',)))
    yearvalue = obj._format(*(context + ('year',)))
    if yearvalue == None:
        yearvalue = ''
    else:
        yearvalue = str(yearvalue)
    if authorvalue == None:
        authorvalue = ''
    else:
        authorvalue = str(authorvalue)
    return authorvalue + yearvalue or None

def longauthoryearproducer(obj, context):
    authorvalue = obj._format(*(context + ('author',)))
    yearvalue = obj._format(*(context + ('year',)))
    if yearvalue == None:
        yearvalue = ''
    else:
        yearvalue = str(yearvalue)
    if authorvalue == None:
        authorvalue = ''
    else:
        authorvalue = str(authorvalue)
    return _punctuate(authorvalue) + yearvalue or None

def authoreditorproducer(obj, context):
    authorvalue = obj._format(*(context + ('author',)))
    if authorvalue == None:
        authorvalue = obj._format(*(context + ('editor',)))
        if authorvalue == None:
            return None
        authorvalue = str(authorvalue) + ', ed.'
    else:
        authorvalue = str(authorvalue)
    return authorvalue

def fullpublicationproducer(obj, context):
    value = obj._format(*(context + ('publication',)))
    booktitlevalue = obj._format(*(context + ('booktitle',)))
    journalvalue = obj._format(*(context + ('journal',)))
    if booktitlevalue:
        value = _punctuate(value, '.') + str(booktitlevalue)
        volumevalue = obj._format(*(context + ('volume',)))
        if volumevalue:
            value += ", volume %s" % volumevalue
            seriesvalue = obj._format(*(context + ('series',)))
            if seriesvalue :
                value += " of \em{%s}" % seriesvalue
        chaptervalue = obj._format(*(context + ('chapter',)))
        if chaptervalue:
            value += ", chapter %s" % chaptervalue
    elif journalvalue:
        value = _punctuate(value, ',') + str(journalvalue)
        numbervalue = obj._format(*(context + ('number',)))
        volumevalue = obj._format(*(context + ('volume',)))
        pagesvalue = obj._format(*(context + ('pages',)))
        if numbervalue or volumevalue or pagesvalue:
            value = _punctuate(value, ',')
        if volumevalue:
            value += str(volumevalue)
        if numbervalue:
            value += "(%s)" % numbervalue
        if pagesvalue:
            if volumevalue or numbervalue:
                value += ":%s" % pagesvalue
            else:
                value += "pages %s" % pagesvalue
    institutionvalue = obj._format(*(context + ('institution',)))
    if institutionvalue:
        value = _punctuate(value, ',') + str(institutionvalue)
    schoolvalue = obj._format(*(context + ('school',)))
    if schoolvalue:
        value = _punctuate(value, ',') + str(schoolvalue)
    if not journalvalue:
        numbervalue = obj._format(*(context + ('number',)))
        if numbervalue:
            value = _punctuate(value, ',')
            numbertypevalue = obj._format(*(context + ('numbertype',)))
            if numbertypevalue:
                value = _punctuate(value + str(numbertypevalue))
            value += str(numbervalue)
        pagesvalue = obj._format(*(context + ('pages',)))
        if pagesvalue:
            value = _punctuate(value, ',') + ("pages %s" % pagesvalue)
    authorvalue = obj._format(*(context + ('author',)))
    editorvalue = obj._format(*(context + ('editor',)))
    if authorvalue and editorvalue:
        value = _punctuate(value, ',') + str(editorvalue)
    publishervalue = obj._format(*(context + ('publisher',)))
    if publishervalue:
        value = _punctuate(value, ',') + str(publishervalue)
    addressvalue = obj._format(*(context + ('address',)))
    if addressvalue:
        value = _punctuate(value, ',') + str(addressvalue)
    yearvalue = obj._format(*(context + ('year',)))
    if yearvalue:
        value = _punctuate(value, ',')
        monthvalue = obj._format(*(context + ('month',)))
        if monthvalue:
            value = _punctuate(value + str(monthvalue))
        value += str(yearvalue)
    return value

def accessedproducer(obj, context):
    urlvalue = str(obj._format(*(context + ('url',))))
    yearvalue = obj._format(*(context + ('accessyear',)))
    monthvalue = obj._format(*(context + ('accessmonth',)))
    if yearvalue or monthvalue:
        urlvalue = _punctuate(urlvalue, ',') + "Accessed"
    if monthvalue:
        urlvalue = _punctuate(urlvalue) + monthvalue
        if yearvalue:
            urlvalue = _punctuate(urlvalue, ',') + yearvalue
    elif yearvalue:
        urlvalue = _punctuate(urlvalue) + yearvalue
    return urlvalue

def citystatecountryproducer(obj, context):
    cityvalue = obj._format(*(context + ('city',)))
    statevalue = obj._format(*(context + ('state',)))
    countryvalue = obj._format(*(context + ('country',)))
    value = ''
    if cityvalue:
        value = _punctuate(value, ',') + str(cityvalue)
    if statevalue:
        value = _punctuate(value, ',') + str(statevalue)
    if countryvalue:
        value = _punctuate(value, ',') + str(countryvalue)
    return value

def thesistypeproducer(obj, context):
    typevalue = obj._format(*(context + ('type',)))
    if typevalue:
        return str(typevalue)
    typevalue = obj._format(*(context + ('thesistype',)))
    if typevalue:
        return _punctuate(typevalue) + "Thesis"
    return None

def emptyproducer(obj, context):
    return ''

def lastfirstfilter(obj, objvalue, context):
    (fnames, mnames, lnames, snames) = _names(objvalue)
    namestr = ""
    for n in mnames:
        namestr = _punctuate(namestr) + n
    for n in lnames:
        namestr = _punctuate(namestr) + n
    if len(fnames) > 0:
        namestr = _punctuate(namestr, ',')
    for n in fnames:
        namestr = _punctuate(namestr) + n
    for n in snames:
        namestr = _punctuate(namestr) + n
    return namestr

def shortnamesfilter(obj, objvalue, context):
    (fnames, mnames, lnames, snames) = _names(objvalue, short=True)
    namestr = ""
    for n in fnames:
        namestr = _punctuate(namestr) + n
    for n in mnames:
        namestr = _punctuate(namestr) + n
    for n in lnames:
        namestr = _punctuate(namestr) + n
    if len(snames) > 0:
        namestr = _punctuate(namestr, ',')
    for n in snames:
        namestr = _punctuate(namestr) + n
    return namestr

def shortnameslistfilter(obj, objvalue, context):
    for i in range(len(objvalue)):
        objvalue[i] = shortnamesfilter(obj, objvalue[i], context)
    return objvalue

def lastfirstlistfilter(obj, objvalue, context):
    if objvalue:
        objvalue = copy.deepcopy(objvalue)
        objvalue[0] = lastfirstfilter(obj, objvalue[0], context)
    return objvalue

def alllastfirstlistfilter(obj, objvalue, context):
    if objvalue:
        objvalue = copy.deepcopy(objvalue)
        for i in range(len(objvalue)):
            objvalue[i] = lastfirstfilter(obj, objvalue[i], context)
    return objvalue

def commalistformatter(obj, objvalue, context):
    value = ''
    for i in range(len(objvalue)):
        if value:
            if len(objvalue) > 2:
                value += ','
            value += ' '
            if i == len(objvalue) - 1:
                value += 'and '
        value += str(objvalue[i])
    return value

def andlistformatter(obj, objvalue, context):
    return ' and '.join([str(element) for element in objvalue])

def andcrosstexlistformatter(obj, objvalue, context):
    return ' and '.join([isinstance(element, entry) and element._primarykey or str(element) for element in objvalue])

def initialslistformatter(obj, objvalue, context):
    value = ''
    if len(objvalue) == 1:
        value = _last_initials(objvalue[0], 3)
    elif len(objvalue) <= 4:
        for i in range(0, min(len(objvalue), 5)):
            value += _last_initials(objvalue[i], 1)
    else:
        for i in range(0, 4):
            value += _last_initials(objvalue[i], 1)
        value += "{\etalchar{+}}"
    return value

def fullnameslistformatter(obj, objvalue, context):
    value = ''
    if len(objvalue) == 2:
        (fnames1, mnames1, lnames1, snames1) = _names(objvalue[0])
        (fnames2, mnames1, lnames2, snames2) = _names(objvalue[1])
        value = ' '.join(lnames1) + " \& " + ' '.join(lnames2)
    else:
        (fnames1, mnames1, lnames1, snames1) = _names(objvalue[0])
        value = ' '.join(lnames1)
        if len(objvalue) > 2:
            value += " et al."
    return value

def emptyfilter(obj, objvalue, context):
    return ''

def extrashtmlfilter(obj, objvalue, context):
    if objvalue:
        objvalue = "\\@open{DIV}{\\@getprint{CLASS=\"extras\"}}" + objvalue + "\\@close{DIV}"
    return objvalue

def makeuniquefilter():
    used = []
    def uniquefilter(obj, objvalue, context):
        if objvalue != '':
            if objvalue in used:
                for char in list("abcdefghijklmnopqrstuvwxyz"):
                    if objvalue + char not in used:
                        objvalue += char
                        break
                else:
                    raise ValueError, "too many citations with key %s" % objvalue
            used.append(objvalue)
        return objvalue
    return uniquefilter

def twodigitfilter(obj, objvalue, context):
    return objvalue[-2:]

def infilter(obj, objvalue, context):
    return "In " + objvalue

def procfilter(obj, objvalue, context):
    return "Proc. of " + objvalue

def emphfilter(obj, objvalue, context):
    return "\\emph{" + objvalue + "}"

def boldfilter(obj, objvalue, context):
    return "\\textbf{" + objvalue + "}"

def proceedingsfilter(obj, objvalue, context):
    return "Proceedings of the " + objvalue

def edfilter(obj, objvalue, context):
    return _punctuate(objvalue, ',', 'ed.')

def bracesfilter(obj, objvalue, context):
    return "{" + str.strip(objvalue) + "}"

def dotfilter(obj, objvalue, context):
    return _punctuate(objvalue, '.')

def conferencetrackfilter(obj, objvalue, context):
    return _punctuate(obj._format(*(context + ('conference',))), ',') + objvalue

def killfilter(obj, objvalue, context):
    if context[-1] in obj._required:
        return objvalue
    else:
        return ''

def titlecasefilter(obj, objvalue, context):
    if len(objvalue) >= 3 and objvalue[0] == "{" and objvalue[-1] == "}" and objvalue[-2] != "\\":
        objvalue = objvalue[1:-1]
    newtitle = ''
    nestingdepth = 0
    for word in _wordre.split(objvalue):
        if word == '{':
            nestingdepth += 1
        elif word == '}':
            nestingdepth -= 1
        elif not _spacere.match(word) and word != '-' and not _specialre.match(word) and (word.islower() or word.istitle() or len(word) <= 1) and nestingdepth == 0:
            word = word.title()
        newtitle += word
    return newtitle

def lowertitlecasefilter(obj, objvalue, context):
    if len(objvalue) >= 3 and objvalue[0] == "{" and objvalue[-1] == "}" and objvalue[-2] != "\\":
        objvalue = objvalue[1:-1]
    newtitle = ''
    needscaps = True
    nestingdepth = 0
    for word in _wordre.split(objvalue):
        if word == '{':
            nestingdepth += 1
            needscaps = False
        elif word == '}':
            nestingdepth -= 1
            needscaps = False
        elif not _spacere.match(word) and word != '-' and nestingdepth == 0:
            if not _specialre.match(word) and (word.islower() or word.istitle() or len(word) <= 1):
                if needscaps:
                    word = word.title()
                else:
                    word = word.lower()
            needscaps = _punctuationre.match(word)
        newtitle += word
    return newtitle

def uppercasefilter(obj, objvalue, context):
    if len(objvalue) >= 3 and objvalue[0] == "{" and objvalue[-1] == "}" and objvalue[-2] != "\\":
        objvalue = objvalue[1:-1]
    newtitle = ''
    nestingdepth = 0
    for word in _wordre.split(objvalue):
        if word == '{':
            nestingdepth += 1
        elif word == '}':
            nestingdepth -= 1
        elif not _spacere.match(word) and word != '-' and not _specialre.match(word) and nestingdepth == 0:
            word = word.upper()
        newtitle += word
    return newtitle

def maketitlephrasefilter(titlephrases):
    def titlephrasefilter(obj, objvalue, context):
        if len(objvalue) >= 3 and objvalue[0] == "{" and objvalue[-1] == "}" and objvalue[-2] != "\\":
            objvalue = objvalue[1:-1]
        newtitle = ''
        nestingdepth = 0
        for word in _wordre.split(objvalue):
            if word == '{':
                nestingdepth += 1
            elif word == '}':
                nestingdepth -= 1
            elif not _spacere.match(word) and word != '-' and not _specialre.match(word) and nestingdepth == 0 and word.lower() in titlephrases:
                word = titlephrases[word.lower()]
            newtitle += word
        return newtitle
    return titlephrasefilter

def makelowerphrasefilter(lowerphrases):
    def lowerphrasefilter(obj, objvalue, context):
        if len(objvalue) >= 3 and objvalue[0] == "{" and objvalue[-1] == "}" and objvalue[-2] != "\\":
            objvalue = objvalue[1:-1]
        newtitle = ''
        needscaps = True
        nestingdepth = 0
        for word in _wordre.split(objvalue):
            if word == '{':
                nestingdepth += 1
                needscaps = False
            elif word == '}':
                nestingdepth -= 1
                needscaps = False
            elif not _spacere.match(word) and word != '-' and nestingdepth == 0:
                if not _specialre.match(word) and not needscaps and word.lower() in lowerphrases:
                    word = word.lower()
                needscaps = _punctuationre.match(word)
            newtitle += word
        return newtitle
    return lowerphrasefilter


#
# Initialization.
#

def makeaccessorproducer(field):
    def accessorproducer(obj, context):
        if obj._fields == None:
            obj._resolve()
        try:
            return obj._fields[field]
        except KeyError:
            return None
    return accessorproducer

for objtype in globals().values():
    if isinstance(objtype, type) and issubclass(objtype, entry):
        objtype._required = []
        for field in [field for field in dir(objtype) if not field.startswith('_')]:
            value = getattr(objtype, field)
            if isinstance(value, list):
                for element in value[::-1]:
                    if isinstance(element, requirement):
                        if element is REQUIRED and field not in objtype._required:
                            objtype._required.append(field)
                    else:
                        objtype._addproducer(makeaccessorproducer(str(element)), field)
            elif isinstance(value, requirement):
                if value is REQUIRED and field not in objtype._required:
                    objtype._required.append(field)
            else:
                objtype._addproducer(makeaccessorproducer(str(value)), field)
            objtype._addproducer(makeaccessorproducer(field), field)

def listproducer(obj, context):
    if isinstance(obj, list):
        return list(obj)
    else:
        return None

entrylist._addproducer(listproducer, 'value')
entry._addlistfilter(alllastfirstlistfilter, 'sort', 'author')