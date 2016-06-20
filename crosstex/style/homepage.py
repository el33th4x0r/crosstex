import math

import crosstex.latex
import crosstex.style
import crosstex.style.plain


class HomepageHtml(object):

    etalchar = '+'

    def header(self, longest):
        return ''

    def heading(self, name, sep):
        return '<h1>{0}</h1>\n'.format(name)

    def footer(self):
        return ''

    def list_begin(self):
        return '<ul class=citations>\n'

    def list_end(self):
        return '</ul>\n'

    def item(self, key, label, rendered_obj):
        return '<li>' + rendered_obj + '</li>\n'

    def block(self, text, classes=''):
        if classes:
            classes = ' ' + classes.strip()
        return '<div classes="line{0}">'.format(classes) + text.strip() + '</div>'

    def block_sep(self):
        return '\n'

    def emph(self, text):
        return '<em>' + text.strip() + '</em>'

    def URLs(self, obj):
        links = []
        if hasattr(obj, 'ps') and obj.ps:
            links.append('[<a href="{0}">PS</a>]'.format(obj.ps.value))
        if hasattr(obj, 'pdf') and obj.pdf:
            links.append('[<a href="{0}">PDF</a>]'.format(obj.pdf.value))
        if hasattr(obj, 'http') and obj.http:
            links.append('[<a href="{0}">URL</a>]'.format(obj.http.value))
        return self.block(' '.join(links), classes='urls')


class Style(crosstex.style.plain.Style):

    formatters = {'html': HomepageHtml}

    @classmethod
    def formats(cls):
        return set(Style.formatters.keys())

    # Stuff for rendering

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
        if title:
            first = self._fmt.block(crosstex.style.punctuate(title, '.', ''), classes='title')
        if author:
            second = self._fmt.block(crosstex.style.punctuate(author, '.', ''), classes='author')
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
        if year:
            third = crosstex.style.punctuate(third, ',', ' ') + year
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        fourth = self._fmt.URLs(article)
        return self._fmt.block_sep().join([b for b in (first, second, third, fourth) if b])

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
        if title:
            first = self._fmt.block(crosstex.style.punctuate(title, '.', ''), classes='title')
        if author:
            second = self._fmt.block(crosstex.style.punctuate(author, '.', ''), classes='author')
        if publisher:
            third = publisher
        if address:
            third = crosstex.style.punctuate(third, ',', ' ') + address
        if year:
            third = crosstex.style.punctuate(third, ',', ' ') + year
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        fourth = self._fmt.URLs(book)
        return self._fmt.block_sep().join([b for b in (first, second, third, fourth) if b])

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
        if title:
            first = self._fmt.block(crosstex.style.punctuate(title, '.', ''), classes='title')
        if author:
            second = self._fmt.block(crosstex.style.punctuate(author, '.', ''), classes='author')
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
        if month and year:
            third = crosstex.style.punctuate(third, ',', ' ')
            third += month + ' ' + year
        elif year:
            third = crosstex.style.punctuate(third, ',', ' ')
            third += year
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        fourth = self._fmt.URLs(inproceedings)
        return self._fmt.block_sep().join([b for b in (first, second, third, fourth) if b])

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
        if title:
            first = self._fmt.block(crosstex.style.punctuate(title, '.', ''), classes='title')
        if author:
            second = self._fmt.block(crosstex.style.punctuate(author, '.', ''), classes='author')
        if howpub:
            third += howpub
        if booktitle:
            third = crosstex.style.punctuate(third, ',', ' ') + self._fmt.emph(booktitle)
        if address:
            third = crosstex.style.punctuate(third, ',', ' ') + address
        if year:
            third = crosstex.style.punctuate(third, ',', ' ') + year
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        fourth = self._fmt.URLs(misc)
        return self._fmt.block_sep().join([b for b in (first, second, third, fourth) if b])

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
        if title:
            first = self._fmt.block(crosstex.style.punctuate(title, '.', ''), classes='title')
        if author:
            second = self._fmt.block(crosstex.style.punctuate(author, '.', ''), classes='author')
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
        if year:
            third = crosstex.style.punctuate(third, ',', ' ') + year
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        fourth = self._fmt.URLs(techreport)
        return self._fmt.block_sep().join([b for b in (first, second, third, fourth) if b])

    def render_phdthesis(self, phdthesis, context=None, history=None):
        author  = self.render_author(phdthesis.author)
        title   = self.render_title(phdthesis.title)
        school  = unicode(phdthesis.school.value) if phdthesis.school else None
        year    = self.render_year(phdthesis.year)
        first = ''
        second = ''
        third = 'PhD thesis'
        if title:
            first = self._fmt.block(crosstex.style.punctuate(title, '.', ''), classes='title')
        if author:
            second = self._fmt.block(crosstex.style.punctuate(author, '.', ''), classes='author')
        if school:
            third = crosstex.style.punctuate(third, ',', ' ') + school
        if year:
            third = crosstex.style.punctuate(third, ',', ' ') + year
        third = crosstex.style.punctuate(third, '.', '')
        third = self._fmt.block(third)
        fourth = self._fmt.URLs(phdthesis)
        return self._fmt.block_sep().join([b for b in (first, second, third, fourth) if b])

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
        if title:
            first = self._fmt.block(crosstex.style.punctuate(title, '.', ''), classes='title')
        if author:
            second = self._fmt.block(crosstex.style.punctuate(author, '.', ''), classes='author')
        if url:
            third = link
        if month and day and year:
            third = self._fmt.block(crosstex.style.punctuate(third, '.', ''))
            third += 'Accessed ' + month + ' ' + day + ', ' + year
        third = self._fmt.block(crosstex.style.punctuate(third, '.', ''))
        third = self._fmt.block(third)
        fourth = self._fmt.URLs(url)
        return self._fmt.block_sep().join([b for b in (first, second, third, fourth) if b])
