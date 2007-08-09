from crosstex.style.basic import *

# Prefer long names.
string._addproducer(makegetterproducer('shortname'), 'value')
string._addproducer(makegetterproducer('longname'), 'value')

# Use 'In' and emphasize book and journal titles.
publication._addfilter(infilter, 'fullpublication', 'booktitle')
publication._addfilter(infilter, 'fullpublication', 'journal')
publication._addfilter(emphfilter, 'fullpublication', 'booktitle')
publication._addfilter(emphfilter, 'fullpublication', 'journal')
book._addfilter(emphfilter, 'fulltitle')
journal._addfilter(emphfilter, 'fulltitle')

# Preface conference names with 'Proceedings of the'.
inproceedings._addfilter(proceedingsfilter, 'fullpublication', 'booktitle')

# Use long labels.
publication._addproducer(makegetterproducer('fullnamelabel'), 'label')
