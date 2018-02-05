#!/usr/bin/env bash
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

set -ex

: "${CLI_VERSION:?CLI_VERSION environment variable not set.}"
: "${BUILD_ARTIFACT_DIR:?BUILD_ARTIFACT_DIR environment variable not set.}"

if [ -z "$1" ]
  then
    echo "Argument should be path to local repo."
    exit 1
fi

local_repo=$1

sudo apt-get update

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
debian_directory_creator=$script_dir/dir_creator.sh

# Install dependencies for the build
sudo apt-get install -y libssl-dev libffi-dev python3-dev debhelper
# Download, Extract, Patch, Build CLI
tmp_pkg_dir=$(mktemp -d)
working_dir=$(mktemp -d)
cd $working_dir
source_dir=$local_repo
deb_file=$local_repo/../azure-cli_${CLI_VERSION}-${CLI_VERSION_REVISION:=1}_all.deb
az_completion_file=$source_dir/az.completion
# clean up old build output
if [ -d "$source_dir/debian" ]
  then
    rm -rf $source_dir/debian
fi
[ -d $local_repo/privates ] && cp $local_repo/privates/*.whl $tmp_pkg_dir

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

# note: This installation step could happen in debian/rules but was unable to escape $ char.
# It does not affect the built .deb file though.
$source_dir/python_env/bin/pip3 install wheel
for d in $source_dir/src/azure-cli $source_dir/src/azure-cli-core $source_dir/src/azure-cli-nspkg \
  $source_dir/src/azure-cli-command_modules-nspkg $source_dir/src/command_modules/azure-cli-*/;
  do cd $d;
  $source_dir/python_env/bin/python3 setup.py bdist_wheel -d $tmp_pkg_dir;
  cd -;
done;
all_modules=`find $tmp_pkg_dir -name "*.whl"`
$source_dir/python_env/bin/pip3 install $all_modules
$source_dir/python_env/bin/pip3 install --force-reinstall --upgrade azure-nspkg azure-mgmt-nspkg
# Add the debian files
mkdir $source_dir/debian
# Create temp dir for the debian/ directory used for CLI build.
cli_debian_dir_tmp=$(mktemp -d)

$debian_directory_creator $cli_debian_dir_tmp $az_completion_file $source_dir
cp -r $cli_debian_dir_tmp/* $source_dir/debian
cd $source_dir
dpkg-buildpackage -us -uc
echo "The archive is available at $working_dir/azure-cli_${CLI_VERSION}-${CLI_VERSION_REVISION:=1}_all.deb"
cp $deb_file ${BUILD_ARTIFACT_DIR}
echo "The archive has also been copied to ${BUILD_ARTIFACT_DIR}"
echo "Done."
