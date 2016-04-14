#!/bin/bash
RSGRP="travistestresourcegroup"
STACC="travistestresourcegr3014"
export AZURE_STORAGE_ACCOUNT=$STACC
unset AZURE_STORAGE_KEY
export AZURE_STORAGE_CONNECTION_STRING=$(az storage account connection-string -g $RSGRP -n $STACC | cut -c 21-1000)
export AZURE_SAS_TOKEN=$(az storage account generate-sas --services b --resource-types sco --permission rwdl --expiry 2017-01-01T00:00Z)
unset AZURE_STORAGE_CONNECTION_STRING
echo SAS token set for storage account $STACC : $AZURE_SAS_TOKEN
echo
echo === Listing storage containers... ===
az storage container list
echo
echo === Trying to list shares should fail... ===
az storage share list
