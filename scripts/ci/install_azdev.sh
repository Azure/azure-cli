#!/usr/bin/env bash

set -e

echo "Install azdev into virtual environment"
export CI="ADO"
pip install virtualenv
python -m virtualenv env
. env/bin/activate
pip install -U pip setuptools wheel -q
git clone https://github.com/Azure/azure-cli-dev-tools.git
cd azure-cli-dev-tools
git checkout pep420
pip install -e .
cd ..
azdev setup -c
