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

    # TODO: Remove when ML extension is compatible with CLI 2.0.69 core
    # https://github.com/Azure/azure-cli-extensions/issues/826
    if [ $ext == 'azure-cli-ml' ]; then
        continue
    fi

    echo
    echo "Verifying extension:" $ext
    az extension add -n $ext
    if [ $? != 0 ]
    then
        exit_code=1
        echo "Failed to load:" $ext
    fi
done

az self-test --debug
if [ $? != 0 ]
then
    exit_code=1
    echo "Failed to verify:" $ext
fi

exit $exit_code
