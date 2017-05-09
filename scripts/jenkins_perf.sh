#!/usr/bin/env bash

# Run performance in jenkins build

python -m virtualenv --clear env
. ./env/bin/activate

echo "Run performance test on $(hostname)"

if [ -z %BUILD_NUMBER ]; then
    echo "Environment variable BUILD_NUMBER is missing."
    exit 1
fi

version=$(printf '%.8d' $BUILD_NUMBER)
echo "Version number: $version"

echo 'Before install'
which az
pip list

build_folder=/var/build_share/$BRANCH_NAME/$version
echo "Install build from $build_folder"

python -m pip install azure-cli --find-links file://$build_folder/artifacts/build -v
python -m pip freeze

python ./scripts/performance/measure.py
