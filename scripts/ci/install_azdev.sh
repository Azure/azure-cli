#!/usr/bin/env bash

set -e

echo "Install azdev into virtual environment"
export CI="ADO"
pip install virtualenv
python -m virtualenv env
. env/bin/activate
pip install -U pip setuptools wheel -q
# TODO: temp install from azdev working branch
pip install git+https://github.com/Azure/azure-cli-dev-tools.git@ConvertCIWork -q
# pip install azdev==0.1.3 -q
azdev setup -c
