# RPM spec file for Azure CLI
# Definition of macros used - https://fedoraproject.org/wiki/Packaging:RPMMacros?rd=Packaging/RPMMacros

%global __python %{__python3}
# Turn off python byte compilation
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')

# The Python package name for dnf/yum/tdnf, such as python39, python3
%define python_package %{getenv:PYTHON_PACKAGE}
# The Python executable name, such as python3.9, python3
%define python_cmd %{getenv:PYTHON_CMD}

%define name           azure-cli
%define release        1%{?dist}
%define version        %{getenv:CLI_VERSION}
%define repo_path      %{getenv:REPO_PATH}
%define cli_lib_dir    %{_libdir}/az

Summary:        Azure CLI
License:        MIT
Name:           %{name}
Version:        %{version}
Release:        %{release}
Url:            https://docs.microsoft.com/cli/azure/install-azure-cli
Requires:       %{python_package}
Prefix:         /usr
Prefix:         /etc

BuildRequires:  gcc, libffi-devel, openssl-devel, perl
BuildRequires:  %{python_package}-devel

%global _python_bytecompile_errors_terminate_build 0

# To get rid of `cannot open linker script file` error on Fedora36. If %_package_note_file is undefined, the
# linker script will not be generated. Related bug: https://bugzilla.redhat.com/show_bug.cgi?id=2043092
# Ref: https://src.fedoraproject.org/rpms/ruby/c/a0bcb33eaa666d3e1d08ca45e77161ca05611487?branch=rawhide
#      https://src.fedoraproject.org/rpms/redhat-rpm-config//blob/rawhide/f/buildflags.md
%undefine _package_note_file

%description
A great cloud needs great tools; we're excited to introduce Azure CLI,
 our next generation multi-platform command line experience for Azure.

%prep
%install
# Create a fully instantiated virtual environment, ready to use the CLI.
%{python_cmd} -m venv %{buildroot}%{cli_lib_dir}
source %{buildroot}%{cli_lib_dir}/bin/activate
%{python_cmd} -m pip install --upgrade pip setuptools
source %{repo_path}/scripts/install_full.sh
# Remove unused SDK version
%{python_cmd} %{repo_path}/scripts/trim_sdk.py

# cffi 1.15.0 doesn't work with RPM: https://foss.heptapod.net/pypy/cffi/-/issues/513
%{python_cmd} -m pip install cffi==1.14.6

deactivate

# Fix up %{buildroot} appearing in some files...
for d in %{buildroot}%{cli_lib_dir}/bin/*; do perl -p -i -e "s#%{buildroot}##g" $d; done;

# Create executable (entry script)

# For PYTHONPATH:
#   - We can't use %{_libdir} (expands to absolute path '/usr/lib64'), because we need to support customized
#     installation location: https://github.com/Azure/azure-cli/pull/17491
#   - We also can't use %{_lib}, because %{_lib} expands to different values on difference OSes：
#     https://github.com/Azure/azure-cli/pull/20061
#     - Fedora/CentOS/RedHat: relative path 'lib64'
#     - Mariner: abolute path '/usr/lib'
# The only solution left is to hard-code 'lib64' as we only release 64-bit RPM packages.
mkdir -p %{buildroot}%{_bindir}
python_version=$(ls %{buildroot}%{cli_lib_dir}/lib/ | head -n 1)
# We make %{python_cmd} the default executable, but if there is a more precise match, such as python3.9, we prefer that.
printf "#!/usr/bin/env bash
bin_dir=\`cd \"\$(dirname \"\$BASH_SOURCE[0]\")\"; pwd\`
python_cmd=%{python_cmd}
if command -v ${python_version} &>/dev/null; then python_cmd=${python_version}; fi
AZ_INSTALLER=RPM PYTHONPATH=\"\$bin_dir/../lib64/az/lib/${python_version}/site-packages\" \$python_cmd -sm azure.cli \"\$@\"
" > %{buildroot}%{_bindir}/az
rm %{buildroot}%{cli_lib_dir}/bin/python* %{buildroot}%{cli_lib_dir}/bin/pip*

# Set up tab completion
mkdir -p %{buildroot}%{_sysconfdir}/bash_completion.d/
cat %{repo_path}/az.completion > %{buildroot}%{_sysconfdir}/bash_completion.d/azure-cli

%files
%exclude %{cli_lib_dir}/bin/
%attr(-,root,root) %{cli_lib_dir}
%config(noreplace) %{_sysconfdir}/bash_completion.d/azure-cli
%attr(0755,root,root) %{_bindir}/az
