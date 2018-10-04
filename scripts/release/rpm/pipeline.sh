#!/usr/bin/env bash

# Build APT package in an Azure Container Instances
# This script assumes the Azure CLI is installed and logged in.

set -ex

CLI_VERSION=`cat src/azure-cli/azure/cli/__init__.py | grep __version__ | sed s/' '//g | sed s/'__version__='// |  sed s/\"//g`

docker run --rm \
           -v "$BUILD_SOURCESDIRECTORY":/mnt/repo \
           -v "$BUILD_STAGINGDIRECTORY":/mnt/output \
           -e CLI_VERSION=$CLI_VERSION \
           centos:7 \
           /mnt/repo/scripts/release/rpm/build.sh
