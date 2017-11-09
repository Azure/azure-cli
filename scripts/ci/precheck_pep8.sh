#!/usr/bin/env bash

set -e

# build packages
. $(cd $(dirname $0); pwd)/artifacts.sh

# install flake 8
pip install -qqq flake8

echo "Run flake8."
flake8 --statistics --exclude=azure_bdist_wheel.py --append-config=./.flake8 ./src

