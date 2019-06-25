#!/usr/bin/env bash

set -ev

REPO_ROOT="$(dirname ${BASH_SOURCE[0]})/../.."

# Uninstall any cruft that can poison the rest of the checks in this script.
pip3 freeze > baseline_deps.txt
pip3 uninstall -y -r baseline_deps.txt
pip3 list
pip3 check

# Install everything from our repository first.
find ${REPO_ROOT}/src -name setup.py -type f | xargs dirname | xargs pip3 install --no-deps

pip3 install -r ${REPO_ROOT}/src/azure-cli/requirements.py3.linux.txt

pip3 check

python3 -m azure.cli --version

python3 -m azure.cli self-test
