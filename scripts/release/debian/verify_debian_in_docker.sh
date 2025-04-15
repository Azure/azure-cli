#!/usr/bin/env bash

# This script should be run in a docker to verify installing deb package from the apt repository.

apt update -y
apt install curl -y
counter=4

while [ $counter -gt 0 ]
do
    curl -sL https://aka.ms/InstallAzureCLIDeb | bash
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
