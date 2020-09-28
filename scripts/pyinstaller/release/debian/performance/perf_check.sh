#!/usr/bin/env bash

set -exv

apt update
apt install -y curl

dpkg -i /mnt/artifacts/azure-cli_$CLI_VERSION-1~${DISTRO}_all.deb
mv /opt/az /opt/paz
curl -sL https://aka.ms/InstallAzureCLIDeb | bash
python3 /azure-cli/scripts/pyinstaller/release/debian/performance/perf_check.py