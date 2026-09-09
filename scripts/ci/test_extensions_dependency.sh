#!/usr/bin/env bash
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
source ./scripts/install_full.sh

cp -r env/lib lib_backup

echo "Listing Available Extensions:"
az extension list-available -otable

# turn off telemetry as it crowds output
export AZURE_CLI_DIAGNOSTICS_TELEMETRY=

output=$(az extension list-available --query [].name -otsv)

ignore_list='attestation cloud-service functionapp serial-console'

exit_code=0
for ext in $output; do
    echo

    echo "Verifying extension:" $ext
    url=$(python -c "from azure.cli.core.extension._resolve import  resolve_from_index;print(resolve_from_index('$ext')[0])")
    echo Download $url
    curl -sOL $url
    pip install *.whl
    # pip still install new package even if conflict occurs, use pip check to verify
    pip check
    if [ $? != 0 ]
        then
            # Use regex to detect if $ext is in $ignore_list
            if [[ $ignore_list =~ $ext ]]; then
                echo "Ignore extension: $ext"
            else
                echo "Dependency conflict detected:" $ext
                exit_code=1
            fi
        fi
    rm *.whl
    deactivate
    rsync -ar --delete "lib_backup/" "env/lib"
    source env/bin/activate

done


exit $exit_code
