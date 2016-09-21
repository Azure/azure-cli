#!/bin/bash
set -e
git clone https://github.com/azure/azure-cli.git
cd azure-cli

# modify versions of the packages (__init__.py and setup.py files)
for initfile in src/azure-cli/azure/cli/__init__.py src/azure-cli-core/azure/cli/core/__init__.py; \
    do sed -i 's/^__version__ = [\x22\x27]\(.*\)\([0-9]\+\)[\x22\x27]/__version__ = \x27\1\2+1.dev'$(date +%Y%m%d)'\x27/' $initfile; \
    done;
for d in src/azure-cli/ src/azure-cli-core/ src/command_modules/azure-cli-*/; \
    do sed -i 's/^VERSION = [\x22\x27]\(.*\)\([0-9]\+\)[\x22\x27]/VERSION = \x27\1\2+1.dev'$(date +%Y%m%d)'\x27/' $d/setup.py; \
    done;

# build the packages
TMP_PKG_DIR=$(mktemp -d)
for d in src/azure-cli src/azure-cli-core src/command_modules/azure-cli-*/; \
    do cd $d; python setup.py sdist -d $TMP_PKG_DIR; cd -; \
    done;

# set up twine
pip install twine
echo "[distutils]
index-servers =
    cli-pypi

[cli-pypi]
repository: ${PYPI_REPO}
username: ${PYPI_USER}
password: ${PYPI_PASS}
" > ~/.pypirc

# upload packages
twine upload -r cli-pypi $TMP_PKG_DIR/*
