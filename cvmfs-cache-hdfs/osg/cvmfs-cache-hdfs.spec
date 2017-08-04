Name: cvmfs-cache-hdfs
Version: 1.0
Release: 1%{?dist}
Summary: HDFS plugin for the CVMFS cache

Group: System Environment/Development
License: BSD
URL: https://github.com/bbockelm/cvmfs-cache-hdfs
# Generated from:
# git archive --format=tgz --prefix=%{name}-%{version}/ v%{version} > %{name}-%{version}.tar.gz
Source0: %{name}-%{version}.tar.gz
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildRequires: xrootd-server-devel >= 1:4.6
BuildRequires: cmake
BuildRequires: hadoop-libhdfs
BuildRequires: openssl-devel
BuildRequires: java7-devel
BuildRequires: jpackage-utils

# 2.3.99 was a HCC-specific version with the external cache plugin API.
BuildRequires: cvmfs-devel >= 2.3.99

Requires: hadoop-client
Requires: cvmfs >= 2.3.99

%description
%{summary}

%prep
%setup -q

%build
%cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo .
make VERBOSE=1 %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_libexecdir}/cvmfs_cache_hdfs/cvmfs_cache_hdfs_plugin
%{_libexecdir}/cvmfs_cache_hdfs/cvmfs_cache_hdfs
%config(noreplace) %{_sysconfdir}/sysconfig/cvmfs_cache_hdfs
%config %{_sysconfdir}/cvmfs/domain.d/osgstorage.org.conf

%changelog
* Thu Aug 03 2017 Brian Bockelman <bbockelm@cse.unl.edu> - 1.0-1
- Initial version of packaging.

