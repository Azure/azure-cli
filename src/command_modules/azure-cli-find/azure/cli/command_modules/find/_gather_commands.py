# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import yaml

from knack.help_files import helps


def build_command_table(cli_ctx):
    from azure.cli.core import MainCommandsLoader
    cmd_table = MainCommandsLoader(cli_ctx).load_command_table(None)
    for command in cmd_table:
        cmd_table[command].load_arguments()

    data = {}
    for command in cmd_table:
        com_descip = {}
        param_descrip = {}
        com_descip['short-summary'] = cmd_table[command].description() \
            if callable(cmd_table[command].description) \
            else cmd_table[command].description or ''
        com_descip['examples'] = ''

        for key in cmd_table[command].arguments:
            required = ''
            help_desc = ''
            if cmd_table[command].arguments[key].type.settings.get('required'):
                required = '[REQUIRED]'
            if cmd_table[command].arguments[key].type.settings.get('help'):
                help_desc = cmd_table[command].arguments[key].type.settings.get('help')

            name_options = []
            for name in cmd_table[command].arguments[key].options_list:
                name_options.append(name)

            options = {
                'name': name_options,
                'required': required,
                'help': help_desc
            }
            param_descrip[cmd_table[command].arguments[key].options_list[0]] = options

        com_descip['parameters'] = param_descrip
        data[command] = com_descip

    for command in helps:
        diction_help = yaml.load(helps[command])
        if command not in data:
            data[command] = {
                'short-summary': diction_help.get(
                    'short-summary', ''),
                'long-summary': diction_help.get('long-summary', ''),
                'parameters': {}
            }
        else:
            data[command]['short-summary'] = diction_help.get('short-summary',
                                                              data[command].get('short-summary', ''))
            data[command]['long-summary'] = diction_help.get("long-summary", '')
            data[command]['parameters'] = {}

        if 'parameters' in diction_help:
            for param in diction_help["parameters"]:
                if param['name'].split()[0] not in data[command]['parameters']:
                    options = {
                        'name': name_options,
                        'required': required,
                        'help': help_desc
                    }
                    data[command]['parameters'] = {
                        param["name"].split()[0]: options
                    }
                if 'short-summary' in param:
                    data[command]['parameters'][param['name'].split()[0]]['help'] \
                        = param['short-summary']
        if 'examples' in diction_help:
            string_example = ''
            for example in diction_help['examples']:
                string_example += example.get('name', '') + '\n' + example.get('text', '') + '\n'
            data[command]['examples'] = string_example

    return data
