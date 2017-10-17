#!/usr/bin/env bash

set -e

. $(cd $(dirname $0); pwd)/artifacts.sh

pip install git+https://github.com/Azure/msrest-for-python.git@master#egg=msrest
pip install -qqq -e ./tools
pip install -qqq coverage codecov
pip install -qqq azure-cli-fulltest -f $share_folder/build

echo '=== List installed packages'
pip freeze

echo '=== Begin testing'
coverage run -m automation.tests.run --parallel --ci
coverage combine
codecov
