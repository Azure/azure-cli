#!/bin/bash
USER="admin2@azuresdkteam.onmicrosoft.com"
PASS="Test1234"
az login -u $USER -p $PASS
unset AZURE_STORAGE_CONNECTION_STRING
unset AZURE_STORAGE_ACCOUNT
unset AZURE_STORAGE_KEY
unset AZURE_SAS_TOKEN
