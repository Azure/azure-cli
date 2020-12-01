#!/usr/bin/env bash

set -exv

export USERNAME=azureuser

apt update
apt install -y apt-transport-https git gcc python3-dev libssl1.1

dpkg -i /mnt/artifacts/pyinstaller/azure-cli_$CLI_VERSION-1~${DISTRO}_all.deb
mv /opt/az /opt/paz

dpkg -i /mnt/artifacts/debian/azure-cli_$CLI_VERSION-1~${DISTRO}_all.deb

az login -u azureclitest@azuresdkteam.onmicrosoft.com -p $PASSWORD
az account set -s 0b1f6471-1bf0-4dda-aec3-cb9272f09590

python3 /azure-cli/scripts/pyinstaller/performance/perf_check.py