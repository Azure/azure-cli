#!/usr/bin/env bash

set -e

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

pip install -e ./tools
pip install $ALL_MODULES

echo '=== List installed packages'
pip freeze

echo '=== Begin testing'
python -m automation.tests.verify_packages $share_folder/build
python -m automation.tests.verify_dependencies