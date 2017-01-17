#!/bin/bash
set -e
export PYTHONPATH=
virtualenv package-verify-env
. package-verify-env/bin/activate
pip install -e scripts
python -m automation.tests.verify_packages
deactivate
# If we get here, all prev. commands returned 0 exit codes so we are done.
rm -rf package-verify-env
