# 'make rpm' will fill in name, version, release, etc.

Summary: CrossTeX is a modern object-oriented bibliography management tool, designed to replace BibTex.
Name: %{name}
Version: %{version}
Release: %{release}
License: GNU Public License
Group: Applications/Publishing
Packager: Emin Gun Sirer, egs at cs.cornell.edu
URL: http://crosstex.sourceforge.net/
Source: http://downloads.sourceforge.net/crosstex/%{name}-%{version}.tar.gz
Requires: python >= 2.0
Requires: ply >= 2.2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Prefix: %{prefix}

%description 
CrossTeX is a modern object-oriented bibliography management tool,
designed to replace BibTex. It comprises a new bibliographic database
format that is much less prone to error compared to other alternatives
like BibTex, and a new tool for creating the citations that appears at
the end of scholarly texts that is very flexible.

%prep
%setup -q

%install
make ROOT=$RPM_BUILD_ROOT VERSION=%{version} RELEASE=%{release} PREFIX=%{prefix} BINDIR=%{bindir} LIBDIR=%{libdir} PLY=%{ply} MANDIR=%{mandir} install

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{prefix}%{bindir}/crosstex
%{prefix}%{bindir}/xtx2bib
%{prefix}%{bindir}/xtx2html
%{prefix}%{bindir}/bib2xtx
%{prefix}%{libdir}
%{prefix}%{mandir}/man1/crosstex.1
%{prefix}%{mandir}/man1/xtx2bib.1
%{prefix}%{mandir}/man1/xtx2html.1
%{prefix}%{mandir}/man1/bib2xtx.1

%changelog
* Wed Nov 15 2006 Emin Gun Sirer <egs@systems.cs.cornell.edu> - 
- Initial build.
