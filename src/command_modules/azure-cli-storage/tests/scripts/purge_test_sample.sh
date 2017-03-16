#!/bin/bash

# clear all blob container and file share in the given storage account
# USE WITH CAUTIOUS

if [ -z $1 ] || [ -z $2 ]; then
    echo "usage: $0 <storage account name> <resource group>"
    exit 1
fi

connection_string=$(az storage account show-connection-string -n $1 -g $2 --query 'connectionString' | tr -d '"')
export AZURE_STORAGE_CONNECTION_STRING=$connection_string

for c in $(az storage container list -o tsv | cut -f2); do
    az storage container delete -n $c -o tsv
done

for s in $(az storage share list -o tsv | cut -f2); do
    az storage share delete -n $s -o tsv
done


