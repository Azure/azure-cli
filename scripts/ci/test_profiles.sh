#!/usr/bin/env bash

set -e

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

pip install -e ./tools
[ -d privates ] && pip install -qqq privates/*.whl
pip install $ALL_MODULES

output=$(az cloud list-profiles -otsv)

for profile in $output; do
    echo
    echo "Verifying profile:" $profile
    az cloud update --profile latest
    azdev verify load-all
    echo $profile "profile has been verified."
done
