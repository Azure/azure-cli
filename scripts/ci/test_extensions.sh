#!/usr/bin/env bash

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

pip install -e ./tools
[ -d privates ] && pip install -qqq privates/*.whl
pip install $ALL_MODULES

echo "Listing Available Extensions:"
az extension list-available -otable

# turn off telemetry as it crowds output
export AZURE_CLI_DIAGNOSTICS_TELEMETRY=
output=$(az extension list-available --query [].name -otsv)
exit_code=0

for ext in $output; do
    echo
    echo "Verifying extension:" $ext
    az extension add -n $ext
    azdev verify load_all
    if [ $? != 0 ]
    then
        exit_code=1
        echo "Failed to verify:" $ext
    fi
    az extension remove -n $ext
    echo $ext "extension has been removed."
done

exit $exit_code
