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

# Disable azure-cli-ml: https://github.com/Azure/azure-cli-extensions/issues/826
# Disable fzf: https://github.com/Azure/azure-cli/pull/17979
# Disable arcappliance arcdata connectedk8s: https://github.com/Azure/azure-cli/pull/20436
# Disable k8s-extension temporarily: https://github.com/Azure/azure-cli-extensions/pull/6702
# Disable alias temporarily: https://github.com/Azure/azure-cli/pull/27717
# hybridaks is going to be deprecated: https://github.com/Azure/azure-cli/pull/29838
# db-up is going to be deprecated: https://github.com/Azure/azure-cli/pull/29887
# serviceconnector-passwordless's dependency is not compatible with 3.13 https://github.com/Azure/azure-cli/pull/31895
# partnercenter is not compatible with latest pydantic: https://github.com/Azure/azure-cli/pull/31967
ignore_list='azure-cli-ml fzf arcappliance arcdata connectedk8s k8s-extension alias hybridaks db-up serviceconnector-passwordless partnercenter'

# Does not exit if az extension add fails until all extensions have been tested
set +e

for ext in $output; do
    echo
    # Exact string matching against each item in the ignore list
    ignore_match=0
    for item in $ignore_list; do
        if [ "$ext" = "$item" ]; then
            ignore_match=1
            break
        fi
    done
    
    if [ $ignore_match -eq 1 ]; then
        echo "Ignore extension: $ext"
        continue
    fi

    echo "Verifying extension:" $ext
    az extension add -n $ext
    if [ $? != 0 ]
    then
        exit_code=1
        echo "Failed to load:" $ext
    fi
done

pip list -v

az self-test --debug
if [ $? != 0 ]
then
    exit_code=1
    echo "Failed to verify"
fi

exit $exit_code
