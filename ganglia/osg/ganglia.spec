%global gangver     3.7.2
%global webver      3.7.1

%if 0%{?rhel} >= 7
%global systemd         1
%else
%global systemd	        0
%endif

Name:               ganglia
Version:            %{gangver}
Release:            2.20160328%{dist}
Summary:            Distributed Monitoring System
Group:              Applications/Internet
License:            BSD
URL:                http://ganglia.sourceforge.net/
Source0:            http://downloads.sourceforge.net/sourceforge/ganglia/ganglia-%{version}.tar.gz
Source1:            http://downloads.sourceforge.net/project/ganglia/ganglia-web/%{webver}/ganglia-web-%{webver}.tar.gz
Source2:            gmond.service
Source3:            gmetad.service
Source4:            ganglia-httpd24.conf.d
Source5:            ganglia-httpd.conf.d
Source6:            conf.php
Patch0:             ganglia-web-3.5.7-statedir.patch
Patch1:             ganglia-3.7.2-apache.patch
Patch2:             gmond-python-netstats-KeyError.patch
%if 0%{?systemd}
BuildRequires:      systemd
%endif
BuildRequires:      rrdtool-devel
BuildRequires:      apr-devel >= 1
BuildRequires:      libpng-devel
BuildRequires:      libart_lgpl-devel
BuildRequires:      libconfuse-devel
BuildRequires:	    libmemcached-devel
BuildRequires:      expat-devel
BuildRequires:      python-devel
BuildRequires:      freetype-devel
BuildRequires:      pcre-devel
BuildRequires:      /usr/bin/pod2man

%description
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

%package web
Summary:            Ganglia Web Frontend
Group:              Applications/Internet
Version:            %{webver}
Requires:           rrdtool
Requires:           php
Requires:           php-gd
Requires:           php-ZendFramework
Requires:           %{name}-gmetad = %{gangver}-%{release}

%description        web
This package provides a web frontend to display the XML tree published by
ganglia, and to provide historical graphs of collected metrics. This website is
written in the PHP4 language.

%package gmetad
Summary:            Ganglia Metadata collection daemon
Group:              Applications/Internet
Requires:           %{name} = %{gangver}-%{release}
%if 0%{?systemd}
Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd
%else
Requires(post):     /sbin/chkconfig
Requires(preun):    /sbin/chkconfig
Requires(preun):    /sbin/service
%endif #systemd

%description        gmetad
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

This gmetad daemon aggregates monitoring data from several clusters
to form a monitoring grid. It also keeps metric history using rrdtool.

%package            gmond
Summary:            Ganglia Monitoring daemon
Group:              Applications/Internet
Requires:           %{name} = %{gangver}-%{release}
%if 0%{?systemd}
Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd
%else
Requires(post):     /sbin/chkconfig
Requires(preun):    /sbin/chkconfig
Requires(preun):    /sbin/service
%endif #systemd

%description        gmond
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

This gmond daemon provides the ganglia service within a single cluster or
Multicast domain.

%package            gmond-python
Summary:            Ganglia Monitor daemon python DSO and metric modules
Group:              Applications/Internet
Requires:           ganglia-gmond
Requires:           python

%description        gmond-python
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

This package provides the gmond python DSO and python gmond modules, which
can be loaded via the DSO at gmond daemon start time.

%package            devel
Summary:            Ganglia Library
Group:              Applications/Internet
Requires:           %{name} = %{gangver}-%{release}

%description        devel
The Ganglia Monitoring Core library provides a set of functions that
programmers can use to build scalable cluster or grid applications

%prep
%setup -q

%if 0%{?systemd}
# fix broken systemd support
install -m 0644 %{SOURCE2} gmond/gmond.service.in
install -m 0644 %{SOURCE3} gmetad/gmetad.service.in
%endif

# web part
%setup -q -T -D -a 1
%patch1 -p0
%patch2 -p1
mv ganglia-web-%{webver} web
cd web
%patch0 -p1

%build
%configure \
    --enable-setuid=ganglia \
    --enable-setgid=ganglia \
    --with-gmetad \
%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
    --with-memcached \
%endif
    --disable-static \
    --enable-shared \
    --sysconfdir=%{_sysconfdir}/ganglia

# Remove rpaths
%{__sed} -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
%{__sed} -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

## Default to run as user ganglia instead of nobody
%{__perl} -pi.orig -e 's|nobody|ganglia|g' \
    gmond/gmond.conf.html ganglia.html gmond/conf.pod

%{__perl} -pi.orig -e 's|.*setuid_username.*|setuid_username ganglia|' \
    gmetad/gmetad.conf.in

## Don't have initscripts turn daemons on by default
%{__perl} -pi.orig -e 's|2345|-|g' gmond/gmond.init gmetad/gmetad.init

make %{?_smp_mflags}

%install
make install DESTDIR=$RPM_BUILD_ROOT

## Create directory structures
mkdir -p $RPM_BUILD_ROOT%{_libdir}/ganglia/python_modules
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/{rrds,conf}
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/dwoo/{cache,compiled}

## Install services
%if 0%{?systemd}
install -Dp -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/gmond.service
install -Dp -m 0644 %{SOURCE3} %{buildroot}%{_unitdir}/gmetad.service
%else
install -Dp -m 0755 gmond/gmond.init $RPM_BUILD_ROOT%{_sysconfdir}/init.d/gmond
install -Dp -m 0755 gmetad/gmetad.init $RPM_BUILD_ROOT%{_sysconfdir}/init.d/gmetad
%endif # systemd

## Build default gmond.conf from gmond using the '-t' flag
LD_LIBRARY_PATH=lib/.libs gmond/gmond -t | %{__perl} -pe 's|nobody|ganglia|g' \
    > $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/gmond.conf

## Python bits
# Copy the python metric modules and .conf files
cp -p gmond/python_modules/conf.d/*.pyconf $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/
cp -p gmond/modules/conf.d/*.conf $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/
cp -p gmond/python_modules/*/*.py $RPM_BUILD_ROOT%{_libdir}/ganglia/python_modules/

## Web bits
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/%{name}
cp -rp web/* $RPM_BUILD_ROOT%{_datadir}/%{name}/
install -p -m 0644 %{SOURCE6} %{buildroot}%{_sysconfdir}/ganglia/conf.php
ln -s ../../..%{_sysconfdir}/%{name}/conf.php \
    $RPM_BUILD_ROOT%{_datadir}/%{name}/conf.php

%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
install -Dp -m 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/httpd/conf.d/%{name}.conf
%else
install -Dp -m 0644 %{SOURCE5} %{buildroot}%{_sysconfdir}/httpd/conf.d/%{name}.conf
%endif

## Various clean up after install:

## Don't install the status modules and example.conf
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/{modgstatus,example}.conf

## Disable the diskusage module until it is configured properly
## mv $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/diskusage.pyconf \
##   $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/diskusage.pyconf.off

## Remove unwanted files from web dir
rm -rf $RPM_BUILD_ROOT%{_datadir}/%{name}/{Makefile*,debian,ganglia-web.spec*,ganglia-web}
rm -rf $RPM_BUILD_ROOT%{_datadir}/%{name}/{conf_default.php.in,version.php.in}

## Included as doc
rm -rf $RPM_BUILD_ROOT%{_datadir}/%{name}/{README,TODO,AUTHORS,COPYING}

## House cleaning
rm -f $RPM_BUILD_ROOT%{_libdir}/*.la

## Use system php-ZendFramework
rm -rf $RPM_BUILD_ROOT/usr/share/ganglia/lib/Zend
ln -s /usr/share/php/Zend $RPM_BUILD_ROOT/usr/share/ganglia/lib/Zend

# Remove execute bit
chmod 0644 $RPM_BUILD_ROOT%{_datadir}/%{name}/header.php
chmod 0644 $RPM_BUILD_ROOT%{_libdir}/%{name}/python_modules/*.py
chmod 0644 $RPM_BUILD_ROOT%{_datadir}/%{name}/css/smoothness/jquery-ui-1.10.2.custom.css
chmod 0644 $RPM_BUILD_ROOT%{_datadir}/%{name}/css/smoothness/jquery-ui-1.10.2.custom.min.css

# Remove shebang
sed -i '1{\@^#!@d}' $RPM_BUILD_ROOT%{_libdir}/%{name}/python_modules/*.py

%pre
## Add the "ganglia" user
/usr/sbin/useradd -c "Ganglia Monitoring System" \
        -s /sbin/nologin -r -d %{_localstatedir}/lib/%{name} ganglia 2> /dev/null || :
/sbin/ldconfig

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%if 0%{?systemd}
%post gmond
%systemd_post gmond.service

%preun gmond
%systemd_preun gmond.service

%postun gmond
%systemd_postun_with_restart gmond.service

%post gmetad
%systemd_post gmetad.service

%preun gmetad
%systemd_preun gmetad.service

%postun gmetad
%systemd_postun_with_restart gmetad.service

%else 

%post gmond
/sbin/chkconfig --add gmond

%post gmetad
/sbin/chkconfig --add gmetad

%preun gmetad
if [ "$1" = 0 ]; then
  /sbin/service gmetad stop >/dev/null 2>&1 || :
  /sbin/chkconfig --del gmetad
fi

%preun gmond
if [ "$1" = 0 ]; then
  /sbin/service gmond stop >/dev/null 2>&1 || :
  /sbin/chkconfig --del gmond
fi

%endif # systemd

%post devel -p /sbin/ldconfig
%postun devel -p /sbin/ldconfig

%post web
if [ ! -L /usr/share/ganglia/lib/Zend ]; then
  ln -s /usr/share/php/Zend /usr/share/ganglia/lib/Zend
fi

%files
%doc AUTHORS COPYING NEWS README ChangeLog
%{_libdir}/libganglia*.so.*
%dir %{_libdir}/ganglia
%{_libdir}/ganglia/*.so
%exclude %{_libdir}/ganglia/modpython.so

%files gmetad
%dir %{_localstatedir}/lib/%{name}
%attr(0755,ganglia,ganglia) %{_localstatedir}/lib/%{name}/rrds
%{_sbindir}/gmetad
%if 0%{?systemd}
%{_unitdir}/gmetad.service
%else
%{_sysconfdir}/init.d/gmetad
%endif
%{_mandir}/man1/gmetad.1*
%{_mandir}/man1/gmetad.py.1*
%dir %{_sysconfdir}/ganglia
%config(noreplace) %{_sysconfdir}/ganglia/gmetad.conf

%files gmond
%{_bindir}/gmetric
%{_bindir}/gstat
%{_sbindir}/gmond
%if 0%{?systemd}
%{_unitdir}/gmond.service
%else
%{_sysconfdir}/init.d/gmond
%endif
%{_mandir}/man5/gmond.conf.5*
%{_mandir}/man1/gmond.1*
%{_mandir}/man1/gstat.1*
%{_mandir}/man1/gmetric.1*
%dir %{_sysconfdir}/ganglia
%dir %{_sysconfdir}/ganglia/conf.d
%config(noreplace) %{_sysconfdir}/ganglia/gmond.conf
%config(noreplace) %{_sysconfdir}/ganglia/conf.d/*.conf
%exclude %{_sysconfdir}/ganglia/conf.d/modpython.conf

%files gmond-python
%dir %{_libdir}/ganglia/python_modules/
%{_libdir}/ganglia/python_modules/*.py*
%{_libdir}/ganglia/modpython.so*
%config(noreplace) %{_sysconfdir}/ganglia/conf.d/*.pyconf*
%config(noreplace) %{_sysconfdir}/ganglia/conf.d/modpython.conf

%files devel
%{_bindir}/ganglia-config
%{_includedir}/*.h
%{_libdir}/libganglia*.so

%files web
%doc web/AUTHORS web/COPYING web/README web/TODO
%config(noreplace) %{_sysconfdir}/%{name}/conf.php
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%{_datadir}/%{name}
%dir %attr(0755,apache,apache) %{_localstatedir}/lib/%{name}/conf
%dir %attr(0755,apache,apache) %{_localstatedir}/lib/%{name}/dwoo
%dir %attr(0755,apache,apache) %{_localstatedir}/lib/%{name}/dwoo/cache
%dir %attr(0755,apache,apache) %{_localstatedir}/lib/%{name}/dwoo/compiled

%changelog
* Mon Mar 28 2016 John Thiltges <jthiltges2@unl.edu> 3.7.2-2.20160328
- Avoid KeyError for new metric groups (ba7c26f5b7)

* Mon Oct 12 2015 Nick Le Mouton <nick@noodles.net.nz> - 3.7.2-2
- ganglia-web 3.7.1

* Wed Aug 19 2015 Nick Le Mouton <nick@noodles.net.nz> - 3.7.2-1
- ganglia 3.7.2
- fix for apache 2.4.16

* Wed Jun 10 2015 Nick Le Mouton <nick@noodles.net.nz> - 3.7.1-3
- ganglia-web 3.7.0
- Re-added memcache support

* Tue Apr 21 2015 Nick Le Mouton <nick@noodles.net.nz> - 3.7.1-1
- Merged from f23 to bring ganglia up to date 
- Removed memcache support (libmemcached on el5 and el6 not up-to-date enough)

* Sun Jul 15 2012 Kostas Georgiou <georgiou@fedoraproject.org> - 3.1.7-6
- Backport of security patch for gangliabz#333

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.7-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Jun 14 2011 Kostas Georgiou <georgiou@fedoraproject.org> - 3.1.7-4
- Fix buffer overflow in moddisk.so #689483

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.7-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sat Jul 31 2010 Thomas Spura <tomspur@fedoraproject.org> - 3.1.7-2
- Rebuild for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Thu Apr 22 2010 Kostas Georgiou <georgiou@fedoraproject.org> - 3.1.7-1
- New upstream release
- Spec file cleanups
- Use the new name_match feature to enable the diskusage plugin by default

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Sun Mar 29 2009 Kostas Georgiou <k.georgiou@imperial.ac.uk> - 3.1.2-3
- Rebuilt for #492703, no obvious reasons why the previous build was bad :(

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Feb 17 2009 Kostas Georgiou <k.georgiou@imperial.ac.uk> - 3.1.2-1
- Update to 3.1.2
- Remove unneeded patch for CVE-2009-0241

* Tue Jan 20 2009 Kostas Georgiou <k.georgiou@imperial.ac.uk> - 3.1.1-4
- [480236] Updated patch for the buffer overflow from upstream with
  additional fixes

* Wed Jan 14 2009 Kostas Georgiou <k.georgiou@imperial.ac.uk> - 3.1.1-3
- Fix for gmetad server buffer overflow
- The private_clusters file should not be readable by everyone

* Sun Nov 30 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 3.1.1-2
- Rebuild for Python 2.6

* Fri Oct 24 2008 Jarod Wilson <jarod@redhat.com> 3.1.1-1
- Update to 3.1.1

* Thu Aug 28 2008 Michael Schwendt <mschwendt@fedoraproject.org> 3.1.0-2
- Include unowned directories.

* Mon Aug 11 2008 Kostas Georgiou <k.georgiou@imperial.ac.uk> 3.1.0-1
- Upstream patches from 3.1.1
- Move private_clusters config to /etc and mark it as a config file
- Only allow connections from localhost by default on the web frontend
- Add some extra module config files (modules are always loaded at the
  moment so removing the configs has no effect beyond metric collection
  (upstream is working on way way to disable module loading from the
  configs)

* Tue Jul 29 2008 Kostas Georgiou <k.georgiou@imperial.ac.uk> 3.1.0-0.5
- Add the config files for the python module

* Thu Jul 17 2008 Kostas Georgiou <k.georgiou@imperial.ac.uk> 3.1.0-0.4
- Update to the 3.1.0 pre-release
- Fixes gmond.conf to use the ganglia user and not nobody
- Removal of the ppc64 work-around
 
* Fri Jun 13 2008 Jarod Wilson <jwilson@redhat.com> 3.1.0-0.3.r1399
- One more try at work-around. Needs powerpc64, not ppc64...

* Fri Jun 13 2008 Jarod Wilson <jwilson@redhat.com> 3.1.0-0.2.r1399
- Work-around for incorrectly hard-coded libdir on ppc64

* Wed Jun 11 2008 Jarod Wilson <jwilson@redhat.com> 3.1.0-0.1.r1399
- Update to 3.1.x pre-release snapshot, svn rev 1399

* Mon Jun 09 2008 Jarod Wilson <jwilson@redhat.com> 3.0.7-2
- Bump and rebuild against latest rrdtool

* Wed Feb 27 2008 Jarod Wilson <jwilson@redhat.com> 3.0.7-1
- New upstream release
- Fixes "Show Hosts" toggle
- Fixes to host view metric graphs
- Fixes two memory leaks

* Thu Feb 14 2008 Jarod Wilson <jwilson@redhat.com> 3.0.6-2
- Bump and rebuild with gcc 4.3

* Mon Dec 17 2007 Jarod Wilson <jwilson@redhat.com> 3.0.6-1
- New upstream release (security fix for web frontend
  cross-scripting vulnerability) {CVE-2007-6465}

* Wed Oct 24 2007 Jarod Wilson <jwilson@redhat.com> 3.0.5-2
- Reorg packages to fix multilib conflicts (#341201)

* Wed Oct 03 2007 Jarod Wilson <jwilson@redhat.com> 3.0.5-1
- New upstream release

* Fri May 18 2007 Jarod Wilson <jwilson@redhat.com> 3.0.4-3
- Add missing Req: php-gd so people will see nifty pie charts

* Sat Mar 24 2007 Jarod Wilson <jwilson@redhat.com> 3.0.4-2
- Own created directories (#233790)

* Tue Jan 02 2007 Jarod Wilson <jwilson@redhat.com> 3.0.4-1
- New upstream release

* Thu Nov 09 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-11
- gmond also needs ganglia user (#214762)

* Tue Sep 05 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-10
- Rebuild for new glibc

* Fri Jul 28 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-9
- Add missing Reqs on chkconfig and service
- Make %%preun sections match Fedora Extras standards
- Minor %%configure tweak

* Tue Jul 11 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-8
- Add missing php req for ganglia-web
- Misc tiny spec cleanups

* Tue Jun 13 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-7
- Clean up documentation

* Mon Jun 12 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-6
- Remove misplaced execute perms on source files

* Thu Jun 08 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-5
- Whack Obsoletes/Provides, since its never been in FE before
- Use mandir macro
- Check if service is running before issuing a stop in postun
- Remove shadow-utils Prereq, its on the FE exception list

* Mon Jun 05 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-4
- Run things as user ganglia instead of nobody
- Don't turn on daemons by default

* Mon Jun 05 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-3
- Kill off static libs
- Add URL for Source0

* Mon Jun 05 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-2
- Move web-frontend from /var/www/html/ to /usr/share/
- Make everything arch-specific

* Thu Jun 01 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-1
- Initial build for Fedora Extras, converting existing spec to
  (attempt to) conform with Fedora packaging guidelines
