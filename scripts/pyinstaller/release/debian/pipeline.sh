#!/usr/bin/env bash

# Build APT package in an Azure Container Instances
# This script assumes the Azure CLI is installed and logged in.

set -exv
DISTRO='xenial'
DISTRO_BASE_IMAGE=ubuntu:xenial
: ${DISTRO:?"DISTRO is not set"}
: ${DISTRO_BASE_IMAGE:?"DISTRO_BASE_IMAGE is not set"}

BUILD_SOURCESDIRECTORY=/home/xiaojxu/code/pyinstaller/azure-cli
BUILD_STAGINGDIRECTORY=/home/xiaojxu/code/pyinstaller/staging

CLI_VERSION=`cat src/azure-cli/azure/cli/__main__.py | grep __version__ | sed s/' '//g | sed s/'__version__='// |  sed s/\"//g`

docker run \
           -v "$BUILD_SOURCESDIRECTORY":/mnt/repo \
           -v "$BUILD_STAGINGDIRECTORY":/mnt/output \
           -e CLI_VERSION=$CLI_VERSION \
           -e CLI_VERSION_REVISION=1~$DISTRO \
           -e DEBIAN_FRONTEND=noninteractive \
	   -it \
           $DISTRO_BASE_IMAGE \
	   /bin/bash

#	   /mnt/repo/scripts/pyinstaller/release/debian/build.sh
