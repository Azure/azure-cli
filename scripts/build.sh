#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

set -e

scripts_root=$(cd $(dirname $0); pwd)

export PYTHONPATH=$PATHONPATH:./src

python -m azure.cli --debug

# Ensure tokens are erased from VCR recordings
python -m automation.tests.check_vcr_recordings

check_style --ci;

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

python -m automation.tests.verify_doc_source_map

python $scripts_root/license/verify.py
