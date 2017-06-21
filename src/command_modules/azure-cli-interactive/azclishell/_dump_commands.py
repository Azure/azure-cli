# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from importlib import import_module

import json
import os
import pkgutil
import yaml

from azure.cli.core.application import APPLICATION, Configuration
from azure.cli.core.commands import _update_command_definitions, BLACKLISTED_MODS
from azure.cli.core.help_files import helps
from azure.cli.core.commands.arm import add_id_parameters

import azclishell.configuration as config

APPLICATION.initialize(Configuration())
CMD_TABLE = APPLICATION.configuration.get_command_table()


def install_modules():
    installed_command_modules = []
    for cmd in CMD_TABLE:
        try:
            CMD_TABLE[cmd].load_arguments()
        except (ImportError, ValueError):
            pass
        mods_ns_pkg = import_module('azure.cli.command_modules')
    for _, modname, _ in pkgutil.iter_modules(mods_ns_pkg.__path__):
        if modname not in BLACKLISTED_MODS:
            installed_command_modules.append(modname)

    for mod in installed_command_modules:
        try:
            mod = import_module('azure.cli.command_modules.' + mod)
            mod.load_params(mod)
            mod.load_commands()

        except Exception:  # pylint: disable=broad-except
            print("Error loading: {}".format(mod))
    _update_command_definitions(CMD_TABLE)


def dump_command_table():
    """ dumps the command table """
    command_file = config.CONFIGURATION.get_help_files()

    install_modules()
    add_id_parameters(CMD_TABLE)

    data = {}
    for cmd in CMD_TABLE:
        com_descrip = {}
        param_descrip = {}
        try:
            command_description = CMD_TABLE[cmd].description
            if callable(command_description):
                command_description = command_description()
            com_descrip['help'] = command_description
            com_descrip['examples'] = ""

            for key in CMD_TABLE[cmd].arguments:
                required = ""
                help_desc = ""
                if CMD_TABLE[cmd].arguments[key].type.settings.get('required'):
                    required = "[REQUIRED]"
                if CMD_TABLE[cmd].arguments[key].type.settings.get('help'):
                    help_desc = CMD_TABLE[cmd].arguments[key].type.settings.get('help')

                name_options = []
                for name in CMD_TABLE[cmd].arguments[key].options_list:
                    name_options.append(name)

                options = {
                    'name': name_options,
                    'required': required,
                    'help': help_desc
                }
                param_descrip[CMD_TABLE[cmd].arguments[key].options_list[0]] = options

            com_descrip['parameters'] = param_descrip
            data[cmd] = com_descrip
        except (ImportError, ValueError):
            pass

    for cmd in helps:
        diction_help = yaml.load(helps[cmd])
        if "short-summary" in diction_help:
            if cmd in data:
                data[cmd]['help'] = diction_help["short-summary"]
            else:
                data[cmd] = {
                    'help': diction_help["short-summary"],
                    'parameters': {}
                }
            if callable(data[cmd]['help']):
                data[cmd]['help'] = data[cmd]['help']()

        if cmd not in data:
            print("Command: {} not in Command Table".format(cmd))
            continue

        if "parameters" in diction_help:
            for param in diction_help["parameters"]:
                if param["name"].split()[0] not in data[cmd]['parameters']:
                    options = {
                        'name': name_options,
                        'required': required,
                        'help': help_desc
                    }
                    data[cmd]['parameters'] = {
                        param["name"].split()[0]: options
                    }
                if "short-summary" in param:
                    data[cmd]['parameters'][param["name"].split()[0]]['help']\
                        = param["short-summary"]
        if "examples" in diction_help:
            examples = []
            for example in diction_help["examples"]:
                examples.append([example['name'], example['text']])
            data[cmd]['examples'] = examples

    with open(os.path.join(get_cache_dir(), command_file), 'w') as help_file:
        json.dump(data, help_file)


class Exporter(json.JSONEncoder):
    def default(self, o):
        try:
            return super(Exporter, self).default(o)
        except TypeError:
            return str(o)


def get_cache_dir():
    """ gets the location of the cache """
    azure_folder = config.get_config_dir()
    cache_path = os.path.join(azure_folder, 'cache')
    if not os.path.exists(azure_folder):
        os.makedirs(azure_folder)
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
    return cache_path
