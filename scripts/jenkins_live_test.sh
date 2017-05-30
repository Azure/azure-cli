#!/usr/bin/env bash

# Run live test in build environment

# Remarks: In an ideal setting, the live test will be run against built azure cli packages
# instead of set up dev environment and run from code itself. However because legacy tests
# take dependencies on vcr_test_base which is in azure-cli-core module but not published,
# these tests have to be run from dev code.

set -e

# Prepare virtual environment
command -v pip >/dev/null 2>&1 || { echo 'PIP is not installed'; exit 1; }
pip install -Uq --user virtualenv
python -m virtualenv --clear env
. ./env/bin/activate

# Set up configuration folder
mkdir -p az_config
export AZURE_CONFIG_DIR=$(cd az_config; pwd)

# Set up dev env
python ./scripts/dev_setup.py

# Log in test subscription
az login -u $AZURE_CLI_TEST_DEV_SP_NAME -p $AZURE_CLI_TEST_DEV_SP_PASSWORD -t $AZURE_CLI_TEST_DEV_SP_TENANT --service-principal
az account list -otable

# Run specified test module
python -m automation.tests.run --module $1 --live
