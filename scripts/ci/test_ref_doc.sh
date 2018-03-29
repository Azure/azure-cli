#!/usr/bin/env bash

set -e

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

pip install -e ./tools
[ -d privates ] && pip install -qqq privates/*.whl
pip install $ALL_MODULES

pip install "sphinx==1.6.7" -q
echo "Installed."

cd doc/sphinx; make xml

echo "OK."
