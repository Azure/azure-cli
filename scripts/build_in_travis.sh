#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

set -e

scripts_root=$(cd $(dirname $0); pwd)

export PYTHONPATH=$PATHONPATH:./src
python -m azure.cli -h

# PyLint does not yet support Python 3.6 https://github.com/PyCQA/pylint/issues/1241
if [ "$TRAVIS_PYTHON_VERSION" != "3.6" ]; then
    check_style --ci;
fi
run_tests
$scripts_root/package_verify.sh

python $scripts_root/license/verify.py
