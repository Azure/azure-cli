#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

set -e

scripts_root=$(cd $(dirname $0); pwd)

export PYTHONPATH=$PATHONPATH:./src

python -m azure.cli -h --debug

# Ensure tokens are erased from VCR recordings
python -m automation.tests.check_vcr_recordings

# PyLint does not yet support Python 3.6 https://github.com/PyCQA/pylint/issues/1241

LOCAL_PYTHON_VERSION=$(python -c 'import sys; print("{0}.{1}".format(sys.version_info[0], sys.version_info[1]))')
if [[ "$TRAVIS_PYTHON_VERSION" == "3.6" || "$LOCAL_PYTHON_VERSION" == "3.6" ]]; then
    echo 'Skipping check_style since it is not supported in python 3.6'
else
    check_style --ci;
fi

if [ "$CODE_COVERAGE" == "True" ]; then
    echo "Run tests with code coverage."
    pip install -qqq coverage codecov
    coverage run -m automation.tests.run

    coverage combine
    coverage report
    codecov
else
    python -m automation.tests.run
fi

if [[ "$CI" == "true" ]]; then
    $scripts_root/package_verify.sh
fi

python $scripts_root/license/verify.py
