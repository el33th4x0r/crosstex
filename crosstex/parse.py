'''
Parse files containing CrossTeX databases and citations.

Care is taken to ensure that even in the face of errors, CrossTeX does
as much as possible.  Additionally, errors are never thrown except when
necessary for the bibliography the user wants.  Entries that are not
cited or use in inheritance will never be resolved or touched beyond
the initial parsing, which is designed to be fast and error-free.
This is for efficiency as much as peace of mind.  To check every entry
in a database, simply cite every entry, and then they will all have to
be resolved and checked.
'''

import collections
import copy
import logging
import os
import cPickle as pickle
import re

import ply.lex
import ply.yacc

import crosstex

logger = logging.getLogger('crosstex.parse')

Entry = collections.namedtuple('Entry', ('kind', 'keys', 'fields', 'file', 'line', 'defaults'))
Value = collections.namedtuple('Value', ('file', 'line', 'kind', 'value'))
Field = collections.namedtuple('Field', ('name', 'value'))
Conditional = collections.namedtuple('Conditional', ('file', 'line', 'if_fields', 'then_fields'))

def create_value(_file, line, value, kind=None):
    if kind is None:
        try:
            value = int(value)
            kind = 'number'
        except ValueError:
            value = unicode(value)
            kind = 'string'
    return Value(_file, line, kind, value)

class XTXFileInfo:
    'Same stuff as in Parser, but only for one file'

    def __init__(self):
        self.cite = set([])
        self.alias = {}
        self.titlephrases = set([])
        self.titlesmalls = set([])
        self.preambles = set([])
        self.entries = collections.defaultdict(list)
        self.tobeparsed = []

    def parse(self, file, **kwargs):
        self.tobeparsed.append(file)

    def merge(self, db):
        db.cite = set(db.cite) | self.cite
        db.alias = db.alias.copy()
        db.alias.update(self.alias)
        db.titlephrases = set(db.titlephrases) | self.titlephrases
        db.titlesmalls = set(db.titlesmalls) | self.titlesmalls
        db.preambles = db.preambles | self.preambles
        for k, es in self.entries.items():
            db.entries[k] += es
        for file in self.tobeparsed:
            db.parse(file, exts=['.xtx', '.bib'])

class Parser:
    'A structure of almost raw data from the databases.'

    def __init__(self, path):
        self.cite = set([])
        self.alias = {}
        self.titlephrases = set([])
        self.titlesmalls = set([])
        self.preambles = set([])
        self.entries = collections.defaultdict(list)
        self.citations = set([])
        self._bibstyle = 'plain'
        self._path = path
        self._seen = collections.defaultdict(dict)
        self._dirstack = []

    def set_path(self, path):
        self._path = path

    def parse(self, name, exts=['.aux', '.xtx', '.bbl']):
        'Find a file with a reasonable extension and extract its information.'
        if name in self._seen:
            logger.debug('Already processed %r.' % name)
            for ext, path in self._seen[name].iteritems():
                if ext in exts:
                    return path
        if os.path.sep in name:
            logger.debug('%r has a %r, treating it as a path to a file.' % (name, os.path.sep))
            path = name
            if self._dirstack:
                path = os.path.join(self._dirstack[-1], path)
            if not os.path.exists(path):
                logger.error('Can not parse %r because it resolves to %r which doesn\'t exist' % (name, path))
                return None
            try:
                self._dirstack.append(os.path.dirname(path))
                return self._parse_from_path(path)
            finally:
                self._dirstack.pop()
        base, ext = os.path.splitext(name)
        if ext:
            if not self._check_ext(name, ext, exts):
                return None
            tryexts = [ext]
        else:
            tryexts = exts
        if self._dirstack:
            trydirs = self._dirstack[-1:] + self._path
        else:
            trydirs = self._path
        for d in trydirs:
            for e in tryexts:
                try:
                    self._dirstack.append(d)
                    path = os.path.join(d, base + e)
                    if not os.path.exists(path):
                        continue
                    return self._parse_from_path(path, name=name)
                finally:
                    self._dirstack.pop()
        logger.error('Can not find %s database.' % name)
        return None

    def _parse_from_path(self, path, name=None):
        'Parse a file from an absolute path'
        assert os.path.sep in path
        name = name or path
        ext = os.path.splitext(path)[1]
        if self._check_ext(path, ext):
            func = '_parse_ext_' + ext[1:]
            self._seen[name][ext] = path
            return getattr(self, func)(path)
        return None

    def _parse_ext_aux(self, path):
        'Parse and handle options set in a TeX .aux file.'
        stream = open(path)
        logger.debug('Processing auxiliary file %s.' % path)
        for line in stream:
            if line.startswith(r'\citation'):
                for citation in line[10:].strip().rstrip('}').split(','):
                    citation = citation.strip(',\t')
                    if citation:
                        self.citations.add(citation)
            elif line.startswith(r'\bibstyle'):
                self._bibstyle = line[10:].rstrip().rstrip('}').split(' ')
            elif line.startswith(r'\bibdata'):
                for f in line[9:].rstrip().rstrip('}').split(','):
                    self.parse(f, ['.xtx', '.bib'])
            elif line.startswith(r'\@input'):
                for f in line[8:].rstrip().rstrip('}').split(','):
                    self.parse(f, ['.aux'])

    def _parse_ext_bib(self, path):
        return self._parse_ext_xtx(path)

    def _parse_ext_xtx(self, path):
        'Parse and handle options set in a CrossTeX .xtx or BibTeX .bib database file.'
        cache_path = os.path.join(os.path.dirname(path),
                                  '.' + os.path.basename(path) + '.cache')
        try:
            if os.path.exists(cache_path) and \
               os.path.getmtime(path) < os.path.getmtime(cache_path):
                logger.debug("Processing database %r from cache." % path)
                with open(cache_path, 'rb') as cache_stream:
                    db = pickle.load(cache_stream)
                db.merge(self)
                return path
        except EOFError as e:
            logger.error("Could not read cache '%r', falling back to database: %s." % (cache_path, e))
        except pickle.UnpicklingError as e:
            logger.error("Could not read cache '%r', falling back to database: %s." % (cache_path, e))
        except IOError as e:
            logger.error("Could not read cache '%r', falling back to database: %s." % (cache_path, e))
        except OSError as e:
            logger.error("Could not read cache '%r', falling back to database: %s." % (cache_path, e))
        logger.debug('Processing database %s.' % path)
        db = XTXFileInfo()
        stream = open(path)
        contents = stream.read().decode('utf8')
        if contents:
            lexer = ply.lex.lex(reflags=re.UNICODE)
            lexer.path = path
            lexer.file = os.path.basename(path)
            lexer.lineno = 1
            lexer.expectstring = False

            lexer.db = db
            lexer.defaults = ()

            parser = ply.yacc.yacc(debug=0, write_tables=0)
            parser.parse(contents, lexer=lexer)
        stream.close()
        db.merge(self)
        try:
            with open(cache_path, 'wb') as cache_stream:
                pickle.dump(db, cache_stream, protocol=2)
        except pickle.PicklingError as e:
            logger.error("Could not write cache '%r', falling back to database: %s." % (cache_path, e))
        except IOError as e:
            logger.error("Could not write cache '%r', falling back to database: %s." % (cache_path, e))
        except OSError as e:
            logger.error("Could not write cache '%r', falling back to database: %s." % (cache_path, e))
        return path

    def _check_ext(self, name, ext, exts=['.aux', '.xtx', '.bib']):
        func = '_parse_ext_' + ext[1:]
        if not hasattr(self, func) or not ext in exts: 
            logger.error('Can not parse %r because the extension is not %s.'
                                % (name, '/'.join([e[1:] for e in exts])))
            return False
        return True

#
# Tokens
#

newlinere = re.compile(r'\r\n|\r|\n')
numberre = re.compile(r'^\d+$')
andre = re.compile(r'\s+and\s+')

tokens = ( 'AT', 'COMMA', 'OPENBRACE', 'CLOSEBRACE', 'LBRACK',
  'RBRACK', 'EQUALS', 'ATINCLUDE', 'ATSTRING', 'ATEXTEND', 'ATPREAMBLE',
  'ATCOMMENT', 'ATDEFAULT', 'ATTITLEPHRASE', 'ATTITLESMALL', 'ATCITE',
  'ATALIAS', 'NAME', 'NUMBER', 'STRING', )

t_ignore = ' \t'

def t_COMMENT(t):
    r'\%.*'
    pass

def t_ATINCLUDE(t):
    r'@[iI][nN][cC][lL][uU][dD][eE]'
    t.lexer.expectstring = False
    return t

def t_ATSTRING(t):
    r'@[sS][tT][rR][iI][nN][gG]'
    t.lexer.expectstring = False
    return t

def t_ATEXTEND(t):
    r'@[eE][xX][tT][eE][nN][dD]'
    t.lexer.expectstring = False
    return t

def t_ATPREAMBLE(t):
    r'@[pP][rR][eE][aA][mM][bB][lL][eE]'
    t.lexer.expectstring = False
    return t

def t_ATCOMMENT(t):
    r'@[Cc][Oo][Mm][Mm][Ee][Nn][Tt]'
    t.lexer.expectstring = True
    return t

def t_ATDEFAULT(t):
    r'@[Dd][Ee][Ff][Aa][Uu][Ll][Tt]'
    t.lexer.expectstring = False
    return t

def t_ATTITLEPHRASE(t):
    r'@[Tt][Ii][Tt][Ll][Ee][Pp][Hh][Rr][Aa][Ss][Ee]'
    t.lexer.expectstring = True
    return t

def t_ATTITLESMALL(t):
    r'@[Tt][Ii][Tt][Ll][Ee][Ss][Mm][Aa][Ll][Ll]'
    t.lexer.expectstring = True
    return t

def t_ATCITE(t):
    r'@[Cc][Ii][Tt][Ee]'
    t.lexer.expectstring = True
    return t

def t_ATALIAS(t):
    r'@[Aa][Ll][Ii][Aa][Ss]'
    t.lexer.expectstring = True
    return t

def t_STRING(t):
    r'"(\\.|[^\\"])*"'
    t.lexer.expectstring = False
    t.lexer.lineno += len(newlinere.findall(t.value))
    t.value = t.value[1:-1]
    return t

def t_EQUALS(t):
    r'='
    t.lexer.expectstring = True
    return t

def t_NAME(t):
    r'[-a-zA-Z:0-9/_.]+'
    t.lexer.expectstring = False
    if numberre.match(t.value):
        t.type = 'NUMBER'
    return t

def t_OPENBRACE(t):
    r'\{'
    if t.lexer.expectstring:

        bracelevel = 1
        while bracelevel > 0:
            c = t.lexer.lexdata[t.lexer.lexpos]
            t.lexer.lexpos += 1
            if c == '{' and t.value[-1] != '\\':
                bracelevel += 1
            if c == '}' and t.value[-1] != '\\':
                bracelevel -= 1
            t.value += c

        t.lexer.expectstring = False
        t.lexer.lineno += len(newlinere.findall(t.value))
        t.value = t.value[1:-1]
        if numberre.match(t.value):
            t.type = 'NUMBER'
        else:
            t.type = 'STRING'

    return t

def t_CLOSEBRACE(t):
    r'\}'
    t.lexer.expectstring = False
    return t

def t_AT(t):
    r'@'
    t.lexer.expectstring = False
    return t

def t_COMMA(t):
    r','
    t.lexer.expectstring = False
    return t

def t_LBRACK(t):
    r'\['
    t.lexer.expectstring = False
    return t

def t_RBRACK(t):
    r'\]'
    t.lexer.expectstring = False
    return t

def t_newline(t):
    r'(\r\n|\r|\n)'
    t.lexer.lineno += 1

def t_error(t):
    logger.error('%s:%d: Syntax error near "%s".' %
                 (t.lexer.file, t.lexer.lineno, t.value[:20]))
    t.skip(1)

#
# Grammar; start symbol is stmts.
#

precedence = ( )

def p_ignore(t):
    '''
    stmts :
          | stmt stmts
    stmt  : ATCOMMENT STRING
    '''

def p_stmt_preamble(t):
    'stmt : ATPREAMBLE OPENBRACE STRING CLOSEBRACE'
    t.lexer.db.preambles.add(t[3])

def p_stmt_titlephrase(t):
    'stmt : ATTITLEPHRASE STRING'
    t.lexer.db.titlephrases.add(t[2])

def p_stmt_titlesmall(t):
    'stmt : ATTITLESMALL STRING'
    t.lexer.db.titlesmalls.add(t[2])

def p_stmt_include(t):
    'stmt : ATINCLUDE NAME'
    t.lexer.db.parse(t[2], exts=['.xtx', '.bib'])

def p_stmt_default(t):
    'stmt : ATDEFAULT field'
    defaults = dict(t.lexer.defaults)
    if t[2][1]:
        defaults[t[2][0]] = t[2][1]
    else:
        try:
            del defaults[t[2]][0]
        except KeyError:
            pass
    t.lexer.defaults = tuple(defaults.items())

def p_stmt_cite(t):
    'stmt : ATCITE STRING'
    t.lexer.db.cite.add(t[2])

def p_stmt_alias(t):
    'stmt : ATALIAS STRING STRING'
    t.lexer.db.alias[t[2]] = t[3]

def p_stmt_string(t):
    'stmt : ATSTRING OPENBRACE fields CLOSEBRACE'
    file, line, defaults = t.lexer.file, t.lineno(2), t.lexer.defaults
    for key, value in t[3]:
        ent = Entry('string', [key], [('name', value)], file, line, defaults)
        t.lexer.db.entries[key].append(ent)

def p_stmt_entry(t):
    'stmt : entry'
    for key in t[1].keys:
        t.lexer.db.entries[key].append(t[1])

def p_entry(t):
    'entry : AT NAME OPENBRACE keys COMMA conditionals CLOSEBRACE'
    file, line, defaults = t.lexer.file, t.lineno(2), t.lexer.defaults
    t[0] = Entry(t[2].lower(), t[4], t[6], file, line, defaults)

def p_entry_extend(t):
    '''
    entry : ATEXTEND OPENBRACE keys COMMA conditionals CLOSEBRACE
          | ATEXTEND OPENBRACE keys CLOSEBRACE
    '''
    if len(t) == 7:
        fields = t[5]
    else:
        fields = []
    file, line, defaults = t.lexer.file, t.lineno(1), t.lexer.defaults
    t[0] = Entry('extend', t[3], fields, file, line, defaults)

def p_keys_singleton(t):
    'keys : NAME'
    t[0] = (t[1],)

def p_keys_multiple(t):
    'keys : NAME EQUALS keys'
    t[0] = (t[1],) + t[3]

def p_conditionals_empty(t):
    'conditionals :'
    t[0] = ()

def p_conditionals_singleton(t):
    'conditionals : conditional'
    t[0] = (t[1],)

def p_conditionals_multiple(t):
    'conditionals : conditional conditionals'
    t[0] = (t[1],) + t[2]

def p_conditionals_unconditional(t):
    'conditionals : fields conditionals'
    t[0] = t[1] + t[2]

def p_conditional(t):
    'conditional : LBRACK fields RBRACK fields'
    t[0] = Conditional(t.lexer.file, t.lineno(1), t[2], t[4])

def p_fields_empty(t):
    'fields :'
    t[0] = ()

def p_fields_singleton(t):
    'fields : field'
    t[0] = (t[1],)

def p_fields(t):
    'fields : field COMMA fields'
    t[0] = (t[1],) + t[3]

def p_field(t):
    'field : NAME EQUALS value'
    t[0] = Field(t[1].lower(), t[3])

def p_value_singleton(t):
    'value : simplevalue'
    t[0] = t[1]

def p_simplevalue_name(t):
    'simplevalue : NAME'
    t[0] = create_value(t.lexer.file, t.lineno(1), t[1], 'key')

def p_simplevalue_number(t):
    'simplevalue : NUMBER'
    t[0] = create_value(t.lexer.file, t.lineno(1), t[1], None)

def p_simplevalue_string(t):
    'simplevalue : STRING'
    t[0] = create_value(t.lexer.file, t.lineno(1), t[1], None)

def p_error(t):
    ply.yacc.errok()
    logger.error('%s:%d: Parse error near "%s".' %
                 (t.lexer.file, t.lexer.lineno, t.value[:20]))
