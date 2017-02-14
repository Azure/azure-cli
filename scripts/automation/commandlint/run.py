# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import pkgutil

import argparse
import os
import sys

from automation.utilities.path import filter_user_selected_modules_with_tests
from azure.cli.core.application import APPLICATION, Application
from azure.cli.core.application import Configuration
from azure.cli.core.commands import load_params, _update_command_definitions

from importlib import import_module


def dump_no_help(modules):
    cmd_table = APPLICATION.configuration.get_command_table()
    exit = 0
    for cmd in cmd_table:
        cmd_table[cmd].load_arguments()

    for mod in modules:
        # print('loading params for', mod)
        try:
            import_module('azure.cli.command_modules.' + mod).load_params(mod)
        except Exception as ex:
            print("EXCPETION: " + ex.message)

    _update_command_definitions(cmd_table)

    for cmd in cmd_table:
        descrip = cmd_table[cmd].description
        if descrip is None or descrip is "":
            exit = 1
            print(cmd)

        for key in cmd_table[cmd].arguments:
            if cmd_table[cmd].arguments[key].type.settings.get('help') is None:
                exit = 1
                print(cmd + " " + str(cmd_table[cmd].arguments[key].name))
    sys.exit(exit)

if __name__ == '__main__':
    parse = argparse.ArgumentParser('Test tools')
    parse.add_argument('--module', dest='modules', action='append',
                       help='The modules of which the test to be run. Accept short names, except '
                            'azure-cli, azure-cli-core and azure-cli-nspkg. The modules list can '
                            'also be set through environment variable AZURE_CLI_TEST_MODULES. The '
                            'value should be a string of comma separated module names. The '
                            'environment variable will be overwritten by command line parameters.')
    parse.add_argument('--non-parallel', action='store_true',
                       help='Not to run the tests in parallel.')
    parse.add_argument('--live', action='store_true', help='Run all the tests live.')
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
        dump_no_help(installed_command_modules)
    else:
        dump_no_help(selected_modules)

