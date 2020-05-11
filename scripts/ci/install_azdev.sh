#!/usr/bin/env bash

set -e

echo "Install azdev into virtual environment"
export CI="ADO"
pip install virtualenv
python -m virtualenv env
. env/bin/activate
pip install -U pip setuptools wheel -q
pip install git+https://github.com/fengzhou-msft/azure-cli-dev-tools.git@dependency_choice -q
azdev setup -c -d requirements
