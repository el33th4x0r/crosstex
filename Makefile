VERSION=`cat version`

all:
	@echo nothing to make, try make install

install: plyinstall
	mkdir -p /usr/share/texmf/crosstex
	cp *.py  /usr/share/texmf/crosstex
	cp *.xtx /usr/share/texmf/crosstex
	cp crosstex /usr/bin
	rm -f /usr/bin/xtx2bib
	ln -s /usr/bin/crosstex /usr/bin/xtx2bib 

plyinstall:
	cd ply-* && python ./setup.py install

clean:
	rm -f *~

rpm:
	cd .. && tar czf crosstex-$(VERSION).tar.gz crosstex
	cp ../crosstex-$(VERSION).tar.gz /usr/src/redhat/SOURCES
	sudo cp crosstexrpm.spec /usr/src/redhat/SPECS/crosstexrpm-$(VERSION).spec
	sudo rpmbuild -ba /usr/src/redhat/SPECS/crosstexrpm-$(VERSION).spec



