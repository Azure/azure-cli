#!/usr/bin/env bash

set -ev

mkdir -p tmp_package
cd tmp_package
VOL=$(pwd)
curl -O https://raw.githubusercontent.com/azure/azure-cli/release-scripts/scripts/release/rpm/verify_rpm_in_docker.sh
cd ..

IMAGE=(
    registry.access.redhat.com/ubi8/ubi:8.4
    registry.access.redhat.com/ubi9/ubi:9.0.0
    cblmariner.azurecr.io/base/core:1.0
    mcr.microsoft.com/cbl-mariner/base/core:2.0
)
IMPORT_KEY=(true true false false)
RPM_URL=(
    https://packages.microsoft.com/config/rhel/8/packages-microsoft-prod.rpm
    https://packages.microsoft.com/config/rhel/9.0/packages-microsoft-prod.rpm
    ""
    ""
)
DNF_COMMAND=(dnf dnf tdnf tdnf)

for i in ${!IMAGE[@]}; do
    echo Verifying ${IMAGE[$i]}
    docker run -e CLI_VERSION=$CLI_VERSION -e IMPORT_KEY=${IMPORT_KEY[$i]} -e RPM_URL=${RPM_URL[$i]} -e DNF_COMMAND=${DNF_COMMAND[$i]} -v $VOL:/_ ${IMAGE[$i]} /bin/bash -c "source /_/verify_rpm_in_docker.sh"
    if [ $? != 0 ]; then
        echo Failed to verify rpm in ${IMAGE[$i]}
        exit 1
    fi
done
