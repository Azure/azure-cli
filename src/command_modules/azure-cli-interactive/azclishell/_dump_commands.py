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

from azure.cli.core.commands import BLACKLISTED_MODS
from azure.cli.core.commands.arm import add_id_parameters

from knack.help_files import helps


class LoadFreshTable(object):
    """
    this class generates and dumps the fresh command table into a file
    as well as installs all the modules
    """
    def __init__(self, shell_ctx):
        self.command_table = None
        self.shell_ctx = shell_ctx

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

    def dump_command_table(self, shell_ctx):
        """ dumps the command table """

        loader = shell_ctx.cli_ctx.invocation.commands_loader
        cmd_table = loader.load_command_table(None)
        loader.load_arguments('')

        data = {}
        for cmd in cmd_table:
            com_descrip = {}  # commands to their descriptions, examples, and parameter info
            param_descrip = {}  # parameters to their aliases, required, and descriptions

            try:
                command_description = cmd_table[cmd].description
                if callable(command_description):
                    command_description = command_description()

                com_descrip['help'] = command_description
                com_descrip['examples'] = ""

                # checking all the parameters for a single command
                for key in cmd_table[cmd].arguments:
                    required = ""
                    help_desc = ""

                    if cmd_table[cmd].arguments[key].type.settings.get('required'):
                        required = "[REQUIRED]"
                    if cmd_table[cmd].arguments[key].type.settings.get('help'):
                        help_desc = cmd_table[cmd].arguments[key].type.settings.get('help')

                    # checking aliasing
                    name_options = []
                    for name in cmd_table[cmd].arguments[key].options_list:
                        name_options.append(name)

                    options = {
                        'name': name_options,
                        'required': required,
                        'help': help_desc
                    }
                    # the key is the first alias option
                    param_descrip[cmd_table[cmd].arguments[key].options_list[0]] = options

                com_descrip['parameters'] = param_descrip
                data[cmd] = com_descrip
            except (ImportError, ValueError):
                pass

        add_id_parameters(cmd_table)
        self.load_help_files(data)

        self.command_table = cmd_table

        # dump into the cache file
        command_file = shell_ctx.config.get_help_files()
        with open(os.path.join(get_cache_dir(shell_ctx), command_file), 'w') as help_file:
            json.dump(data, help_file)


def get_cache_dir(shell_ctx):
    """ gets the location of the cache """
    azure_folder = shell_ctx.config.config_dir
    cache_path = os.path.join(azure_folder, 'cache')
    if not os.path.exists(azure_folder):
        os.makedirs(azure_folder)
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
    return cache_path
