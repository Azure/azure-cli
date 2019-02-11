#!/usr/bin/env bash

set -e

export AZDEV_CLI_REPO_PATH=$(pwd)
export AZDEV_EXT_REPO_PATHS='_NONE_'

azdev setup -c $AZDEV_CLI_REPO_PATH

pip install -qqq coverage codecov

if [ "$REDUCE_SDK" == "True" ]
then
    echo 'azure.mgmt file counts'
    (cd $(dirname $(which python)); cd ../lib/*/site-packages/azure/mgmt; find . -name '*.py' | wc)

    python $(cd $(dirname $0); cd ..; pwd)/sdk_process/patch_models.py

    echo 'azure.mgmt file counts after reduce'
    (cd $(dirname $(which python)); cd ../lib/*/site-packages/azure/mgmt; find . -name '*.py' | wc)
fi

target_profile=${AZURE_CLI_TEST_TARGET_PROFILE:-latest}
if [ "$target_profile" = "2017-03-09" ]; then
    # example: 2017-03-09-profile
    target_profile=$target_profile-profile
elif [ "$target_profile" = "2018-03-01" ]
then
    target_profile=$target_profile-hybrid
fi

# test basic az commands
az -v
az -h

azdev test --profile $target_profile
