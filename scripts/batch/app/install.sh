#!/usr/bin/env bash

# install the product and test builds to a virtual environment

rm -rf $AZ_BATCH_NODE_SHARED_DIR/env
rm -rf $AZ_BATCH_NODE_SHARED_DIR/venv
rm -rf $AZ_BATCH_NODE_SHARED_DIR/app

pip install --user virtualenv
python -m virtualenv $AZ_BATCH_NODE_SHARED_DIR/venv

. $AZ_BATCH_NODE_SHARED_DIR/venv/bin/activate

pip install azure-cli-fulltest -f ./build
pip install nose

cp -R ./app $AZ_BATCH_NODE_SHARED_DIR
