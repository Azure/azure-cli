#!/usr/bin/env bash

set -ev

wd=`cd $(dirname $0); pwd`

. $wd/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

pip install -e ./tools
[ -d privates ] && pip install -qqq privates/*.whl
pip install $ALL_MODULES

pip install sphinx==1.6.7 Jinja2==3.0.3
echo "Installed."

cd doc/sphinx; python ./__main__.py

python $wd/test_help_doc_arguments.py "./_build/xml/ind.xml"

echo "OK."
