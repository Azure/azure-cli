#!/usr/bin/env bash

set -exv

pip install virtualenv
python -m virtualenv env
. .env/bin/activate
pip install azdev==0.1.3
azdev setup -c
