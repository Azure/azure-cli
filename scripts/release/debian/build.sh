#!/usr/bin/env bash
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# This script is expected to be run in a container environment, therefore sudo doesn't present
# here.

set -ex

: "${CLI_VERSION:?CLI_VERSION environment variable not set.}"
: "${OUTPUT_DIR:?OUTPUT_DIR environment variable not set.}"

WORKDIR=`cd $(dirname $0); cd ../../../; pwd`
PYTHON_VERSION="3.6.5"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Update APT packages
apt-get update
apt-get install -y libssl-dev libffi-dev python3-dev debhelper zlib1g-dev
apt-get install -y wget

# Download Python source code
PYTHON_SRC_DIR=$(mktemp -d)
wget -qO- https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz | tar -xz -C "$PYTHON_SRC_DIR"
echo "Python source code is in $PYTHON_SRC_DIR"

# Build Python
$PYTHON_SRC_DIR/*/configure --srcdir $PYTHON_SRC_DIR/* --prefix $WORKDIR/python_env
make
make install

export PATH=$PATH:$WORKDIR/python_env/bin

# note: This installation step could happen in debian/rules but was unable to escape $ char.
# It does not affect the built .deb file though.
pip3 install wheel

if [ -d $WORKDIR/privates ]; then
    # The private pages are used when a dependency is not published yet
    find $WORKDIR/private -name '*.whl' | xargs pip3 install
fi

# The product whl are expected to be pre-built
find $OUTPUT_DIR/pypi -name '*.whl' | xargs pip3 install

pip3 install --force-reinstall --upgrade azure-nspkg azure-mgmt-nspkg

# Create create directory for debian build
mkdir -p $WORKDIR/debian
$SCRIPT_DIR/prepare.sh $WORKDIR/debian $WORKDIR/az.completion $WORKDIR

cd $WORKDIR
dpkg-buildpackage -us -uc

deb_file=$WORKDIR/../azure-cli_${CLI_VERSION}-${CLI_VERSION_REVISION:=1}_all.deb
cp $deb_file ${OUTPUT_DIR}
