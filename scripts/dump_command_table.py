# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import inspect
import json
import re
import types
import sys

from azure.cli.core.application import APPLICATION, Application

class Exporter(json.JSONEncoder):

    def default(self, o):#pylint: disable=method-hidden
        try:
            return super(Exporter, self).default(o)
        except TypeError:
            return str(o)

def _dump_command_table(**kwargs):
    cmd_table = APPLICATION.configuration.get_command_table()
    cmd_list = []
    if cmd_set_names is None :
        # if no command prefix specified, use all command table entries
        cmd_list = list(cmd_table.keys())
    else:
        # if the command name matches a prefix, add it to the output list
        for name in cmd_table.keys():
            for prefix in cmd_set_names:
                if name.startswith(prefix):
                    cmd_list.append(name)
                    break

    filtered_cmd_list = []
    param_dict = {k : [] for k in param_names} if param_names else {}
    if param_names:
        for cmd_name in cmd_list:
            table_entry = cmd_table[cmd_name]
            table_entry.arguments.update(table_entry.arguments_loader())
            cmd_args = list(table_entry.arguments.keys())
            for arg in cmd_args:
                if arg in param_names:
                    param_dict[arg].append(cmd_name)
                    if cmd_name not in filtered_cmd_list:
                        filtered_cmd_list.append(cmd_name)
    else:
        filtered_cmd_list = cmd_list

    table_entries = []
    for cmd_name in filtered_cmd_list:
        table_entry = cmd_table[cmd_name]
        table_entry.arguments.update(table_entry.arguments_loader())
        table_entries.append(_format_entry(cmd_table[cmd_name]))
    
    # output results to STDOUT
    result_dict = {'commands': table_entries}
    print(json.dumps(result_dict, indent=2, sort_keys=True))
    
    # display summary info with STDERR
    print('\n===RESULTS===', file=sys.stderr)
    print('{} commands dumped within {} scope with {} parameters'.format(len(table_entries),
        cmd_set_names or '*', param_names or 'ANY'), file=sys.stderr)
    for param, commands in param_dict.items():
        print('\nPARAM: "{}" - {} commands - scope "{}" - {}'.format(
            param, len(commands), _get_parameter_scope(param, commands), commands), file=sys.stderr)

    sys.exit(0)

def _format_entry(obj):
    if not obj:
        return obj
    elif isinstance(obj, tuple):
        return [_format_entry(x) for x in list(obj)]
    elif isinstance(obj, PRIMITIVES):
        return obj
    elif isinstance(obj, types.FunctionType):
        return 'function <{}>'.format(obj.__name__)
    elif callable(obj):
        return 'callable {}'.format(type(obj))
    elif isinstance(obj, dict):
        new_dict = {key: _format_entry(obj[key]) for key in obj.keys() if key not in IGNORE_ARGS}
        _process_null_values(new_dict)
        return new_dict
    elif isinstance(obj, list):
        new_list = [_format_entry(x) for x in obj]
        return new_list
    else:
        new_dict = {key: _format_entry(value) for key, value in vars(obj).items() if key not in IGNORE_ARGS}
        _process_null_values(new_dict)
        return new_dict

def _get_parameter_scope(param, cmd_list):
        
    if not cmd_list:
        return 'N/A (NOT FOUND)'
    test_list = cmd_list[0].split(' ')
    while len(test_list) > 0:
        test_entry = ' '.join(test_list)
        all_match = True
        for entry in cmd_list[1:]:
            if test_entry not in entry:
                all_match = False
                break
        if not all_match:
            test_list.pop()
        else:
            return test_entry
    return '_ROOT_'

def _process_null_values(dict_):
    if hide_nulls:
        null_values = [x for x in dict_.keys() if dict_[x] is None]
        for key in null_values:
            dict_.pop(key)

def _dashed_to_camel(string):
    return string.replace('-', '_')

parser = argparse.ArgumentParser(description='Command Table Parser')
parser.add_argument('--commands', metavar='N', nargs='+', help='Filter by first level command (OR)')
parser.add_argument('--params', metavar='N', nargs='+', help='Filter by parameters (OR)')
parser.add_argument('--hide-nulls', action='store_true', default=False, help='Show null entries')
args = parser.parse_args()
cmd_set_names = args.commands
param_names = [_dashed_to_camel(x) for x in args.params or []]
hide_nulls = args.hide_nulls

PRIMITIVES = (str, int, bool, float)
IGNORE_ARGS = ['help', 'help_file', 'base_type', 'arguments_loader']

APPLICATION.register_command(Application.COMMAND_PARSER_LOADED, _dump_command_table)
APPLICATION.execute([])
