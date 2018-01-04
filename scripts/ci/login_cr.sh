#!/usr/bin/env bash

# Login a container registry before build test droid
#
# This command assume you have az on the path and have login the subscription 
# containing the Azure Container Registry.
#

acr_name=${AZURE_CLI_BUILD_CR%%'.azurecr.io'}
az acr login -n $acr_name

