#!/usr/bin/env bash
pwd
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
source /scripts/install_full.sh

echo "Listing Available Extensions:"
az extension list-available -otable

# turn off telemetry as it crowds output
export AZURE_CLI_DIAGNOSTICS_TELEMETRY=

output=$(az extension list-available --query [].name -otsv)

exit_code=0
for ext in $output; do
    echo
    # Use regex to detect if $ext is in $ignore_list

    echo "Verifying extension:" $ext
    url=$(python -c 'from azure.cli.core.extension._resolve import  resolve_from_index;print(resolve_from_index("$ext")[0])')
    curl -O $url
    pip install *.whl --dry-run
    if [ $? != 0 ]
        then
            exit_code=1
            echo "Failed to install:" $ext
        fi
    rm *.whl

done


exit $exit_code
