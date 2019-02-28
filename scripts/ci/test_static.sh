#!/usr/bin/env bash

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

[ -d privates ] && pip install privates/*.whl
pip install pylint==1.9.2
pip install $ALL_MODULES

echo '=== List installed packages'
pip freeze

echo '=== Begin testing'

proc_number=`python -c 'import multiprocessing; print(multiprocessing.cpu_count())'`

echo "Run pylint with $proc_number proc."

set +e
pylint azure.cli --rcfile=./pylintrc -j $proc_number

exit $exit_code
