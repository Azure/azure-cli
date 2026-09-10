#!/usr/bin/env bash

# This script should be run in a Azure Linux docker container.
set -exv

export USERNAME=azureuser

tdnf --nogpgcheck install /mnt/rpm/$RPM_NAME -y

tdnf install git gcc python3-devel python3-pip findutils ca-certificates -y

ln -s -f /usr/bin/python3 /usr/bin/python
time az self-test
time az --version

cd /azure-cli/
# Cap setuptools<81: 81 removes setup.py --dry-run and changes distutils command signatures (82 removes pkg_resources).
# scripts/ci/build.sh builds with `python -m build --no-isolation`, so this pin is the setuptools the build uses.
# `build` is the PEP 517 frontend that script invokes.
python -m pip install --upgrade "setuptools<81" build
./scripts/ci/build.sh

# From Fedora36, when using `pip install --prefix` with root privileges, the package is installed into `{prefix}/local/lib`.
# In order to keep the original installation path, I have to set RPM_BUILD_ROOT
# Ref https://docs.fedoraproject.org/en-US/fedora/latest/release-notes/developers/Development_Python/#_pipsetup_py_installation_with_prefix
export RPM_BUILD_ROOT=/

# Detect where azure-cli was installed (supports both /usr/lib64/az on Fedora/RHEL and /usr/lib/az on Azure Linux)
if [ -d /usr/lib/az ]; then
    AZ_LIB_DIR=/usr/lib/az
else
    AZ_LIB_DIR=/usr/lib64/az
fi

pip install pytest --prefix "$AZ_LIB_DIR"
pip install pytest-xdist --prefix "$AZ_LIB_DIR"
pip install pytest-forked --prefix "$AZ_LIB_DIR"

find /azure-cli/artifacts/build -name "azure_cli_testsdk*" | xargs pip install --prefix "$AZ_LIB_DIR" --upgrade --ignore-installed
find /azure-cli/artifacts/build -name "azure_cli_fulltest*" | xargs pip install --prefix "$AZ_LIB_DIR" --upgrade --ignore-installed --no-deps

AZ_LIB_DIR="$AZ_LIB_DIR" python /azure-cli/scripts/release/rpm/test_rpm_package.py
