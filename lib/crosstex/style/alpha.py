from crosstex.style.basic import *

# Prefer long names.
string._addproducer(makegetterproducer('shortname'), 'value')
string._addproducer(makegetterproducer('longname'), 'value')

# Use alphabetic labels.
misc._addproducer(makegetterproducer('initialslabel'), 'label')

# Emphasize book and journal titles.
misc._addfilter(emphfilter, 'fullpublication', 'booktitle')
misc._addfilter(emphfilter, 'fullpublication', 'journal')
