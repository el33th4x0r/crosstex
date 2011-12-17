'''
Handle CrossTeX's many command-line options.

This is somewhat complicated further by the fact that options can be
set in .aux files on a per-document, on-the-fly basis using \bibstyle.
It is therefore a desirable property to build up options iteratively.
'''

import sys
import optparse
import crosstex.objects


def heading(option, opt, value, parser, reversed=False):
    parser.values.heading.append((reversed, value))

def sorting(option, opt, value, parser, reversed=False):
    if parser.values.sort == None or value == 'none':
        parser.values.sort = []
    if value != 'none':
        parser.values.sort.append((reversed, value))

def message(opts, level, details):
    if level >= opts.check:
        if level > 0:
            opts.errors += 1
        else:
            opts.warnings += 1
        sys.stderr.write(str(details) + '\n')

def warning(opts, details):
    message(opts, 0, details)

def error(opts, details):
    message(opts, 1, details)


_strings = [ name for name in dir(crosstex.objects) \
             if (isinstance(getattr(crosstex.objects, name), type) and \
                 issubclass(getattr(crosstex.objects, name), \
                            crosstex.objects.string)) ]

_dumpable = ['file', 'titlephrase', 'titlesmall'] + _strings


class OptionParser(optparse.OptionParser):

    def __init__(self, version='Testing', xtxlib=[]):
        optparse.OptionParser.__init__(self,
          usage='usage: %prog [options] files',
          version='CrossTeX %s' % version,
          description='A modern, object-oriented bibliographic tool.')

        self.set_defaults(errors=0)
        self.set_defaults(warnings=0)

        self.set_defaults(check=1)
        self.add_option('--quiet',
          action='store_const',
          const=2,
          dest='check',
          help='Do not sanity check the input.')
        self.add_option('--strict',
          action='store_const',
          const=0,
          dest='check',
          help='Apply stricter checks and check all entries.')

        self.set_defaults(dump=[])
        self.add_option('--dump',
          metavar='TYPE',
          action='append',
          type='choice',
          choices=_dumpable,
          help='After parsing the bibliography, dump a list of all objects of the '
               'type specified, or, with "file", print a list of files processed.')

        dirs = xtxlib
        if '.' not in dirs:
            dirs += '.'
        self.set_defaults(dir=dirs)
        self.add_option('-d', '--dir',
          type='string',
          action='append',
          help='Add a directory in which to find data files, searched from last '
               'specified to first. Default: %default')

        self.set_defaults(cite=[])
        self.add_option('--cite',
          type='string',
          action='append',
          help='Cite a key exactly as with the \\cite LaTeX command.')

        self.set_defaults(cite_by='style')
        self.add_option('--cite-by',
          type='choice',
          choices=['number', 'initials', 'fullname', 'style'],
          help='With "number", use numeric labels such as [1]. With "initials", '
               'use labels based on author last-names such as [SBRD04b]. With '
               '"fullname", use labels based on author names such as '
               '[Sirer et al. 2004]. With "style", use the style default.')

        self.set_defaults(style=None)
        self.add_option('--style',
          metavar='STYLE',
          type='string',
          help='Use a standard style such as plain, unsrt, abbrv, full, or alpha. '
               'Options set by the style may be overidden by further command-line '
               'options.')

        self.set_defaults(sort=[(False, 'title'), (False, 'monthno'),
                                (False, 'year'), (False, 'author')])
        self.add_option('-s', '--sort',
          metavar='FIELD',
          type='string',
          action='callback',
          callback=sorting,
          help='Sort by specified field. Multiple sort orders are applied in the '
               'order specified, e.g. "-s year -s author" will cause elements to '
               'be grouped primarily by author and sub-grouped by year.')
        self.add_option('-S', '--reverse-sort',
          metavar='FIELD',
          type='string',
          action='callback',
          callback=sorting,
          callback_args=(True,),
          help='Exactly as --sort, but sort by descending field values rather '
               'than ascending.')
        self.add_option('--no-sort',
          action='store_const',
          const=[],
          dest='sort')

        self.set_defaults(heading=[])
        self.add_option('--heading',
          metavar='FIELD',
          type='string',
          action='callback',
          callback=heading,
          help='Divide entries and create headings in bibliography by the value '
               'of the given field.')
        self.add_option('--reverse-heading',
          metavar='FIELD',
          type='string',
          action='callback',
          callback=heading,
          callback_args=(True,),
          help='Divide entries and create headings in bibliography by the value '
               'of the given field.')

        self.set_defaults(short=[])
        self.add_option('--short',
          metavar='TYPE',
          type='choice',
          action='append',
          choices=_strings,
          help='Specify any string-like object, i.e. one with name and shortname '
               'fields. Whenever possible,the short name will be used,e.g. '
               'two-letter state codes for "state",conference acronyms such as '
               'NSDI for "conference",or initials such as E. G. Sirer for '
               '"author".')

        self.set_defaults(capitalize=[])
        self.add_option('--capitalize',
          metavar='TYPE',
          type='choice',
          choices=_strings,
          action='append',
          help='Specify any string-like object, i.e. one with name and shortname '
               'fields. Strings of the specified types will appear in ALL CAPS.')

        self.set_defaults(no_field=[])
        self.add_option('--no-field',
          metavar='FIELD',
          action='append',
          help='Specify a field name, and in any objects where that field is '
               'optional it will be unassigned no matter what appears in the '
               'database.  For example, to turn off page numbers, use '
               '"--no-field pages".')

        self.set_defaults(link=[])
        self.add_option('-l', '--link',
          metavar='FIELD',
          type='string',
          action='append',
          help='Add to the list of fields used to generate links. LaTeX documents '
               'should make use of links by including the hyperref package. When '
               'converting to HTML, this defaults to [Abstract, URL, PS, PDF, '
               'HTML, DVI, TEX, BIB, FTP, HTTP, and RTF].')
        self.add_option('--no-link',
          action='store_const',
          const=[],
          dest='link')

        self.set_defaults(titlecase='default')
        self.add_option('--titlecase',
          type='choice',
          choices=['lower', 'upper', 'as-is', 'default'],
          help='In the bibliography, force titles into lower-, upper-, or '
               'title-case. Default: Leave titles unchanged.')

        self.set_defaults(convert='bbl')
        self.add_option('--xtx2bib',
          action='store_const',
          const='bib',
          dest='convert',
          help='Convert the bibliography information to old-style BibTeX.')
        self.add_option('--xtx2html',
          action='store_const',
          const='html',
          dest='convert',
          help='Format the bibliography as HTML.')
        self.add_option('--bib2xtx',
          action='store_const',
          const='xtx',
          dest='convert',
          help='Format the bibliography as HTML.')

        self.add_option('--add-in',
          action='store_true',
          help='Add "In" for articles.')
        self.add_option('--add-proc',
          action='store_true',
          help='Add "Proc. of" to conference and workshop publications.')
        self.set_defaults(add_in=[])
        self.add_option('--add-proceedings',
          action='store_true',
          help='Add "Proceedings of the" to conference and workshop publications.')
        self.add_option('--abstract',
          action='store_true',
          help='In the bibliography, include paper abstracts if available.')
        self.add_option('--no-abstract',
          action='store_false',
          dest='abstract')
        self.add_option('--keywords',
          action='store_true',
          help='In the bibliography, include paper keywords if available.')
        self.add_option('--no-keywords',
          action='store_false',
          dest='keywords')
        self.add_option('--popups',
          action='store_true',
          help='If abstracts or keywords are to appear for an entry when '
               'generating HTML, instead hide these extra blocks and reveal them '
               'as popups when the mouse hovers over the entry.')
        self.add_option('--no-popups',
          action='store_false')
        self.add_option('--title-head',
          action='store_true',
          help='In the bibliography, put the title bold and first.')
        self.add_option('--no-title-head',
          action='store_false',
          dest='title_head')
        self.add_option('--blank-labels',
          action='store_true',
          help='In the bibliography, leave out item labels.')
        self.add_option('--no-blank-labels',
          action='store_false',
          dest='blank_labels')
        self.add_option('--break-lines',
          action='store_true',
          help='In the bibliography, put author, title, and publication '
               'information on separate lines.')
        self.add_option('--no-break-lines',
          action='store_false',
          dest='break_lines')
        self.add_option('--last-first',
          action='store_true',
          help='The first name in each author list will appear "Last, First" '
               'instead of "First Last" (the latter is the default).')
        self.add_option('--no-last-first',
          action='store_false',
          dest='last_first')
