#!/usr/bin/env bash

# This is the script builds the final wheel packages for shipping. The major difference between this script and the
# scripts/ci/build.sh is that this script doesn't build testsdk and test packages. It doesn't update version string, 
# either. Therefore this script is shorter and cleaner.

set -e

WORKDIR=`cd $(dirname $0); cd ../../../; pwd`
: ${OUTPUT_DIR:=$WORKDIR/artifacts}

mkdir -p $OUTPUT_DIR

cd $WORKDIR
for setup_file in $(find src -name 'setup.py' | grep -v azure-cli-testsdk); do
    pushd `dirname $setup_file`
    python setup.py bdist_wheel -d $OUTPUT_DIR
    python setup.py sdist -d $OUTPUT_DIR
    popd
done
