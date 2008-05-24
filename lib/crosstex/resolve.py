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

import re
import math
import crosstex.objects

from copy import copy
from crosstex.parse import Key
from crosstex.options import warning, error


class Constraint(dict):
  'A convenience representation of a constrained citation.'

  def __init__(self, key):
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
          values = [str(values)]
      else:
        field = constraint[0]
        values = constraint[1].split('-')
      if not field:
        error(self.options, 'Empty field in constraint "%s".' % key)
      if not values:
        error(self.options, 'Empty values in constraint "%s".' % key)
      if field and values:
        self[field] = values

  def match(self, entry):
    for field, values in self.iteritems():
      try:
        actual = str(entry.fields[field]).lower()
      except KeyError:
        return False
      for value in values:
        if value not in actual:
          return False
    return True


class Database(list):
  'A structure of almost raw data from the databases.'

  def __init__(self, parser):
    self.titlephrases = parser.titlephrases
    self.titlesmalls = parser.titlesmalls
    self.preambles = parser.preambles
    self.entries = parser.entries
    self.options = parser.options
    self.resolved = {}

    all = not self.options.cite
    semantic = []
    for key in self.options.cite:
      if key == '*':
        all = True
      elif key.startswith('!'):
        semantic.append(key)
      else:
        entry = self._resolve(key)
        if entry is None:
          continue
        if not entry._citeable:
          error(self.options, '%s is not a citeable object.' % key)
        elif entry.citation is None:
          entry.citation = key
          self.append(entry)
        elif entry.citation != key:
          error(self.options,
                'Citations "%s" and "%s" refer to the same object.' %
                (entry.citation, key))

    entries = {}
    if all or semantic:
      for key in self.entries:
        entry = self._resolve(key)
        if entry is not None and entry._citeable:
          entries[entry] = True

    for key in semantic:
      constraint = Constraint(key)
      if not constraint:
        error(self.options, 'Empty constraint.')
        continue
      matches = [ entry for entry in entries if constraint.match(entry) ]
      if not matches:
        error(self.options, 'Constraint "%s" has no matches.' % key)
      else:
        if matches[0].citation is None:
          matches[0].citation = key
          self.append(matches[0])
        elif matches[0].citation != key:
          error(self.options,
                'Citations "%s" and "%s" refer to the same object.' %
                (matches[0].citation, key))
        if len(matches) > 1:
          error(self.options, 'Ambiguous constraint "%s" has %d matches:' %
                (key, len(matches)))
          error(self.options, '  accepted key %s.' % (matches[0].keys[0]))
          for match in matches[1:]:
            error(self.options, '  rejected key %s.' % (match.keys[0]))

    if all:
      for entry in entries:
        if entry.citation is None:
          entry.citation = entry.keys[0]
          self.append(entry)

    self._sort()

  def dump(self, kind):
    entries = {}
    kind = getattr(crosstex.objects, kind)
    for key in self.entries:
      entry = self._resolve(key)
      if entry is not None and isinstance(entry, kind):
        entries[str(entry)] = True
    return entries.keys()

  def write(self, out, entries=None, headings=None):
    'Print the formatted database to the stream out.'

    if entries is None:
      entries = self
    if headings is None:
      headings = self.options.heading
    if (self.options.convert == 'html' or self.options.convert == 'bbl') and len(headings) > 1:
      error(self.options, 'The output format does not support multiple heading levels.')
      headings = headings[:1]

    if not headings:
      if self.options.convert == 'html' or self.options.convert == 'bbl':
        max = ''
        for entry in entries:
          label = entry._format('label')
          label = label.replace('{\\etalchar{+}}', 'X')
          if len(label) > len(max):
            max = label
        if not max:
          max = '0' * int(math.ceil(math.log(len(entries) + 1, 10)))
        out.write("\\begin{thebibliography}{%s}\n" % max)
      for entry in entries:
        out.write(str(entry))
      if self.options.convert == 'html' or self.options.convert == 'bbl':
        out.write("\\end{thebibliography}\n")
      return

    heading = headings[0][1]
    cats = {}
    for entry in entries:
      cats.setdefault(entry.fields.get(heading, ''), []).append(entry)

    values = [k for k in cats.keys() if k != '']
    values.sort()
    if headings[0][0]:
      values.reverse()
    if '' in cats:
      values.insert(0, '')

    for value in values:
      if (self.options.convert == 'html' or self.options.convert == 'bbl') and value != '':
        out.write("{\\renewcommand{\\refname}{%s}\n" % value)
      elif self.options.convert == 'xtx':
        default = crosstex.style.common._fieldval(heading, value)
        out.write('@default %s \n\n' % default)
      self.write(out, cats[value], headings[1:])
      if (self.options.convert == 'html' or self.options.convert == 'bbl') and value != '':
        out.write("}\n")

  def _sort(self):
    citations = self
    for reverse, field in self.options.sort:
      def keyfunc(x):
        value = x._format('sort', field)
        if value is None:
          return x._format('sort', 'key')
        try:
          return int(value)
        except ValueError:
          return value
      if reverse:
        sortlist = [ (keyfunc(x), len(citations) - i, x) for i, x in enumerate(citations) ]
        sortlist.sort()
        sortlist.reverse()
      else:
        sortlist = [ (keyfunc(x), i, x) for i, x in enumerate(citations) ]
        sortlist.sort()
      citations = [ x[-1] for x in sortlist ]
    self[:] = citations

  def _get(self, key):
    '''
    Resolve a key to a single entry and all its aliases and extensions.

    This involves looking up each entry and extension of that key,
    following out through aliases.  Complain if this process reveals
    two objects aliased to each other (note that this can happen through
    multiple levels of extensions, and need not be immediately obvious).
    '''

    keys = {}
    seen = {}
    work = {key: True}
    base = None
    extensions = []
    while work:
      key, value = work.popitem()
      keys[key] = True
      for entry in self.entries.get(key, []):
        if entry in seen:
          continue
        seen[entry] = True
        if entry.kind == 'extend':
          extensions.append(entry)
        elif base is None:
          base = entry
        else:
          error(self.options, '%s:%d: Alias %s is also defined at %s:%d.' %
                (base.file, base.line, key, entry.file, entry.line))
          continue
        newwork = [k for k in entry.keys if k not in keys]
        work.update(dict.fromkeys(newwork, True))

    if base is None:
      if extensions:
        error(self.options, '%s is extended but never defined.' % key)
      else:
        error(self.options, '%s is never defined.' % key)
    return (keys.keys(), base, extensions)

  def _resolve(self, key, seen=None):
    '''
    Resolve the entry referenced by the given key.

    Evaluate conditional fields, inheritance, @extend entries, etc. until
    the entry is stable, and return the result.  The resolved entry is
    also memoized, so it is efficient to call this twice on one key or
    aliased keys.
    '''

    # Return memoized results.
    try:
      return self.resolved[key]
    except KeyError:
      pass

    # Find all entries relevant to the given key while guarding against
    # inheritance loops.
    keys, base, extensions = self._get(key)
    if base is None or not keys:
      return None
    if seen is None:
      seen = {}
    elif base in seen:
      error(self.options, '%s inherits itself recursively.' % key)
      return None
    seen[base] = True

    # Get the class corresponding to this object type.
    try:
      kind = getattr(crosstex.objects, base.kind)
    except AttributeError:
      error(self.options, '%s:%d: There is no such thing as a @%s.\n' %
            (base.file, base.line, base.kind))
      return None
    if not (isinstance(kind, type) and issubclass(kind, crosstex.objects.Object)):
      error(self.options, '%s:%d: There is no such thing as a @%s.\n' %
            (base.file, base.line, base.kind))
      return None

    # Resolve fields.  Put in conditions a list of lists of conditionals,
    # each from an entry.  Now is when to complain about duplicated
    # fields. Note that the conditions for each entry are flatly
    # concatenated into the whole list, in order of preference (extensions
    # first, then the base entry, then finally inherited objects in the
    # order in which they are assigned).
    conditions = []
    for entry in extensions + [base]:
      for condition, assignments in entry.fields:
        fieldsdict = {}
        for field, value in assignments:
          field = field.lower()
          if field in fieldsdict:
            warning(self.options, '%s:%d: %s field is duplicated.' %
                    (entry.file, entry.line, field))
          else:
            fieldsdict[field] = value

        # Inherit fields, e.g. longname from name.
        for field in kind._fillin:
          if field in fieldsdict:
            continue
          for fill in kind._fillin[field]:
            if fill in fieldsdict:
              fieldsdict[field] = fieldsdict[fill]
              break

        conditiondict = {}
        for field, value in condition:
          field = field.lower()
          if field in conditiondict:
            warning(self.options, '%s:%d: Conditional %s field is duplicated.' %
                    (entry.file, entry.line, field))
          else:
            conditiondict[field] = value
        conditions.append((conditiondict, fieldsdict, entry))

    # Do the resolution, adding inherited entries as they are assigned.
    # When the fields stabilize, add in the defaults as a last resort and
    # continue until the fields are re-stabilized.
    defaulted = False
    inherited = {}
    fields = {}
    i = 0
    while i < len(conditions):
      condition, assignments, source = conditions[i]
      for field, value in condition.iteritems():
        try:
          if fields[field] != value:
            del conditions[i]
            break
        except KeyError:
          i += 1
          break
      else:
        del conditions[i]
        for field, value in assignments.iteritems():

          # Do not assign to fields that do not exist.
          if field not in kind._allowed:
            if source is base:
              # Complain iff they were set directly, e.g. not inherited.
              warning(self.options, '%s:%d: No such field %s in %s.' %
                      (base.file, base.line, field, base.kind))
            continue

          if field not in fields:
            i = 0
            if isinstance(value, Key):
              entry = self._resolve(value, seen)
              if entry is None:
                error(self.options, '%s:%d: No such key "%s".' %
                      (source.file, source.line, value))
                value = str(value)
              else:
                inherited[value] = True
                conditions.append(({}, entry.fields, entry))
                conditions.extend(entry.conditions)
                value = entry
            else:
              value = str(value)
              if field in ['author', 'editor']:
                authors = crosstex.objects.ObjectList()
                oldcheck = self.options.check
                self.options.check = 5 # Ignore everything
                for part in re.split('\s+and\s+', value): # XXX split on word boundaries properly
                  entry = self._resolve(part, seen)
                  if entry is None:
                    authors.append(part)
                  else:
                    inherited[part] = True
                    conditions.append(({}, entry.fields, entry))
                    conditions.extend(entry.conditions)
                    authors.append(entry)
                self.options.check = oldcheck
                value = authors
            fields[field] = value
      if i >= len(conditions) and not defaulted:
        defaulted = True
        i = 0
        conditions.append(({}, base.defaults, copy(base)))

    # Ensure required fields are all provided.
    for field in kind._required:
      if field not in fields:
        error(self.options, '%s:%d: Missing required field %s in %s.' %
              (base.file, base.line, field, base.kind))

    # Memoize the result and return it.
    ent = kind(keys, fields, conditions, base.file, base.line)
    for key in keys:
      self.resolved[key] = ent

    return ent
