Summary: CrossTeX is a modern object-oriented bibliography management tool, designed to replace BibTex.
Name: crosstexrpm
Version: 0.1
Release: 1
License: GNU Public License
Group: 
URL: http://www.cs.cornell.edu/people/egs/crosstex/
Packager: Emin Gun Sirer, egs at cs.cornell.edu
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description 
CrossTeX is a modern object-oriented bibliography management tool,
designed to replace BibTex. It comprises a new bibliographic database
format that is much less prone to error compared to other alternatives
like BibTex, and a new tool for creating the citations that appears at
the end of scholarly texts that is very flexible.

%prep
%setup -q

%build

%install
make install

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc
/usr/bin/crosstex
/usr/bin/xtx2bib
/usr/share/texmf/crosstex/conferences.xtx
/usr/share/texmf/crosstex/crosstexobjects.py
/usr/share/texmf/crosstex/crosstexstyles.py
/usr/share/texmf/crosstex/dates.xtx
/usr/share/texmf/crosstex/journals.xtx
/usr/share/texmf/crosstex/locations.xtx
/usr/share/texmf/crosstex/workshops.xtx
/usr/share/texmf/crosstex/egs.xtx

%changelog
* Wed Nov 15 2006 Emin Gun Sirer <egs@systems.cs.cornell.edu> - 
- Initial build.

