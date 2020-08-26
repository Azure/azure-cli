#!/usr/bin/env bash

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

pip install -e ./tools
[ -d privates ] && pip install -qqq privates/*.whl
pip install $ALL_MODULES

set -ev

output=$(az cloud list-profiles -otsv)

azdev verify package $share_folder/build/

for profile in $output; do
    echo
    echo "Verifying profile:" $profile
    az cloud update --profile $profile
    azdev verify load-all
    echo $profile "profile has been verified."
done

echo "Successfully loaded all commands in each profile."
