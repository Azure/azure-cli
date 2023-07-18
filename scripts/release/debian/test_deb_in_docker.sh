#!/usr/bin/env bash

# This script should be run in a ubuntu/debian docker.
set -exv

export USERNAME=azureuser

apt update
apt install -y apt-transport-https git gcc python3-dev

dpkg -i /mnt/artifacts/azure-cli_$CLI_VERSION-1~${DISTRO}_*.deb

time az self-test
time az --version

cd /azure-cli/
/opt/az/bin/python3 -m pip install wheel
ln -sf /opt/az/bin/python3 /usr/bin/python
./scripts/ci/build.sh

/opt/az/bin/python3 -m pip install pytest
/opt/az/bin/python3 -m pip install pytest-xdist
/opt/az/bin/python3 -m pip install pytest-forked

find /azure-cli/artifacts/build -name "azure_cli_testsdk*" | xargs /opt/az/bin/python3 -m pip install --upgrade --ignore-installed
find /azure-cli/artifacts/build -name "azure_cli_fulltest*" | xargs /opt/az/bin/python3 -m pip install --upgrade --ignore-installed --no-deps

/opt/az/bin/python3 /azure-cli/scripts/release/debian/test_deb_package.py
