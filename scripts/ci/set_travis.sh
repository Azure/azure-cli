#!/usr/bin/env bash

# Set the storage credentials for the given travis repo.

# Pre-requisite:
# 1. Travis CLI https://github.com/travis-ci/travis.rb
# 2. Azure CLI
# 3. Login Azure CLI with credential which has access to the target storage account.

# Input:
# $1 - storage account name
# $2 - travis CI repo name

set -ev

export AZURE_STORAGE_ACCOUNT=$1

az storage container create -n store -otsv
az storage container create -n edge -otsv

expiry_date=`date -v+6m +'%Y-%m-%dT00:00Z'`
echo "Set SAS expiry date to $expiry_date"

travis env set -r $2 PUBLISH_STORAGE_ACCT $1
travis env set -r $2 PUBLISH_STORAGE_SAS $(az storage container generate-sas -n store --permissions w --expiry $expiry_date -otsv)
travis env set -r $2 -P PUBLISH_CONTAINER store

travis env set -r $2 EDGE_STORAGE_ACCT $1
travis env set -r $2 EDGE_STORAGE_SAS $(az storage container generate-sas -n edge --permissions lw --expiry $expiry_date -otsv)
travis env set -r $2 -P EDGE_CONTAINER edge

travis env list -r $2
