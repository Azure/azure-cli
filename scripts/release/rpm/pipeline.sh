#!/usr/bin/env bash

# Build assets related to Linux Distributions that use RPM/yum for installation.

set -exv

: "${BUILD_STAGINGDIRECTORY:?BUILD_STAGINGDIRECTORY environment variable not set.}"

CLI_VERSION=`cat src/azure-cli/azure/cli/__main__.py | grep __version__ | sed s/' '//g | sed s/'__version__='// |  sed s/\"//g`

# Create a container image that includes the source code and a built RPM using this file.
docker build \
    --target build-env \
    --build-arg cli_version=${CLI_VERSION} \
    -f ./scripts/release/rpm/Dockerfile.centos \
    -t azure/azure-cli:centos7-builder \
    .

# Continue the previous build, and create a container that has the current azure-cli build but not the source code.
docker build \
    --build-arg cli_version=${CLI_VERSION} \
    -f ./scripts/release/rpm/Dockerfile.centos \
    -t azure/azure-cli:centos7 \
    .

# Extract the built RPM so that it can be distributed independently.
docker run \
    azure/azure-cli:centos7-builder \
    cat /root/rpmbuild/RPMS/x86_64/azure-cli-${CLI_VERSION}-1.el7.x86_64.rpm \
    > ${BUILD_STAGINGDIRECTORY}/azure-cli-${CLI_VERSION}-1.el7.x86_64.rpm

# Save these too a staging directory so that later build phases can choose to save them as Artifacts or publish them to
# a registry.
#
# The products of `docker save` can be rehydrated using `docker load`.
mkdir -p ${BUILD_STAGINGDIRECTORY}/docker
docker save azure/azure-cli:centos7-builder | gzip > ${BUILD_STAGINGDIRECTORY}/docker/azure_azure-cli_centos7-builder.tar.gz &
docker save azure/azure-cli:centos7 | gzip > ${BUILD_STAGINGDIRECTORY}/docker/azure_azure-cli_centos7.tar.gz &
wait
