# PASST - Plug A Simple Socket Transport
#  for qemu/UNIX domain socket mode
#
# PASTA - Pack A Subtle Tap Abstraction
#  for network namespace/tap device mode
#
# Copyright (c) 2022 Red Hat GmbH
# Author: Stefano Brivio <sbrivio@redhat.com>

%global git_hash d04c48032bcf724550d0b8f652fd00efcd2dfad0
%global selinuxtype targeted
%global selinux_policy_version 41.41

Name:		passt
Version:	0^20251210.gd04c480
Release:	5%{?dist}
Summary:	User-mode networking daemons for virtual machines and namespaces
License:	GPL-2.0-or-later AND BSD-3-Clause
Group:		System Environment/Daemons
URL:		https://passt.top/
Source:		https://passt.top/passt/snapshot/passt-%{git_hash}.tar.xz

Patch1:		0001-selinux-Drop-user_namespace-create-allow-rules.patch
Patch2:		0002-selinux-Use-systemd_logind_exec_t-instead-of-systemd.patch
Patch3:		0003-tcp-Use-less-than-MSS-window-on-no-queued-data-or-no.patch
Patch4:		0004-pasta-Warn-disable-matching-IP-version-if-not-suppor.patch
Patch5:		0005-selinux-Enable-read-and-watch-permissions-on-netns-d.patch
Patch6:		0006-selinux-Enable-open-permissions-on-netns-directory-o.patch
Patch7:		0007-tcp-Fix-rounding-issue-in-check-for-approximating-wi.patch
Patch8:		0008-udp_flow-remove-unneeded-epoll_ref-indirection.patch
Patch9:		0009-udp_flow-Assign-socket-to-flow-inside-udp_flow_sock.patch
Patch10:	0010-tcp_splice-Refactor-tcp_splice_conn_epoll_events-to-.patch
Patch11:	0011-flow-Introduce-flow_epoll_set-to-centralize-epoll-op.patch
Patch12:	0012-tcp-Properly-propagate-tap-side-RST-to-socket-side.patch
Patch13:	0013-udp-Split-activity-timeouts-for-UDP-flows.patch
Patch14:	0014-tcp-Remove-non-working-activity-timeout-mechanism.patch
Patch15:	0015-tcp-Re-introduce-inactivity-timeouts-based-on-a-cloc.patch
Patch16:	0016-tcp-Extend-tcp_send_flag-to-send-TCP-keepalive-segme.patch
Patch17:	0017-tcp-Send-TCP-keepalive-segments-after-a-period-of-ta.patch
Patch18:	0018-tcp-Replace-send-buffer-boost-with-EPOLLOUT-monitori.patch
Patch19:	0019-udp_vu-Discard-datagrams-when-RX-virtqueue-is-not-us.patch
Patch20:	0020-conf-util-Disable-IPv6-if-explicit-IPv6-socket-probe.patch

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

%package		    selinux
BuildArch:		    noarch
Summary:		    SELinux support for passt and pasta
%if 0%{?fedora} > 43
BuildRequires:      selinux-policy-devel
%selinux_requires_min
%else
BuildRequires:      pkgconfig(systemd)
Requires(post):     libselinux-utils
Requires(post):     policycoreutils
%endif
Requires:		    container-selinux
Requires:		    selinux-policy-%{selinuxtype}
Requires(post):		container-selinux
Requires(post):		selinux-policy-%{selinuxtype}

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
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/passt.pp %{_datadir}/selinux/packages/%{selinuxtype}/pasta.pp %{_datadir}/selinux/packages/%{selinuxtype}/passt-repair.pp

%postun selinux
if [ $1 -eq 0 ]; then
	%selinux_modules_uninstall -s %{selinuxtype} passt pasta passt-repair
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
* Thu Jun 11 2026 Stefano Brivio <sbrivio@redhat.com> - 0^20251210.gd04c480-5
- Resolves: RHEL-184106 RHEL-183990

* Tue Apr 21 2026 Stefano Brivio <sbrivio@redhat.com> - 0^20251210.gd04c480-4
- Resolves: RHEL-169637 RHEL-169639 RHEL-169648

* Wed Feb 11 2026 Stefano Brivio <sbrivio@redhat.com> - 0^20251210.gd04c480-3
- Resolves: RHEL-137588 RHEL-136313

* Wed Dec 24 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20251210.gd04c480-2
- Resolves: RHEL-136313 RHEL-136461 RHEL-137439 RHEL-137588

* Wed Dec 10 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20251210.gd04c480-1
- Resolves: RHEL-134942 RHEL-134943

* Tue Dec  9 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20251209.gc3f1ba7-1
- Resolves: RHEL-134119

* Thu Oct 23 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250512.g8ec1341-3
- Resolves: RHEL-123376 RHEL-123438

* Tue Jul 29 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250512.g8ec1341-2
- Resolves: RHEL-106326

* Tue May 13 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250512.g8ec1341-1
- Resolves: RHEL-84283

* Thu Mar 20 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250320.g32f6212-1
- Resolves: RHEL-84283

* Mon Feb 17 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250217.ga1e48a0-1
- Resolves: RHEL-79787

* Wed Jan 22 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250121.g4f2c8e7-3
- Resolves: RHEL-75654

* Tue Jan 21 2025 Stefano Brivio <sbrivio@redhat.com> - 0^20250121.g4f2c8e7-1
- Resolves: RHEL-75654

* Thu Nov 21 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20241121.g238c69f-1
- Resolves: RHEL-65502

* Wed Aug 14 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20240806-gee36266-2
- Resolves: RHEL-54268

* Wed Aug  7 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20240806.gee36266-1
- Resolves: RHEL-53189

* Fri Aug  2 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20240726.g57a21d2-1
- Resolves: RHEL-52638

* Mon Jun 24 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20240624.g1ee2eca-1
- Resolves: RHEL-44837

* Wed May 22 2024 Stefano Brivio <sbrivio@redhat.com> - 0^20240510.g7288448-1
- Resolves: RHEL-37647

* Fri Dec 15 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20231204.gb86afe3-1
- Resolves: RHEL-19590

* Tue Aug 22 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230818.g0af928e-4
- Switch to copies instead of links for pasta: previous workaround unreliable
- Resolves: RHELPLAN-155811

* Tue Aug 22 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230818.g0af928e-3
- Explicit restorecon in scriptlet as rpm(8) mix up contexts with hard links
- Resolves: RHELPLAN-155811

* Mon Aug 21 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230818.g0af928e-2
- Drop user_namespace create allow rule, incompatible with current el9 kernel
- Resolves: RHELPLAN-155811

* Sat Aug 19 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230818.g0af928e-1
- Rebase from Fedora 39
- Resolves: RHELPLAN-155811

* Sun Jun 11 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230222.g4ddbcb9-4
- Drop (pointless) patches 20, 21, 22, actually apply changes to the spec file!
- Refresh SELinux labels in scriptlets, require -selinux package (rhbz#2183089)
- Don't install useless SELinux interface file for pasta (rhbz#2183106)

* Fri Apr 28 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230222.g4ddbcb9-3
- Refresh SELinux labels in scriptlets, require -selinux package (rhbz#2183089)
- Don't install useless SELinux interface file for pasta (rhbz#2183106)

* Thu Mar 16 2023 Stefano Brivio <sbrivio@redhat.com> - 0^20230222.g4ddbcb9-2
- udp: Actually use host resolver to forward DNS queries (rhbz#2177075)
- conf: Split add_dns{4,6}() out of get_dns() (rhbz#2177075)
- conf, udp: Allow any loopback address to be used as resolver (rhbz#2177075)
- tcp, tcp_splice: Get rid of false positive CWE-394 Coverity warning from fls() (rhbz#2177084)
- tcp: Avoid false (but convoluted) positive Coverity CWE-476 warning (rhbz#2177084)
- tcp: Avoid (theoretical) resource leak (CWE-772) Coverity warning (rhbz#2177084)
- Fix definitions of SOCKET_MAX, TCP_MAX_CONNS (rhbz#2177084)
- doc/demo: Fix and suppress ShellCheck warnings (rhbz#2177084)
- contrib/selinux: Drop duplicate init_daemon_domain() rule (rhbz#2176813)
- contrib/selinux: Let passt write to stdout and stderr when it starts (rhbz#2176813)
- contrib/selinux: Allow binding and connecting to all UDP and TCP ports (rhbz#2176813)
- contrib/selinux: Let interface users set paths for log, PID, socket files (rhbz#2176813)
- contrib/selinux: Drop "example" from headers: this is the actual policy (rhbz#2176813)
- contrib/selinux: Drop unused passt_read_data() interface (rhbz#2176813)
- contrib/selinux: Split interfaces into smaller bits (rhbz#2176813)
- fedora: Install SELinux interface files to shared include directory (rhbz#2176813)
- tcp, udp, util: Pass socket creation errors all the way up (rhbz#2177080)
- tcp, udp: Fix partial success return codes in {tcp,udp}_sock_init() (rhbz#2177080)
- conf: Terminate on EMFILE or ENFILE on sockets for port mapping (rhbz#2177080)
- tcp: Clamp MSS value when queueing data to tap, also for pasta (rhbz#2177083)
- Fix up SELinux labels on install/uninstall, require matching -selinux package (rhbz#2176813)
- Resolves: rhbz#2177075 rhbz#2177084 rhbz#2177080 rhbz#2177083 rhbz#2176813

* Wed Feb 22 2023 Camilla Conte <cconte@redhat.com> - 0^20230222.g4ddbcb9-1
- Import from fedora to CentOS/RHEL
- Resolves: rhbz#2172244

* Wed Nov 16 2022 Miroslav Rezanina <mrezanin@redhat.com> - 0^20221110.g4129764-1
- Import from fedora to CentOS/RHEL
- Resolves: rhbz#2131015

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
