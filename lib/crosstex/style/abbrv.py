from crosstex.style.basic import *

# Prefer long names, except for journals and conferences.
string._addproducer(makegetterproducer('shortname'), 'value')
string._addproducer(makegetterproducer('longname'), 'value')
journal._addproducer(makegetterproducer('shortname'), 'value')
conference._addproducer(makegetterproducer('shortname'), 'value')

# Use first initials for authors.
misc._addlistfilter(shortnameslistfilter, 'author')

# Use numeric labels.
misc._addproducer(emptyproducer, 'label')

# Emphasize book and journal titles.
misc._addfilter(emphfilter, 'fullpublication', 'booktitle')
misc._addfilter(emphfilter, 'fullpublication', 'journal')
