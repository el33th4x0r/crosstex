from crosstex.style.basic import *

# Prefer long names.
string._addproducer(makegetterproducer('shortname'), 'value')
string._addproducer(makegetterproducer('longname'), 'value')

# Use 'In' and emphasize book and journal titles.
misc._addfilter(infilter, 'fullpublication', 'booktitle')
misc._addfilter(infilter, 'fullpublication', 'journal')
misc._addfilter(emphfilter, 'fullpublication', 'booktitle')
misc._addfilter(emphfilter, 'fullpublication', 'journal')

# Preface conference names with 'Proceedings of the'.
inproceedings._addfilter(proceedingsfilter, 'fullpublication', booktitle')

# Use long labels.
misc._addproducer(makegetterproducer('fullnamelabel'), 'label')