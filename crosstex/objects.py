'''
Information about the objects that can occur in databases.

The class hierarchy here describes how formatting works, which fields
are required, optional, and can derive values from other fields, etc.

REQUIRED and OPTIONAL are constants describing requirement levels for
fields in objects.
'''

import re
from copy import copy


REQUIRED = object()
OPTIONAL = object()


def cmpclasses(a, b):
  'A comparison function sorting subclasses before parents.'

  le = issubclass(a, b)
  ge = issubclass(b, a)
  if le and not ge:
    return -1
  if ge and not le:
    return 1
  return cmp(a.__name__, b.__name__)


_producers = {}
_listfilters = {}
_listformatters = {}
_filters = {}


class Formatter(object):

  _citeable = False

  def __init__(self, *kargs, **kwargs):
    self._value = None
    super(Formatter, self).__init__(*kargs, **kwargs)

  def _chain(cls, filter, chain, context):
    if not context:
      raise ValueError, 'Empty context'
    l = chain.setdefault(context, {}).setdefault(cls, [])
    v = filter
    if not hasattr(v, '__call__'):
      v = lambda obj, value, context: filter
    if chain is _producers:
      l.insert(0, v)
    else:
      l.append(v)
  _chain = classmethod(_chain)

  def _addproducer(cls, filter, *context):
    cls._chain(filter, _producers, context)
  _addproducer = classmethod(_addproducer)

  def _addlistfilter(cls, filter, *context):
    cls._chain(filter, _listfilters, context)
  _addlistfilter = classmethod(_addlistfilter)

  def _addlistformatter(cls, filter, *context):
    cls._chain(filter, _listformatters, context)
  _addlistformatter = classmethod(_addlistformatter)

  def _addfilter(cls, filter, *context):
    cls._chain(filter, _filters, context)
  _addfilter = classmethod(_addfilter)

  def _filter(self, chain, value, stop, context):
    if stop(value):
      return value
    for i in range(len(context)):
      try:
        filters = chain[context[i:]]
      except KeyError:
        continue
      kinds = [ t for t in filters if isinstance(self, t) ]
      kinds.sort(cmpclasses)
      for kind in kinds:
	for filter in filters[kind]:
	  newvalue = filter(self, value, context)
	  if newvalue is not None:
	    value = newvalue
	    if stop(value):
	      return value
    return value

  def _format(self, *context):
    listtest = lambda x: x is None or not hasattr(x, '__iter__')
    value = self._filter(_producers, None, lambda x: x is not None, context)
    value = self._filter(_listfilters, value, listtest, context)
    value = self._filter(_listformatters, value, listtest, context)
    if value is not None:
      value = str(value)
    value = self._filter(_filters, value, lambda x: x is None, context)
    if value is not None:
      value = str(value)
    return value

  def __str__(self):
    if self._value is None:
      self._value = self._format('value')
      if self._value is None:
        self._value = ''
    return self._value


class ObjectList(Formatter, list):
  def __init__(self, *kargs, **kwargs):
    super(ObjectList, self).__init__(*kargs, **kwargs)


class Object(Formatter):
  def __init__(self, keys, fields, conditions, file, line, *kargs, **kwargs):
    super(Object, self).__init__(*kargs, **kwargs)
    self.keys = keys
    self.file = file
    self.line = line
    self.kind = type(self).__name__
    self.kind = self.kind[self.kind.rfind('.')+1:]
    self.conditions = conditions
    self.fields = fields
    self.citation = None


class Concatenation(list):
  def __str__(self):
    return ''.join([str(x) for x in self])


#
# The actual objects.
#

class string(Object):
  name = ['longname', 'shortname']
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
  name = [REQUIRED, 'longname', 'shortname', 'city', 'state', 'country']
  shortname = ['name', 'longname']
  longname = ['name', 'shortname']
  city = OPTIONAL
  state = OPTIONAL
  country = OPTIONAL

class month(string):
  monthno = REQUIRED

class journal(string):
  pass

class institution(string):
  address = OPTIONAL

class school(institution):
  pass

class publication(Object):
  _citeable = True

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
  journal = 'newspaper'
  newspaper = 'journal'
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

class misc(publication):
  pass

class article(publication):
  author = REQUIRED
  title = REQUIRED
  journal = [REQUIRED, 'newspaper']
  newspaper = 'journal'
  year = REQUIRED

class book(publication):
  author = REQUIRED
  editor = OPTIONAL
  title = REQUIRED
  publisher = REQUIRED
  year = REQUIRED

class booklet(publication):
  title = REQUIRED

class inbook(publication):
  author = REQUIRED
  editor = REQUIRED
  title = REQUIRED
  chapter = REQUIRED
  pages = REQUIRED
  publisher = REQUIRED
  year = REQUIRED

class incollection(publication):
  author = REQUIRED
  title = REQUIRED
  booktitle = REQUIRED
  publisher = REQUIRED
  year = REQUIRED

class inproceedings(publication):
  author = REQUIRED
  title = REQUIRED
  booktitle = REQUIRED
  year = REQUIRED

class manual(publication):
  title = REQUIRED

class thesis(publication):
  author = REQUIRED
  title = REQUIRED
  school = REQUIRED
  year = REQUIRED

class mastersthesis(thesis):
  pass

class phdthesis(thesis):
  pass

class proceedings(publication):
  title = REQUIRED
  year = REQUIRED

class collection(proceedings):
  pass

class patent(publication):
  author = REQUIRED
  title = REQUIRED
  number = REQUIRED
  month = REQUIRED
  year = REQUIRED

class techreport(publication):
  author = REQUIRED
  title = REQUIRED
  institution = REQUIRED
  year = REQUIRED

class unpublished(publication):
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
  journal = 'newspaper'
  newspaper = 'journal'
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

class rfc(publication):
  author = REQUIRED
  title = REQUIRED
  number = REQUIRED
  month = REQUIRED
  year = REQUIRED

class url(publication):
  url = REQUIRED
  accessmonth = OPTIONAL
  accessyear = OPTIONAL
  accessday = OPTIONAL

class newspaperarticle(article):
  author = OPTIONAL

class newspaper(journal):
  pass


#
# Initialization
#

def _fieldproducer(obj, value, context):
  try:
    return obj.fields.get(context[-1], None)
  except AttributeError:
    return
  except IndexError:
    return

for kind in globals().values():
  if not (isinstance(kind, type) and issubclass(kind, Object)):
    continue

  kind._required = {}
  kind._allowed = {}
  kind._fillin = {}

  for field in dir(kind):
    if field.startswith('_'):
      continue
    kind._allowed[field] = True
    value = getattr(kind, field)

    if hasattr(value, '__iter__'):
      if REQUIRED in value:
	kind._required[field] = True
      kind._fillin[field] = [str(f) for f in value \
			     if f is not REQUIRED and f is not OPTIONAL]
    else:
      if value is REQUIRED:
	kind._required[field] = True
      elif value is not OPTIONAL:
	kind._fillin[field] = [str(value)]

    kind._addproducer(_fieldproducer, field)
