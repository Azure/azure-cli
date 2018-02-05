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
unset AZURE_CLI_DIAGNOSTICS_TELEMETRY
azdev verify package $share_folder/build/
azdev verify commands
azdev verify dependencies
