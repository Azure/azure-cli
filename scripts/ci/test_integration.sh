#!/usr/bin/env bash

set -e

. $(cd $(dirname $0); pwd)/artifacts.sh

pip install -e ./tools
pip install azure-cli -f $share_folder/build

echo '=== List installed packages'
pip freeze

echo '=== Begin testing'
python -m automation.tests.verify_packages $share_folder/build
python -m automation.tests.verify_dependencies