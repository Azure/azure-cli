#!/usr/bin/env bash

# Build assets related to Linux Distributions that use RPM/yum for installation specific for Azure Linux

set -exv

: "${BUILD_STAGINGDIRECTORY:?BUILD_STAGINGDIRECTORY environment variable not set.}"

# IMAGE should be Azure Linux docker image url, such as mcr.microsoft.com/cbl-mariner/base/core:2.0
: "${IMAGE:?IMAGE environment variable not set.}"

CLI_VERSION=`cat src/azure-cli/azure/cli/__main__.py | grep __version__ | sed s/' '//g | sed s/'__version__='// |  sed s/\"//g`

# PIP_INDEX_URL env must exist in `docker build --secret`, use an empty string if it doesn't exist.
export PIP_INDEX_URL=${PIP_INDEX_URL}

# Create a container image that includes the source code and a built RPM using this file.
docker build \
    --target build-env \
    --build-arg cli_version=${CLI_VERSION} \
    --build-arg image=${IMAGE} \
    --secret id=PIP_INDEX_URL \
    -f ./scripts/release/rpm/azurelinux.dockerfile \
    -t azure/azure-cli:azurelinux-builder \
    .

# Continue the previous build, and create a container that has the current azure-cli build but not the source code.
docker build \
    --build-arg cli_version=${CLI_VERSION} \
    --build-arg image=${IMAGE} \
    -f ./scripts/release/rpm/azurelinux.dockerfile \
    -t azure/azure-cli:azurelinux \
    .

# Extract the built RPM so that it can be distributed independently.
# The RPM file looks like azure-cli-2.32.0-1.x86_64.rpm
id=$(docker create azure/azure-cli:azurelinux-builder bash)
# https://docs.docker.com/engine/reference/commandline/cp/
# Append /. so that the x86_64 folder's content is copied, instead of x86_64 folder itself.
docker cp $id:/out/. ${BUILD_STAGINGDIRECTORY}

# Save these too a staging directory so that later build phases can choose to save them as Artifacts or publish them to
# a registry.
#
# The products of `docker save` can be rehydrated using `docker load`.
# mkdir -p ${BUILD_STAGINGDIRECTORY}/docker
# docker save azure/azure-cli:azurelinux-builder | gzip > ${BUILD_STAGINGDIRECTORY}/docker/azure_azure-cli_azurelinux-builder.tar.gz &
# docker save azure/azure-cli:azurelinux | gzip > ${BUILD_STAGINGDIRECTORY}/docker/azure_azure-cli_azurelinux.tar.gz &
# wait
