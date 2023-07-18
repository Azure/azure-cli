#!/bin/bash

: "${CLI_VERSION:?CLI_VERSION environment variable not set.}"

yum check-update
yum install -y gcc rpm-build rpm-level rpmlint make bash corutils diffutils \
               path rpmdevtools python libffi-devel python3-devel openssl-devel \
               wget

set -ev

export REPO_PATH=`cd $(dirname $0); cd ../../../; pwd`
rpmbuild -v -bb --clean $REPO_PATH/scripts/release/rpm/azure-cli.spec && cp /root/rpmbuild/RPMS/x86_64/* /mnt/output
