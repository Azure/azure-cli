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
import yaml
from importlib import import_module

from automation.utilities.path import filter_user_selected_modules_with_tests
from azure.cli.core.application import APPLICATION, Application
from azure.cli.core.application import Configuration
from azure.cli.core.commands import load_params, _update_command_definitions
from azure.cli.core.help_files import helps



def dump_no_help(modules):
    cmd_table = APPLICATION.configuration.get_command_table()

    exit_val = 0
    for cmd in cmd_table:
        cmd_table[cmd].load_arguments()

    for mod in modules:
        try:
            import_module('azure.cli.command_modules.' + mod).load_params(mod)
        except Exception as ex:
            print("EXCEPTION: " + str(mod))

    _update_command_definitions(cmd_table)

    command_list = []
    subgroups_list = []
    parameters = {}
    for cmd in cmd_table:
        if not cmd_table[cmd].description and cmd not in helps:
            command_list.append(cmd)
            exit_val = 1
        group_name = " ".join(cmd.split()[:-1])
        if group_name not in helps:
            exit_val = 1
            if group_name not in subgroups_list:
                subgroups_list.append(group_name)

        param_list = []
        for key in cmd_table[cmd].arguments:
            if not cmd_table[cmd].arguments[key].type.settings.get('help'):
                exit_val = 1
                param_list.append(cmd_table[cmd].arguments[key].name)
        if param_list:
            parameters[cmd] = param_list

    for cmd in helps:
        diction_help = yaml.load(helps[cmd])
        if "short-summary" in diction_help and "type" in diction_help:
            if diction_help["type"] == "command" and cmd in command_list:
                command_list.remove(cmd)
            elif diction_help["type"] == "group" and cmd in subgroups_list:
                subgroups_list.remove(cmd)
        if "parameters" in diction_help:
            for param in diction_help["parameters"]:
                if "short-summary" in param and param["name"].split()[0] in parameters:
                    parameters.pop(cmd, None)

    data = {
        "subgroups" : subgroups_list,
        "commands" : command_list,
        "parameters" : parameters
    }

    print(json.dumps(data, indent=2, sort_keys=True))

    return exit_val

if __name__ == '__main__':
    try:
        mods_ns_pkg = import_module('azure.cli.command_modules')
        installed_command_modules = [modname for _, modname, _ in
                                     pkgutil.iter_modules(mods_ns_pkg.__path__)]
    except ImportError:
        pass
    exit_value = dump_no_help(installed_command_modules)
    sys.exit(exit_value)

