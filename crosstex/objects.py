import collections
import copy

import crosstex.parse

class CiteableTrue(object):
    def __get__(self, obj, objtype):
        return True

class CiteableFalse(object):
    def __get__(self, obj, objtype):
        return False

class Field(object):
    def __init__(self, required=False, alternates=None, types=None, iterable=False):
        self.required = required
        self.alternates = alternates or []
        self.types = tuple(types or [])
        self.types += (str, crosstex.parse.Value)
        self.iterable = iterable
        self.name = None
    def __get__(self, obj, objtype):
        if hasattr(obj, '_' + self.name):
            return getattr(obj, '_' + self.name)
        return None
    def __set__(self, obj, value):
        if value is not None and \
           value.__class__ not in self.types and \
           not (self.iterable and isinstance(value, collections.Iterable) and
                all([isinstance(v, self.types) for v in value])):
            raise TypeError('Field %s does not allow type %s' %
                            (self.name, unicode(type(value))))
        setattr(obj, '_' + self.name, value)

class ObjectMeta(type):
    def __new__(cls, name, bases, dct):
        allowed = set([])
        required = set([])
        alternates = {}
        for attr, value in dct.iteritems():
            if attr == 'citeable':
                assert value.__class__ in (CiteableTrue, CiteableFalse)
            elif not attr.startswith('_') and not callable(value):
                assert attr not in ('kind', 'required', 'allowed', 'alternates')
                assert isinstance(value, Field)
                allowed.add(attr)
                if value.required:
                    required.add(attr)
                if isinstance(value.alternates, unicode):
                    alternates[attr] = value.alternates
                elif isinstance(value.alternates, collections.Iterable):
                    assert all([isinstance(a, str) for a in value.alternates])
                    alternates[attr] = [a for a in value.alternates]
                else:
                    assert False
                value.name = attr
        optional = allowed - required
        assert len(bases) <= 1
        for base in bases:
            if hasattr(base, 'allowed'):
                allowed |= base.allowed
            if hasattr(base, 'required'):
                required |= base.required - optional
            if hasattr(base, 'alternates'):
                newalternates = copy.copy(base.alternates)
                newalternates.update(alternates)
                alternates = newalternates
                del newalternates
        dct['kind'] = name
        dct['allowed'] = allowed
        dct['required'] = required
        dct['alternates'] = alternates
        return super(ObjectMeta, cls).__new__(cls, name, bases, dct)

class Object(object):
    __metaclass__ = ObjectMeta
    citeable = CiteableFalse()

    def __init__(self, **kwargs):
        for key, word in kwargs.iteritems():
            assert not key.startswith('_') and hasattr(self, key)
            setattr(self, key, word)

    def isset_field(self, name):
        return getattr(self, name, None) is not None

    def set_field(self, name, value):
        setattr(self, name, value)

    def iteritems(self):
        for f in self.allowed:
            v = getattr(self, f, None)
            yield (f, v)

###############################################################################

class string(Object):
    name      = Field(alternates=('longname', 'shortname'))
    shortname = Field(required=True, alternates=('name', 'longname'))
    longname  = Field(required=True, alternates=('name', 'shortname'))

class country(string):
    pass

class state(string):
    country = Field(types=(country,))

class location(string):
    name    = Field(required=True, alternates=('longname', 'shortname', 'city', 'state', 'country'))
    city    = Field()
    state   = Field(types=(state,))
    country = Field(types=(country,))

class month(string):
    monthno = Field()

class institution(string):
    address = Field(types=(location, country, state))

class school(institution):
    pass

class author(string):
    address      = Field(types=(location, country, state))
    affiliation  = Field()
    email        = Field()
    institution  = Field()
    organization = Field()
    phone        = Field()
    school       = Field()
    url          = Field()

###############################################################################

class journal(string):
    pass

class conference(string):
    pass

class conferencetrack(conference):
    conference = Field(types=(conference,))

class workshop(conferencetrack):
    conference = Field(types=(conference,))

###############################################################################

def Author(required=False):
    return Field(required=True, types=(author,), iterable=True)

def BookTitle(required=False):
    return Field(required=required, types=(conference, conferencetrack, workshop))

###############################################################################

class citeableref(Object):
    citeable = CiteableTrue()
    abstract    = Field()
    category    = Field()
    subcategory = Field()
    ps   = Field()
    pdf  = Field()
    http = Field()

class article(citeableref):
    author  = Author(required=True)
    title   = Field(required=True)
    journal = Field(required=True, alternates=('newspaper'), types=(journal,))
    year    = Field(required=True)
    month   = Field(types=(month,))
    volume  = Field()
    number  = Field()
    pages   = Field()

class book(citeableref):
    author    = Author(required=True)
    editor    = Field()
    title     = Field(required=True)
    publisher = Field(required=True)
    address   = Field(required=True,types=(location,country,state))
    year      = Field(required=True)

class booklet(citeableref):
    title = Field(required=True)

class inbook(citeableref):
    author    = Author(required=True)
    editor    = Field()
    title     = Field(required=True)
    chapter   = Field(required=True)
    pages     = Field(required=True)
    publisher = Field(required=True)
    year      = Field(required=True)

class incollection(citeableref):
    author    = Author(required=True)
    title     = Field(required=True)
    booktitle = BookTitle(required=True)
    publisher = Field(required=True)
    year      = Field(required=True)

class inproceedings(citeableref):
    author    = Author(required=True)
    title     = Field(required=True)
    booktitle = BookTitle(required=True)
    pages     = Field()
    address   = Field(types=(location, country, state))
    year      = Field()
    month     = Field(types=(month,))

class manual(citeableref):
    title = Field(required=True)

class misc(citeableref):
    author       = Author()
    title        = Field()
    howpublished = Field()
    booktitle    = BookTitle()
    address      = Field(types=(location, country, state))
    year         = Field()

class patent(citeableref):
    author = Author(required=True)
    title  = Field(required=True)
    number = Field(required=True)
    month  = Field(required=True, types=(month,))
    year   = Field(required=True)

class rfc(citeableref):
    author = Author(required=True)
    title  = Field(required=True)
    number = Field(required=True)
    month  = Field(required=True, types=(month,))
    year   = Field(required=True)

class techreport(citeableref):
    author      = Author(required=True)
    title       = Field(required=True)
    number      = Field()
    institution = Field(required=True)
    address     = Field(types=(location, country, state))
    year        = Field(required=True)
    month       = Field(types=(month,))

class thesis(citeableref):
    author = Author(required=True)
    title  = Field(required=True)
    school = Field(required=True)
    number = Field()
    year   = Field(required=True)

class mastersthesis(thesis):
    pass

class phdthesis(thesis):
    pass

class unpublished(citeableref):
    author = Author(required=True)
    title  = Field(required=True)
    note   = Field(required=True)

class url(citeableref):
    author      = Author()
    title       = Field()
    url         = Field(required=True)
    accessmonth = Field(types=(month,))
    accessyear  = Field()
    accessday   = Field()
