import math

import crosstex.latex
import crosstex.style


class ACMJournalBbl(object):

    etalchar = '{\etalchar{+}}'

    def header(self, longest):
        return '\\newcommand{\etalchar}[1]{$^{#1}$}\n' + \
               '\\begin{thebibliography}{%s}\n' % longest

    def heading(self, name, sep):
        return ''

    def footer(self):
        return '\n\end{thebibliography}\n'

    def list_begin(self):
        return ''

    def list_end(self):
        return ''

    def item(self, key, label, rendered_obj):
        if label:
            label = '[%s]' % label
        return '\n' + ('\\bibitem%s{%s}\n' % (label, key)) + crosstex.latex.to_latex(rendered_obj) + '\n'

    def block(self, text):
        return text.strip()

    def block_sep(self):
        return '\n\\newblock '

    def emph(self, text):
        return r'\emph{' + text.strip() + '}'


class ACMJournalTxt(object):

    etalchar = '+'

    def header(self, longest):
        return ''

    def heading(self, name, sep):
        if sep:
            return '\n%s\n' % name
        else:
            return '%s\n' % name

    def footer(self):
        return ''

    def list_begin(self):
        return ''

    def list_end(self):
        return ''

    def item(self, key, label, rendered_obj):
        return rendered_obj + '\n'

    def block(self, text):
        return text.strip()

    def block_sep(self):
        return '  '

    def emph(self, text):
        return text.strip()


class ACMJournalHtml(object):

    etalchar = '+'

    def header(self, longest):
        return '<table class="xtxlist">'

    def heading(self, name, sep):
        return '\n<th colspan="2">%s</th>\n' % name

    def footer(self):
        return '</table>'

    def list_begin(self):
        return ''

    def list_end(self):
        return ''

    def item(self, key, label, rendered_obj):
        return '<tr class="xtxentry"><td class="xtxlabel">' \
               + '<a name="xtx:%s">%s</a></td><td class="xtxtext">' % (label, label) \
               + rendered_obj + '</td></tr>\n'

    def block(self, text):
        return '<span>' + text.strip() + '</span>'

    def block_sep(self):
        return '\n'

    def emph(self, text):
        return '<em>' + text.strip() + '</em>'


class Style(crosstex.style.Style):

    formatters = {'bbl': ACMJournalBbl,
                  'txt': ACMJournalTxt,
                  'html': ACMJournalHtml}

    @classmethod
    def formats(cls):
        return set(Style.formatters.keys())

    def __init__(self, fmt, flags, options, db):
        fmtr = self.formatters.get(fmt, None)
        assert fmtr
        self._fmt = fmtr()
        self._db = db
        self._flags = flags or set([])
        self._options = options or {}

    def sort_key(self, citation):
        cite, obj = citation
        author = None
        if 'author' in obj.allowed and obj.author:
            author = self.get_field(obj, 'author')
        title = None
        if 'title' in obj.allowed and obj.title:
            title = obj.title.value
        where = None
        if 'booktitle' in obj.allowed and obj.booktitle:
            where = self.render_booktitle(obj.booktitle)
        elif 'journal' in obj.allowed and obj.journal:
            where = self.render_journal(obj.journal)
        when = None
        if 'year' in obj.allowed and obj.year:
            when = unicode(obj.year.value)
        return author, title, where, when

    def get_field(self, obj, field):
        # return or set attr
        if field == 'author':
            author = [a.name.value if hasattr(a, 'name') else a.value for a in obj.author]
            author = [crosstex.style.name_sort_last_first(a) for a in author]
            author = tuple(author)
            return author
        elif field == 'monthno' and not hasattr(obj, 'monthno'):
            attr = getattr(obj, 'month', None)
            if hasattr(attr, 'monthno'):
                attr = attr.monthno
            else:
                attr = None
        else:
            attr = getattr(obj, field, None)
        # do something with attr
        if attr is not None:
            return attr.name.value if hasattr(attr, 'name') else attr.value
        return None

    def render(self, citations):
        label_dict, longest = self.get_label_dict(citations)
        bib = self._fmt.header(longest)
        in_list = False
        for idx, citation in enumerate(citations):
            if isinstance(citation, crosstex.style.Heading):
                if in_list:
                    bib += self._fmt.list_end()
                bib += self._fmt.heading(citation.name, in_list)
                bib += self._fmt.list_begin()
                in_list = True
                continue
            cite, obj = citation
            cb = self._callback(obj.kind)
            if cb is None:
                raise crosstex.style.UnsupportedCitation(obj.kind)
            item = cb(obj)
            label = label_dict[cite]
            if not in_list:
                bib += self._fmt.list_begin()
                in_list = True
            bib += self._fmt.item(cite, label, item)
        if in_list:
            in_list = False
            bib += self._fmt.list_end()
        bib += self._fmt.footer()
        return label_dict, bib

    def get_label_dict(self, citations):
        citations = [c for c in citations
                     if not isinstance(c, crosstex.style.Heading)]
        labels  = crosstex.style.label_generate_lastnames(citations)
        longest = '00' #XXX what is this?
        label_dict = dict(zip([c for c, o in citations], labels))
        return label_dict, longest

    def _callback(self, kind):
        if not hasattr(self, 'render_' + kind):
            return None
        else:
            return getattr(self, 'render_' + kind)

    # Stuff for rendering

    def render_str(self, string, which):
        if isinstance(string, crosstex.parse.Value):
            string = unicode(string.value)
        elif 'short-' + which in self._flags:
            string = unicode(string.shortname.value)
        elif 'short-' + which not in self._flags:
            string = unicode(string.longname.value)
        return string

    def render_author(self, author, context=None, history=None):
        author = [a.name.value if hasattr(a, 'name') else a.value for a in author]
        if 'short-author' in self._flags:
            author = crosstex.style.names_shortfirst_last(author)
        else:
            author = crosstex.style.names_first_last(author)
        author = [a.strip('{}') for a in author]
        author = crosstex.style.list_comma_and(author)
        return author

    def render_title(self, title, context=None, history=None):
        title = title.value
        if 'titlecase-default' in self._flags:
            return title
        elif 'titlecase-upper' in self._flags:
            return crosstex.style.title_uppercase(title)
        elif 'titlecase-title' in self._flags:
            return crosstex.style.title_titlecase(title, self._db.titlephrases())
        elif 'titlecase-lower' in self._flags:
            return crosstex.style.title_lowercase(title, self._db.titlesmalls())
        return title

    def render_booktitle(self, booktitle, context=None, history=None):
        if isinstance(booktitle, crosstex.objects.workshop):
            return self.render_str(booktitle, 'workshop')
        elif isinstance(booktitle, crosstex.objects.conference):
            return self.render_str(booktitle, 'conference')
        elif isinstance(booktitle, crosstex.parse.Value):
            return self.render_str(booktitle, 'booktitle')

    def render_journal(self, journal, context=None, history=None):
        return self.render_str(journal, 'journal')

    def render_pages(self, pages, context=None, history=None):
        pages = unicode(pages)
        if '-' in pages:
            return 'pages %s' % pages
        else:
            return 'page %s' % pages

    def render_address(self, address, context=None, history=None):
        city, state, country = None, None, None
        if isinstance(address, crosstex.objects.location):
            if address.city:
                city = self.render_str(address.city, 'city')
            if address.state:
                state = self.render_str(address.state, 'state')
            if address.country:
                country = self.render_str(address.country, 'country')
        elif isinstance(address, crosstex.objects.country):
            country = self.render_str(address, 'country')
        elif isinstance(address, crosstex.objects.state):
            state = self.render_str(address, 'state')
            if address.country:
                country = self.render_str(address.country, 'country')
        elif isinstance(address, crosstex.parse.Value):
            return self.render_str(address, 'address')
        return ', '.join([x for x in (city, state, country) if x is not None and x != ''])

    def render_year(self, year, context=None, history=None):
        if isinstance(year, crosstex.parse.Value):
            return self.render_str(year, 'year')

    def render_month(self, month, context=None, history=None):
        return self.render_str(month, 'month')

    def render_article(self, article, context=None, history=None):
        author  = self.render_author(article.author)
        title   = self.render_title(article.title)
        journal = self.render_journal(article.journal)
        year    = self.render_year(article.year) 
        volume  = unicode(article.volume.value) if article.volume else None
        number  = unicode(article.number.value) if article.number else None
        pages   = unicode(article.pages.value) if article.pages and 'no-pages' not in self._flags else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self._fmt.block(crosstex.style.punctuate(author, '.', ''))
        if year:
            first += ' ' + crosstex.style.punctuate(year, '.', '')
        if title:
            second = self._fmt.block(crosstex.style.punctuate(title, '.', ''))
        if journal:
            if 'add-in' in self._flags:
                third += 'In '
            third += self._fmt.emph(journal)
        volnumpages = ''
        if number or volume or pages:
            if volume:
                volnumpages += unicode(volume)
            if number:
                volnumpages += '(%s)' % number
            if pages:
                if volume or number:
                    volnumpages += ':%s' % pages
                else:
                    volnumpages += self.render_pages(pages)
        if volnumpages:
            third = crosstex.style.punctuate(third, ',', ' ')
            third += volnumpages
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        return self._fmt.block_sep().join([b for b in (first, second, third) if b])

    def render_book(self, book, context=None, history=None):
        author    = self.render_author(book.author)
        # XXX need to handle editors
        title     = self.render_title(book.title)
        publisher = self.render_str(book.publisher, 'publisher') if book.publisher else None
        address   = self.render_address(book.address) if book.address and 'no-address' not in self._flags else None
        year      = self.render_year(book.year) if book.year else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self._fmt.block(crosstex.style.punctuate(author, '.', ''))
        if year:
            first += ' ' + crosstex.style.punctuate(year, '.', '')
        if title:
            second = self._fmt.block(crosstex.style.punctuate(title, '.', ''))
        if publisher:
            third = publisher
        if address:
            third = crosstex.style.punctuate(third, ',', ' ') + address
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        return self._fmt.block_sep().join([b for b in (first, second, third) if b])

    def render_inproceedings(self, inproceedings, context=None, history=None):
        author    = self.render_author(inproceedings.author)
        title     = self.render_title(inproceedings.title)
        booktitle = self.render_booktitle(inproceedings.booktitle)
        pages     = self.render_pages(inproceedings.pages.value) if inproceedings.pages and 'no-pages' not in self._flags else None
        address   = self.render_address(inproceedings.address) if inproceedings.address and 'no-address' not in self._flags else None
        year      = self.render_year(inproceedings.year) if inproceedings.year else None
        month     = self.render_month(inproceedings.month) if inproceedings.month else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self._fmt.block(crosstex.style.punctuate(author, '.', ''))
        if year:
            first += ' ' + crosstex.style.punctuate(year, '.', '')
        if title:
            second = self._fmt.block(crosstex.style.punctuate(title, '.', ''))
        if booktitle:
            if 'add-in' in self._flags:
                third += 'In '
            if 'add-proceedings' in self._flags:
                third += 'Proceedings of the '
            elif 'add-proc' in self._flags:
                third += 'Proc. of '
            third += crosstex.style.punctuate(self._fmt.emph(booktitle), ',', ' ')
        if pages:
            third = crosstex.style.punctuate(third, ',', ' ') + pages
        if address:
            third = crosstex.style.punctuate(third, ',', ' ') + address
        #if month and year:
        #    third = crosstex.style.punctuate(third, ',', ' ')
        #    third += month + ' ' + year
        #elif year:
        #    third = crosstex.style.punctuate(third, ',', ' ')
        #    third += year
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        return self._fmt.block_sep().join([b for b in (first, second, third) if b])

    def render_misc(self, misc, context=None, history=None):
        author    = self.render_author(misc.author) if misc.author else None
        title     = self.render_title(misc.title) if misc.title else None
        howpub    = unicode(misc.howpublished.value) if misc.howpublished else None
        booktitle = self.render_booktitle(misc.booktitle) if misc.booktitle else None
        address   = self.render_address(misc.address) if misc.address and 'no-address' not in self._flags else None
        year      = self.render_year(misc.year) if misc.year else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self._fmt.block(crosstex.style.punctuate(author, '.', ''))
        if year:
            first += ' ' + crosstex.style.punctuate(year, '.', '')
        if title:
            second = self._fmt.block(crosstex.style.punctuate(title, '.', ''))
        if howpub:
            third += howpub
        if booktitle:
            third = crosstex.style.punctuate(third, ',', ' ') + self._fmt.emph(booktitle)
        if address:
            third = crosstex.style.punctuate(third, ',', ' ') + address
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        return self._fmt.block_sep().join([b for b in (first, second, third) if b])

    def render_techreport(self, techreport, context=None, history=None):
        author  = self.render_author(techreport.author)
        title   = self.render_title(techreport.title)
        number  = unicode(techreport.number.value) if techreport.number else None
        insti   = unicode(techreport.institution.value) if techreport.institution else None
        address = self.render_address(techreport.address) if techreport.address and 'no-address' not in self._flags else None
        year    = self.render_year(techreport.year) 
        month   = self.render_month(techreport.month) if techreport.month else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self._fmt.block(crosstex.style.punctuate(author, '.', ''))
        if year:
            first += ' ' + crosstex.style.punctuate(year, '.', '')
        if title:
            second = self._fmt.block(crosstex.style.punctuate(title, '.', ''))
        if insti:
            third = insti
        if address:
            third = crosstex.style.punctuate(third, ',', ' ') + address
        if number:
            third = crosstex.style.punctuate(third, ',', ' ')
            third += 'Technical Report ' +  number
        else:
            third = crosstex.style.punctuate(third, ',', ' ')
            third += 'Technical Report'
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        return self._fmt.block_sep().join([b for b in (first, second, third) if b])

    def render_phdthesis(self, phdthesis, context=None, history=None):
        author  = self.render_author(phdthesis.author)
        title   = self.render_title(phdthesis.title)
        school  = unicode(phdthesis.school.value) if phdthesis.school else None
        year    = self.render_year(phdthesis.year)
        first = ''
        second = ''
        third = 'PhD thesis'
        if author:
            first = self._fmt.block(crosstex.style.punctuate(author, '.', ''))
        if year:
            first += ' ' + crosstex.style.punctuate(year, '.', '')
        if title:
            second = self._fmt.block(crosstex.style.punctuate(title, '.', ''))
        if school:
            third = crosstex.style.punctuate(third, ',', ' ') + school
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        return self._fmt.block_sep().join([b for b in (first, second, third) if b])

    def render_url(self, url, context=None, history=None):
        author = self.render_author(url.author) if url.author else None
        title  = self.render_title(url.title) if url.title else None
        link   = unicode(url.url.value)
        month  = self.render_month(url.accessmonth) if url.accessmonth else None
        day    = self.render_str(url.accessday, 'day') if url.accessday else None
        year   = self.render_year(url.accessyear) if url.accessyear else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self._fmt.block(crosstex.style.punctuate(author, '.', ''))
        if year:
            first += ' ' + crosstex.style.punctuate(year, '.', '')
        if title:
            second = self._fmt.block(crosstex.style.punctuate(title, '.', ''))
        if url:
            third = '\url{%s}' % link
        if month and day and year:
            third = self._fmt.block(crosstex.style.punctuate(third, '.', ''))
            third += ' Accessed ' + month + ' ' + day + ', ' + year
        elif month and year:
            third = self._fmt.block(crosstex.style.punctuate(third, '.', ''))
            third += ' Accessed ' + month + ' ' + year
        elif year:
            third = self._fmt.block(crosstex.style.punctuate(third, '.', ''))
            third += ' Accessed ' + year
        third = self._fmt.block(crosstex.style.punctuate(third, '.', ''))
        third = self._fmt.block(third)
        return self._fmt.block_sep().join([b for b in (first, second, third) if b])
