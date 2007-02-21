%define name crosstex
%define version # Filled in by 'make rpm'
%define release 1

Summary: CrossTeX is a modern object-oriented bibliography management tool, designed to replace BibTex.
Name: %{name}
Version: %{version}
Release: %{release}
License: GNU Public License
Group: Applications/Publishing
Packager: Emin Gun Sirer, egs at cs.cornell.edu
URL: http://www.cs.cornell.edu/people/egs/crosstex/
Source: http://www.cs.cornell.edu/people/egs/crosstex/%{name}-%{version}.tar.gz
Requires: python >= 2.0
Requires: ply >= 2.2

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch

%description 
CrossTeX is a modern object-oriented bibliography management tool,
designed to replace BibTex. It comprises a new bibliographic database
format that is much less prone to error compared to other alternatives
like BibTex, and a new tool for creating the citations that appears at
the end of scholarly texts that is very flexible.

%prep
%setup -q

%install
make ROOT=$RPM_BUILD_ROOT install

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/usr/bin/crosstex
/usr/bin/xtx2bib
/usr/bin/xtx2html
/usr/share/texmf/crosstex

%changelog
* Wed Nov 15 2006 Emin Gun Sirer <egs@systems.cs.cornell.edu> - 
- Initial build.
