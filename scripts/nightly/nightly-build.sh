#!/bin/bash
set -e
git clone https://github.com/azure/azure-cli.git
cd azure-cli

# modify versions of the packages (__init__.py and setup.py files)
for initfile in src/azure-cli/azure/cli/__init__.py src/azure-cli-core/azure/cli/core/__init__.py; \
    do sed -i 's/^__version__ = [\x22\x27]\(.*\)+dev[\x22\x27]/__version__ = \x27\1+1.dev'$(date +%Y%m%d)'\x27/' $initfile; \
    done;
for d in src/azure-cli/ src/azure-cli-core/ src/azure-cli-nspkg/ src/azure-cli-command_modules-nspkg/ src/command_modules/azure-cli-*/; \
    do sed -i 's/^VERSION = [\x22\x27]\(.*\)+dev[\x22\x27]/VERSION = \x27\1+1.dev'$(date +%Y%m%d)'\x27/' $d/setup.py; \
    done;

pip install --upgrade pip wheel setuptools
pip install azure-storage==0.33.0
python /nightly/nightly-build.py
