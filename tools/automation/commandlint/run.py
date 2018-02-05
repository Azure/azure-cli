# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function
import pkgutil

import os
import sys
import json
from importlib import import_module

import yaml

from azure.cli.core.application import APPLICATION, Application
from azure.cli.core.application import Configuration
from azure.cli.core.commands import load_params, _update_command_definitions
from azure.cli.core.help_files import helps
from azure.cli.core.commands.arm import add_id_parameters

try:
    from sets import Set as set
except ImportError:
    pass

WHITE_DATA_FILE = os.path.join(os.path.dirname(__file__), 'allowed-error.json')


def dump_no_help(modules):
    APPLICATION.initialize(Configuration())
    cmd_table = APPLICATION.configuration.get_command_table()

    exit_val = 0
    for cmd in cmd_table:
        cmd_table[cmd].load_arguments()

    for mod in modules:
        try:
            import_module('azure.cli.command_modules.' + mod).load_params(mod)
        except Exception as ex:
            print("EXCEPTION: {} for module {}".format(ex, str(mod)))

    _update_command_definitions(cmd_table)
    add_id_parameters(cmd_table)

    with open(WHITE_DATA_FILE, 'r') as white:
        white_data = json.load(white)

    white_list_commands = set(white_data.get('commands', []))
    white_list_subgroups = set(white_data.get('subgroups', []))
    white_list_parameters = white_data.get('parameters', {})

    command_list = set()
    subgroups_list = set()
    parameters = {}
    for cmd in cmd_table:
        if not cmd_table[cmd].description and cmd not in helps and cmd not in white_list_commands:
            command_list.add(cmd)
            exit_val = 1
        group_name = " ".join(cmd.split()[:-1])
        if group_name not in helps:
            if group_name not in subgroups_list and group_name not in white_list_subgroups and group_name:
                exit_val = 1
                subgroups_list.add(group_name)

        param_list = set()
        for key in cmd_table[cmd].arguments:
            name = cmd_table[cmd].arguments[key].name
            if not cmd_table[cmd].arguments[key].type.settings.get('help') and name not in white_list_parameters.get(
                    cmd, []):
                exit_val = 1
                param_list.add(name)
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
        "subgroups": subgroups_list,
        "commands": command_list,
        "parameters": parameters
    }

    return exit_val, data


def set_default(obj):
    """ change sets to lists for json """
    if isinstance(obj, set):
        return list(obj)


if __name__ == '__main__':
    try:
        mods_ns_pkg = import_module('azure.cli.command_modules')
        installed_command_modules = [modname for _, modname, _ in
                                     pkgutil.iter_modules(mods_ns_pkg.__path__)]
    except ImportError:
        pass

    result, failed_commands = dump_no_help(installed_command_modules)

    if any(len(failed_commands[key]) > 0 for key in failed_commands) or result != 0:
        print('==== FAILED COMMANDS ====')
        print(json.dumps(failed_commands, default=set_default, indent=2))

    sys.exit(0)  # enforce it
