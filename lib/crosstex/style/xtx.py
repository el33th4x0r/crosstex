from crosstex.objects import *

# Standard producers for top-level objects.
misc._addproducer(crosstexproducer, 'value')
string._addproducer(crosstexproducer, 'value')
location._addproducer(crosstexproducer, 'value')
entrylist._addlistformatter(andcrosstexlistformatter, 'value')

# Use empty labels (irrelevant, but labels determine what is 'citeable' and thus produced.
misc._addproducer(emptyproducer, 'label')
string._addproducer(emptyproducer, 'label')
location._addproducer(emptyproducer, 'label')
