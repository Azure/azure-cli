#!/usr/bin/env bash

# Build APT package in an Azure Container Instances
# This script assumes the Azure CLI is installed and logged in.

set -exv

: ${DISTRO:?"DISTRO is not set"}
: ${DISTRO_BASE_IMAGE:?"DISTRO_BASE_IMAGE is not set"}

CLI_VERSION=`cat src/azure-cli/azure/cli/__main__.py | grep __version__ | sed s/' '//g | sed s/'__version__='// |  sed s/\"//g`

docker run --rm \
           -v "$BUILD_SOURCESDIRECTORY":/mnt/repo \
           -v "$BUILD_STAGINGDIRECTORY":/mnt/output \
           -v "$SYSTEM_ARTIFACTSDIRECTORY":/mnt/artifacts \
           -e CLI_VERSION=$CLI_VERSION \
           -e CLI_VERSION_REVISION=1~$DISTRO \
           -e DEBIAN_FRONTEND=noninteractive \
           $DISTRO_BASE_IMAGE \
           /mnt/repo/scripts/release/debian/build.sh

if [ -d $BUILD_STAGINGDIRECTORY/pypi ]; then
    rm -rf $BUILD_STAGINGDIRECTORY/pypi
fi