from crosstex.objects import *

# Standard producers for top-level objects.
misc._addproducer(authortitlepublicationproducer, 'value')
location._addproducer(citystatecountryproducer, 'value')
entrylist._addlistformatter(commalistformatter, 'value')

# Long labels.
misc._addproducer(longauthoryearproducer, 'fullnamelabel') # Default to author and year, separated by space.
misc._addfilter(makeuniquefilter(), 'fullnamelabel') # Ensure unique labels by appending letters.
misc._addproducer(makegetterproducer('editor'), 'fullnamelabel', 'author') # Fall back to editor if there are no authors.
misc._addlistformatter(fullnameslistformatter, 'fullnamelabel', 'author') # Format authors as last names.

# Alphabetic labels.
misc._addproducer(authoryearproducer, 'initialslabel') # Default to author and year with no space between.
misc._addfilter(makeuniquefilter(), 'initialslabel') # Ensure unique labels by appending letters.
misc._addproducer(makegetterproducer('editor'), 'initialslabel', 'author') # Fall back to editor if there are no authors.
misc._addlistformatter(initialslistformatter, 'initialslabel', 'author') # Format authors as a concatenation of last initials.
misc._addfilter(twodigitfilter, 'initialslabel', 'year') # Format year with only two least-significant digits.

# By default, use key as label if provided.
misc._addproducer(makegetterproducer('key'), 'label')

# The virtual fullauthor field contains the list of authors (or editors, with no authors).
misc._addproducer(authoreditorproducer, 'fullauthor')
misc._addfilter(bracesfilter, 'fullauthor')
misc._addfilter(dotfilter, 'fullauthor')

# The virtual fulltitle field contains the title.
misc._addproducer(makegetterproducer('title'), 'fulltitle')
misc._addfilter(bracesfilter, 'fulltitle')
misc._addfilter(dotfilter, 'fulltitle')

# The virtual fullpublication field collects the rest of the relevant information.
misc._addproducer(fullpublicationproducer, 'fullpublication')
misc._addfilter(bracesfilter, 'fullpublication')
misc._addfilter(dotfilter, 'fullpublication')
misc._addfilter(edfilter, 'fullpublication', 'editor') # Editors are denoted with 'ed.'

# Preface conference tracks and workshops with the name of the conference.
conferencetrack._addfilter(conferencetrackfilter, 'value')

# Specialized publication information.
misc._addproducer(makegetterproducer('howpublished'), 'publication')
url._addproducer(accessedproducer, 'publication')
thesis._addproducer(thesistypeproducer, 'publication')

# Specialized type information.
patent._addproducer('United States Patent', 'numbertype')
techreport._addproducer('Technical Report', 'numbertype')
rfc._addproducer('IETF Request for Comments', 'numbertype')
mastersthesis._addproducer("Master's", 'thesistype')
phdthesis._addfilter('Ph.D.', 'thesistype')
