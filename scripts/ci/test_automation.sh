#!/usr/bin/env bash

set -e

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

target_profile=${AZURE_CLI_TEST_TARGET_PROFILE:-latest}
if [ "$target_profile" != "latest" ]; then
    # example: 2017-03-09-profile
    target_profile=$target_profile-profile
fi
title "Switch profile to $target_profile"

az cloud set -n AzureCloud --profile $target_profile

title 'Runing tests'
coverage run -m automation test --parallel --ci
coverage combine
codecov
