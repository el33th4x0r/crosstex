all:
	@echo nothing to make, try make install

install:
	mkdir -p /usr/share/texmf/crosstex
	cp *.py  /usr/share/texmf/crosstex
	cp *.xtx /usr/share/texmf/crosstex
	cp crosstex /usr/bin
	rm -f /usr/bin/xtx2bib
	ln -s /usr/bin/crosstex /usr/bin/xtx2bib 

clean:
	rm -f *~

