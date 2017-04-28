#!/usr/bin/env bash

# Archive build

# Load command build variables
. $(cd $(dirname $0); pwd)/jenkins_common.sh

if [ -d /var/build_share ]; then
    echo 'Directory /var/build_share is found. The artifacts will be archived there.'
    mkdir -p /var/build_share/$BRANCH_NAME/$version
    cp -R ./artifacts/ /var/build_share/$BRANCH_NAME/$version
else
    echo 'Directory /var/build_share is not found. Exit without taking any actions.'
fi
