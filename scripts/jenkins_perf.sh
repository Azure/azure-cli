#!/usr/bin/env bash

# Run performance in jenkins build

# Activate virtual environment
python -m virtualenv --clear env
. ./env/bin/activate

# Load command build variables
. $(cd $(dirname $0); pwd)/jenkins_common.sh

echo "Run performance test on $(hostname)"

if [ -z %BUILD_NUMBER ]; then
    echo "Environment variable BUILD_NUMBER is missing."
    exit 1
fi

echo 'Before install'
which az
pip list

python -m pip install azure-cli --find-links file://$build_share/artifacts/build -v
python -m pip freeze

python ./scripts/performance/measure.py
