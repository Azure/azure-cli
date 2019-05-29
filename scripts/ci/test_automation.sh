#!/usr/bin/env bash

set -ev

. $(dirname ${BASH_SOURCE[0]})/artifacts.sh

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
    (find $(dirname $(which python))/../lib -name '*.py' | grep azure/mgmt/ | wc)

    python $(dirname ${BASH_SOURCE[0]})/../sdk_process/patch_models.py

    title 'azure.mgmt file counts after reduce'
    (find $(dirname $(which python))/../lib -name '*.py' | grep azure/mgmt/ | wc)
fi

target_profile=${AZURE_CLI_TEST_TARGET_PROFILE:-latest}
if [ "$target_profile" != "latest" ]; then
    # example: 2019-03-01-hybrid
    target_profile=$target_profile-hybrid
fi

# test basic az commands
az -v
az -h

title 'Running tests'
python -m automation test --ci --profile $target_profile
