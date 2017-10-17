#!/usr/bin/env bash

set -e

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

pip install pylint flake8
pip install $ALL_MODULES

echo '=== List installed packages'
pip freeze

echo '=== Begin testing'

proc_number=`python -c 'import multiprocessing; print(multiprocessing.cpu_count())'`

echo "Run pylint with $proc_number proc."
pylint azure.cli --rcfile=./pylintrc -j $proc_number

echo "Run flake8."
flake8 --statistics --exclude=azure_bdist_wheel.py --append-config=./.flake8 ./src

pip install -e ./tools
echo "Scan license"
azdev verify license

echo "Documentation Map"
azdev verify document-map

echo "Command lint"
python -m automation.commandlint.run 

echo "Verify readme history"
python -m automation.tests.verify_readme_history

echo "Verify package versions"
python -m automation.tests.verify_package_versions

echo "Verify default modules"
azdev verify default-modules $share_folder/build
