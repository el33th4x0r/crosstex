VERSION=0.4
RELEASE=1
PACKAGE=crosstex-${VERSION}

ROOT=
PREFIX=/usr/local
LIBDIR=/lib/crosstex
BINDIR=/bin
PLY=${LIBDIR}

all:
	@echo nothing to make, try make install

install:
	mkdir -p $(ROOT)$(PREFIX)$(BINDIR) $(ROOT)$(PREFIX)$(LIBDIR)
	cp *.py data/*.xtx $(ROOT)$(PREFIX)$(LIBDIR)
	sed -e "/^version = /c\\version = '${VERSION}'" \
	    -e "/^xtxlib = /c\\xtxlib = '${PREFIX}${LIBDIR}'" \
	    -e "/^plylib = /c\\plylib = '${PLY}'" \
	    crosstex >$(ROOT)$(PREFIX)$(BINDIR)/crosstex
	chmod 0755 $(ROOT)$(PREFIX)$(BINDIR)/crosstex
	ln -sf crosstex $(ROOT)$(PREFIX)$(BINDIR)/xtx2bib
	ln -sf crosstex $(ROOT)$(PREFIX)$(BINDIR)/xtx2html

crosstex.pdf: crosstex.tex
	pdflatex crosstex && pdflatex crosstex

.PHONY: pdf
pdf: crosstex.pdf

${PACKAGE}.tar.gz: Makefile COPYING crosstex crosstex.spec crosstex.tex crosstex.pdf
	rm -rf ${PACKAGE}
	mkdir ${PACKAGE} ${PACKAGE}/tests ${PACKAGE}/data
	cp Makefile COPYING crosstex *.py crosstex.tex crosstex.pdf ${PACKAGE}
	cp tests/*.xtx ${PACKAGE}/tests
	cp data/*.xtx ${PACKAGE}/data
	sed -e "1i %define name crosstex" \
	    -e "1i %define version ${VERSION}" \
	    -e "1i %define release ${RELEASE}" \
	    -e "1i %define prefix ${PREFIX}" \
	    -e "1i %define bindir ${BINDIR}" \
	    -e "1i %define libdir ${LIBDIR}" \
	    -e "1i %define ply ${PLY}" \
	    crosstex.spec >${PACKAGE}/crosstex.spec
	tar czf ${PACKAGE}.tar.gz ${PACKAGE}
	rm -rf ${PACKAGE}

.PHONY: dist
dist: ${PACKAGE}.tar.gz

.PHONY: rpm
rpm: dist
	mkdir -p ${PACKAGE}-rpm/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
	rpmbuild -ta --define "_topdir `pwd`/${PACKAGE}-rpm" ${PACKAGE}.tar.gz
	find ${PACKAGE}-rpm -name \*.rpm -exec mv {} . \;
	rm -r ${PACKAGE}-rpm

clean:
	rm -rf *~ *.pyc *.aux *.bbl *.dvi *.log *.tar.gz *.rpm *.html \
	       *.out *.toc *.pdf *.haux *.htoc *-rpm *.bak
