from crosstex.style.basic import *

# Use ACM publication syntax.
publication._addproducer(acmfullpublicationproducer, 'fullpublication')

# Prefer long names.
string._addproducer(makegetterproducer('shortname'), 'value')
string._addproducer(makegetterproducer('longname'), 'value')

# Use 'In' and emphasize book and journal titles.
publication._addfilter(emphfilter, 'fullpublication', 'booktitle')
publication._addfilter(emphfilter, 'fullpublication', 'journal')
publication._addfilter(infilter, 'fullpublication', 'booktitle')

# Use first initials and small caps for authors.
publication._addlistfilter(shortnameslistfilter, 'fullauthor', 'author')
publication._addlistfilter(alllastfirstlistfilter, 'fullauthor', 'author')
publication._addfilter(scfilter, 'fullauthor', 'author')
publication._addlistfilter(shortnameslistfilter, 'fullauthor', 'editor')
publication._addlistfilter(alllastfirstlistfilter, 'fullauthor', 'editor')
publication._addfilter(scfilter, 'fullauthor', 'editor')

# Sort on last names only.
publication._addlistfilter(alllastlistfilter, 'sort', 'author')
publication._addlistfilter(alllastlistfilter, 'sort', 'editor')
publication._addlistformatter(plainlistformatter, 'sort', 'author')
publication._addlistformatter(plainlistformatter, 'sort', 'editor')

# Use numeric labels.
publication._addproducer(emptyproducer, 'label')
