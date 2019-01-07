#!/usr/bin/env bash

set -ev

. $(cd $(dirname $0); pwd)/artifacts.sh

ls -la $share_folder/build

ALL_MODULES=`find $share_folder/build/ -name "*.whl"`

##############################################
# Define colored output func
function title {
    LGREEN='\033[1;32m'
    CLEAR='\033[0m'

    echo -e ${LGREEN}$1${CLEAR}
}

title 'Install azdev'
pip install -qqq -e ./tools

title 'Install code coverage tools'
pip install -qqq coverage codecov

title 'Install private packages (optional)'
[ -d privates ] && pip install -qqq privates/*.whl

title 'Install products'
pip install -qqq $ALL_MODULES

title 'Installed packages'
pip freeze

if [ "$REDUCE_SDK" == "True" ]
then
    title 'azure.mgmt file counts'
    (cd $(dirname $(which python)); cd ../lib/*/site-packages/azure/mgmt; find . -name '*.py' | wc)

    python $(cd $(dirname $0); cd ..; pwd)/sdk_process/patch_models.py

    title 'azure.mgmt file counts after reduce'
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

title 'Running tests'
python -m automation test --ci --profile $target_profile
