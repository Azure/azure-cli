#!/usr/bin/env bash

set -e

export AZDEV_CLI_REPO_PATH=$(pwd)
export AZDEV_EXT_REPO_PATHS='_NONE_'

azdev setup -c $AZDEV_CLI_REPO_PATH

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
    if [ $? != 0 ]
    then
        exit_code=1
        echo "Failed to load:" $ext
    fi
    az self-test
    if [ $? != 0 ]
    then
        exit_code=1
        echo "Failed to verify:" $ext
    fi
    az extension remove -n $ext
    echo $ext "extension has been removed."
done

exit $exit_code
