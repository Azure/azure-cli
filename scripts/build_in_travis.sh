#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

set -e

scripts_root=$(cd $(dirname $0); pwd)

export PYTHONPATH=$PATHONPATH:./src
python -m azure.cli -h

$scripts_root/run_pylint.sh
$scripts_root/run_tests.sh
$scripts_root/package_verify.sh

python $scripts_root/license/verify.py
