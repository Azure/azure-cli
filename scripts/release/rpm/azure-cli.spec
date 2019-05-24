# RPM spec file for Azure CLI
# Definition of macros used - https://fedoraproject.org/wiki/Packaging:RPMMacros?rd=Packaging/RPMMacros

# .el7.centos -> .el7
%if 0%{?rhel}
  %define dist .el%{?rhel}
%endif

%if 0%{?rhel} && 0%{?rhel} < 8
    %define python_cmd python2
%else
    %define python_cmd python3
%endif

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
Url:            https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
BuildArch:      x86_64
Requires:       %{python_cmd}, %{python_cmd}-virtualenv

BuildRequires:  gcc, libffi-devel, openssl-devel, perl
BuildRequires:  %{python_cmd}-devel

%global _python_bytecompile_errors_terminate_build 0

%description
A great cloud needs great tools; we're excited to introduce Azure CLI,
 our next generation multi-platform command line experience for Azure.

%prep
%install
# Create the venv
%{python_cmd} -m virtualenv --python %{python_cmd} %{buildroot}%{cli_lib_dir}

# Build the wheels from the source
source_dir=%{repo_path}
dist_dir=$(mktemp -d)
for d in $source_dir/src/azure-cli $source_dir/src/azure-cli-core $source_dir/src/azure-cli-telemetry $source_dir/src/azure-cli-nspkg $source_dir/src/azure-cli-command_modules-nspkg $source_dir/src/command_modules/azure-cli-*/; \
do cd $d; %{buildroot}%{cli_lib_dir}/bin/python setup.py bdist_wheel -d $dist_dir; cd -; done;

[ -d $source_dir/privates ] && cp $source_dir/privates/*.whl $dist_dir

# Install the CLI
all_modules=`find $dist_dir -name "*.whl"`
%{buildroot}%{cli_lib_dir}/bin/pip install --no-compile $all_modules
%{buildroot}%{cli_lib_dir}/bin/pip install --no-compile --force-reinstall --upgrade azure-nspkg azure-mgmt-nspkg
%{buildroot}%{cli_lib_dir}/bin/pip install --no-compile --force-reinstall urllib3==1.24.2

# Fix up %{buildroot} appearing in some files...
for d in %{buildroot}%{cli_lib_dir}/bin/*; do perl -p -i -e "s#%{buildroot}##g" $d; done;

# Create executable
mkdir -p %{buildroot}%{_bindir}
python_version=$(ls %{buildroot}%{cli_lib_dir}/lib/ | head -n 1)
printf "#!/usr/bin/env bash\nPYTHONPATH=%{cli_lib_dir}/lib/${python_version}/site-packages %{python_cmd} -sm azure.cli \"\$@\"" > %{buildroot}%{_bindir}/az
rm %{buildroot}%{cli_lib_dir}/bin/python* %{buildroot}%{cli_lib_dir}/bin/pip*

# Set up tab completion
mkdir -p %{buildroot}%{_sysconfdir}/bash_completion.d/
cat $source_dir/az.completion > %{buildroot}%{_sysconfdir}/bash_completion.d/azure-cli

%files
%exclude %{cli_lib_dir}/bin/
%attr(-,root,root) %{cli_lib_dir}
%config(noreplace) %{_sysconfdir}/bash_completion.d/azure-cli
%attr(0755,root,root) %{_bindir}/az
