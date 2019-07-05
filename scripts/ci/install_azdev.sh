#!/usr/bin/env bash

set -e

echo "Install azdev into virtual environment"
export CI="ADO"
pip install virtualenv
python -m virtualenv env
. env/bin/activate
pip install -U pip setuptools wheel -q
pip install azdev==0.1.4 -q
azdev setup -c
