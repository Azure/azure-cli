#!/usr/bin/env bash

set -ev

# install flake 8
pip install -qqq flake8

echo "Run flake8."
flake8 --statistics --config=./.flake8 

if [[ $TRAVIS_REPO_SLUG == "Azure/azure-cli" ]]; then
    # build packages
    . $(cd $(dirname $0); pwd)/artifacts.sh
fi
