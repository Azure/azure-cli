#!/usr/bin/env bash
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

set -ex

: "${CLI_VERSION:?CLI_VERSION environment variable not set.}"
: "${CLI_DOWNLOAD_SHA256:?CLI_DOWNLOAD_SHA256 environment variable not set.}"

if [ -z "$1" ]
  then
    echo "First argument should be path to executable debian directory creator."
    exit 1
fi

sudo apt-get update

debian_directory_creator=$1

# Install dependencies for the build
sudo apt-get install -y libssl-dev libffi-dev python3-dev debhelper
# Download, Extract, Patch, Build CLI
working_dir=$(mktemp -d)
source_archive=$working_dir/azure-cli-${CLI_VERSION}.tar.gz
source_dir=$working_dir/azure-cli-${CLI_VERSION}
cd $working_dir
wget https://azurecliprod.blob.core.windows.net/releases/azure-cli_packaged_${CLI_VERSION}.tar.gz -qO $source_archive
echo "$CLI_DOWNLOAD_SHA256  $source_archive" | sha256sum -c -
mkdir $source_dir
# Extract archive
archive_extract_dir=$(mktemp -d)
tar -xvzf $source_archive -C $archive_extract_dir
cp -r $archive_extract_dir/azure-cli_packaged_${CLI_VERSION}/* $source_dir
# Build Python from source and include
python_dir=$(mktemp -d)
python_archive=$(mktemp)
wget https://www.python.org/ftp/python/3.6.1/Python-3.6.1.tgz -qO $python_archive
tar -xvzf $python_archive -C $python_dir
echo "Python dir is $python_dir"
#  clean any previous make files
make clean || echo "Nothing to clean"
$python_dir/*/configure --srcdir $python_dir/* --prefix $source_dir/python_env
make
#  required to run the 'make install'
sudo apt-get install -y zlib1g-dev
make install
tmp_pkg_dir=$(mktemp -d)

# note: This installation step could happen in debian/rules but was unable to escape $ char.
# It does not affect the built .deb file though.
$source_dir/python_env/bin/pip3 install wheel
for d in $source_dir/src/azure-cli $source_dir/src/azure-cli-core $source_dir/src/azure-cli-nspkg $source_dir/src/azure-cli-command_modules-nspkg $source_dir/src/command_modules/azure-cli-*/; do cd $d; $source_dir/python_env/bin/python3 setup.py bdist_wheel -d $tmp_pkg_dir; cd -; done;
$source_dir/python_env/bin/pip3 install azure-cli --find-links $tmp_pkg_dir
$source_dir/python_env/bin/pip3 install --force-reinstall --upgrade azure-nspkg azure-mgmt-nspkg
# Add the debian files
mkdir $source_dir/debian
# Create temp dir for the debian/ directory used for CLI build.
cli_debian_dir_tmp=$(mktemp -d)

$debian_directory_creator $cli_debian_dir_tmp $source_dir/az.completion $source_dir
cp -r $cli_debian_dir_tmp/* $source_dir/debian
cd $source_dir
dpkg-buildpackage -us -uc
echo "The archive is available at $working_dir/azure-cli_${CLI_VERSION}-1_all.deb."
echo "Done."
