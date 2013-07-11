'''Parse files containing CrossTeX databases and citations.

Care is taken to ensure that even in the face of errors, CrossTeX does as much
as possible.  Additionally, errors are never thrown except when necessary for
the bibliography the user wants.  Entries that are not cited or use in
inheritance will never be resolved or touched beyond the initial parsing, which
is designed to be fast and error-free.  This is for efficiency as much as peace
of mind.  To check every entry in a database, simply cite every entry, and then
they will all have to be resolved and checked.
'''

import logging

# Setup logging before importing any crosstex things
logging.basicConfig(format='%(message)s')

import copy
import importlib
import itertools
import operator
import re

import crosstex.objects
import crosstex.parse

logger = logging.getLogger('crosstex')

class UNIQUE(object): pass

_author = re.compile('\s+and\s+')

class Constraint(object):
    'A convenience representation of a constrained citation.'

    def __init__(self, key):
        self._fields = {}
        parts = key[1:].lower().split(':')
        for i in range(len(parts)):
            constraint = parts[i].split('=', 1)
            if len(constraint) == 1:
                try:
                    values = int(constraint[0])
                except ValueError:
                    if i == 0:
                        field = 'author'
                    else:
                        field = 'title'
                    values = constraint[0].split('-')
                else:
                    field = 'year'
                    values = [unicode(values)]
            else:
                field = constraint[0]
                values = constraint[1].split('-')
            if not field:
                logger.error(self.options, 'Empty field in constraint "%s".' % key)
            if not values:
                logger.error(self.options, 'Empty values in constraint "%s".' % key)
            if field and values:
                self._fields[field] = values

    def empty(self):
        return not len(self._fields)

    def match(self, entry):
        entry = entry[0]
        for field, values in self._fields.iteritems():
            if not hasattr(entry, field):
                return False
            tocheck = getattr(entry, field)
            strings = set([])
            if isinstance(tocheck, crosstex.parse.Value):
                strings.add(unicode(tocheck.value).lower())
            elif isinstance(tocheck, crosstex.objects.string):
                strings.add(unicode(tocheck.name.value).lower())
                strings.add(unicode(tocheck.shortname.value).lower())
                strings.add(unicode(tocheck.longname.value).lower())
            elif field == 'author' and isinstance(tocheck, list):
                for a in tocheck:
                    strings.add(unicode(a.value).lower())
            strings = tuple(strings)
            for value in values:
                v = value.lower()
                found = False
                for s in strings:
                    if v in s:
                        found = True
                        break
                if not found:
                    return False
        return True

class Database(object):

    def __init__(self):
        self._path = ['.']
        self._parser = crosstex.parse.Parser(self._path)
        self._cache = {}

    def append_path(self, path):
        self._path.append(path)
        self._parser.set_path(self._path)

    def parse_file(self, path):
        self._parser.parse(path)

    def aux_citations(self):
        return copy.copy(self._parser.citations)

    def all_citations(self):
        return copy.copy(self._parser.entries.keys())

    def titlephrases(self):
        return copy.copy(self._parser.titlephrases)

    def titlesmalls(self):
        return copy.copy(self._parser.titlesmalls)

    def lookup(self, key):
        if key.startswith('!'):
            return self._semantic_lookup(key)
        return self._lookup(key)[0]

    def _semantic_lookup(self, key, context=None):
        '''Resolve an entry matching the constrained citation.'''
        const = Constraint(key)
        if const.empty():
            logger.error('Empty constraint "%s".' % key)
            return None
        matches = []
        for k in self._parser.entries.keys():
            obj = self._lookup(k)
            if obj and const.match(obj):
                matches.append(obj)
        if not matches:
            return None
        if len(matches) > 1:
            logger.warning('Constraint "%s" matches multiple objects' % key)
        return matches[0][0]

    def _lookup(self, key, context=None):
        '''Resolve an entry matching the given key or constrained citation.

        Evaluate conditional fields, inheritance, @extend entries, etc. until
        the entry is stable and return the result.
        '''
        # Check for loops
        context = list(context or [])
        if key in context:
            context.append(key)
            logger.error('There is a reference cycle: %s' % ', '.join(context))
            return (None, None)
        context.append(key)
        # This makes things about 30% faster
        if key in self._cache:
            return self._cache[key]
        # Lookup all raw Entry objects
        keys, base, extensions = self._select(key)
        if base is None:
            return (None, None)
        # Get the class from crosstex.objects that corresponds to this object
        if not hasattr(crosstex.objects, base.kind):
            logger.error('%s:%d: There is no such thing as a @%s.' % (base.file, base.line, base.kind))
            return (None, None)
        kind = getattr(crosstex.objects, base.kind)
        if not isinstance(kind, type) or \
           not issubclass(kind, crosstex.objects.Object):
            logger.error('%s:%d: There is no such thing as a @%s.' % (base.file, base.line, base.kind))
            return (None, None)
        fields = {}
        conditionals = []
        # This loop iterates through the base and extensions, applying fields
        # from each.
        for entry in [base] + extensions:
            dupes = set([])
            for name, value in entry.defaults:
                if name in kind.allowed and name not in fields:
                    fields[name] = value
            for f in entry.fields:
                if not isinstance(f, crosstex.parse.Field):
                    continue
                if f.name in dupes:
                    logger.warning('%s:%d: %s field is duplicated.' %
                                   (f.value.file, f.value.line, f.name))
                elif f.name not in kind.allowed:
                    logger.warning('%s:%d: No such field %s in %s.' %
                                   (f.value.file, f.value.line, f.name, base.kind))
                else:
                    fields[f.name] = f.value
                    dupes.add(f.name)
            for c in entry.fields:
                if not isinstance(c, crosstex.parse.Conditional):
                    continue
                conditionals.append(c)
        assert all([isinstance(c, crosstex.parse.Conditional) for c in conditionals])
        # This loop resolves conditionals or references until the object reaches
        # a fixed point
        anotherpass = True
        applied_conditionals = set([])
        while anotherpass:
            anotherpass = False
            # This loop pulls references from other objects
            for name, value in fields.iteritems():
                if not isinstance(value, crosstex.parse.Value):
                    continue
                if value.kind != 'key':
                    continue
                obj, conds = self._lookup(value.value, context)
                if obj is not None:
                    assert conds is not None
                    fields[name] = obj
                    conditionals = conds + conditionals
                    anotherpass = True
                    break
            # We want to make only one change at a time
            if anotherpass:
                continue
            # This loop applies conditionals
            for c in reversed(conditionals):
                if c in applied_conditionals:
                    continue
                # Skip if not all of the fields match
                if not all([fields[f.name].kind == f.value.kind and
                            fields[f.name].value == f.value.value
                            for f in c.if_fields if f.name in fields] +
                           [False for f in c.if_fields if f.name not in fields]):
                    continue
                dupes = set([])
                for f in c.then_fields:
                    if f.name in dupes:
                        logger.warning('%s:%d: %s field is duplicated.' %
                                       (f.file, f.line, field.name, base.kind))
                    elif f.name in kind.allowed and f.name not in fields:
                        # no warning here because we just percolate these
                        # things up willy-nilly
                        fields[f.name] = f.value
                        dupes.add(f.name)
                    elif f.name in kind.allowed:
                        if f.value.kind == 'key':
                            obj, conds = self._lookup(f.value.value, context)
                            if obj != fields[f.name]:
                                logger.warning('%s:%d: %s field not applied from conditional at %s:%d because it conflicts with other value' %
                                               (base.file, base.line, f.name, c.file, c.line))
                        elif fields[f.name] != value:
                            logger.warning('%s:%d: %s field not applied from conditional at %s:%d' %
                                           (base.file, base.line, f.name, c.file, c.line))
                applied_conditionals.add(c)
            # This loop expands author/editor fields
            for name, value in fields.iteritems():
                if name not in ('author', 'editor'):
                    continue
                if not isinstance(value, crosstex.parse.Value):
                    continue
                names = []
                for n in _author.split(value.value):
                    if n in self._parser.entries:
                        obj, conds = self._lookup(n, context)
                    else:
                        obj, conds = None, None
                    if obj is not None:
                        assert conds is not None
                        names.append(obj)
                        conditionals = conds + conditionals
                    else:
                        names.append(crosstex.parse.Value(file=value.file, line=value.line, kind='string', value=n))
                fields[name] = names
                anotherpass = True
                break
        # Do a pass over alternate fields to copy them
        for name, alternates in kind.alternates.iteritems():
            if name not in fields:
                for f in alternates:
                    if f in fields:
                        fields[name] = fields[f]
                        break
        # Ensure required fields are all provided
        for name in kind.required:
            if name not in fields:
                logger.error('%s:%d: Missing required field %s in %s.' %
                             (base.file, base.line, name, base.kind))
        # Create the object
        k = kind(**fields)
        # Memoize
        for key in keys:
            self._cache[key] = (k, conditionals)
        return k, conditionals

    def _select(self, key):
        '''Select Entry objects tagged with "key".

        Aliases will be transitively followed to select all Entry objects.

        The return value will be a tuple of (keys, base, extensions).  "keys"
        will be a set consisting of key and all its aliases.  "base" will be the
        Entry object that the key maps to.  "extensions" will be a list of
        objects that extend "base".
        '''
        keys = set([])
        todo = set([key])
        seen = set([])
        base = None
        extensions = []
        while todo:
            key = todo.pop()
            keys.add(key)
            for entry in self._parser.entries.get(key, []):
                if entry in seen:
                    continue;
                seen.add(entry)
                if entry.kind == 'extend':
                    extensions.append(entry)
                elif base is None:
                    base = entry
                else:
                    logger.error('%s:%d: Alias %s is also defined at %s:%d.' %
                                 (base.file, base.line, key, entry.file, entry.line))
                    continue
                for k in entry.keys:
                    if k not in keys:
                        todo.add(k)
        if base is None:
            if extensions:
                logger.error('%s is extended but never defined.' % key)
            else:
                logger.error('%s is never defined.' % key)
        # XXX provide a guaranteed order for the extensions.
        # In an ideal world we'd traverse includes in a DFS manner according to
        # include order, thus guaranteeing that extensions will be resolved in a
        # consistent fashion.  Right now, conflicting extensions will be
        # resolved in a predictable manner
        return (keys, base, extensions)

class CrossTeXError(Exception): pass

class CrossTeX(object):

    def __init__(self, xtx_path=None):
        self._db = Database()
        for p in xtx_path or []:
            self._db.append_path(p)
        self._flags = set([])
        self._options = {}
        self._style = None

    def add_in(self):
        self._flags.add('add-in')

    def add_proc(self):
        if 'add-proceedings' in self._flags:
            self._flags.remove('add-proceedings')
        self._flags.add('add-proc')

    def add_proceedings(self):
        if 'add-proc' in self._flags:
            self._flags.remove('add-proc')
        self._flags.add('add-proceedings')

    def add_short(self, field):
        self._flags.add('short-' + field)

    def set_titlecase(self, case):
        self._flags.add('titlecase-' + case)

    def set_style(self, fmt, style, cite_by):
        if fmt == 'bib':
            raise CrossTeXError('CrossTeX currently doesn\'t write bib files.') # XXX
        if fmt == 'xtx':
            raise CrossTeXError('CrossTeX currently doesn\'t write xtx files.') # XXX
        if cite_by not in ('number', 'initials', 'fullname', 'style'):
            raise CrossTeXError('Unknown label style %r.' % cite_by)
        self._options['cite-by'] = cite_by
        try:
            stylemod = importlib.import_module('crosstex.style.' + style)
            if not hasattr(stylemod, 'Style'):
                raise CrossTeXError('Could not import style %r' % style)
            styleclass = getattr(stylemod, 'Style')
        except ImportError as e:
            raise CrossTeXError('Could not import style %r' % style)
        if fmt not in styleclass.formats():
            raise CrossTeXError('Style %r does not support format %r' % (style, fmt))
        self._style = styleclass(fmt, self._flags, self._options, self._db)

    def parse(self, xtxname):
        self._db.parse_file(xtxname)

    def aux_citations(self):
        return self._db.aux_citations()

    def all_citations(self):
        return self._db.all_citations()

    def lookup(self, key):
        return self._db.lookup(key)

    def sort(self, citations, fields=None):
        if self._style is None:
            raise CrossTeXError('Cannot sort citations because no style is set')
        fields = fields or []
        citations = list(citations)
        citations = sorted(citations, key=operator.itemgetter(0))
        citations = sorted(citations, key=self._style.sort_key)
        for field, reverse in reversed(fields):
            def sort_key(x):
                k, o = x
                return self._style.get_field(o, field)
            citations = sorted(citations, key=sort_key, reverse=reverse)
        return citations

    def heading(self, citations, field, reverse=False):
        def sort_key(x):
            k, o = x
            return self._style.get_field(o, field)
        citations = sorted(citations, key=sort_key, reverse=reverse)
        new_citations = []
        for heading, group in itertools.groupby(citations, sort_key):
            if heading is not None:
                new_citations.append(crosstex.style.Heading(heading))
            new_citations += list(group)
        return new_citations

    def render(self, citations):
        return self._style.render(citations)[1]

    def render_with_labels_dict(self, citations):
        return self._style.render(citations)
