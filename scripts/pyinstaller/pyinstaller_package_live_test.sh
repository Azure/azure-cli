#!/usr/bin/env bash

# This script should be run in a ubuntu/debian docker.
set -exv

export USERNAME=azureuser

# Update APT packages
apt-get update
apt install -y apt-transport-https git gcc libssl1.1
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y libssl-dev libffi-dev python3-dev debhelper zlib1g-dev
apt-get install -y python3.7 python3.7-dev python3.7-venv

dpkg -i /mnt/artifacts/debian/azure-cli_$CLI_VERSION-1~${DISTRO}_all.deb

python3.7 -m venv /env
source /env/bin/activate
# pip install azdev
# git clone https://github.com/Azure/azure-cli-dev-tools.git
git clone -b fix https://github.com/qwordy/azure-cli-dev-tools.git
pip install -e azure-cli-dev-tools
pip install pytest-json-report
pip install pytest-html
pip install pytest-rerunfailures

cd /azure-cli/
azdev setup -c .

az login -u azureclitest@azuresdkteam.onmicrosoft.com -p $PASSWORD
az account set -s 0b1f6471-1bf0-4dda-aec3-cb9272f09590

azdev test ${TARGET} --live --mark "not serial" --xml-path test_results.parallel.xml --no-exitfirst -a "-n 2 --json-report --json-report-summary --json-report-file=${TARGET}.report.parallel.json --html=${TARGET}.report.parallel.html --self-contained-html --reruns 3 -s"
