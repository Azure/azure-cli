from __future__ import print_function

import argparse
import inspect
import json
import re
import types
import sys

from azure.cli.application import Application, Configuration

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

    results = []
    if param_names:
        for cmd_name in cmd_list:
            cmd_args = cmd_table[cmd_name].arguments
            match = False
            for arg in list(cmd_args.keys()):
                if match:
                    break
                if arg in param_names:
                    results.append(cmd_name)
                    match = True
    else:
        results = cmd_list

    result_dict = {}
    for cmd_name in results:
        table_entry = cmd_table[cmd_name]
        result_dict[cmd_name] = _format_entry(cmd_table[cmd_name])
    print(json.dumps(result_dict, indent=4, sort_keys=True))
    
    # print the 'lowest common denominator' for scope for each param
    if param_names:
        print('\nPARAMETER SCOPES\n')
        for param in param_names:
            print('{} = {}'.format(param, _get_parameter_scope(param, result_dict)))
    
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

def _get_parameter_scope(param, result):
    cmd_list = [key for key, value in result.items() if param in list(value['arguments'].keys())]
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
    if not show_nulls:
        null_values = [x for x in dict_.keys() if dict_[x] is None]
        for key in null_values:
            dict_.pop(key)

parser = argparse.ArgumentParser(description='Command Table Parser')
parser.add_argument('--commands', metavar='N', nargs='+', help='Filter by first level command (OR)')
parser.add_argument('--params', metavar='N', nargs='+', help='Filter by parameters (OR)')
parser.add_argument('--show-nulls', action='store_true', default=False, help='Show null entries')
args = parser.parse_args()
cmd_set_names = args.commands
param_names = args.params
show_nulls = args.show_nulls

PRIMITIVES = (str, int, bool, float)
IGNORE_ARGS = ['help', 'help_file', 'name', 'base_type']

APPLICATION = Application(Configuration([]))
APPLICATION.register(Application.COMMAND_TABLE_LOADED, _dump_command_table)
APPLICATION.execute([''])