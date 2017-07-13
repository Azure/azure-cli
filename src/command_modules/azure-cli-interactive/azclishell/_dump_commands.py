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


class LoadFreshTable(object):
    """
    this class generates and dumps the fresh command table into a file
    as well as installs all the modules
    """
    def __init__(self):
        self.command_table = None

    def install_modules(self):
        installed_command_modules = []
        for cmd in self.command_table:
            try:
                self.command_table[cmd].load_arguments()
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
        _update_command_definitions(self.command_table)

    def load_help_files(self, data):
        """ loads all the extra information from help files """
        for cmd in helps:
            diction_help = yaml.load(helps[cmd])
            # extra descriptions
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

            # if there is extra help for this command but it's not reflected in the command table
            if cmd not in data:
                print("Command: {} not in Command Table".format(cmd))
                continue

            # extra parameters
            if "parameters" in diction_help:
                for param in diction_help["parameters"]:
                    if param["name"].split()[0] not in data[cmd]['parameters']:
                        options = {
                            'name': [],
                            'required': '',
                            'help': ''
                        }
                        data[cmd]['parameters'] = {
                            param["name"].split()[0]: options
                        }
                    if "short-summary" in param:
                        data[cmd]['parameters'][param["name"].split()[0]]['help']\
                            = param["short-summary"]
            # extra examples
            if "examples" in diction_help:
                examples = []
                for example in diction_help["examples"]:
                    examples.append([example['name'], example['text']])
                data[cmd]['examples'] = examples

    def dump_command_table(self):
        """ dumps the command table """

        self.command_table = APPLICATION.configuration.get_command_table()
        command_file = config.CONFIGURATION.get_help_files()

        self.install_modules()
        add_id_parameters(self.command_table)

        data = {}
        for cmd in self.command_table:
            com_descrip = {}  # commands to their descriptions, examples, and parameter info
            param_descrip = {}  # parameters to their aliases, required, and descriptions

            try:
                command_description = self.command_table[cmd].description
                if callable(command_description):
                    command_description = command_description()

                com_descrip['help'] = command_description
                com_descrip['examples'] = ""

                # checking all the parameters for a single command
                for key in self.command_table[cmd].arguments:
                    required = ""
                    help_desc = ""

                    if self.command_table[cmd].arguments[key].type.settings.get('required'):
                        required = "[REQUIRED]"
                    if self.command_table[cmd].arguments[key].type.settings.get('help'):
                        help_desc = self.command_table[cmd].arguments[key].type.settings.get('help')

                    # checking aliasing
                    name_options = []
                    for name in self.command_table[cmd].arguments[key].options_list:
                        name_options.append(name)

                    options = {
                        'name': name_options,
                        'required': required,
                        'help': help_desc
                    }
                    # the key is the first alias option
                    param_descrip[self.command_table[cmd].arguments[key].options_list[0]] = options

                com_descrip['parameters'] = param_descrip
                data[cmd] = com_descrip
            except (ImportError, ValueError):
                pass

        self.load_help_files(data)

        # dump into the cache file
        with open(os.path.join(get_cache_dir(), command_file), 'w') as help_file:
            json.dump(data, help_file)


def get_cache_dir():
    """ gets the location of the cache """
    azure_folder = config.get_config_dir()
    cache_path = os.path.join(azure_folder, 'cache')
    if not os.path.exists(azure_folder):
        os.makedirs(azure_folder)
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
    return cache_path


FRESH_TABLE = LoadFreshTable()
