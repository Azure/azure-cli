#!/usr/bin/env bash

# Build assets related to Linux Distributions that use RPM/yum for installation.

set -exv

: "${BUILD_STAGINGDIRECTORY:?BUILD_STAGINGDIRECTORY environment variable not set.}"

# DOCKERFILE should be one of 'ubi' or 'fedora'
: "${DOCKERFILE:?DOCKERFILE environment variable not set.}"
# IMAGE should be RHEL or Fedora image url
: "${IMAGE:?IMAGE environment variable not set.}"
# PYTHON_PACKAGE should be python package name
: "${PYTHON_PACKAGE:?PYTHON_PACKAGE environment variable not set.}"

CLI_VERSION=`cat src/azure-cli/azure/cli/__main__.py | grep __version__ | sed s/' '//g | sed s/'__version__='// |  sed s/\"//g`

# Create a container image that includes the source code and a built RPM using this file.
docker build \
    --target build-env \
    --build-arg cli_version=${CLI_VERSION} \
    --build-arg image=${IMAGE} \
    --build-arg python_package=${PYTHON_PACKAGE} \
    -f ./scripts/release/rpm/${DOCKERFILE}.dockerfile \
    -t azure/azure-cli:${DOCKERFILE}-builder \
    .

# Continue the previous build, and create a container that has the current azure-cli build but not the source code.
docker build \
    --build-arg cli_version=${CLI_VERSION} \
    --build-arg image=${IMAGE} \
    --build-arg python_package=${PYTHON_PACKAGE} \
    -f ./scripts/release/rpm/${DOCKERFILE}.dockerfile \
    -t azure/azure-cli:${DOCKERFILE} \
    .

# Extract the built RPM so that it can be distributed independently.
# The RPM file looks like azure-cli-2.32.0-1.el7.x86_64.rpm
id=$(docker create azure/azure-cli:${DOCKERFILE}-builder)
# https://docs.docker.com/engine/reference/commandline/cp/
# Append /. so that the x86_64 folder's content is copied, instead of x86_64 folder itself.
docker cp $id:/root/rpmbuild/RPMS/x86_64/. ${BUILD_STAGINGDIRECTORY}

# Save these too a staging directory so that later build phases can choose to save them as Artifacts or publish them to
# a registry.
#
# The products of `docker save` can be rehydrated using `docker load`.
# mkdir -p ${BUILD_STAGINGDIRECTORY}/docker
# docker save azure/azure-cli:${IMAGE}-builder | gzip > ${BUILD_STAGINGDIRECTORY}/docker/azure_azure-cli_${IMAGE}-builder.tar.gz &
# docker save azure/azure-cli:${IMAGE} | gzip > ${BUILD_STAGINGDIRECTORY}/docker/azure_azure-cli_${IMAGE}.tar.gz &
# wait
