#!/usr/bin/env bash

root=$(cd $(dirname $0); pwd)

if command -v tdnf &> /dev/null; then
    # Azure Linux
    tdnf install -y ca-certificates
elif command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    apt-get update && apt-get install -y ca-certificates
fi

pip install wheel
pip install -U pip
pip install -r $root/requirements.txt
find /mnt/src/ -name setup.py -type f | xargs -I {} dirname {} | grep -v azure-cli-testsdk | xargs pip install --no-deps
pip install -r /mnt/src/azure-cli/requirements.py3.Darwin.txt

pip list

# default option is update_existing to build from homebrew master branch,
# append '-b use_template' to build from formula_template.txt 
python3 $root/formula_generate.py
