# RPM spec file for Azure CLI 2.0
# Definition of macros used - https://fedoraproject.org/wiki/Packaging:RPMMacros?rd=Packaging/RPMMacros

# .el7.centos -> .el7
%if 0%{?rhel} == 7
  %define dist .el7
%endif

%define name           azure-cli
%define release        1%{?dist}
%define version        %{getenv:CLI_VERSION}
%define source_sha256  %{getenv:CLI_DOWNLOAD_SHA256}
%define source_url     https://azurecliprod.blob.core.windows.net/releases/azure-cli_packaged_%{version}.tar.gz
%define venv_url       https://pypi.python.org/packages/source/v/virtualenv/virtualenv-15.0.0.tar.gz
%define venv_sha256    70d63fb7e949d07aeb37f6ecc94e8b60671edb15b890aa86dba5dfaf2225dc19
%define cli_lib_dir    %{_libdir}/az

Summary:        Azure CLI 2.0
License:        MIT
Name:           %{name}
Version:        %{version}
Release:        %{release}
Source0:        %{source_url}
Url:            https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
BuildArch:      x86_64
Requires:       python

BuildRequires:  gcc
BuildRequires:  python
BuildRequires:  libffi-devel
BuildRequires:  python-devel
BuildRequires:  openssl-devel

%description
A great cloud needs great tools; we're excited to introduce Azure CLI 2.0,
 our next generation multi-platform command line experience for Azure.

%prep
# Create some tmp files
tmp_venv_archive=$(mktemp)
tmp_source_archive=$(mktemp)

# Download, Extract Source
wget %{source_url} -qO $tmp_source_archive
echo "%{source_sha256}  $tmp_source_archive" | sha256sum -c -
tar -xvzf $tmp_source_archive -C %{_builddir}

# Download, Extract Virtualenv
wget %{venv_url} -qO $tmp_venv_archive
echo "%{venv_sha256}  $tmp_venv_archive" | sha256sum -c -
tar -xvzf $tmp_venv_archive -C %{_builddir}

%install
# Create the venv
python %{_builddir}/virtualenv-15.0.0/virtualenv.py --python python %{buildroot}%{cli_lib_dir}

# Build the wheels from the source
source_dir=%{_builddir}/azure-cli_packaged_%{version}
dist_dir=$(mktemp -d)
for d in $source_dir/src/azure-cli $source_dir/src/azure-cli-core $source_dir/src/azure-cli-nspkg $source_dir/src/azure-cli-command_modules-nspkg $source_dir/src/command_modules/azure-cli-*/; \
do cd $d; %{buildroot}%{cli_lib_dir}/bin/python setup.py bdist_wheel -d $dist_dir; cd -; done;

# Install the CLI
%{buildroot}%{cli_lib_dir}/bin/pip install azure-cli --find-links $dist_dir
%{buildroot}%{cli_lib_dir}/bin/pip install --force-reinstall --upgrade azure-nspkg azure-mgmt-nspkg

# Fix up %{buildroot} appearing in some files...
for d in %{buildroot}%{cli_lib_dir}/bin/*; do perl -p -i -e "s#%{buildroot}##g" $d; done;

# Create executable
mkdir -p %{buildroot}%{_bindir}
printf '#!/usr/bin/env bash\n%{cli_lib_dir}/bin/python -Esm azure.cli "$@"' > %{buildroot}%{_bindir}/az

# Set up tab completion
mkdir -p %{buildroot}%{_sysconfdir}/bash_completion.d/
cat $source_dir/az.completion > %{buildroot}%{_sysconfdir}/bash_completion.d/azure-cli

%files
%attr(-,root,root) %{cli_lib_dir}
%config(noreplace) %{_sysconfdir}/bash_completion.d/azure-cli
%attr(0755,root,root) %{_bindir}/az
