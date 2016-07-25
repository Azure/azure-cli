#!/bin/bash
set -e
export PYTHONPATH=
virtualenv package-verify-env
export AZURE_CLI_DISABLE_POST_INSTALL=1
. package-verify-env/bin/activate
python scripts/command_modules/package_verify.py
deactivate
# If we get here, all prev. commands returned 0 exit codes so we are done.
rm -rf package-verify-env
