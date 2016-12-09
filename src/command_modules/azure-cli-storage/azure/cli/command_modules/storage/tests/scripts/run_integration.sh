#!/bin/bash

if [ -z $1 ] || [ -z $2 ]; then
    echo "usage: $0 <storage account name> <resource group name>"
    echo "       NOTE log in with your azure account with az first"
    exit 1
fi

command -v nosetests >/dev/null 2>&1 || {
    echo 'installing python nosetests ...'
    pip install nose
}

command -v coverage >/dev/null 2>&1 || {
    echo 'installing python coverage ...'
    pip install coverage
}

export test_connection_string=$(az storage account show-connection-string -n $1 -g $2 --query 'connectionString' | tr -d '"')

nosetests -v -i integration_test_*

