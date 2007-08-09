from crosstex.objects import *

# Standard producers for top-level objects.
publication._addproducer(makejoinproducer(".", "\n\\newblock ", ".", "", 'fullauthor', 'fulltitlepublicationextras'), 'value')
location._addproducer(citystatecountryproducer, 'value')
entrylist._addlistformatter(commalistformatter, 'value')

# Long labels.
publication._addproducer(longauthoryearproducer, 'fullnamelabel') # Default to author and year, separated by space.
publication._addfilter(makeuniquefilter(), 'fullnamelabel') # Ensure unique labels by appending letters.
publication._addproducer(makegetterproducer('editor'), 'fullnamelabel', 'author') # Fall back to editor if there are no authors.
publication._addlistformatter(fullnameslistformatter, 'fullnamelabel', 'author') # Format authors as last names.

# Alphabetic labels.
publication._addproducer(authoryearproducer, 'initialslabel') # Default to author and year with no space between.
publication._addfilter(makeuniquefilter(), 'initialslabel') # Ensure unique labels by appending letters.
publication._addproducer(makegetterproducer('editor'), 'initialslabel', 'author') # Fall back to editor if there are no authors.
publication._addlistformatter(initialslistformatter, 'initialslabel', 'author') # Format authors as a concatenation of last initials.
publication._addfilter(twodigitfilter, 'initialslabel', 'year') # Format year with only two least-significant digits.

# By default, use key as label if provided.
publication._addproducer(makegetterproducer('key'), 'label')

# The virtual fullauthor field contains the list of authors (or editors, with no authors).
publication._addproducer(authoreditorproducer, 'fullauthor')

# The virtual fulltitle field contains the title.
publication._addproducer(makegetterproducer('title'), 'fulltitle')

# The virtual fullpublication field collects the rest of the relevant information.
publication._addproducer(fullpublicationproducer, 'fullpublication')
publication._addfilter(edfilter, 'fullpublication', 'editor') # Editors are denoted with 'ed.'

# The virtual fullextras field collects the miscellanous extra information.
publication._addproducer(makejoinproducer(".", " ", ".", "", 'links', 'extras'), 'fullextras')

# The following are various combinations of useful fields.
publication._addproducer(makejoinproducer(".", "\n\\newblock ", "", "", 'fullauthor', 'fulltitle'), 'fullauthortitle')
publication._addproducer(makejoinproducer(".", "\n\\newblock ", "", "", 'fulltitle', 'fullpublication'), 'fulltitlepublication')
publication._addproducer(makejoinproducer(".", "\n\\newblock ", "", "", 'fullpublication', 'fullextras'), 'fullpublicationextras')
publication._addproducer(makejoinproducer(".", "\n\\newblock ", "", "", 'fulltitle', 'fullpublication', 'fullextras'), 'fulltitlepublicationextras')
publication._addproducer(makejoinproducer(".", "\n\\newblock ", "", "", 'fullauthor', 'fullpublication', 'fullextras'), 'fullauthorpublicationextras')
publication._addproducer(makejoinproducer(".", "\n\\newblock ", "", "", 'fullauthor', 'fulltitle', 'fullpublication'), 'fullauthortitlepublication')

# Preface conference tracks and workshops with the name of the conference.
conferencetrack._addfilter(conferencetrackfilter, 'value')

# Specialized publication information.
publication._addproducer(makegetterproducer('howpublished'), 'publication')
url._addproducer(accessedproducer, 'publication')
thesis._addproducer(thesistypeproducer, 'publication')

# Specialized type information.
patent._addproducer('United States Patent', 'numbertype')
techreport._addproducer('Technical Report', 'numbertype')
rfc._addproducer('IETF Request for Comments', 'numbertype')
mastersthesis._addproducer("Master's", 'thesistype')
phdthesis._addproducer('Ph.D.', 'thesistype')

# Wrap publications in \bibitem entries.
publication._addfilter(bibitemfilter, 'value')

# The note field appears at the end of misc objects.
misc._addproducer(makejoinproducer(".", " ", ".", "", 'note', 'links', 'extras'), 'fullextras')
misc._addfilter(killfilter, 'fullpublication', 'note')
