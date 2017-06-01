#!/bin/bash
set -ex
export PYTHONPATH=
virtualenv package-verify-env
. package-verify-env/bin/activate
pip install -e scripts
python -m automation.tests.verify_packages
python -m automation.tests.verify_dependencies
deactivate
# If we get here, all prev. commands returned 0 exit codes so we are done.
rm -rf package-verify-env
