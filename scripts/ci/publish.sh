#!/usr/bin/env bash

set -ev

unset AZURE_CLI_DIAGNOSTICS_TELEMETRY
pip install azure-storage-blob==1.1.0

wd=`cd $(dirname $0); pwd`

if [ -z "$PUBLISH_STORAGE_SAS" ] || [ -z "$PUBLISH_STORAGE_ACCT" ] || [ -z "$PUBLISH_CONTAINER" ]; then
    echo 'Missing publish storage account credential. Skip publishing to store.'
    exit 0
fi

echo 'Generate artifacts'
. $wd/artifacts.sh 

echo 'Upload artifacts to store'
python $wd/publish.py store -b $share_folder -c $PUBLISH_CONTAINER -a $PUBLISH_STORAGE_ACCT -s "$PUBLISH_STORAGE_SAS"

if [ -z "$EDGE_STORAGE_SAS" ] || [ -z "$EDGE_STORAGE_ACCT" ] || [ -z "$EDGE_CONTAINER" ]; then
    echo 'Missing edge storage account credential. Skip publishing the edge build.'
    exit 0
fi

echo 'Upload artifacts to edge feed'
python $wd/publish.py nightly -b $share_folder -c $EDGE_CONTAINER -a $EDGE_STORAGE_ACCT -s "$EDGE_STORAGE_SAS"

