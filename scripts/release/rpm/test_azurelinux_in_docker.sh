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
python -m pip install --upgrade pip setuptools
./scripts/ci/build.sh

# From Fedora36, when using `pip install --prefix` with root privileges, the package is installed into `{prefix}/local/lib`.
# In order to keep the original installation path, I have to set RPM_BUILD_ROOT
# Ref https://docs.fedoraproject.org/en-US/fedora/latest/release-notes/developers/Development_Python/#_pipsetup_py_installation_with_prefix
export RPM_BUILD_ROOT=/

pip install pytest --prefix /usr/lib64/az
pip install pytest-xdist --prefix /usr/lib64/az
pip install pytest-forked --prefix /usr/lib64/az

find /azure-cli/artifacts/build -name "azure_cli_testsdk*" | xargs pip install --prefix /usr/lib64/az --upgrade --ignore-installed
find /azure-cli/artifacts/build -name "azure_cli_fulltest*" | xargs pip install --prefix /usr/lib64/az --upgrade --ignore-installed --no-deps

python /azure-cli/scripts/release/rpm/test_rpm_package.py
