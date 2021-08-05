#!/usr/bin/env bash
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

set -evx

# Create the debian/ directory for building the azure-cli Debian package

# This script takes an argument of the empty directory where the files will be placed.

if [ -z "$1" ]
  then
    echo "No argument supplied for debian directory."
    exit 1
fi

if [ -z "$2" ]
  then
    echo "No argument supplied for completion script."
    exit 1
fi

if [ -z "$3" ]
  then
    echo "No argument supplied for source directory."
    exit 1
fi

TAB=$'\t'

debian_dir=$1
completion_script=$2
source_dir=$3
mkdir $debian_dir/source

echo '1.0' > $debian_dir/source/format
echo '9' > $debian_dir/compat

cat > $debian_dir/changelog <<- EOM
azure-cli (${CLI_VERSION}-${CLI_VERSION_REVISION:=1}) unstable; urgency=low

  * Debian package release.

 -- Azure Python CLI Team <azpycli@microsoft.com>  $(date -R)

EOM

cat > $debian_dir/control <<- EOM
Source: azure-cli
Section: python
Priority: extra
Maintainer: Azure Python CLI Team <azpycli@microsoft.com>
Build-Depends: debhelper (>= 9), libssl-dev, libffi-dev, python3-dev
Standards-Version: 3.9.5
Homepage: https://github.com/azure/azure-cli

Package: azure-cli
Architecture: all
Depends: \${shlibs:Depends}, \${misc:Depends}
Description: Azure CLI
 A great cloud needs great tools; we're excited to introduce Azure CLI,
 our next generation multi-platform command line experience for Azure.

EOM

cat > $debian_dir/copyright <<- EOM
Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: azure-cli
Upstream-Contact: Azure Python CLI Team <azpycli@microsoft.com>
Source: https://github.com/azure/azure-cli

Files: *
Copyright: Copyright (c) Microsoft Corporation
License: MIT
Azure CLI

Copyright (c) Microsoft Corporation

All rights reserved. 

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the ""Software""), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

EOM

# TODO: Instead of "_ssl.cpython-36m-x86_64-linux-gnu.so" only, find all .so files with "find debian/azure-cli/opt/az -type f -name '*.so'"

cat > $debian_dir/rules << EOM
#!/usr/bin/make -f

# Uncomment this to turn on verbose mode.
export DH_VERBOSE=1
export DH_OPTIONS=-v

%:
${TAB}dh \$@ --sourcedirectory $source_dir

override_dh_install:
${TAB}mkdir -p debian/azure-cli/opt/az
${TAB}cp -a python_env/* debian/azure-cli/opt/az
${TAB}mkdir -p debian/azure-cli/usr/bin/
${TAB}echo "\043!/usr/bin/env bash\nbin_dir=\140cd \"\044(dirname \"\044BASH_SOURCE[0]\")\"; pwd\140\nAZ_INSTALLER=DEB \"\044bin_dir\"/../../opt/az/bin/python3 -Im azure.cli \"\044\100\"" > debian/azure-cli/usr/bin/az
${TAB}chmod 0755 debian/azure-cli/usr/bin/az
${TAB}mkdir -p debian/azure-cli/etc/bash_completion.d/
${TAB}cat ${completion_script} > debian/azure-cli/etc/bash_completion.d/azure-cli
${TAB}dpkg-shlibdeps -v --warnings=7 -Tdebian/azure-cli.substvars -dDepends -edebian/azure-cli/opt/az/bin/python3 debian/azure-cli/opt/az/lib/python3.6/lib-dynload/_ssl.cpython-36m-x86_64-linux-gnu.so


override_dh_strip:
${TAB}dh_strip --exclude=_cffi_backend

EOM

cat $debian_dir/rules

# debian/rules should be executable
chmod 0755 $debian_dir/rules
