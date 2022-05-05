#!/usr/bin/env bash
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# This script is expected to be run in a container environment, therefore sudo doesn't present
# here.

set -exv

: "${CLI_VERSION:?CLI_VERSION environment variable not set.}"
: "${CLI_VERSION_REVISION:?CLI_VERSION_REVISION environment variable not set.}"

ls -Rl /mnt/artifacts

WORKDIR=`cd $(dirname $0); cd ../../../; pwd`
PYTHON_VERSION="3.10.4"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Update APT packages
apt-get update
# uuid-dev is used to build _uuid module: https://github.com/python/cpython/pull/3796
apt-get install -y libssl-dev libffi-dev python3-dev debhelper zlib1g-dev uuid-dev
apt-get install -y wget

# Download Python source code
PYTHON_SRC_DIR=$(mktemp -d)
wget -qO- https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz | tar -xz -C "$PYTHON_SRC_DIR"
echo "Python source code is in $PYTHON_SRC_DIR"

# Build Python
$PYTHON_SRC_DIR/*/configure --srcdir $PYTHON_SRC_DIR/* --prefix $WORKDIR/python_env
make
make install

$WORKDIR/python_env/bin/python3 -m pip install --upgrade pip

export PATH=$PATH:$WORKDIR/python_env/bin

find ${WORKDIR}/src/ -name setup.py -type f | xargs -I {} dirname {} | grep -v azure-cli-testsdk | xargs pip3 install --no-deps
pip3 install -r ${WORKDIR}/src/azure-cli/requirements.py3.$(uname).txt

# Create create directory for debian build
mkdir -p $WORKDIR/debian
$SCRIPT_DIR/prepare.sh $WORKDIR/debian $WORKDIR/az.completion $WORKDIR

cd $WORKDIR
dpkg-buildpackage -us -uc

deb_file=$WORKDIR/../azure-cli_${CLI_VERSION}-${CLI_VERSION_REVISION:=1}_all.deb
cp $deb_file /mnt/output/
