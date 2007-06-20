VERSION=0.5.3
RELEASE=1
PACKAGE=crosstex-${VERSION}

ROOT=
PREFIX=/usr/local
LIBDIR=/share/crosstex
BINDIR=/bin
MANDIR=/share/man
PLY=${PREFIX}${LIBDIR}

all:
	@echo nothing to make, try make install

install:
	mkdir -p $(ROOT)$(PREFIX)$(BINDIR) $(ROOT)$(PREFIX)$(LIBDIR)/crosstex/style $(ROOT)$(PREFIX)$(MANDIR)/man1
	install -m 0644 lib/crosstex/*.py $(ROOT)$(PREFIX)$(LIBDIR)/crosstex
	install -m 0644 lib/crosstex/style/*.py $(ROOT)$(PREFIX)$(LIBDIR)/crosstex/style
	install -m 0644 data/*.xtx $(ROOT)$(PREFIX)$(LIBDIR)
	install -m 0644 crosstex.1 $(ROOT)$(PREFIX)$(MANDIR)/man1
	ln -sf crosstex.1 $(ROOT)$(PREFIX)$(MANDIR)/man1/xtx2bib.1
	ln -sf crosstex.1 $(ROOT)$(PREFIX)$(MANDIR)/man1/xtx2html.1
	ln -sf crosstex.1 $(ROOT)$(PREFIX)$(MANDIR)/man1/bib2xtx.1
	echo '/^version = /c\' >crosstex.sed
	echo "version = '${VERSION}'" >>crosstex.sed
	echo '/^xtxlib = /c\' >>crosstex.sed
	echo "xtxlib = '${PREFIX}${LIBDIR}'" >>crosstex.sed
	echo '/^plylib = /c\' >>crosstex.sed
	echo "plylib = '${PLY}'" >>crosstex.sed
	sed -f crosstex.sed <crosstex >$(ROOT)$(PREFIX)$(BINDIR)/crosstex
	rm -f crosstex.sed
	chmod 0755 $(ROOT)$(PREFIX)$(BINDIR)/crosstex
	ln -sf crosstex $(ROOT)$(PREFIX)$(BINDIR)/xtx2bib
	ln -sf crosstex $(ROOT)$(PREFIX)$(BINDIR)/xtx2html
	ln -sf crosstex $(ROOT)$(PREFIX)$(BINDIR)/bib2xtx

crosstex.pdf: crosstex.tex
	pdflatex crosstex && pdflatex crosstex

.PHONY: pdf
pdf: crosstex.pdf

${PACKAGE}.tar.gz: COPYING Makefile crosstex crosstex.1 crosstex.pdf crosstex.spec crosstex.tex
	rm -rf ${PACKAGE}
	mkdir -p ${PACKAGE}/data ${PACKAGE}/debian ${PACKAGE}/lib/crosstex/style ${PACKAGE}/tests
	install -m 0644 COPYING Makefile crosstex crosstex.1 crosstex.pdf crosstex.tex ${PACKAGE}
	install -m 0644 data/*.xtx ${PACKAGE}/data
	install -m 0644 lib/crosstex/*.py ${PACKAGE}/lib/crosstex
	install -m 0644 lib/crosstex/style/*.py ${PACKAGE}/lib/crosstex/style
	install -m 0644 tests/*.tex tests/*.xtx ${PACKAGE}/tests
	install debian/* ${PACKAGE}/debian
	sed -e "1i %define name crosstex" \
	    -e "1i %define version ${VERSION}" \
	    -e "1i %define release ${RELEASE}" \
	    -e "1i %define prefix ${PREFIX}" \
	    -e "1i %define bindir ${BINDIR}" \
	    -e "1i %define libdir ${LIBDIR}" \
	    -e "1i %define mandir ${MANDIR}" \
	    -e "1i %define ply ${PLY}" \
	    crosstex.spec >${PACKAGE}/crosstex.spec
	tar czf ${PACKAGE}.tar.gz ${PACKAGE}

.PHONY: dist
dist: ${PACKAGE}.tar.gz

.PHONY: rpm
rpm: dist
	mkdir -p ${PACKAGE}-rpm/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
	rpmbuild -ta --define "_topdir `pwd`/${PACKAGE}-rpm" ${PACKAGE}.tar.gz
	find ${PACKAGE}-rpm -name \*.rpm -exec mv {} . \;
	rm -r ${PACKAGE}-rpm

.PHONY: deb
deb: dist
	cp ${PACKAGE}.tar.gz crosstex_${VERSION}.orig.tar.gz
	(cd ${PACKAGE} && dpkg-buildpackage -rfakeroot)

clean:
	rm -rf *~ *.pyc *.aux *.bbl *.dvi *.log *.tar.gz *.rpm *.html \
	       *.out *.toc *.pdf *.haux *.htoc *-rpm *.bak ${PACKAGE} \
	       crosstex_${VERSION}*
