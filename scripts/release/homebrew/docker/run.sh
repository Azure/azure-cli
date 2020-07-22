#!/usr/bin/env bash

root=$(cd $(dirname $0); pwd)

pip install wheel
pip install -U pip
pip install -r $root/requirements.txt
find /mnt/src/ -name setup.py -type f | xargs -I {} dirname {} | grep -v azure-cli-testsdk | xargs pip install --no-deps
pip install -r /mnt/src/azure-cli/requirements.py3.Darwin.txt

pip list

python $root/formula_generate.py -b use_template
