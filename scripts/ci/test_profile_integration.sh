#!/usr/bin/env bash

set -e

export AZDEV_CLI_REPO_PATH=$(pwd)
export AZDEV_EXT_REPO_PATHS='_NONE_'

azdev setup -c $AZDEV_CLI_REPO_PATH

output=$(az cloud list-profiles -otsv)

for profile in $output; do
    echo
    echo "Verifying profile:" $profile
    az cloud update --profile $profile
    az self-test
    echo $profile "profile has been verified."
done

echo "Successfully loaded all commands in each profile."
