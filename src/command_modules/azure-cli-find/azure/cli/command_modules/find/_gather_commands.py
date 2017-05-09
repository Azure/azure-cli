# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import yaml

from azure.cli.core.commands import _update_command_definitions
from azure.cli.core.help_files import helps


def build_command_table():
    import azure.cli.core.commands as commands
    cmd_table = commands.get_command_table()
    for cmd in cmd_table:
        cmd_table[cmd].load_arguments()
    _update_command_definitions(cmd_table)

    data = {}
    for cmd in cmd_table:
        com_descip = {}
        param_descrip = {}
        com_descip['short-summary'] = cmd_table[cmd].description() \
            if callable(cmd_table[cmd].description) \
            else cmd_table[cmd].description or ''
        com_descip['examples'] = ''

        for key in cmd_table[cmd].arguments:
            required = ''
            help_desc = ''
            if cmd_table[cmd].arguments[key].type.settings.get('required'):
                required = '[REQUIRED]'
            if cmd_table[cmd].arguments[key].type.settings.get('help'):
                help_desc = cmd_table[cmd].arguments[key].type.settings.get('help')

            name_options = []
            for name in cmd_table[cmd].arguments[key].options_list:
                name_options.append(name)

            options = {
                'name': name_options,
                'required': required,
                'help': help_desc
            }
            param_descrip[cmd_table[cmd].arguments[key].options_list[0]] = options

        com_descip['parameters'] = param_descrip
        data[cmd] = com_descip

    for cmd in helps:
        diction_help = yaml.load(helps[cmd])
        if cmd not in data:
            data[cmd] = {
                'short-summary': diction_help.get(
                    'short-summary', ''),
                'long-summary': diction_help.get('long-summary', ''),
                'parameters': {}
            }
        else:
            data[cmd]['short-summary'] = diction_help.get('short-summary',
                                                          data[cmd].get('short-summary', ''))
            data[cmd]['long-summary'] = diction_help.get("long-summary", '')
            data[cmd]['parameters'] = {}

        if 'parameters' in diction_help:
            for param in diction_help["parameters"]:
                if param['name'].split()[0] not in data[cmd]['parameters']:
                    options = {
                        'name': name_options,
                        'required': required,
                        'help': help_desc
                    }
                    data[cmd]['parameters'] = {
                        param["name"].split()[0]: options
                    }
                if 'short-summary' in param:
                    data[cmd]['parameters'][param['name'].split()[0]]['help'] \
                        = param['short-summary']
        if 'examples' in diction_help:
            string_example = ''
            for example in diction_help['examples']:
                string_example += example.get('name', '') + '\n' + example.get('text', '') + '\n'
            data[cmd]['examples'] = string_example

    return data
