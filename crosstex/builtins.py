from crosstex.objects import month
from crosstex.parse import Entry, Field

from crosstex.constants import LONG_MONTHS

builtins = {}

# Create a builtin type for every month
for i in range(len(LONG_MONTHS)):
    builtins[LONG_MONTHS[i]] = Entry(-1, 'month', ['monthno'], [Field('monthno', i+1)], __file__, 0,  {})

