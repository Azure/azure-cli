#!/usr/bin/env bash

# This script should be run in a centos8 docker.
set -exv
yum install which -y
rpm --import https://packages.microsoft.com/keys/microsoft.asc

sh -c 'echo -e "[azure-cli]
name=Azure CLI
baseurl=https://packages.microsoft.com/yumrepos/azure-cli
enabled=1
gpgcheck=1
gpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/azure-cli.repo'

yum install azure-cli -y
ln -s /usr/bin/python3 /usr/bin/python
ln -s /usr/bin/pip3 /usr/bin/pip

yum install git -y
git clone https://github.com/Azure/azure-cli.git
cd azure-cli/
git checkout release
pip3 install wheel
./scripts/ci/build.sh
pip3 install pytest --prefix /usr/lib64/az
pip3 install pytest-xdist --prefix /usr/lib64/az

find /azure-cli/artifacts/build -name "azure_cli_testsdk*" | xargs pip3 install --prefix /usr/lib64/az --upgrade --ignore-installed
find /azure-cli/artifacts/build -name "azure_cli_fulltest*" | xargs pip3 install --prefix /usr/lib64/az --upgrade --ignore-installed --no-deps

python3 test_rpm_package.py