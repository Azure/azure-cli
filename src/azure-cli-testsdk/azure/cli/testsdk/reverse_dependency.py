# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from importlib import import_module

DUMMY_CLI_TYPE = 'DummyCli'
DUMMY_CLI_MODULE = 'azure.cli.core.mock'


def get_dummy_cli(*args, **kwargs):
    mod = import_module('azure.cli.core.mock')
    return getattr(mod, 'DummyCli')(*args, **kwargs)


def get_support_api_version_func():
    mod = import_module('azure.cli.core.profiles')
    return getattr(mod, 'supported_api_version')


def get_commands_loggers():
    mod = import_module('azure.cli.core.commands')
    return getattr(mod, 'logger')
