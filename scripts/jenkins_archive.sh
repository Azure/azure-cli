#!/usr/bin/env bash

# Archive build

set -x

if [ -z $BUILD_NUMBER ]; then
    echo "Environment variable BUILD_NUMBER is missing."
    exit 1
fi

export
echo "build branch $BRANCH_NAME"

version=$(printf '%.8d' $BUILD_NUMBER)
echo "Version number: $version"

if [ -d /var/build_share ]; then
    echo 'Directory /var/build_share is found. The artifacts will be archived there.'
    mkdir -p /var/build_share/$BRANCH_NAME/$version
    cp -R ./artifacts/ /var/build_share/$BRANCH_NAME/$version
else
    echo 'Directory /var/build_share is not found. Exit without taking any actions.'
fi
