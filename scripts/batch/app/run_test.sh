#!/usr/bin/env bash

# execute individual test in current task

# expected input: 
#	$1 the test class
#	$2 the test method

# expected virtual environment (if run live):
#   AUTOMATION_SP_NAME
#   AUTOMATION_SP_PASSWORD
#   AUTOMATION_SP_TENANT

set -e

# enter virtual environment:
. $AZ_BATCH_NODE_SHARED_DIR/venv/bin/activate

# execute az to create the configure folder
az --version

if [ "$AZURE_TEST_RUN_LIVE" == "True" ]; then
    az login --service-principal -u $AUTOMATION_SP_NAME -p $AUTOMATION_SP_PASSWORD -t $AUTOMATION_SP_TENANT
fi

# execute the test
python -m unittest -v $1.$2 2>&1
