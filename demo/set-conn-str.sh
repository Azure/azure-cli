#!/bin/bash
RSGRP="travistestresourcegroup"
STACC="travistestresourcegr3014"
export AZURE_STORAGE_CONNECTION_STRING=$(az storage account connection-string -g $RSGRP -n $STACC | cut -c 21-1000)
echo Connection string set : $AZURE_STORAGE_CONNECTION_STRING
echo
echo === Listing storage containers... ===
az storage container list
echo
echo === Listing storage shares... ===
az storage share list
