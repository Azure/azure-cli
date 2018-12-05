#!/usr/bin/env bash

# Build an RPM containing the Azure CLI at a paritcular

set -exv

CLI_VERSION=`cat src/azure-cli/azure/cli/__init__.py | grep __version__ | sed s/' '//g | sed s/'__version__='// |  sed s/\"//g`

docker build \
    --target build-env \
    --build-arg cli_version=${CLI_VERSION} \
    -f ./scripts/release/rpm/Dockerfile \
    -t microsoft/azure-cli:centos7-builder \
    .

docker run \
    microsoft/azure-cli:centos7-builder \
    cat /root/rpmbuild/RPMS/x86_64/azure-cli-${CLI_VERSION}-1.el7.x86_64.rpm \
    > ${BUILD_STAGINDIRECTORY}/azure-cli-${CLI_VERSION}-1.el7.x86_64.rpm
