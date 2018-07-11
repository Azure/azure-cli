# RPM spec file for Azure CLI
# Definition of macros used - https://fedoraproject.org/wiki/Packaging:RPMMacros?rd=Packaging/RPMMacros

# .el7.centos -> .el7
%if 0%{?rhel} == 7
  %define dist .el7
%endif

%define name           azure-cli
%define release        1%{?dist}
%define version        %{getenv:CLI_VERSION}
%define repo_path      %{getenv:REPO_PATH}
%define venv_url       https://pypi.python.org/packages/source/v/virtualenv/virtualenv-15.0.0.tar.gz
%define venv_sha256    70d63fb7e949d07aeb37f6ecc94e8b60671edb15b890aa86dba5dfaf2225dc19
%define cli_lib_dir    %{_libdir}/az

Summary:        Azure CLI
License:        MIT
Name:           %{name}
Version:        %{version}
Release:        %{release}
Url:            https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
BuildArch:      x86_64
Requires:       python

BuildRequires:  gcc
BuildRequires:  python
BuildRequires:  libffi-devel
BuildRequires:  python-devel
BuildRequires:  openssl-devel

%global _python_bytecompile_errors_terminate_build 0

%description
A great cloud needs great tools; we're excited to introduce Azure CLI,
 our next generation multi-platform command line experience for Azure.

%prep
# Create some tmp files
tmp_venv_archive=$(mktemp)

# Download, Extract Virtualenv
wget %{venv_url} -qO $tmp_venv_archive
echo "%{venv_sha256}  $tmp_venv_archive" | sha256sum -c -
tar -xvzf $tmp_venv_archive -C %{_builddir}

%install
# Create the venv
python %{_builddir}/virtualenv-15.0.0/virtualenv.py --python python %{buildroot}%{cli_lib_dir}

# Build the wheels from the source
source_dir=%{repo_path}
dist_dir=$(mktemp -d)
for d in $source_dir/src/azure-cli $source_dir/src/azure-cli-core $source_dir/src/azure-cli-nspkg $source_dir/src/azure-cli-command_modules-nspkg $source_dir/src/command_modules/azure-cli-*/; \
do cd $d; %{buildroot}%{cli_lib_dir}/bin/python setup.py bdist_wheel -d $dist_dir; cd -; done;

[ -d $source_dir/privates ] && cp $source_dir/privates/*.whl $dist_dir

# Install the CLI
all_modules=`find $dist_dir -name "*.whl"`
%{buildroot}%{cli_lib_dir}/bin/pip install --no-compile $all_modules
%{buildroot}%{cli_lib_dir}/bin/pip install --no-compile --force-reinstall --upgrade azure-nspkg azure-mgmt-nspkg

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
