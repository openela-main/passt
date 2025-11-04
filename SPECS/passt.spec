# PASST - Plug A Simple Socket Transport
#  for qemu/UNIX domain socket mode
#
# PASTA - Pack A Subtle Tap Abstraction
#  for network namespace/tap device mode
#
# Copyright (c) 2022 Red Hat GmbH
# Author: Stefano Brivio <sbrivio@redhat.com>

%global git_hash a1e48a02ff3550eb7875a7df6726086e9b3a1213
%global selinuxtype targeted

Name:		passt
Version:	0^20250217.ga1e48a0
Release:	7%{?dist}
Summary:	User-mode networking daemons for virtual machines and namespaces
License:	GPL-2.0-or-later AND BSD-3-Clause
Group:		System Environment/Daemons
URL:		https://passt.top/
Source:		https://passt.top/passt/snapshot/passt-%{git_hash}.tar.xz

Patch2:		0002-migrate-flow-Trivially-succeed-if-migrating-with-no-.patch
Patch3:		0003-migrate-flow-Don-t-attempt-to-migrate-TCP-flows-with.patch
Patch4:		0004-tcp-Correct-error-code-handling-from-tcp_flow_repair.patch
Patch5:		0005-tcp-Unconditionally-move-to-CLOSED-state-on-tcp_rst.patch
Patch6:		0006-migrate-tcp-Don-t-flow_alloc_cancel-during-incoming-.patch
Patch7:		0007-ip-Helpers-to-access-IPv6-flow-label.patch
Patch8:		0008-tap-Consider-IPv6-flow-label-when-building-packet-se.patch
Patch9:		0009-tcp-Send-RST-in-response-to-guest-packets-that-match.patch
Patch10:	0010-selinux-Fixes-workarounds-for-passt-and-passt-repair.patch
Patch11:	0011-passt-repair-Add-directory-watch.patch
Patch12:	0012-flow-repair-Wait-for-a-short-while-for-passt-repair-.patch
Patch13:	0013-passt-repair-Fix-build-with-Werror-format-security.patch
Patch14:        0014-migrate-tcp-More-careful-marshalling-of-mss-paramete.patch
Patch15:        0015-flow-Add-flow_perror-helper.patch
Patch16:        0016-migrate-tcp-Migrate-RFC-7323-timestamp.patch
Patch17:        0017-migrate-Bump-migration-version-number.patch
Patch18:	0018-tcp-Flush-socket-before-checking-for-more-data-in-ac.patch
Patch19:	0019-pasta-passt-repair-Support-multiple-events-per-read-.patch
Patch20:	0020-migrate-tcp-bind-migrated-sockets-in-repair-mode.patch
Patch21:	0021-passt-repair-Correct-off-by-one-error-verifying-name.patch
Patch22:	0022-passt-repair-Ensure-that-read-buffer-is-NULL-termina.patch
Patch23:	0023-tcp_splice-Don-t-double-count-bytes-read-on-EINTR.patch
Patch24:	0024-tcp_splice-Don-t-clobber-errno-before-checking-for-E.patch
Patch25:	0025-tcp-Cast-operands-of-sequence-comparison-macros-to-u.patch
Patch26:	0026-tcp-Don-t-consider-FIN-flags-with-mismatching-sequen.patch

BuildRequires:	gcc, make, git, checkpolicy, selinux-policy-devel
Requires:	(%{name}-selinux = %{version}-%{release} if selinux-policy-%{selinuxtype})

%description
passt implements a translation layer between a Layer-2 network interface and
native Layer-4 sockets (TCP, UDP, ICMP/ICMPv6 echo) on a host. It doesn't
require any capabilities or privileges, and it can be used as a simple
replacement for Slirp.

pasta (same binary as passt, different command) offers equivalent functionality,
for network namespaces: traffic is forwarded using a tap interface inside the
namespace, without the need to create further interfaces on the host, hence not
requiring any capabilities or privileges.

%package    selinux
BuildArch:  noarch
Summary:    SELinux support for passt and pasta
Requires:   %{name} = %{version}-%{release}
Requires:   selinux-policy
Requires(post): %{name}
Requires(post): policycoreutils
Requires(preun): %{name}
Requires(preun): policycoreutils

%description selinux
This package adds SELinux enforcement to passt(1), pasta(1), passt-repair(1).

%prep
%autosetup -S git_am -n passt-%{git_hash}

%build
%set_build_flags
# The Makefile creates symbolic links for pasta, but we need actual copies for
# SELinux file contexts to work as intended. Same with pasta.avx2 if present.
# Build twice, changing the version string, to avoid duplicate Build-IDs.
%make_build VERSION="%{version}-%{release}.%{_arch}-pasta"
mv -f passt pasta
%ifarch x86_64
mv -f passt.avx2 pasta.avx2
%make_build passt passt.avx2 VERSION="%{version}-%{release}.%{_arch}"
%else
%make_build passt VERSION="%{version}-%{release}.%{_arch}"
%endif

%install
# Already built (not as symbolic links), see above
touch pasta
%ifarch x86_64
touch pasta.avx2
%endif

%make_install DESTDIR=%{buildroot} prefix=%{_prefix} bindir=%{_bindir} mandir=%{_mandir} docdir=%{_docdir}/%{name}
%ifarch x86_64
ln -sr %{buildroot}%{_mandir}/man1/passt.1 %{buildroot}%{_mandir}/man1/passt.avx2.1
ln -sr %{buildroot}%{_mandir}/man1/pasta.1 %{buildroot}%{_mandir}/man1/pasta.avx2.1
install -p -m 755 %{buildroot}%{_bindir}/passt.avx2 %{buildroot}%{_bindir}/pasta.avx2
%endif

pushd contrib/selinux
make -f %{_datadir}/selinux/devel/Makefile
install -p -m 644 -D passt.pp %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/passt.pp
install -p -m 644 -D passt.if %{buildroot}%{_datadir}/selinux/devel/include/distributed/passt.if
install -p -m 644 -D pasta.pp %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/pasta.pp
install -p -m 644 -D passt-repair.pp %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/passt-repair.pp
popd

%pre selinux
%selinux_relabel_pre -s %{selinuxtype}

%post selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/passt.pp
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/pasta.pp
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/passt-repair.pp

%postun selinux
if [ $1 -eq 0 ]; then
	%selinux_modules_uninstall -s %{selinuxtype} passt
	%selinux_modules_uninstall -s %{selinuxtype} pasta
	%selinux_modules_uninstall -s %{selinuxtype} passt-repair
fi

%posttrans selinux
%selinux_relabel_post -s %{selinuxtype}

%files
%license LICENSES/{GPL-2.0-or-later.txt,BSD-3-Clause.txt}
%dir %{_docdir}/%{name}
%doc %{_docdir}/%{name}/README.md
%doc %{_docdir}/%{name}/demo.sh
%{_bindir}/passt
%{_bindir}/pasta
%{_bindir}/qrap
%{_bindir}/passt-repair
%{_mandir}/man1/passt.1*
%{_mandir}/man1/pasta.1*
%{_mandir}/man1/qrap.1*
%{_mandir}/man1/passt-repair.1*
%ifarch x86_64
%{_bindir}/passt.avx2
%{_mandir}/man1/passt.avx2.1*
%{_bindir}/pasta.avx2
%{_mandir}/man1/pasta.avx2.1*
%endif

%files selinux
%{_datadir}/selinux/packages/%{selinuxtype}/passt.pp
%{_datadir}/selinux/devel/include/distributed/passt.if
%{_datadir}/selinux/packages/%{selinuxtype}/pasta.pp
%{_datadir}/selinux/packages/%{selinuxtype}/passt-repair.pp

%changelog
* Thu Oct 23 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250217.ga1e48a0-7
- Resolves: RHEL-123414 RHEL-123421

* Thu Apr 10 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250217.ga1e48a0-5
- Resolves: RHEL-83979 RHEL-84157 RHEL-86761

* Thu Mar 20 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250217.ga1e48a0-4
- Resolves: RHEL-84249 RHEL-83979 RHEL-84157 RHEL-84248

* Fri Feb 28 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250217.ga1e48a0-3
- Resolves: RHEL-80297

* Wed Feb 26 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250217.ga1e48a0-2
- Resolves: RHEL-80297

* Mon Feb 17 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250217.ga1e48a0-1
- Resolves: RHEL-79788

* Wed Jan 22 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250121.g4f2c8e7-3
- Resolves: RHEL-75657

* Tue Jan 21 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250121.g4f2c8e7-1
- Resolves: RHEL-75657

* Thu Nov 21 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20241121.g238c69f-1
- Resolves: RHEL-67556

* Tue Oct 29 2024 Troy Dawson <tdawson@redhat.com> - 0^20240806.gee36266-3
- Bump release for October 2024 mass rebuild:
  Resolves: RHEL-64018

* Wed Aug 14 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20240806-gee36266-2
- Resolves: RHEL-54269

* Wed Aug  7 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20240806.gee36266-1
- Resolves: RHEL-53190

* Fri Aug  2 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20240726.g57a21d2-1
- Resolves: RHEL-52639

* Mon Jun 24 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20240624.g1ee2eca-1
- Resolves: RHEL-44838

* Mon Jun 24 2024 Troy Dawson <tdawson@redhat.com> - 0^20240523.g765eb0b-2
- Bump release for June 2024 mass rebuild

* Thu May 23 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20240523.g765eb0b-1
- Resolves: RHEL-36045

* Wed May 22 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20240510.g7288448-1
- Resolves: RHEL-37647

* Thu Jan 25 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0^20231230.gf091893-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sun Jan 21 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0^20231230.gf091893-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sat Dec 30 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20231230.gf091893-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_12_04.b86afe3..2023_12_30.f091893

* Mon Dec  4 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20231204.gb86afe3-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_11_19.4f1709d..2023_12_04.b86afe3

* Sun Nov 19 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20231119.g4f1709d-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_11_10.5ec3634..2023_11_19.4f1709d

* Fri Nov 10 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20231110.g5ec3634-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_11_07.74e6f48..2023_11_10.5ec3634

* Tue Nov  7 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20231107.g56d9f6d-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_10_04.f851084..2023_11_07.56d9f6d
- SELinux: allow passt_t to use unconfined_t UNIX domain sockets for
  --fd option (https://bugzilla.redhat.com/show_bug.cgi?id=2247221)

* Wed Oct  4 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20231004.gf851084-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_09_08.05627dc..2023_10_04.f851084

* Fri Sep  8 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230908.g05627dc-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_09_07.ee58f37..2023_09_08.05627dc

* Thu Sep  7 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230907.gee58f37-1
- Replace pasta hard links by separate builds
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_08_23.a7e4bfb..2023_09_07.ee58f37

* Wed Aug 23 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230823.ga7e4bfb-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_08_18.0af928e..2023_08_23.a7e4bfb

* Fri Aug 18 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230818.g0af928e-1
- Install pasta as hard link to ensure SELinux file context match
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_06_27.289301b..2023_08_18.0af928e

* Thu Jul 20 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0^20230627.g289301b-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Tue Jun 27 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230627.g289301b-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_06_25.32660ce..2023_06_27.289301b

* Sun Jun 25 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230625.g32660ce-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_06_03.429e1a7..2023_06_25.32660ce

* Sat Jun  3 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230603.g429e1a7-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_05_09.96f8d55..2023_06_03.429e1a7

* Tue May  9 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230509.g96f8d55-1
- Relicense to GPL 2.0, or any later version
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_03_29.b10b983..2023_05_09.96f8d55

* Wed Mar 29 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230329.gb10b983-1
- Adjust path for SELinux policy and interface file to latest guidelines
- Don't install useless SELinux interface file for pasta
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_03_21.1ee2f7c..2023_03_29.b10b983

* Tue Mar 21 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230321.g1ee2f7c-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_03_17.dd23496..2023_03_21.1ee2f7c

* Fri Mar 17 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230317.gdd23496-1
- Refresh SELinux labels in scriptlets, require -selinux package
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_03_10.70c0765..2023_03_17.dd23496

* Fri Mar 10 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230310.g70c0765-1
- Install SELinux interface files to shared include directory
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_03_09.7c7625d..2023_03_10.70c0765

* Thu Mar  9 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230309.g7c7625d-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_02_27.c538ee8..2023_03_09.7c7625d

* Mon Feb 27 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230227.gc538ee8-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_02_22.4ddbcb9..2023_02_27.c538ee8

* Wed Feb 22 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230222.g4ddbcb9-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2023_02_16.4663ccc..2023_02_22.4ddbcb9

* Thu Feb 16 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230216.g4663ccc-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_11_16.ace074c..2023_02_16.4663ccc

* Thu Jan 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0^20221116.gace074c-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Wed Nov 16 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20221116.gace074c-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_11_10.4129764..2022_11_16.ace074c

* Thu Nov 10 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20221110.g4129764-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_11_04.e308018..2022_11_10.4129764

* Fri Nov  4 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20221104.ge308018-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_10_26.f212044..2022_11_04.e308018

* Wed Oct 26 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20221026.gf212044-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_10_26.e4df8b0..2022_10_26.f212044

* Wed Oct 26 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20221026.ge4df8b0-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_10_24.c11277b..2022_10_26.e4df8b0

* Mon Oct 24 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20221024.gc11277b-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_10_22.b68da10..2022_10_24.c11277b

* Sat Oct 22 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20221022.gb68da10-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_10_15.b3f3591..2022_10_22.b68da10

* Sat Oct 15 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20221015.gb3f3591-1
- Add versioning information
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_09_29.06aa26f..2022_10_15.b3f3591

* Thu Sep 29 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220929.g06aa26f-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_09_24.8978f65..2022_09_29.06aa26f

* Sat Sep 24 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220924.g8978f65-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_09_23.d6f865a..2022_09_24.8978f65

* Fri Sep 23 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220923.gd6f865a-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_09_06.e2cae8f..2022_09_23.d6f865a

* Wed Sep  7 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220907.ge2cae8f-1
- Escape %% characters in spec file's changelog
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_09_01.7ce9fd1..2022_09_06.e2cae8f

* Fri Sep  2 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220902.g7ce9fd1-1
- Add selinux-policy Requires: tag
- Add %%dir entries for own SELinux policy directory and documentation
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_08_29.0cb795e..2022_09_01.7ce9fd1

* Tue Aug 30 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220830.g0cb795e-1
- Pass explicit bindir, mandir, docdir, and drop OpenSUSE override
- Use full versioning for SELinux subpackage Requires: tag
- Define git_hash in spec file and reuse it
- Drop comment stating the spec file is an example file
- Drop SPDX identifier from spec file
- Adopt versioning guideline for snapshots
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_08_24.60ffc5b..2022_08_29.0cb795e

* Wed Aug 24 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220824.g60ffc5b-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_08_21.7b71094..2022_08_24.60ffc5b

* Sun Aug 21 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220821.g7b71094-1
- Use more GNU-style directory variables, explicit docdir for OpenSUSE
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_08_20.f233d6c..2022_08_21.7b71094

* Sat Aug 20 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220820.gf233d6c-1
- Fix man pages wildcards in spec file
- Don't hardcode CFLAGS setting, use %%set_build_flags macro instead
- Build SELinux subpackage as noarch
- Change source URL to HEAD link with explicit commit SHA
- Drop VCS tag from spec file
- Start Release tag from 1, not 0
- Introduce own rpkg macro for changelog
- Install "plain" README, instead of web version, and demo script
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_08_04.b516d15..2022_08_20.f233d6c

* Mon Aug  1 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220801.gb516d15-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_07_20.9af2e5d..2022_08_04.b516d15

* Wed Jul 20 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220720.g9af2e5d-1
- Upstream changes: https://passt.top/passt/log/?qt=range&q=2022_07_14.b86cd00..2022_07_20.9af2e5d

* Thu Jul 14 2022 Stefano Brivio <sbrivio@redhat.com> - 0^20220714.gb86cd00-1
- Use pre-processing macros in spec file
- Drop dashes from version
- Add example spec file for Fedora
- Upstream changes: https://passt.top/passt/log/?qt=range&q=e653f9b3ed1b60037e3bc661d53b3f9407243fc2..2022_07_14.b86cd00
