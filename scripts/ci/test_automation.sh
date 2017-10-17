#!/usr/bin/env bash

set -e

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

pip install -qqq -e ./tools
pip install -qqq coverage codecov

# remove this before integrate back to public
pip install -qqq ./privates/azure_mgmt_containerservice-2.0.0-py2.py3-none-any.whl

pip install -qqq $ALL_MODULES

echo '=== List installed packages'
pip freeze

echo '=== Begin testing'
coverage run -m automation.tests.run --parallel --ci
coverage combine
codecov
