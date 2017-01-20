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

# Modify dh-virtualenv/debian/control to not include the virtualenv or python-virtualenv
# dependencies as we don't use python-virtualenv but our own.
dh_virtualenv_debian_control=$(mktemp)
cat > $dh_virtualenv_debian_control <<- EOM
Source: dh-virtualenv
Section: python
Priority: extra
Maintainer: Jyrki Pulliainen <jyrki@spotify.com>
Build-Depends: debhelper (>= 9), python(>= 2.6.6-3~),
 python-setuptools, python-sphinx, python-mock
Standards-Version: 3.9.8
Homepage: http://www.github.com/spotify/dh-virtualenv
X-Python-Version: >= 2.6

Package: dh-virtualenv
Architecture: all
Depends: \${python:Depends}, \${misc:Depends},  \${sphinxdoc:Depends}
Description: wrap and build python packages using virtualenv
 This package provides a dh sequencer that helps you to deploy your
 virtualenv wrapped installation inside a Debian package.
EOM

# Install latest versions of pip and virtualenv
sudo apt-get install -y curl
get_pip_py=$(mktemp)
curl "https://bootstrap.pypa.io/get-pip.py" -o $get_pip_py
sudo python $get_pip_py
sudo pip install virtualenvwrapper
# Install dh-virtualenv by building from GitHub repo
sudo apt-get install -y devscripts git equivs
dh_virtualenv_git_dir=$(mktemp -d)
git clone https://github.com/spotify/dh-virtualenv.git $dh_virtualenv_git_dir
cd $dh_virtualenv_git_dir
git checkout tags/1.0
echo "y\n" | sudo mk-build-deps -ri
# Apply dh-virtualenv debian/control patch
mv $dh_virtualenv_debian_control $dh_virtualenv_git_dir/debian/control
# Build dh-virtualenv
dpkg-buildpackage -us -uc -b
sudo dpkg -i ../dh-virtualenv_1.0-1_all.deb
# Install dependencies for the build
sudo apt-get install -y libssl-dev libffi-dev python-dev
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
# Add the debian files
mkdir $source_dir/debian
# Create temp dir for the debian/ directory used for CLI build.
cli_debian_dir_tmp=$(mktemp -d)
$debian_directory_creator $cli_debian_dir_tmp $source_dir/az.completion
cp -r $cli_debian_dir_tmp/* $source_dir/debian
cd $source_dir
dpkg-buildpackage -us -uc
echo "The archive is available at $working_dir/azure-cli_${CLI_VERSION}-1_all.deb."
echo "Done."
