#!/usr/bin/env bash

set -e

unset AZURE_CLI_DIAGNOSTICS_TELEMETRY

if [ -z $PUBLISH_STORAGE_SAS ] || [ -z $PUBLISH_STORAGE_ACCT ] || [ -z $PUBLISH_CONTAINER ]; then
    echo 'Missing publish storage account credential. Skip publishing.'
    exit 0
fi

echo 'Generate artifacts'
. $(cd $(dirname $0); pwd)/artifacts.sh 

echo 'Set up output folder'
mkdir -p ./publish/$TRAVIS_REPO_SLUG/$TRAVIS_BRANCH/$TRAVIS_BUILD_NUMBER
cp -R $share_folder/* ./publish/$TRAVIS_REPO_SLUG/$TRAVIS_BRANCH/$TRAVIS_BUILD_NUMBER

echo 'Listing output folder'
ls -R ./publish

echo 'Installing public Azure CLI for uploading operation.'
pip install -qqq azure-cli

echo 'Uploading ...'
az storage blob upload-batch -s ./publish \
                             -d $PUBLISH_CONTAINER \
                             --account-name $PUBLISH_STORAGE_ACCT \
                             --sas-token $PUBLISH_STORAGE_SAS \
                             -otable
