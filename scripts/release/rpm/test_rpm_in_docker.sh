#!/usr/bin/env bash

# This script should be run in a ubi8, ubi9 docker.
set -exv

export USERNAME=azureuser
# Pinned UBI 8/9 images contain an older Expat incompatible with current Python 3.12 pyexpat.
dnf update -y expat
dnf --nogpgcheck install /mnt/rpm/$RPM_NAME -y

dnf install git findutils $PYTHON_PACKAGE-pip -y

ln -s -f /usr/bin/$PYTHON_CMD /usr/bin/python
ln -s -f /usr/bin/$PIP_CMD /usr/bin/pip
time az self-test
time az --version

cd /azure-cli/
# Provision build and setuptools for scripts/ci/build.sh's --no-isolation builds,
# keeping setuptools at or above the security floor.
python -m pip install --upgrade pip "setuptools>=78.1.1" build
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
