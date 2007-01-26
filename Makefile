VERSION = `cat version`
PACKAGE = crosstex-${VERSION}

all:
	@echo nothing to make, try make install

install:
	mkdir -p $(ROOT)/usr/bin $(ROOT)/usr/share/texmf/crosstex
	cp *.py data/*.xtx $(ROOT)/usr/share/texmf/crosstex
	cp crosstex $(ROOT)/usr/bin
	ln -sf crosstex $(ROOT)/usr/bin/xtx2bib

clean:
	rm -rf *~ *.pyc *.aux *.bbl *.dvi *.log *.tar.gz *.rpm ${PACKAGE}-rpm

dist: ${PACKAGE}.tar.gz

${PACKAGE}.tar.gz: Makefile COPYING version crosstex crosstex.spec
	rm -rf ${PACKAGE}
	mkdir ${PACKAGE} ${PACKAGE}/tests ${PACKAGE}/data
	cp Makefile COPYING version crosstex *.py *.xtx ${PACKAGE}
	sed "/^%define version/c %define version ${VERSION}" \
		crosstex.spec >${PACKAGE}/crosstex.spec
	cp tests/*.xtx ${PACKAGE}/tests
	cp data/*.xtx ${PACKAGE}/data
	tar czf ${PACKAGE}.tar.gz ${PACKAGE}
	rm -rf ${PACKAGE}

rpm: ${PACKAGE}.tar.gz
	mkdir -p ${PACKAGE}-rpm/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
	rpmbuild -ta --define "_topdir `pwd`/${PACKAGE}-rpm" ${PACKAGE}.tar.gz
	find ${PACKAGE}-rpm -name \*.rpm -exec mv {} . \;
	rm -r ${PACKAGE}-rpm
