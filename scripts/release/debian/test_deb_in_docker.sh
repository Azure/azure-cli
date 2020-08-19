#!/usr/bin/env bash

# This script should be run in a ubuntu/debian docker.
set -exv

export USERNAME=azureuser

apt update
apt install -y apt-transport-https python3-pip

# The distros that need libssl1.1
case ${DISTRO} in
    bionic|buster|eoan|focal) apt install -y libssl1.1;;
    *)                        :;;
esac

dpkg -i /mnt/artifacts/azure-cli_$CLI_VERSION-1~${DISTRO}_all.deb

ln -s /usr/bin/python3 /usr/bin/python
ln -s /usr/bin/pip3 /usr/bin/pip
time az self-test
time az --version

cd /azure-cli/
pip3 install wheel
./scripts/ci/build.sh

/opt/az/bin/python3 -m pip install pytest
/opt/az/bin/python3 -m pip install pytest-xdist

find /azure-cli/artifacts/build -name "azure_cli_testsdk*" | xargs /opt/az/bin/python3 -m pip install --upgrade --ignore-installed
find /azure-cli/artifacts/build -name "azure_cli_fulltest*" | xargs /opt/az/bin/python3 -m pip install --upgrade --ignore-installed --no-deps

/opt/az/bin/python3 /azure-cli/scripts/release/rpm/test_deb_package.py
