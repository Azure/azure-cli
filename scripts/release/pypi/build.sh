#!/usr/bin/env bash

# This is the script builds the final wheel packages for shipping. The major difference between this script and the
# scripts/ci/build.sh is that this script doesn't build testsdk and test packages. It doesn't update version string,
# either. Therefore this script is shorter and cleaner.

set -ev

: "${BUILD_STAGINGDIRECTORY:?BUILD_STAGINGDIRECTORY environment variable not set}"
: "${BUILD_SOURCESDIRECTORY:=`cd $(dirname $0); cd ../../../; pwd`}"

cd $BUILD_SOURCESDIRECTORY

echo "Search setup files from `pwd`."
python --version

pip install -U pip setuptools wheel
pip list

for setup_file in $(find src -name 'setup.py' | grep -v azure-cli-testsdk); do
    pushd `dirname $setup_file`

    cp ../../../NOTICE.txt .

    python setup.py bdist_wheel -d $BUILD_STAGINGDIRECTORY
    python setup.py sdist -d $BUILD_STAGINGDIRECTORY
    popd
done
