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
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Update APT packages
apt-get update
apt install -y apt-transport-https git gcc
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y libssl-dev libffi-dev python3-dev debhelper zlib1g-dev
apt-get install -y python3.7 python3.7-dev python3.7-venv

cd $WORKDIR
python3.7 -m venv env
source ./env/bin/activate

# build & install testsdk/fulltests
pip install wheel
./scripts/ci/build.sh
mkdir -p ${WORKDIR}/fulltests
find ./artifacts/build -name "azure_cli_testsdk*" | xargs pip install --prefix ${WORKDIR}/fulltests --upgrade --ignore-installed
find ./artifacts/build -name "azure_cli_fulltest*" | xargs pip install --prefix ${WORKDIR}/fulltests --upgrade --ignore-installed --no-deps

# prepare environment for pyinstaller
pip install pyinstaller==3.5
pip install --upgrade "setuptools<45.0.0"
rm -f ${WORKDIR}/src/azure-cli/azure/__init__.py ${WORKDIR}/src/azure-cli/azure/cli/__init__.py ${WORKDIR}/src/azure-cli-core/azure/__init__.py ${WORKDIR}/src/azure-cli-core/azure/cli/__init__.py ${WORKDIR}/src/azure-cli-telemetry/azure/__init__.py ${WORKDIR}/src/azure-cli-telemetry/azure/cli/__init__.py
pip install --no-deps -e ./src/azure-cli-telemetry
pip install --no-deps -e ./src/azure-cli-core
pip install --no-deps -e ./src/azure-cli
python ./scripts/pyinstaller/test/add_run_tests_command.py
python ./scripts/pyinstaller/test/update_core_init_command_modules.py
pip install -r ${WORKDIR}/src/azure-cli/requirements.py3.$(uname).txt

# add pytest & pytest-xdist for test purpose
pip install pytest pytest-xdist
pyinstaller ${WORKDIR}/az.spec
deactivate

# Create create directory for debian build
mkdir -p $WORKDIR/debian
$SCRIPT_DIR/prepare.sh $WORKDIR/debian $WORKDIR/az.completion $WORKDIR

dpkg-buildpackage -us -uc

deb_file=$WORKDIR/../azure-cli_${CLI_VERSION}-${CLI_VERSION_REVISION:=1}_all.deb
cp $deb_file /mnt/output/

dpkg -i $deb_file

shopt -s dotglob
cd ${WORKDIR}/fulltests/lib/python3.7/site-packages/azure/cli/command_moduels
find * -prune -type d | while IFS= read -r d; do
    if [[ "$d" != \__* ]]; then
        az run-tests --path ${WORKDIR}/fulltests/lib/python3.7/site-packages --module $d
    fi
done
