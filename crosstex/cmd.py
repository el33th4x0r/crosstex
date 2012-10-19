import argparse
import importlib
import logging
import os
import os.path
import sys

import crosstex
import crosstex.style


logger = logging.getLogger('crosstex')


parser = argparse.ArgumentParser(prog='crosstex',
                                 description='A modern, object-oriented bibliographic tool.')
#parser.add_argument('--quiet',
#                    help='Do not sanity check the input (XXX: ignored.')
#parser.add_argument('--strict',
#                    help='Apply stricter checks and check all entries (XXX:ignored.')
#parser.add_argument('--dump', metavar='TYPE',
#                    help='After parsing the bibliography, dump a list of all '
#                         'objects of the type specified, or, with "file", print '
#                         'a list of files processed. XXX: ignored')
#parser.add_argument('--cite-by', metavar='CITE_BY', default='style',
#                    help='With "number", use numeric labels such as [1]. With '
#                         '"initials", use labels based on author last-names such '
#                         'as [SBRD04b]. With "fullname", use labels based on '
#                         'author names such as [Sirer et al. 2004]. With '
#                         '"style", use the style default. XXX:ignored')
#parser.add_argument('-s', '--sort', metavar='FIELD', action='append',
#                    help='Sort by specified field. Multiple sort orders are '
#                         'applied in the order specified, e.g. "-s year -s '
#                         'author" will cause elements to be grouped primarily by '
#                         'author and sub-grouped by year.'
#                         ' XXX: this is currently ignored')
#parser.add_argument('-S', '--reverse-sort', metavar='FIELD', action='append',
#                    help='Exactly as --sort, but sort by descending field values '
#                         'rather than ascending.'
#                         ' XXX: this is currently ignored')
#parser.add_argument('--no-sort', help='XXX: ignored')
#parser.add_argument('--heading', metavar='FIELD',
#                    help='Divide entries and create headings in bibliography by '
#                         'the value of the given field. XXX: ignored')
#parser.add_argument('--reverse-heading', metavar='FIELD',
#                    help='Exactly as --heading, but sort by descending field '
#                         'values rather than ascending. XXX: ignored')
#parser.add_argument('--capitalize', metavar='TYPE', action='append',
#                    help='Specify any string-like object, i.e. one with name and '
#                         'shortname fields. Strings of the specified types will '
#                         'appear in ALL CAPS. XXX: ignored')
#parser.add_argument('--no-field', metavar='TYPE', action='append',
#                    help='Specify a field name, and in any objects where that '
#                         'field is optional it will be unassigned no matter what '
#                         'appears in the database.  For example, to turn off '
#                         'page numbers, use "--no-field pages". XXX: ignored')
#parser.add_argument('-l', '--link', metavar='FIELD', action='append',
#                    help='Add to the list of fields used to generate links. '
#                         'LaTeX documents should make use of links by including '
#                         'the hyperref package. When converting to HTML, this '
#                         'defaults to [Abstract, URL, PS, PDF, HTML, DVI, TEX, '
#                         'BIB, FTP, HTTP, and RTF]. XXX: ignored')
#parser.add_argument('--no-link', help='XXX: ignored')
#parser.add_argument('--abstract',
#                    help='In the bibliography, include paper abstracts if available. XXX: ignored')
#parser.add_argument('--no-abstract')
#parser.add_argument('--keywords',
#                    help='In the bibliography, include paper keywords if available. XXX: ignored')
#parser.add_argument('--no-keywords')
#parser.add_argument('--popups',
#                    help='If abstracts or keywords are to appear for an entry'
#                         'when generating HTML, instead hide these extra blocks'
#                         'and reveal them as popups when the mouse hovers over'
#                         'the entry. XXX: ignored')
#parser.add_argument('--no-popups')
#parser.add_argument('--title-head',
#                    help='In the bibliography, put the title bold and first.  XXX:ignored')
#parser.add_argument('--no-title-head')
#parser.add_argument('--blank-labels',
#                    help='In the bibliography, leave out item labels. XXX:ignored')
#parser.add_argument('--no-blank-labels')
#parser.add_argument('--break-lines',
#                    help='In the bibliography, put author, title, and '
#                         'publication information on separate lines.  XXX:ignored')
#parser.add_argument('--no-break-lines')
#parser.add_argument('--last-first',
#                    help='The first name in each author list will appear "Last, '
#                         'First" instead of "First Last" (the latter is the '
#                         'default).  XXX:ignored')
#parser.add_argument('--no-last-first')
parser.add_argument('--version', version='CrossTeX 0.7.0', action='version')
parser.add_argument('-d', '--dir', metavar='DIR', action='append', dest='dirs',
                    help='Add a directory in which to find data files, searched '
                         'from last specified to first.')
parser.add_argument('--cite', metavar='CITE', action='append',
                    help='Cite a key exactly as with the \cite LaTeX command.')
parser.add_argument('--style', metavar='STYLE', default='plain',
                    help='Use a standard style such as plain, unsrt, abbrv, '
                         'full, or alpha. Options set by the style may be '
                         'overidden by further command-line options.')
parser.add_argument('--short', metavar='TYPE', action='append',
                    help='Specify any string-like object, i.e. one with name and '
                         'shortname fields. Whenever possible,the short name '
                         'will be used, e.g. two-letter state codes for '
                         '"state", conference acronyms such as NSDI for '
                         '"conference", or initials such as E. G. Sirer for '
                         '"author".')
parser.add_argument('--titlecase', metavar='TITLECASE', default='default',
                    choices=('default', 'lower', 'upper', 'title'),
                    help='In the bibliography, force titles into lower-, upper-, '
                         'or title-case.  Default: leave the titles unchanged.')
parser.add_argument('-f', '--format', metavar='FORMAT', dest='fmt', default='bbl',
                    help='Select a format for the output.  Examples include '
                         '"bbl", "html", "bib", or "xtx".  "bib" and "xtx" are '
                         'always available and not affected by "--style".  '
                         'Other formats are dependent upon the choice of style.')
parser.add_argument('-o', '--output', metavar='FILE',
                    help='Write the bibliography to the specified output file.')
parser.add_argument('--add-in', action='store_const', const=True, default=False,
                    help='Add "In" for articles.')
parser.add_argument('--add-proc', dest='add_proc',
                    action='store_const', const='proc', default=None,
                    help='Add "Proc. of" to conference and workshop publications.')
parser.add_argument('--add-proceedings', dest='add_proc',
                    action='store_const', const='proceedings',
                    help='Add "Proceedings of the" to conference and workshop publications.')
parser.add_argument('files', metavar='FILES', nargs='+',
                    help='A list of xtx, aux, or bib files to process.')


def main(argv):
    try:
        args = parser.parse_args()
        path = list(args.dirs or []) + \
               [os.path.join(os.path.join(os.path.expanduser('~'), '.crosstex'))] + \
               ['/XXX']
        xtx = crosstex.CrossTeX(xtx_path=path)
        xtx.set_titlecase(args.titlecase)
        if args.add_in:
            xtx.add_in()
        if args.add_proc == 'proc':
            xtx.add_proc()
        if args.add_proc == 'proceedings':
            xtx.add_proceedings()
        for s in args.short or []:
            xtx.add_short(s)
        xtx.set_style(args.fmt, args.style)
        for f in reversed(args.files):
            xtx.parse(f)
        # We'll use this check later
        is_aux = os.path.splitext(args.files[-1])[1] == '.aux' or \
                 xtx.aux_citations() and os.path.splitext(args.files[-1])[1] == ''
        # Get a list of things to cite
        cite = []
        if args.cite:
            cite = args.cite
        elif is_aux:
            cite = xtx.aux_citations()
        else:
            cite = xtx.all_citations()
        objects = [(c, xtx.lookup(c)) for c in cite]
        for c in [c for c, o in objects if not o or not o.citeable]:
            logger.warning('Cannot find object for citation %r' % c)
        citeable = [(c, o) for c, o in objects if o and o.citeable]
        citeable = xtx.sort(citeable)
        try:
            rendered = xtx.render(citeable)
        except crosstex.style.UnsupportedCitation as e:
            logger.error('Style does not support citations for %s' % e.citetype)
            return 1
        if args.output:
            with open(args.output, 'w') as fout:
                fout.write(rendered)
                fout.flush()
        elif is_aux and args.fmt == 'bbl':
            with open(os.path.splitext(args.files[-1])[0] + '.bbl', 'w') as fout:
                fout.write(rendered)
                fout.flush()
        else:
            sys.stdout.write(rendered)
            sys.stdout.flush()
        return 0
    except crosstex.CrossTeXError as e:
        print >>sys.stderr, e
        return 1
