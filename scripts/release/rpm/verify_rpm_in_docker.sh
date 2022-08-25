#!/usr/bin/env bash

# This script should be run in a docker to verify installing rpm package from the yum repository.

if [ "$IMPORT_KEY" == "true" ]; then
    rpm --import https://packages.microsoft.com/keys/microsoft.asc
    if [ ! -z $RPM_URL ]; then
        dnf install -y $RPM_URL
    fi
fi

counter=4

while [ $counter -gt 0 ]; do
    $DNF_COMMAND install azure-cli -y
    ACTUAL_VERSION=$(az version | sed -n 's|"azure-cli": "\(.*\)",|\1|p' | sed 's|[[:space:]]||g')
    echo "actual version:${ACTUAL_VERSION}"
    echo "expected version:${CLI_VERSION}"

    if [ "$ACTUAL_VERSION" != "$CLI_VERSION" ]; then
        if [ ! -z "$ACTUAL_VERSION" ]; then
            echo "Latest package is not in the repo."
            exit 1
        fi
        echo "wait 5m"
        sleep 300
        counter=$(( $counter - 1 ))
    else
        echo "Latest package is verified."
        exit 0
    fi
done
echo "Timeout!"
exit 1
