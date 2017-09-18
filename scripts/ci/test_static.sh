#!/usr/bin/env bash

set -e

. $(cd $(dirname $0); pwd)/artifacts.sh

pip install pylint flake8
pip install azure-cli-fulltest -f $share_folder/build

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

echo "Verify default modules"
azdev verify default-modules $share_folder/build
