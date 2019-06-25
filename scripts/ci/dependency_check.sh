#!/usr/bin/env bash

set -ev

REPO_ROOT="$(dirname ${BASH_SOURCE[0]})/../.."

# Install everything from our repository first.
find ${REPO_ROOT}/src -name setup.py -type f | xargs dirname | xargs pip3 install --no-deps

pip3 install -r ${REPO_ROOT}/src/azure-cli/requirements.py3.linux.txt

pip3 check

python3 -m azure.cli --version

python3 -m azure.cli self-test
