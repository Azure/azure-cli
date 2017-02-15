# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function
import pkgutil

import argparse
import os
import sys
import json
from importlib import import_module

from automation.utilities.path import filter_user_selected_modules_with_tests
from azure.cli.core.application import APPLICATION, Application
from azure.cli.core.application import Configuration
from azure.cli.core.commands import load_params, _update_command_definitions



def dump_no_help(modules):
    cmd_table = APPLICATION.configuration.get_command_table()

    exit_val = 0
    for cmd in cmd_table:
        cmd_table[cmd].load_arguments()

    for mod in modules:
        try:
            import_module('azure.cli.command_modules.' + mod).load_params(mod)
        except Exception as ex:
            print("EXCEPTION: " + ex.message)

    _update_command_definitions(cmd_table)

    command_list = []
    subgroups_list = []
    parameters = {}
    for cmd in cmd_table:
        if not cmd_table[cmd].description:
            command_list.append(cmd)
            exit_val = 1
        group_name = " ".join(cmd.split()[:-1])
        if group_name in cmd_table and not cmd_table[group_name].description:
            exit_val = 1
            if group_name not in subgroups_list:
                subgroups_list.append(group_name)

        param_list = []
        for key in cmd_table[cmd].arguments:
            if cmd_table[cmd].arguments[key].type.settings.get('help') is None:
                exit_val = 1
                param_list.append(cmd_table[cmd].arguments[key].type.settings.get('name'))

        parameters[cmd] = param_list
    data = {
        "subgroups" : subgroups_list,
        "commands" : command_list,
        "parameters" : parameters
    }
    json.dumps(data)
    return exit_val

if __name__ == '__main__':
    parse = argparse.ArgumentParser('Test tools')
    parse.add_argument('--module', dest='modules', action='append',
                       help='The modules of which the test to be run. Accept short names, except '
                            'azure-cli, azure-cli-core and azure-cli-nspkg. The modules list can '
                            'also be set through environment variable AZURE_CLI_TEST_MODULES. The '
                            'value should be a string of comma separated module names. The '
                            'environment variable will be overwritten by command line parameters.')
    args = parse.parse_args()

    if not args.modules and os.environ.get('AZURE_CLI_TEST_MODULES', None):
        print('Test modules list is parsed from environment variable AZURE_CLI_TEST_MODULES.')
        args.modules = [m.strip() for m in os.environ.get('AZURE_CLI_TEST_MODULES').split(',')]

    selected_modules = filter_user_selected_modules_with_tests(args.modules)
    if not selected_modules:
        try:
            mods_ns_pkg = import_module('azure.cli.command_modules')
            installed_command_modules = [modname for _, modname, _ in
                                         pkgutil.iter_modules(mods_ns_pkg.__path__)]
        except ImportError:
            pass
        exit_value = dump_no_help(installed_command_modules)
    else:
        exit_value = dump_no_help(selected_modules)
    sys.exit(exit_value)

