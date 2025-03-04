# Building from fedora dependencies not possible
# Latest upstream rtnetlink frequently required
# sha2, zbus, zvariant are currently out of date

# RHEL doesn't include the package rust-packaging which provides %%__cargo macro, but EPEL
# does. So we set it separately here and skip rust-packaging dependency for RHEL.
# Buildability without EPEL is essential for packit builds.
# ELN doesn't need this.
%if %{defined rhel} && 0%{?rhel} < 10
%define __cargo %{_bindir}/env CARGO_HOME=.cargo RUSTC_BOOTSTRAP=1 RUSTFLAGS='-Copt-level=3 -Cdebuginfo=2 -Ccodegen-units=1 -Clink-arg=-Wl,-z,relro -Clink-arg=-Wl,-z,now --cap-lints=warn' %{_bindir}/cargo
%endif

%global with_debug 1

%if 0%{?with_debug}
%global _find_debuginfo_dwz_opts %{nil}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package %{nil}
%endif

# Minimum X.Y dep for aardvark-dns
%define major_minor %((v=%{version}; echo ${v%.*}))

Name: netavark
# Set a different Epoch for copr builds
%if %{defined copr_username}
Epoch: 102
%else
Epoch: 0
%endif
Version: 0
Release: %autorelease
# The `AND` needs to be uppercase in the License for SPDX compatibility
License: Apache-2.0 AND BSD-3-Clause AND MIT
%if %{defined golang_arches_future}
ExclusiveArch: %{golang_arches_future}
%else
ExclusiveArch: aarch64 ppc64le s390x x86_64
%endif
Summary: OCI network stack
URL: https://github.com/containers/%{name}
# Tarballs fetched from upstream's release page
Source0: %{url}/archive/v%{version}.tar.gz
Source1: %{url}/releases/download/v%{version}/%{name}-v%{version}-vendor.tar.gz
BuildRequires: cargo
BuildRequires: %{_bindir}/go-md2man
# aardvark-dns and %%{name} are usually released in sync
Recommends: aardvark-dns >= %{epoch}:%{major_minor}
Requires: (aardvark-dns >=  %{epoch}:%{major_minor} if fedora-release-identity-server)
Provides: container-network-stack = 2
BuildRequires: make
BuildRequires: protobuf-c
BuildRequires: protobuf-compiler
%if %{defined rhel}
# rust-toolset requires the `local` repo enabled on non-koji ELN build environments
BuildRequires: rust-toolset
%else
BuildRequires: rust-packaging
BuildRequires: rust-srpm-macros
%endif
BuildRequires: git-core
BuildRequires: systemd
BuildRequires: systemd-devel

%description
%{summary}

Netavark is a rust based network stack for containers. It is being
designed to work with Podman but is also applicable for other OCI
container management applications.

Netavark is a tool for configuring networking for Linux containers.
Its features include:
* Configuration of container networks via JSON configuration file
* Creation and management of required network interfaces,
    including MACVLAN networks
* All required firewall configuration to perform NAT and port
    forwarding as required for containers
* Support for iptables and firewalld at present, with support
    for nftables planned in a future release
* Support for rootless containers
* Support for IPv4 and IPv6
* Support for container DNS resolution via aardvark-dns.

%prep
%autosetup -Sgit %{name}-%{version}
# Following steps are only required on environments like koji which have no
# network access and thus depend on the vendored tarball. Copr pulls
# dependencies directly from the network.
%if !%{defined copr_username}
tar fx %{SOURCE1}
mkdir -p .cargo

cat >.cargo/config << EOF
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "vendor"
EOF
%endif

%build
%{__make} CARGO="%{__cargo}" build

cd docs
%{__make}

%install
%{__make} DESTDIR=%{buildroot} PREFIX=%{_prefix} install

%preun
%systemd_preun %{name}-dhcp-proxy.service
%systemd_preun %{name}-firewalld-reload.service

%postun
%systemd_postun %{name}-dhcp-proxy.service
%systemd_postun %{name}-firewalld-reload.service

%files
%license LICENSE
%dir %{_libexecdir}/podman
%{_libexecdir}/podman/%{name}*
%{_mandir}/man1/%{name}.1*
%{_unitdir}/%{name}-dhcp-proxy.service
%{_unitdir}/%{name}-dhcp-proxy.socket
%{_unitdir}/%{name}-firewalld-reload.service

%changelog
%if %{defined autochangelog}
%autochangelog
%else
# NOTE: This changelog will be visible on CentOS 8 Stream builds
# Other envs are capable of handling autochangelog
* Fri Jun 16 2023 RH Container Bot <rhcontainerbot@fedoraproject.org>
- Placeholder changelog for envs that are not autochangelog-ready
- Contact upstream if you need to report an issue with the build.
%endif
