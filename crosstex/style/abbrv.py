from crosstex.style.basic import *

# Prefer short names.
string._addproducer(makegetterproducer('longname'), 'value')
string._addproducer(makegetterproducer('shortname'), 'value')

# Use first initials for authors.
publication._addlistfilter(shortnameslistfilter, 'author')

# Use numeric labels.
publication._addproducer(emptyproducer, 'label')

# Emphasize book and journal titles.
publication._addfilter(emphfilter, 'fullpublication', 'booktitle')
publication._addfilter(emphfilter, 'fullpublication', 'journal')
book._addfilter(emphfilter, 'fulltitle')
journal._addfilter(emphfilter, 'fulltitle')
