"""tooling integration"""
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function

import os
import traceback
from importlib import import_module
from sys import stderr
import pkgutil
import yaml

from six.moves import configparser

from azure.cli.core.application import APPLICATION, Configuration
from azure.cli.core.commands import _update_command_definitions, BLACKLISTED_MODS
from azure.cli.core._profile import _SUBSCRIPTION_NAME, Profile
from azure.cli.core._session import ACCOUNT
from azure.cli.core._environment import get_config_dir as cli_config_dir
from azure.cli.core._config import az_config, GLOBAL_CONFIG_PATH, DEFAULTS_SECTION
from azure.cli.core.help_files import helps
from azure.cli.core.util import CLIError


GLOBAL_ARGUMENTS = {
    'verbose': {
        'options': ['--verbose'],
        'help': 'Increase logging verbosity. Use --debug for full debug logs.'
    },
    'debug': {
        'options': ['--debug'],
        'help': 'Increase logging verbosity to show all debug logs.'
    },
    'output': {
        'options': ['--output', '-o'],
        'help': 'Output format',
        'choices': ['json', 'tsv', 'table', 'jsonc']
    },
    'help': {
        'options': ['--help', '-h'],
        'help': 'Get more information about a command'
    },
    'query': {
        'options': ['--query'],
        'help': 'JMESPath query string. See http://jmespath.org/ for more information and examples.'
    }
}


def initialize():
    _load_profile()


def _load_profile():
    azure_folder = cli_config_dir()
    if not os.path.exists(azure_folder):
        os.makedirs(azure_folder)

    ACCOUNT.load(os.path.join(azure_folder, 'azureProfile.json'))


def load_command_table():
    APPLICATION.initialize(Configuration())
    command_table = APPLICATION.configuration.get_command_table()
    _install_modules(command_table)
    return command_table


def _install_modules(command_table):
    for cmd in command_table:
        command_table[cmd].load_arguments()

    try:
        mods_ns_pkg = import_module('azure.cli.command_modules')
        installed_command_modules = [modname for _, modname, _ in
                                     pkgutil.iter_modules(mods_ns_pkg.__path__)
                                     if modname not in BLACKLISTED_MODS]
    except ImportError:
        pass
    for mod in installed_command_modules:
        try:
            mod = import_module('azure.cli.command_modules.' + mod)
            mod.load_params(mod)
            mod.load_commands()

        except Exception:  # pylint: disable=broad-except
            print("Error loading: {}".format(mod), file=stderr)
            traceback.print_exc(file=stderr)
    _update_command_definitions(command_table)


HELP_CACHE = {}


def get_help(group_or_command):
    if group_or_command not in HELP_CACHE and group_or_command in helps:
        HELP_CACHE[group_or_command] = yaml.load(helps[group_or_command])
    return HELP_CACHE.get(group_or_command)


PROFILE = Profile()


def get_current_subscription():
    _load_profile()
    try:
        return PROFILE.get_subscription()[_SUBSCRIPTION_NAME]
    except CLIError:
        return None  # Not logged in


def get_configured_defaults():
    _reload_config()
    try:
        options = az_config.config_parser.options(DEFAULTS_SECTION)
        defaults = {}
        for opt in options:
            value = az_config.get(DEFAULTS_SECTION, opt)
            if value:
                defaults[opt] = value
        return defaults
    except configparser.NoSectionError:
        return {}


def is_required(argument):
    required_tooling = hasattr(argument.type, 'required_tooling') and argument.type.required_tooling is True
    return required_tooling and argument.name != 'is_linux'


def get_defaults(arguments):
    _reload_config()
    return {name: _get_default(argument) for name, argument in arguments.items()}


def _get_default(argument):
    configured = _find_configured_default(argument)
    return configured or argument.type.settings.get('default')


def run_argument_value_completer(command, argument, cli_arguments):
    try:
        args = _to_argument_object(command, cli_arguments)
        _add_defaults(command, args)
        return argument.completer('', '', args)
    except TypeError:
        try:
            return argument.completer('')
        except TypeError:
            try:
                return argument.completer()
            except TypeError:
                return None


def _to_argument_object(command, cli_arguments):
    result = lambda: None  # noqa: E731
    for argument_name, value in cli_arguments.items():
        name, _ = _find_argument(command, argument_name)
        setattr(result, name, value)
    return result


def _find_argument(command, argument_name):
    for name, argument in command.arguments.items():
        if argument_name in argument.options_list:
            return name, argument
    return None, None


def _add_defaults(command, arguments):
    _reload_config()
    for name, argument in command.arguments.items():
        if not hasattr(arguments, name):
            default = _find_configured_default(argument)
            if default:
                setattr(arguments, name, default)

    return arguments


def _reload_config():
    az_config.config_parser.read(GLOBAL_CONFIG_PATH)


def _find_configured_default(argument):
    if not (hasattr(argument.type, 'default_name_tooling') and argument.type.default_name_tooling):
        return None
    try:
        return az_config.get(DEFAULTS_SECTION, argument.type.default_name_tooling, None)
    except configparser.NoSectionError:
        return None
