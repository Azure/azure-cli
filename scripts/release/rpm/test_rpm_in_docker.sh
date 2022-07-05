#!/usr/bin/env bash

# This script should be run in a centos7 docker.
set -exv

export USERNAME=azureuser

PYTHON_PACKAGE=python39
PYTHON_CMD=python3.9
PIP_CMD=pip3.9

dnf --nogpgcheck install /mnt/rpm/$RPM_NAME -y

dnf install git gcc $PYTHON_PACKAGE-devel -y

ln -s -f /usr/bin/$PYTHON_CMD /usr/bin/python
ln -s -f /usr/bin/$PIP_CMD /usr/bin/pip
time az self-test
time az --version

cd /azure-cli/
pip install wheel
./scripts/ci/build.sh
pip install pytest --prefix /usr/lib64/az
pip install pytest-xdist --prefix /usr/lib64/az

find /azure-cli/artifacts/build -name "azure_cli_testsdk*" | xargs pip install --prefix /usr/lib64/az --upgrade --ignore-installed
find /azure-cli/artifacts/build -name "azure_cli_fulltest*" | xargs pip install --prefix /usr/lib64/az --upgrade --ignore-installed --no-deps

python /azure-cli/scripts/release/rpm/test_rpm_package.py
