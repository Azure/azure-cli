# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import pkgutil

import argparse
import os
import sys
from importlib import import_module

from automation.utilities.path import filter_user_selected_modules_with_tests
from azure.cli.core.application import APPLICATION, Application
from azure.cli.core.application import Configuration
from azure.cli.core.commands import load_params, _update_command_definitions



def dump_no_help(modules):
    cmd_table = APPLICATION.configuration.get_command_table()
    exit = 0
    for cmd in cmd_table:
        cmd_table[cmd].load_arguments()

    for mod in modules:
        try:
            import_module('azure.cli.command_modules.' + mod).load_params(mod)
        except Exception as ex:
            print("EXCEPTION: " + ex.message)

    _update_command_definitions(cmd_table)

    for cmd in cmd_table:
        descrip = cmd_table[cmd].description
        if not descrip:
            exit = 1
            print(cmd)

        for key in cmd_table[cmd].arguments:
            if cmd_table[cmd].arguments[key].type.settings.get('help') is None:
                exit = 1
                print(cmd + " " + str(cmd_table[cmd].arguments[key].name))
    return exit

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
        exit = dump_no_help(installed_command_modules)
    else:
        exit = dump_no_help(selected_modules)
    sys.exit(exit)

