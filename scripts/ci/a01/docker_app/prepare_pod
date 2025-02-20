#!/bin/bash

if [ "$AZURE_TEST_RUN_LIVE" != "True" ]; then
    echo "Environment variable AZURE_TEST_RUN_LIVE is NOT True."
    exit 0
fi

echo "Environment variable AZURE_TEST_RUN_LIVE is True. Login azure with service principal."

if [ -z "$A01_SP_USERNAME" ]; then
    echo "Missing service principal username." >&2
    exit 1
fi

if [ -z "$A01_SP_PASSWORD" ]; then
    echo "Missing service principal password." >&2
    exit 1
fi

if [ -z "$A01_SP_TENANT" ]; then
    echo "Missing service principal tenant." >&2
    exit 1
fi

az login --service-principal -u $A01_SP_USERNAME -p $A01_SP_PASSWORD -t $A01_SP_TENANT