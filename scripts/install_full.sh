#!/usr/bin/env bash

#######################################################################################################################
# This script installs all dependencies found in this repository directly, without transitive dependencies, then uses
# the appropriate requirements.txt file to install all transitive dependencies.
#
# NOTE: It should be invoked from an activated virtual environment, unless targeting system python directly is
# acceptable.
#
# The intention is to allow packagers, people working with the RPM spec or debian rules file for example, to not have
# duplicate that logic required to install from source what is distributed in this repository and via PyPI for items
# living outside of this repository.
#######################################################################################################################

REPO_ROOT="$(dirname ${BASH_SOURCE[0]})/.."

pushd ${REPO_ROOT} > /dev/null

find src/ -name setup.py -type f | xargs -I {} dirname {} | grep -v azure-cli-testsdk | xargs pip install --no-deps
pip install ./privates/azure_mgmt_containerregistry-3.0.0rc15-py2.py3-none-any.whl
pip install -r ./src/azure-cli/requirements.$(python ./scripts/get-python-version.py).$(uname).txt
pip show azure-mgmt-containerregistry
pip list

popd > /dev/null
