from crosstex.style.basic import *

# Prefer long names.
string._addproducer(makegetterproducer('shortname'), 'value')
string._addproducer(makegetterproducer('longname'), 'value')

# Use numeric labels.
publication._addproducer(emptyproducer, 'label')

# Use 'In' and emphasize book and journal titles.
publication._addfilter(emphfilter, 'fullpublication', 'booktitle')
publication._addfilter(emphfilter, 'fullpublication', 'journal')
book._addfilter(emphfilter, 'fulltitle')
journal._addfilter(emphfilter, 'fulltitle')
