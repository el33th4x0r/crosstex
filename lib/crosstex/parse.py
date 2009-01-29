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

import os
import re
import cPickle as pickle
import traceback
import ply.lex
import ply.yacc

from copy import copy
from crosstex.options import OptionParser, error, warning


class Value:
  'A field value containing a string, number, key, or concatenation.'

  def __init__(self, file, line, value, kind=None):
    self.file = file
    self.line = line
    if kind is not None:
      self.kind = kind
      self.value = value
    else: 
      try:
	self.value = int(value)
	self.kind = 'number'
      except ValueError:
	self.value = str(value)
	self.kind = 'string'

  def concat(self, other, file, line):
    if self.kind != 'concat':
      self.value = [Value(self.file, self.line, self.value, self.kind)]
      self.kind = 'concat'
      self.file = file
      self.line = line
    if other.kind == 'concat':
      self.value.extend(other)
    else:
      self.value.append(other)

  def resolve(self, db, seen=None, trystrings=False):
    entries = []
    if self.kind == 'concat':
      for other in self.value:
	entries.extend(other.resolve(db, seen))
    elif self.kind == 'key' or (trystrings and self.kind == 'string'):
      entry = db._resolve(self.value, seen)
      if entry is not None:
	entries.append(entry)
	self.value = entry
	self.kind = 'entry'
      elif self.kind == 'key':
	error(db.options, '%s:%d: No such key "%s".' % (self.file, self.line, self.value))
	self.kind = 'string'
    return entries

  def __str__(self):
    if self.kind == 'concat':
      return ''.join([str(other) for other in self.value])
    else:
      return str(self.value)


class Entry:
  '''
  A single, raw entry in a database.

  Every piece of information is designed to avoid causing errors in the
  lexer/parser, and instead allow errors to be noticed during resolution.
  Thus, all fields (fields and defaults) are stored as lists of pairs
  rather than dictionaries, in order to preserve duplicates, etc.
  '''

  def __init__(self, kind, keys, fields, file, line, defaults={}):
    self.kind = kind
    self.keys = keys
    self.fields = fields
    self.file = file
    self.line = line
    self.defaults = defaults


class XTXFileInfo:
  'Same stuff as in Parser, but only for one file'

  def __init__(self):
    self.titlephrases = []
    self.titlesmalls = []
    self.preambles = []
    self.entries = {}
    self.tobeparsed = []

  def parse(self, file, **kwargs):
    self.tobeparsed.append(file)

  def merge(self, db):
    db.titlephrases = db.titlephrases + self.titlephrases
    db.titlesmalls = db.titlesmalls + self.titlesmalls
    db.preambles = db.preambles + self.preambles
    db.entries.update(self.entries)
    for file in self.tobeparsed:
      db.parse(file, exts=['.xtx', '.bib'])


class Parser:
  'A structure of almost raw data from the databases.'

  def __init__(self, options, optparser):
    self.optparser = optparser
    self.options = options
    self.titlephrases = []
    self.titlesmalls = []
    self.preambles = []
    self.entries = {}
    self.seen = {}
    self.cur = []

  def parse(self, file, exts=['.aux', '.xtx', '.bib']):
    'Find a file with a reasonable extension and extract its information.'

    filepath, file = os.path.split(file)
    file, fileext = os.path.splitext(file)
    if fileext in exts:
      tryexts = [fileext]
    else:
      file += fileext
      tryexts = exts

    if file in self.seen:
      if 'file' in self.options.dump:
        print 'Already processed %s.' % file
      return self.seen[file]

    if os.path.isabs(filepath):
      trydirs = [filepath]
    else:
      trydirs = [os.path.join(dir, filepath) for dir in self.options.dir]
      if self.cur:
        trydirs.append(os.path.join(self.cur[-1], filepath))
      trydirs.reverse()

    for dir in trydirs:
      for ext in tryexts:
        try:
	  self.cur.append(dir)
	  path = os.path.join(dir, file + ext)
	  try:
	    stream = open(path, 'r')
	  except IOError:
	    continue

	  if ext == '.aux':
	    if 'file' in self.options.dump:
	      print 'Processing auxiliary file %s.' % path
	    self.parseaux(stream, path)
	    return path

	  self.seen[file] = path
	  cpath = os.path.join(dir, '.' + file + ext + '.cache')
	  try:
	    if os.path.getmtime(path) < os.path.getmtime(cpath):
	      cstream = open(cpath, 'rb')
	      if 'file' in self.options.dump:
		print "Processing database %s from cache." % path
	      try:
		db = pickle.load(cstream)
		cstream.close()
		db.merge(self)
		return path
	      except:
		if 'file' in self.options.dump:
		  print "Could not read cache %s, falling back to database." % cpath
	  except IOError:
	    pass
	  except OSError:
	    pass

	  if 'file' in self.options.dump:
	    print 'Processing database %s.' % path
	  db = self.parsextx(stream, path)
	  stream.close()
	  db.merge(self)

	  cpath = os.path.join(dir, '.' + file + ext + '.cache')
	  try:
	    cstream = open(cpath, 'wb')
	    try:
	      pickle.dump(db, cstream, protocol=2)
	    except:
	      if 'file' in self.options.dump:
		print "Could not write cache %s." % cpath
	    cstream.close()
	  except IOError:
	    pass

	  return path
        finally:
	  self.cur.pop()

    error(self.options, 'Can not find %s database.' % file)
    return file

  def parseaux(self, stream, path):
    'Parse and handle options set in a TeX .aux file.'

    for line in stream:
      if line.startswith(r'\citation'):
        for citation in line[10:].strip().rstrip('}').split(','):
          citation = citation.strip(',\t')
          if citation:
	    self.addopts(['--cite', citation])
      elif line.startswith(r'\bibstyle'):
        self.addopts(['--style'] + line[10:].rstrip().rstrip('}').split(' '))
      elif line.startswith(r'\bibdata'):
        self.files(line[9:].rstrip().rstrip('}').split(','), exts=['.bib', '.xtx'])
      elif line.startswith(r'\@input'):
        self.files(line[8:].rstrip().rstrip('}').split(','), exts=['.aux'])

  def parsextx(self, stream, path):
    'Parse and handle options set in a CrossTeX .xtx or .bib database file.'

    db = XTXFileInfo()
    db.options = self.options
    contents = stream.read()
    if contents:
      lexer = ply.lex.lex(reflags=re.UNICODE)
      lexer.path = path
      lexer.file = os.path.basename(path)
      lexer.lineno = 1
      lexer.expectstring = False

      lexer.db = db
      lexer.defaults = {}

      parser = ply.yacc.yacc(debug=0, write_tables=0)
      parser.parse(contents, lexer=lexer)
    return db

  def files(self, files, **kwargs):
    return [ self.parse(file, **kwargs) for file in files ]

  def addopts(self, opts):
    return self.optparser.parse_args(args=opts, values=self.options)


#
# Tokens
#

newlinere = re.compile(r'\r\n|\r|\n')
numberre = re.compile(r'^\d+$')
andre = re.compile(r'\s+and\s+')

tokens = ( 'AT', 'COMMA', 'SHARP', 'OPENBRACE', 'CLOSEBRACE', 'LBRACK',
  'RBRACK', 'EQUALS', 'ATINCLUDE', 'ATSTRING', 'ATEXTEND', 'ATPREAMBLE',
  'ATCOMMENT', 'ATDEFAULT', 'ATTITLEPHRASE', 'ATTITLESMALL', 'NAME', 'NUMBER',
  'STRING', )

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

def t_SHARP(t):
  r'\#'
  t.lexer.expectstring = True
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
  error(t.lexer.db.options, '%s:%d: Syntax error near "%s".' %
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
  t.lexer.db.preambles.append(t[3])

def p_stmt_titlephrase(t):
  'stmt : ATTITLEPHRASE STRING'
  t.lexer.db.titlephrases.append(t[2])

def p_stmt_titlesmall(t):
  'stmt : ATTITLESMALL STRING'
  t.lexer.db.titlesmalls.append(t[2])

def p_stmt_include(t):
  'stmt : ATINCLUDE NAME'
  t.lexer.db.parse(t[2], exts=['.xtx', '.bib'])

def p_stmt_default(t):
  'stmt : ATDEFAULT field'
  t.lexer.defaults = copy(t.lexer.defaults)
  if t[2][1]:
    t.lexer.defaults[t[2][0]] = t[2][1]
  else:
    try:
      del t.lexer.defaults[t[2][0]]
    except KeyError:
      pass

def p_stmt_string(t):
  'stmt : ATSTRING OPENBRACE fields CLOSEBRACE'
  file, line, defaults = t.lexer.file, t.lineno(2), t.lexer.defaults
  for key, value in t[3]:
    ent = Entry('string', [key], [([], [('name', value)])],
                file, line, defaults)
    t.lexer.db.entries.setdefault(key, []).append(ent)

def p_stmt_entry(t):
  'stmt : entry'
  for key in t[1].keys:
    t.lexer.db.entries.setdefault(key, []).append(t[1])

def p_entry(t):
  'entry : AT NAME OPENBRACE keys COMMA conditionals CLOSEBRACE'
  file, line, defaults = t.lexer.file, t.lineno(2), t.lexer.defaults
  t[0] = Entry(t[2].lower(), t[4], t[6], file, line, defaults)

def p_entry_extend(t):
  '''
  entry : ATEXTEND OPENBRACE keys COMMA conditionals CLOSEBRACE
        | ATEXTEND OPENBRACE keys CLOSEBRACE
  '''
  try:
    fields = t[5]
  except IndexError:
    fields = []
  file, line, defaults = t.lexer.file, t.lineno(1), t.lexer.defaults
  t[0] = Entry('extend', t[3], fields, file, line, defaults)

def p_keys_singleton(t):
  'keys : NAME'
  t[0] = [t[1]]

def p_keys_multiple(t):
  'keys : NAME EQUALS keys'
  t[0] = [t[1]] + t[3]

def p_conditionals_empty(t):
  'conditionals :'
  t[0] = []

def p_conditionals_singleton(t):
  'conditionals : conditional'
  t[0] = [t[1]]

def p_conditionals_multiple(t):
  'conditionals : conditional conditionals'
  t[0] = [t[1]] + t[2]

def p_conditionals_unconditional(t):
  'conditionals : fields conditionals'
  t[0] = [([], t[1])] + t[2]

def p_conditional(t):
  'conditional : LBRACK fields RBRACK fields'
  t[0] = (t[2], t[4])

def p_fields_empty(t):
  'fields :'
  t[0] = []

def p_fields_singleton(t):
  'fields : field'
  t[0] = [t[1]]

def p_fields(t):
  'fields : field COMMA fields'
  t[0] = [t[1]] + t[3]

def p_field(t):
  'field : NAME EQUALS value'
  t[0] = (t[1].lower(), t[3])

def p_value_singleton(t):
  'value : simplevalue'
  t[0] = t[1]

def p_value_concat(t):
  'value : value SHARP simplevalue'
  warning(t.lexer.db.options, '%s:%d: The implementation of concatenation is currently broken.' % 
        (t.lexer.file, t.lexer.lineno, t.value))
  t[0] = t[1]
  t[0].concat(t[3])

def p_simplevalue_name(t):
  'simplevalue : NAME'
  t[0] = Value(t.lexer.file, t.lineno(1), t[1], 'key')

def p_simplevalue_number(t):
  'simplevalue : NUMBER'
  t[0] = Value(t.lexer.file, t.lineno(1), t[1])

def p_simplevalue_string(t):
  'simplevalue : STRING'
  t[0] = Value(t.lexer.file, t.lineno(1), t[1])

def p_error(t):
  ply.yacc.errok()
  error(t.lexer.db.options, '%s:%d: Parse error near "%s".' %
	(t.lexer.file, t.lexer.lineno, t.value[:20]))

