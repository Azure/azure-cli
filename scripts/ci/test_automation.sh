#!/usr/bin/env bash

set -e

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

pip install -qqq -e ./tools
pip install -qqq coverage codecov
[ -d privates ] && pip install -qqq privates/*.whl
pip install -qqq $ALL_MODULES

echo '=== List installed packages'
pip freeze

echo '=== Begin testing'
coverage run -m automation.tests.run --parallel --ci
coverage combine
codecov
