from crosstex.objects import *

_wordre = re.compile('(-+|\s+|\\\w+|\\\W+|\$[^\$]*\$|[{}])', re.IGNORECASE)
_spacere = re.compile(r'^\s*$')
_specialre = re.compile(r'^(\\.*|\$[^\$]*\$)$')
_punctuationre = re.compile('([:!.?]|-{2,})[\'}\n]*$')
_linkre = re.compile("[a-zA-Z][-+.a-zA-Z0-9]*://([:/?#[\]@!$&'()*+,;=a-zA-Z0-9_\-.~]|%[0-9a-fA-F][0-9a-fA-F]|\\-|\s)*")
_linksub = re.compile('\\-\s')
_protectre = re.compile(r'[\\{}]')
_endre = re.compile(r"(\\end\{[^}]*\}|['\s}])*$")

_bibtexkinds = ['article', 'book', 'booklet', 'conference', 'inbook', \
  'incollection', 'inproceedings', 'manual', 'mastersthesis', 'phdthesis', \
  'proceedings', 'techreport', 'unpublished']

# Clean up a string to be a search for the literal
def _sanitize(r):
  value = ''
  for char in r:
    if char == '^':
      value += r'\^'
    else:
      value += '[' + char + ']'
  return value

# Piece an entry together.
def _punctuate(string, punctuation='', tail=' '):
  if string == None:
    string = ''
  i = _endre.search(string).start()
  end = string[i:]
  string = string[:i]
  if string and not (string.endswith('?') or string.endswith('!') or string.endswith(':') or string.endswith('--') or string.endswith(punctuation)):
    string += punctuation
  if string or end:
    end += tail
  return string + end

def _names(name, short=False, plain=False):
  value = ''
  lastchar = ' '
  names = []
  nesting = 0
  if isinstance(name, Formatter):
    name = name._format('value') or ''
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

def _last_initials(name, size):
  (fnames, mnames, lnames, snames) = _names(name)
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

def _fieldval(field, value):
  if isinstance(value, Object):
    return '%s = %s' % (field, value.citation)
  else:
    value = str(value)
    try:
      return '%s = %d' % (field, int(value))
    except:
      if '{' in value or '}' in value:
        return '%s = {%s}' % (field, value)
      else:
        return '%s = "%s"' % (field, value)

def makegetterproducer(field):
  def getterproducer(obj, value, context):
    return obj._format(*(context + (field,)))
  return getterproducer

def makejoinproducer(punctuation, space, final, finalspace, *fields):
  def joinproducer(obj, value, context):
    value = ''
    for field in fields:
      fieldvalue = obj._format(*(context + (field,)))
      if fieldvalue:
        value = _punctuate(value, punctuation, space) + fieldvalue
    return _punctuate(value, final, finalspace)
  return joinproducer

def bibtexproducer(obj, value, context):
  kind = obj.kind
  if kind not in _bibtexkinds:
    kind = 'misc'
  value = '@%s{%s' % (kind, obj.citation)
  for field in obj.fields:
    fieldvalue = obj._format(*(context + (field,)))
    if fieldvalue:
      value += ',\n\t' + _fieldval(field, fieldvalue)
  value += '}\n\n'
  return value

def crosstexproducer(obj, value, context):
  if not obj.keys:
    return ''
  value = '@%s{%s' % (obj.kind, ' = '.join(obj.keys))
  for field in obj.fields:
    value += ',\n\t' + _fieldval(field, obj.fields[field])
  value += '}\n\n'
  return value

def makelinksproducer(fields):
  def linksproducer(obj, value, context):
    links = ''
    for field in fields:
      myfield = field.lower()
      fieldvalue = obj._format(*(context + (myfield,)))
      if fieldvalue:
        for m in _linkre.finditer(str(fieldvalue)):
          uri = m.group()
          _linksub.sub(uri, '')
          links = _punctuate(links) + '\\href{%s}{\\small\\textsc{%s}}' % (uri, field)
    return links
  return linksproducer

def extrasproducer(obj, value, context):
  extras = ''
  abstractvalue = obj._format(*(context + ('abstract',)))
  keywordsvalue = obj._format(*(context + ('keywords',)))
  if abstractvalue:
    extras = _punctuate(extras, '\n', tail='') + '\\noindent\\begin{small}%s\\end{small}' % abstractvalue
  if keywordsvalue:
    extras = _punctuate(extras, '\n\n', tail='') + '\\noindent\\begin{small}\\textsc{Keywords:} %s\\end{small}' % keywordsvalue
  if extras:
    extras = '\\begin{quotation}' + extras + '\\end{quotation}'
  return extras

def authoryearproducer(obj, value, context):
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

def longauthoryearproducer(obj, value, context):
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

def authoreditorproducer(obj, value, context):
  authorvalue = obj._format(*(context + ('author',)))
  if authorvalue == None:
    authorvalue = obj._format(*(context + ('editor',)))
    if authorvalue == None:
      return None
    if ' and ' in authorvalue:
      authorvalue = str(authorvalue) + ', eds.'
    else:
      authorvalue = str(authorvalue) + ', ed.'
  else:
    authorvalue = str(authorvalue)
  return authorvalue

def dateproducer(obj, value, context):
  value = ''
  monthvalue = obj._format(*(context + ('month',)))
  if monthvalue:
    value = _punctuate(value, ',') + str(monthvalue)
  yearvalue = obj._format(*(context + ('year',)))
  if yearvalue:
    value = _punctuate(value, ',') + str(yearvalue)
  return value

def fullpublicationproducer(obj, value, context):
  value = obj._format(*(context + ('publication',)))
  booktitlevalue = obj._format(*(context + ('booktitle',)))
  journalvalue = obj._format(*(context + ('journal',)))
  if booktitlevalue:
    value = _punctuate(value, '.') + str(booktitlevalue)
    volumevalue = obj._format(*(context + ('volume',)))
    if volumevalue:
      value += ', volume %s' % volumevalue
      seriesvalue = obj._format(*(context + ('series',)))
      if seriesvalue :
        value += ' of \\emph{%s}' % seriesvalue
    chaptervalue = obj._format(*(context + ('chapter',)))
    if chaptervalue:
      value += ', chapter %s' % chaptervalue
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
      value += '(%s)' % numbervalue
    if pagesvalue:
      if volumevalue or numbervalue:
        value += ':%s' % pagesvalue
      elif pagesvalue :
        value += 'page %s' % pagesvalue
      else:
        try:
	  pagenum = int(pagesvalue)
	  value += 'page %d' % pagenum
	except ValueError:
	  value += 'pages %s' % pagesvalue
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
      try:
	pagenum = int(pagesvalue)
	value = _punctuate(value, ',') + ('page %d' % pagenum)
      except ValueError:
        value = _punctuate(value, ',') + ('pages %s' % pagesvalue)
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
  notevalue = obj._format(*(context + ('note',)))
  if notevalue:
    value = _punctuate(value, ',') + str(notevalue)
  yearvalue = obj._format(*(context + ('year',)))
  if yearvalue:
    value = _punctuate(value, ',')
    monthvalue = obj._format(*(context + ('month',)))
    if monthvalue:
      value = _punctuate(value + str(monthvalue))
    value += str(yearvalue)
  return value

def acmfullpublicationproducer(obj, value, context):
  value = obj._format(*(context + ('publication',)))
  booktitlevalue = obj._format(*(context + ('booktitle',)))
  journalvalue = obj._format(*(context + ('journal',)))
  if booktitlevalue:
    value = _punctuate(value, '.') + str(booktitlevalue)
    volumevalue = obj._format(*(context + ('volume',)))
    if volumevalue:
      value += ', vol. %s' % volumevalue
      seriesvalue = obj._format(*(context + ('series',)))
      if seriesvalue :
        value += ' of \\emph{%s}' % seriesvalue
    chaptervalue = obj._format(*(context + ('chapter',)))
    if chaptervalue:
      value += ', chap. %s' % chaptervalue
  elif journalvalue:
    value = _punctuate(value, ',') + str(journalvalue)
    volumevalue = obj._format(*(context + ('volume',)))
    if volumevalue:
      value = _punctuate(value) + '\\emph{%s}' % str(volumevalue)
    numbervalue = obj._format(*(context + ('number',)))
    if numbervalue:
      value = _punctuate(value, ',') + str(numbervalue)

  addryearvalue = ''
  addressvalue = obj._format(*(context + ('address',)))
  if addressvalue:
    addryearvalue = _punctuate(addryearvalue, ',') + str(addressvalue)
  datevalue = ''
  monthvalue = obj._format(*(context + ('month',)))
  if monthvalue:
    datevalue = _punctuate(datevalue) + str(monthvalue)
  yearvalue = obj._format(*(context + ('year',)))
  if yearvalue:
    datevalue = _punctuate(datevalue) + str(yearvalue)
  if datevalue:
    addryearvalue = _punctuate(addryearvalue, ',') + str(datevalue)
  if addryearvalue:
    value = _punctuate(value) + '(%s)' % addryearvalue

  institutionvalue = obj._format(*(context + ('institution',)))
  if institutionvalue:
    value = _punctuate(value, ',') + str(institutionvalue)
  schoolvalue = obj._format(*(context + ('school',)))
  if schoolvalue:
    value = _punctuate(value, ',') + str(schoolvalue)

  publishervalue = obj._format(*(context + ('publisher',)))
  if publishervalue:
    value = _punctuate(value, ',') + str(publishervalue)

  authorvalue = obj._format(*(context + ('author',)))
  editorvalue = obj._format(*(context + ('editor',)))
  if authorvalue and editorvalue:
    value = _punctuate(value, ',') + str(editorvalue)

  pagesvalue = obj._format(*(context + ('pages',)))
  if pagesvalue:
    if not journalvalue:
      try:
	pagenum = int(pagesvalue)
	pagesvalue = 'p. ' + pagenum
      except ValueError:
        pagesvalue = 'pp. ' + pagesvalue
    value = _punctuate(value, ',') + str(pagesvalue)
  notevalue = obj._format(*(context + ('note',)))
  if notevalue:
    value = _punctuate(value, ',') + str(notevalue)
  return value

def accessedproducer(obj, value, context):
  urlvalue = str(obj._format(*(context + ('url',))))
  dayvalue = obj._format(*(context + ('accessday',)))
  yearvalue = obj._format(*(context + ('accessyear',)))
  monthvalue = obj._format(*(context + ('accessmonth',)))
  if yearvalue or monthvalue:
    urlvalue = _punctuate(urlvalue, ',') + 'Accessed'
  if monthvalue:
    urlvalue = _punctuate(urlvalue) + monthvalue
    if dayvalue:
      urlvalue = _punctuate(urlvalue) + dayvalue
    if yearvalue:
      urlvalue = _punctuate(urlvalue, ',') + yearvalue
  elif yearvalue:
    urlvalue = _punctuate(urlvalue) + yearvalue
  return urlvalue

def citystatecountryproducer(obj, value, context):
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

def thesistypeproducer(obj, value, context):
  typevalue = obj._format(*(context + ('type',)))
  if typevalue:
    return str(typevalue)
  typevalue = obj._format(*(context + ('thesistype',)))
  if typevalue:
    return _punctuate(typevalue) + 'Thesis'
  return None

def emptyproducer(obj, value, context):
  return ''

def lastfirstfilter(obj, objvalue, context):
  (fnames, mnames, lnames, snames) = _names(objvalue)
  namestr = ''
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
  namestr = ''
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
    objvalue = copy(objvalue)
    objvalue[0] = lastfirstfilter(obj, objvalue[0], context)
  return objvalue

def alllastfirstlistfilter(obj, objvalue, context):
  if objvalue:
    objvalue = copy(objvalue)
    for i in range(len(objvalue)):
      objvalue[i] = lastfirstfilter(obj, objvalue[i], context)
  return objvalue

def alllastlistfilter(obj, objvalue, context):
  if objvalue:
    objvalue = copy(objvalue)
    for i in range(len(objvalue)):
      (fnames, mnames, lnames, snames) = _names(objvalue[i])
      objvalue[i] = ''
      for n in lnames:
        objvalue[i] = _punctuate(objvalue[i]) + n
  return objvalue

def plainlistformatter(obj, objvalue, context):
  value = ''
  for i in range(len(objvalue)):
    value = _punctuate(value, ',') + str(objvalue[i])
  return value

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
  return ' and '.join([isinstance(element, Object) and element._primarykey or str(element) for element in objvalue])

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
    value += '{\etalchar{+}}'
  return value

def fullnameslistformatter(obj, objvalue, context):
  value = ''
  if len(objvalue) == 2:
    (fnames1, mnames1, lnames1, snames1) = _names(objvalue[0])
    (fnames2, mnames2, lnames2, snames2) = _names(objvalue[1])
    value = ' '.join(mnames1 + lnames1) + ' \& ' + ' '.join(mnames2 + lnames2)
  elif objvalue:
    (fnames1, mnames1, lnames1, snames1) = _names(objvalue[0])
    value = ' '.join(mnames1 + lnames1)
    if len(objvalue) > 2:
      value += ' et al.'
  return value

def makebracketfilter(left, right):
  def bracketfilter(obj, objvalue, context):
    if objvalue:
      return '%s%s%s' % (left, objvalue.strip(), right)
    return objvalue
  return bracketfilter

def makesuffixfilter(suffix):
  def suffixfilter(obj, objvalue, context):
    if objvalue:
      return '%s%s' % (objvalue.strip(), suffix)
    return objvalue
  return suffixfilter

def edfilter(obj, objvalue, context):
  if objvalue:
    if ' and ' in objvalue:
      objvalue = objvalue + ', eds.'
    else:
      objvalue = objvalue + ', ed.'
  return objvalue

def makeprefixfilter(prefix):
  def prefixfilter(obj, objvalue, context):
    if objvalue:
      return '%s%s' % (prefix, objvalue.strip())
    return objvalue
  return prefixfilter

def bibitemfilter(obj, objvalue, context):
  if objvalue:
    label = obj._format(*(context + ('label',)))
    if label:
      label = '[%s]' % label
    return '\\bibitem%s{%s}\n%s\n\n' % (label, obj.citation, objvalue.strip())
  return objvalue

def emptyfilter(obj, objvalue, context):
  return ''

def makeuniquefilter():
  used = []
  def uniquefilter(obj, objvalue, context):
    if objvalue != '':
      if objvalue in used:
        for char in list('abcdefghijklmnopqrstuvwxyz'):
          if objvalue + char not in used:
            objvalue += char
            break
        else:
          raise ValueError, 'too many citations with key %s' % objvalue
      used.append(objvalue)
    return objvalue
  return uniquefilter

def twodigitfilter(obj, objvalue, context):
  return objvalue[-2:]

infilter = makeprefixfilter('In ')
procfilter = makeprefixfilter('Proc. of ')
proceedingsfilter = makeprefixfilter('Proceedings of the ')
emphfilter = makebracketfilter('\\emph{', '}')
boldfilter = makebracketfilter('\\textbf{', '}')
scfilter = makebracketfilter('\\textsc{', '}')
bracesfilter = makebracketfilter('{', '}')
quotefilter = makebracketfilter("``", "''")

def conferencetrackfilter(obj, objvalue, context):
  value = obj._format(*(context + ('conference',)))
  value = _punctuate(value, ',') + objvalue
  return value

def killfilter(obj, objvalue, context):
  if context[-1] in obj._required:
    return objvalue
  else:
    return ''

def titlecasefilter(obj, objvalue, context):
  newtitle = ''
  dollars = 0
  dashlen = 0
  inmath = False
  inliteral = False
  incommand = False
  wordbreak = True
  sentencebreak = True
  for i, char in enumerate(objvalue):
    if char == '{':
      close = _protectre.search(objvalue[i+1:])
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
      if wordbreak:
	newtitle += char.upper()
      else:
	newtitle += char.lower()
    else:
      newtitle += char

    sentencebreak = (not inliteral and not inmath and not incommand and (char in '!?:.' or dashlen > 1)) or (sentencebreak and (char.isspace() or incommand or inmath or char == '{'))
    wordbreak = sentencebreak or (not inliteral and not inmath and not incommand and (char.isspace() or char in ',-')) or (wordbreak and (incommand or inmath or char == '{'))

    if not char.isalnum() and char not in '_\\':
      incommand = False
  return newtitle

def lowertitlecasefilter(obj, objvalue, context):
  newtitle = ''
  dollars = 0
  dashlen = 0
  inmath = False
  inliteral = False
  incommand = False
  sentencebreak = True
  for i, char in enumerate(objvalue):
    if char == '{':
      close = _protectre.search(objvalue[i+1:])
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
      if sentencebreak:
	newtitle += char.upper()
      else:
	newtitle += char.lower()
    else:
      newtitle += char

    sentencebreak = (not inliteral and not inmath and not incommand and (char in '!?:.' or dashlen > 1)) or (sentencebreak and (char.isspace() or incommand or inmath or char == '{'))

    if not char.isalnum() and char not in '_\\':
      incommand = False
  return newtitle

def uppercasefilter(obj, objvalue, context):
  newtitle = ''
  dollars = 0
  dashlen = 0
  inmath = False
  inliteral = False
  incommand = False
  for i, char in enumerate(objvalue):
    if char == '{':
      close = _protectre.search(objvalue[i+1:])
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

def maketitlephrasefilter(titlephrases):
  def titlephrasefilter(obj, objvalue, context):
    newtitle = ''
    ignoreuntil = 0
    dollars = 0
    dashlen = 0
    inmath = False
    inliteral = False
    incommand = False
    wordbreak = True
    sentencebreak = True
    for i, char in enumerate(objvalue):
      if char == '{':
	close = _protectre.search(objvalue[i+1:])
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
	    if objvalue.lower().startswith(phrase.lower(), i) and len(phrase) > len(match) and (i + len(phrase) >= len(objvalue) - 1 or not objvalue[i + len(phrase)].isalnum()):
	      match = phrase
	  if len(match) > 0:
	    ignoreuntil = i + len(match)
	    newtitle += match
	  else:
	    newtitle += char
        else:
	  newtitle += char

      sentencebreak = (not inliteral and not inmath and not incommand and (char in '!?:.' or dashlen > 1)) or (sentencebreak and (char.isspace() or incommand or inmath or char == '{'))
      wordbreak = sentencebreak or (not inliteral and not inmath and not incommand and (char.isspace() or char in ',-')) or (wordbreak and (incommand or inmath or char == '{'))

      if not char.isalnum() and char not in '_\\':
	incommand = False
    return newtitle
  return titlephrasefilter

def makelowerphrasefilter(lowerphrases):
  def lowerphrasefilter(obj, objvalue, context):
    newtitle = ''
    ignoreuntil = 0
    dollars = 0
    dashlen = 0
    inmath = False
    inliteral = False
    incommand = False
    wordbreak = True
    sentencebreak = True
    for i, char in enumerate(objvalue):
      if char == '{':
	close = _protectre.search(objvalue[i+1:])
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
	    if objvalue.lower().startswith(phrase.lower(), i) and len(phrase) > len(match) and (i + len(phrase) >= len(objvalue) - 1 or not objvalue[i + len(phrase)].isalnum()):
	      match = phrase.lower()
	  if len(match) > 0:
	    ignoreuntil = i + len(match)
	    newtitle += match
	  else:
	    newtitle += char
        else:
	  newtitle += char
	    
      sentencebreak = (not inliteral and not inmath and not incommand and (char in '!?:.' or dashlen > 1)) or (sentencebreak and (char.isspace() or incommand or inmath or char == '{'))
      wordbreak = sentencebreak or (not inliteral and not inmath and not incommand and (char.isspace() or char in ',-')) or (wordbreak and (incommand or inmath or char == '{'))

      if not char.isalnum() and char not in '_\\':
	incommand = False
    return newtitle
  return lowerphrasefilter

def listproducer(obj, value, context):
  if isinstance(obj, list):
    return list(obj)
  else:
    return None

ObjectList._addproducer(listproducer, 'value')
Object._addlistfilter(alllastfirstlistfilter, 'sort', 'author')
Object._addfilter(titlecasefilter, 'sort', 'author')
