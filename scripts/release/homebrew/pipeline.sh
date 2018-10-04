#!/bin/bash

root=$(cd $(dirname $0); pwd)

set -ex

CLI_VERSION=`cat $SYSTEM_ARTIFACTSDIRECTORY/metadata/version`
HOMEBREW_UPSTREAM_URL=`cat $BUILD_STAGINGDIRECTORY/github/upstream_url`
TAR_NAME=azure-cli-$CLI_VERSION.tar.gz

docker_files=$(cd $BUILD_SOURCESDIRECTORY/scripts/release/homebrew/docker; pwd)
pypi_files=$(cd $SYSTEM_ARTIFACTSDIRECTORY/pypi; pwd)

echo "Generating formula in docker container ... "
docker run -v $docker_files:/mnt/scripts \
           -v $pypi_files:/mnt/pypi \
           -e CLI_VERSION=$CLI_VERSION \
           -e HOMEBREW_UPSTREAM_URL=$HOMEBREW_UPSTREAM_URL \
           --name azurecli \
           python:3.6 \
           /mnt/scripts/run.sh

# clean up
rm -rf $BUILD_STAGINGDIRECTORY/metadata
rm -rf $BUILD_STAGINGDIRECTORY/pypi

docker cp azurecli:azure-cli.rb $BUILD_STAGINGDIRECTORY/azure-cli.rb
docker rm --force azurecli
