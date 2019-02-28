#!/usr/bin/env bash

set -ev

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

pip install -e ./tools
[ -d privates ] && pip install -qqq privates/*.whl
pip install $ALL_MODULES

echo '=== List installed packages'
pip freeze

echo '=== Test Module Loading Performance'
unset AZURE_CLI_DIAGNOSTICS_TELEMETRY
azdev verify module-load-perf
