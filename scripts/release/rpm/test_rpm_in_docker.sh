#!/usr/bin/env bash

# This script should be run in a centos7 docker.
set -exv

export USERNAME=azureuser

yum --nogpgcheck localinstall /mnt/yum/$YUM_NAME -y

yum install git gcc python3-devel -y

ln -s /usr/bin/python3 /usr/bin/python
ln -s /usr/bin/pip3 /usr/bin/pip
time az self-test
time az --version

cd /azure-cli/
pip3 install wheel
./scripts/ci/build.sh
pip3 install pytest --prefix /usr/lib64/az
pip3 install pytest-xdist --prefix /usr/lib64/az

find /azure-cli/artifacts/build -name "azure_cli_testsdk*" | xargs pip3 install --prefix /usr/lib64/az --upgrade --ignore-installed
find /azure-cli/artifacts/build -name "azure_cli_fulltest*" | xargs pip3 install --prefix /usr/lib64/az --upgrade --ignore-installed --no-deps

python3 /azure-cli/scripts/release/rpm/test_rpm_package.py
