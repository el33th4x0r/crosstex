VERSION = $(shell ./crosstex --version | cut -d' ' -f2)
PACKAGE = crosstex-${VERSION}

all:
	@echo nothing to make, try make install

install:
	mkdir -p $(ROOT)/usr/bin $(ROOT)/usr/share/texmf/crosstex
	cp *.py data/*.xtx $(ROOT)/usr/share/texmf/crosstex
	cp crosstex $(ROOT)/usr/bin
	ln -sf crosstex $(ROOT)/usr/bin/xtx2bib
	ln -sf crosstex $(ROOT)/usr/bin/xtx2html

clean:
	rm -rf *~ *.pyc *.aux *.bbl *.dvi *.log *.tar.gz *.rpm *.html *.out *.toc *.pdf *.haux *.htoc *-rpm

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
	sed "/^%define version/c %define version ${VERSION}" \
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
