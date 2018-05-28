import collections
import itertools
import re

import crosstex
import crosstex.style


class Heading(object):

    def __init__(self, name):
        self.name = name


class UnsupportedCitation(Exception):

    def __init__(self, citetype):
        self.citetype = citetype

    def __str__(self):
        return self.citetype


class Style(object):

    @classmethod
    def formats(cls):
        return set([])

    def __init__(self, fmt, flags, options, db):
        pass

    def sort_key(self, citation, fields=None):
        '''Create a tuple for the default sort of the (key, obj) citation'''
        raise NotImplementedError()

    def get_attr(self, obj, field):
        '''Return a comparable representation of the field (for sorting)'''
        raise NotImplementedError()

    def render(self, citations):
        '''Render the list of (key, obj) citations'''
        raise NotImplementedError()

################################### Utilities ##################################

_endre = re.compile(r"(\\end\{[^}]*\}|['\s}])*$")
_protectre = re.compile(r'[\\{}]')

def punctuate(string, punctuation='', tail=' '):
    if string == None:
        string = ''
    i = _endre.search(string).start()
    end = string[i:]
    string = string[:i]
    if string and not (string.endswith('?') or string.endswith('!') or string.endswith(':') or string.endswith('--') or string.endswith(punctuation)):
        string += punctuation
    if string or end:
        end = end.strip() + tail
    return string + end

################################# Format Names #################################

def break_name(name, short=False, plain=False):
    '''Break a name into 'first', 'von', 'last', 'jr' parts'''
    value = ''
    lastchar = ' '
    names = []
    nesting = 0
    assert isinstance(name, str)
    for i in range(0, len(name)):
        charc = name[i]
        if nesting == 0 and lastchar != '\\' and lastchar != ' ' and charc == ' ':
            names.append(value)
            value = ''
        elif lastchar != '\\' and charc == '}':
            if not plain:
                value += charc
            if nesting == 0:
                names.append(value)
                value = ''
            else:
                nesting -= 1
        elif lastchar != '\\' and charc == '{':
            if not plain:
                value += charc
            nesting += 1
        elif nesting == 0 and lastchar != '\\' and charc == ',':
            pass
        else:
            if not plain or (charc != '\\' and lastchar != '\\'):
                value += charc
        lastchar = charc
    names.append(value)

    # extract lastname, check suffixes and last name modifiers
    # extract also a list of first names
    snames = ['Jr.', 'Sr.', 'Jr', 'Sr', 'III', 'IV']
    mnames = ['van', 'von', 'de', 'bin', 'ibn']
    sname = ''
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
            initial = 0
            sep = ''
            while initial < len(n):
                if n[initial] == '\\':
                    initial += 1
                elif n[initial] in '{}':
                    pass
                elif n[initial] == '~':
                    abbr += n[initial]
                elif n[initial] in '-.':
                    sep = n[initial]
                elif sep != None:
                    if sep != '.':
                        abbr += sep
                    abbr += n[initial] + '.'
                    sep = None
                initial += 1
            if abbr:
                fnamesabbr.append(abbr)
        return (['~'.join(fnamesabbr)], mnames, lnames, snames)
    else:
        return (fnames, mnames, lnames, snames)

def name_last_initials(name, size):
    (fnames, mnames, lnames, snames) = break_name(name)
    mnamestr = ''
    for mname in mnames:
        first = 0
        while first < len(mname):
            if mname[first] not in '{}\\':
                mnamestr += mname[first]
                break
            elif mname[first] == '\\':
                first += 2
            else:
                first += 1
    lnamestr = ''
    for lname in lnames:
        if len(lnamestr) >= size:
            break
        first = 0
        while first < len(lname):
            if lname[first] not in '{}\\':
                lnamestr += lname[first]
                if mnamestr != '' or len(lnamestr) >= size:
                    break
                else:
                    first += 1
            elif lname[first] == '\\':
                first += 2
            else:
                first += 1
    return mnamestr + lnamestr

def name_sort_last_first(name):
    (fnames, mnames, lnames, snames) = break_name(name)
    fnames = [n.lower().strip(' \t{}') for n in fnames]
    mnames = [n.lower().strip(' \t{}') for n in mnames]
    lnames = [n.lower().strip(' \t{}') for n in lnames]
    snames = [n.lower().strip(' \t{}') for n in snames]
    return tuple([tuple(x) for x in ((mnames + lnames), fnames, snames)])

def name_last_first(name):
    (fnames, mnames, lnames, snames) = break_name(name)
    namestr = ''
    for n in mnames:
        namestr = punctuate(namestr) + n
    for n in lnames:
        namestr = punctuate(namestr) + n
    if len(fnames) > 0:
        namestr = punctuate(namestr, ',')
    for n in fnames:
        namestr = punctuate(namestr) + n
    for n in snames:
        namestr = punctuate(namestr) + n
    return namestr

def name_first_last(name):
    (fnames, mnames, lnames, snames) = break_name(name)
    namestr = ''
    for n in fnames:
        namestr = punctuate(namestr) + n
    for n in mnames:
        namestr = punctuate(namestr) + n
    for n in lnames:
        namestr = punctuate(namestr) + n
    if len(snames) > 0:
        namestr = punctuate(namestr, ',')
    for n in snames:
        namestr = punctuate(namestr) + n
    return namestr

def name_shortfirst_last(name):
    (fnames, mnames, lnames, snames) = break_name(name, short=True)
    namestr = ''
    for n in fnames:
        namestr = punctuate(namestr) + n
    for n in mnames:
        namestr = punctuate(namestr) + n
    for n in lnames:
        namestr = punctuate(namestr) + n
    if len(snames) > 0:
        namestr = punctuate(namestr, ',')
    for n in snames:
        namestr = punctuate(namestr) + n
    return namestr

def names_last(names):
    '''Return just the last names as a tuple'''
    if names:
        names = list(names)
        for i in range(len(names)):
            (fnames, mnames, lnames, snames) = break_name(names[i])
            names[i] = ''
            for n in lnames:
                names[i] = punctuate(names[i]) + n
    return tuple(names)

def names_first_last(names):
    '''Make all entries (first, last)'''
    names = list(names)
    for i in range(len(names)):
        names[i] = name_first_last(names[i])
    return tuple(names)

def names_shortfirst_last(names):
    '''Make all entries (first, last)'''
    names = list(names)
    for i in range(len(names)):
        names[i] = name_shortfirst_last(names[i])
    return tuple(names)

def names_last_first_first_last(names):
    '''Make the first entry (last, first), and the rest (first, last)'''
    names = list(names)
    if len(names) > 0:
        names[0] = name_last_first(names[0])
    return tuple(names)

def names_last_first(names):
    '''Make all entries (last, first)'''
    names = list(names)
    for i in range(len(names)):
        names[i] = name_last_first(names[i])
    return tuple(names)

################################ List Formatters ###############################

def list_comma_and(objs):
    assert all([isinstance(s, str) or isinstance(s, str) for s in objs])
    value = ''
    for i in range(len(objs)):
        if value:
            if len(objs) > 2:
                value += ','
            value += ' '
            if i == len(objs) - 1:
                value += 'and '
        value += str(objs[i])
    return value

############################### Title Formatters ###############################

def title_uppercase(title):
    newtitle = ''
    dollars = 0
    dashlen = 0
    inmath = False
    inliteral = False
    incommand = False
    for i, char in enumerate(title):
        if char == '{':
            close = _protectre.search(title[i+1:])
            inliteral = not incommand and (close is not None and close.group() == '}')
        if char == '}':
            inliteral = False

        if char == '\\':
            incommand = True
        elif char.isspace():
            incommand = False

        if char == '-':
            dashlen += 1
        else:
            dashlen = 0

        if char == '$':
            dollars += 1
        elif dollars > 0:
            inmath = not inmath
            dollars = 0

        if not (inliteral or inmath or incommand):
            newtitle += char.upper()
        else:
            newtitle += char

        if not char.isalnum() and char not in '_\\':
            incommand = False
    return newtitle

def title_titlecase(title, titlephrases):
    newtitle = ''
    ignoreuntil = 0
    dollars = 0
    dashlen = 0
    inmath = False
    inliteral = False
    incommand = False
    wordbreak = True
    sentencebreak = True
    for i, char in enumerate(title):
        if char == '{':
            close = _protectre.search(title[i+1:])
            inliteral = not incommand and (close is not None and close.group() == '}')
        if char == '}':
            inliteral = False

        if char == '\\':
            incommand = True
        elif char.isspace():
            incommand = False

        if char == '-':
            dashlen += 1
        else:
            dashlen = 0

        if char == '$':
            dollars += 1
        elif dollars > 0:
            inmath = not inmath
            dollars = 0

        if i >= ignoreuntil:
            if wordbreak and not (inliteral or inmath or incommand):
                match = ''
                for phrase in titlephrases:
                    if title.lower().startswith(phrase.lower(), i) and len(phrase) > len(match) and (i + len(phrase) >= len(title) - 1 or not title[i + len(phrase)].isalnum()):
                        match = phrase
                if len(match) > 0:
                    ignoreuntil = i + len(match)
                    newtitle += match
                else:
                    newtitle += char.upper()
            else:
                newtitle += char

        sentencebreak = (not inliteral and not inmath and not incommand and (char in '!?:.' or dashlen > 1)) or (sentencebreak and (char.isspace() or incommand or inmath or char == '{'))
        wordbreak = sentencebreak or (not inliteral and not inmath and not incommand and (char.isspace() or char in ',-')) or (wordbreak and (incommand or inmath or char == '{'))

        if not char.isalnum() and char not in '_\\':
            incommand = False
    return newtitle

def title_lowercase(title, lowerphrases):
    newtitle = ''
    ignoreuntil = 0
    dollars = 0
    dashlen = 0
    inmath = False
    inliteral = False
    incommand = False
    wordbreak = True
    sentencebreak = True
    for i, char in enumerate(title):
        if char == '{':
            close = _protectre.search(title[i+1:])
            inliteral = not incommand and (close is not None and close.group() == '}')
        if char == '}':
            inliteral = False

        if char == '\\':
            incommand = True
        elif char.isspace():
            incommand = False

        if char == '-':
            dashlen += 1
        else:
            dashlen = 0

        if char == '$':
            dollars += 1
        elif dollars > 0:
            inmath = not inmath
            dollars = 0

        if i >= ignoreuntil:
            if wordbreak and not (sentencebreak or inliteral or inmath or incommand):
                match = ''
                for phrase in lowerphrases:
                    if title.lower().startswith(phrase.lower(), i) and len(phrase) > len(match) and (i + len(phrase) >= len(title) - 1 or not title[i + len(phrase)].isalnum()):
                        match = phrase.lower()
                if len(match) > 0:
                    ignoreuntil = i + len(match)
                    newtitle += match
                else:
                    newtitle += char.lower()
            else:
                newtitle += char.lower()

        sentencebreak = (not inliteral and not inmath and not incommand and (char in '!?:.' or dashlen > 1)) or (sentencebreak and (char.isspace() or incommand or inmath or char == '{'))
        wordbreak = sentencebreak or (not inliteral and not inmath and not incommand and (char.isspace() or char in ',-')) or (wordbreak and (incommand or inmath or char == '{'))

        if not char.isalnum() and char not in '_\\':
            incommand = False
    return newtitle

################################# Label Makers #################################

def label_initials(authors):
    value = ''
    if len(authors) == 1:
        value = name_last_initials(authors[0], 3)
    elif len(authors) <= 4:
        value += ''.join([name_last_initials(a, 1) for a in authors])
    else:
        value += ''.join([name_last_initials(a, 1) for a in authors[:4]])
        value += '{etalchar}'
    return value

def label_fullnames(authors):
    value = ''
    if len(authors) == 2:
        (fnames1, mnames1, lnames1, snames1) = break_name(authors[0])
        (fnames2, mnames2, lnames2, snames2) = break_name(authors[1])
        value = ' '.join(mnames1 + lnames1) + ' \& ' + ' '.join(mnames2 + lnames2)
    elif authors:
        (fnames1, mnames1, lnames1, snames1) = break_name(authors[0])
        value = ' '.join(mnames1 + lnames1)
        if len(authors) > 2:
            value += ' et al.'
        return value

def label_lastnames_list(authors):
    broken_names = [break_name(a) for a in authors]
    last_names   = [' '.join(mname + lname) for (fname, mname, lname, sname) in broken_names]
    return last_names

def label_lastnames_all(authors):
    value = ''
    last_names = label_lastnames_list(authors)
    if len(last_names) == 1:
        value = last_names[0]
    elif len(last_names) == 2:
        value = '%s and %s' % (last_names[0], last_names[1])
    elif len(last_names) > 0:
        value = '%s, and %s' % (', '.join(last_names[:-1]), last_names[-1])
    return value

def label_lastnames_first(authors):
    last_names = label_lastnames_list(authors)
    if len(last_names) == 0:
        return ''
    elif len(last_names) == 1:
        return last_names[0]
    else:
        return '%s et~al\mbox{.}' % last_names[0]

def label_generate_initials(citations):
    by_label = collections.defaultdict(list)
    for cite, obj in citations:
        if not obj.author:
            continue
        author = [a.name.value if hasattr(a, 'name') else a.value for a in obj.author]
        year = getattr(obj, 'year', None)
        label = crosstex.style.label_initials(author)
        if year:
            if isinstance(year, crosstex.parse.Value):
                label += '%02i' % (year.value % 100)
            else:
                label += '%02i' % (year % 100)
        by_label[label].append(cite)
    by_cite = {}
    for label, citelist in by_label.iteritems():
        suffixes = itertools.repeat('')
        if len(citelist) > 1:
            alpha = ['', ''] + list('abcdefghijklmnopqrstuvwxyz')
            suffixes = itertools.imap(lambda y: ''.join(y), itertools.combinations(alpha, 3))
        try:
            for suffix, cite in itertools.izip(suffixes, citelist):
                by_cite[cite] = label + suffix
        except StopIteration:
            raise crosstex.CrossTeXError('Way too many citations with the same author initials in the same year')
    return [by_cite[c] for c, o in citations]

def label_generate_fullnames(citations):
    assert False # XXX

def label_generate_lastnames(citations):
    by_label = collections.defaultdict(list)
    for cite, obj in citations:
        if not obj.author:
            print('author', cite)
        assert obj.author
        author = [a.name.value if hasattr(a, 'name') else a.value for a in obj.author]
        year = getattr(obj, 'year', None)
        if not year:
            year = getattr(obj, 'accessyear', None)
        if not year:
            print('year', cite)
        assert year

        label = '\protect\citeauthoryear{%s}{%s}' % (label_lastnames_all(author), label_lastnames_first(author))
        if year:
            if isinstance(year, crosstex.parse.Value):
                label += '{%i}' % year.value
            else:
                label += '{%i}' % year
        by_label[label].append(cite)
    by_cite = {}
    for label, citelist in by_label.iteritems():
        suffixes = itertools.repeat('')
        if len(citelist) > 1:
            alpha = ['', ''] + list('abcdefghijklmnopqrstuvwxyz')
            suffixes = itertools.imap(lambda y: ''.join(y), itertools.combinations(alpha, 3))
        try:
            for suffix, cite in itertools.izip(suffixes, citelist):
                by_cite[cite] = label + suffix
        except StopIteration:
            raise crosstex.CrossTeXError('Way too many citations with the same author initials in the same year')
    return [by_cite[c] for c, o in citations]

