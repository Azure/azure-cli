#!/usr/bin/env bash

set -ev

pip install virtualenv

python -m virtualenv venv/
. ./venv/bin/activate
pip install azdev==0.1.3
azdev setup -c $(pwd)
