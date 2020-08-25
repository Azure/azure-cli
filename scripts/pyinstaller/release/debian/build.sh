#!/usr/bin/env bash
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# This script is expected to be run in a container environment, therefore sudo doesn't present
# here.

set -exv

: "${CLI_VERSION:?CLI_VERSION environment variable not set.}"
: "${CLI_VERSION_REVISION:?CLI_VERSION_REVISION environment variable not set.}"

WORKDIR=`cd $(dirname $0); cd ../../../../; pwd`

# Update APT packages
apt-get update
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.7 python3.7-venv


cd $WORKDIR
python3.7 -m venv env
source ./env/bin/activate
pip install pyinstaller==3.6
find ${WORKDIR}/src/ -name setup.py -type f | xargs -I {} dirname {} | grep -v azure-cli-testsdk | xargs pip install --no-deps
pip install -r ${WORKDIR}/src/azure-cli/requirements.py3.$(uname).txt
# pyinstaller ${WORKDIR}/az.spec


