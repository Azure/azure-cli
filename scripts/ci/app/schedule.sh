#!/usr/bin/env bash

# The Job Management Task has its own virtualenv because it requires an azure-batch package to function.
pip install --user virtualenv
python -m virtualenv venv
. ./venv/bin/activate

pip install azure-batch==3.0.0

# schedule test tasks
scripts_dir=$(cd $(dirname $0); pwd)
python $scripts_dir/schedule.py $scripts_dir/all_tests.txt
