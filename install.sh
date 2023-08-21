#!/bin/bash

CLI_SRC=~/2023/08/21/azure-cli/src
BUILDING_DIR=./build
PYTHON_EXEC=~/.pyenv/shims/python

for dir in "$CLI_SRC/azure-cli" "$CLI_SRC/azure-cli-core" "$CLI_SRC/azure-cli-telemetry"; do
  pushd "$dir"
  "$PYTHON_EXEC" -m pip install --no-warn-script-location --no-cache-dir --no-deps .
  popd
done
