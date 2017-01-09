#!/usr/bin/env bash
set -ex

# TODO-DEREK Modify script so it uses temp directories to avoid conflict when running the script twice

: "${CLI_VERSION:?CLI_VERSION environment variable not set.}"
: "${CLI_DOWNLOAD_SHA256:?CLI_DOWNLOAD_SHA256 environment variable not set.}"
: "${CLI_PATCH1_SHA256:?CLI_PATCH1_SHA256 environment variable not set.}"
: "${CLI_PATCH2_SHA256:?CLI_PATCH2_SHA256 environment variable not set.}"

if [ -z "$1" ]
  then
    echo "First argument should be path to executable debian directory creator."
    exit 1
fi

debian_directory_creator=$1

# Create temp dir for the debian/ directory used for CLI build.
cli_debian_dir_tmp=$(mktemp -d)
$debian_directory_creator $cli_debian_dir_tmp

# Modify dh-virtualenv/debian/control to not include the virtualenv or python-virtualenv dependencies as we don't use python-virtualenv but use the ones above instead.
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

sudo apt-get update
# Install latest versions of pip and virtualenv
sudo apt-get install -y curl
curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
sudo python get-pip.py
sudo pip install virtualenvwrapper
# Install dh-virtualenv by building from GitHub repo
sudo apt-get install -y devscripts git equivs
git clone https://github.com/spotify/dh-virtualenv.git
cd dh-virtualenv
git checkout tags/1.0
sudo mk-build-deps -ri
# Apply dh-virtualenv debian/control patch
mv $dh_virtualenv_debian_control debian/control
# Build dh-virtualenv
dpkg-buildpackage -us -uc -b
sudo dpkg -i ../dh-virtualenv_1.0-1_all.deb
# Install dependencies for the build
sudo apt-get install -y libssl-dev libffi-dev python-dev
# Download source and apply patches
cd ~
wget https://azurecliprod.blob.core.windows.net/releases/azure-cli_packaged_${CLI_VERSION}.tar.gz -qO azure-cli-${CLI_VERSION}.tar.gz
echo "$CLI_DOWNLOAD_SHA256  azure-cli-${CLI_VERSION}.tar.gz" | sha256sum -c -
mkdir azure-cli-${CLI_VERSION}
tmpdir=$(mktemp -d); tar -xvzf azure-cli-${CLI_VERSION}.tar.gz -C $tmpdir; cp -r $tmpdir/azure-cli_packaged_${CLI_VERSION}/* azure-cli-${CLI_VERSION}
wget https://azurecliprod.blob.core.windows.net/patches/patch_0.1.5_component_custom.diff -qO patch1.patch
echo "$CLI_PATCH1_SHA256  patch1.patch" | sha256sum -c -
patch -p1 azure-cli-${CLI_VERSION}/src/command_modules/azure-cli-component/azure/cli/command_modules/component/custom.py patch1.patch
wget https://azurecliprod.blob.core.windows.net/patches/patch_0.1.5_pkg_util.diff -qO patch2.patch
echo "$CLI_PATCH2_SHA256  patch2.patch" | sha256sum -c -
patch -p1 azure-cli-${CLI_VERSION}/src/azure-cli-core/azure/cli/core/_pkg_util.py patch2.patch
cd azure-cli-${CLI_VERSION}
# Add the debian files
mkdir debian
cp -r $cli_debian_dir_tmp/* debian
dpkg-buildpackage -us -uc
