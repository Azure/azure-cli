#!/usr/bin/env bash

root=$(cd $(dirname $0); pwd)

pip install wheel
pip install -U pip
pip install -r $root/requirements.txt
pip install azure-cli==$CLI_VERSION -f /mnt/pypi

pip install msrestazure==0.4.34

pip list

python $root/formula_generate.py
