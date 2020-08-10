# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import sys

COMMAND_MODULE_PREFIX = 'azure-cli-'
EXTENSION_PREFIX = 'azext_'
EXT_REPO_NAME = 'azure-cli-extensions'
IS_WINDOWS = sys.platform.lower() in ['windows', 'win32']

ENV_VAR_TEST_MODULES = 'AZDEV_TEST_TESTS'               # comma-separated list of modules to test
ENV_VAR_VIRTUAL_ENV = ['VIRTUAL_ENV', 'CONDA_PREFIX']   # used by system to identify virtual environment
ENV_VAR_TEST_LIVE = 'AZURE_TEST_RUN_LIVE'               # denotes that tests should be run live instead of played back
