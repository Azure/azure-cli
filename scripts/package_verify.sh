#!/bin/bash
set -e
export PYTHONPATH=
virtualenv package-verify-env
export AZURE_CLI_DISABLE_POST_INSTALL=1
export AZURE_CLI_PRIVATE_PYPI_URL=http://40.112.211.51:8080
export AZURE_CLI_PRIVATE_PYPI_HOST=40.112.211.51
. package-verify-env/bin/activate
python scripts/command_modules/package_verify.py
deactivate
# If we get here, all prev. commands returned 0 exit codes so we are done.
rm -rf package-verify-env
