#!/usr/bin/env bash
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

set -evx

IMAGE_NAME=clibuild$BUILD_BUILDNUMBER
CLI_VERSION=`cat src/azure-cli/azure/cli/__main__.py | grep __version__ | sed s/' '//g | sed s/'__version__='// |  sed s/\"//g`

docker build --no-cache \
             --build-arg BUILD_DATE="`date -u +"%Y-%m-%dT%H:%M:%SZ"`" \
             --build-arg CLI_VERSION=$CLI_VERSION \
             --tag $IMAGE_NAME:latest \
             $BUILD_SOURCESDIRECTORY

docker save -o "$BUILD_STAGINGDIRECTORY/docker-azure-cli-${CLI_VERSION}.tar" $IMAGE_NAME:latest
