from __future__ import print_function

import argparse
import inspect
import json
import re
import types
import sys

from azure.cli.application import Configuration

PRIMITIVES = (str, int, bool, float)
IGNORE_ARGS = ['help']

class Exporter(json.JSONEncoder):

    def default(self, o):#pylint: disable=method-hidden
        try:
            return super(Exporter, self).default(o)
        except TypeError:
            return str(o)

def _format_entry(obj):
    if isinstance(obj, PRIMITIVES):
        return obj
    elif isinstance(obj, types.FunctionType):
        return 'function <{}>'.format(obj.__name__)
    elif isinstance(obj, types.TypeType):
        return 'type <{}>'.format(obj.__name__)
    elif callable(obj):
        return 'callable {}'.format(type(obj))
    elif isinstance(obj, dict):
        new_dict = {key: _format_entry(obj[key]) for key in obj.keys() if key not in IGNORE_ARGS}
        return new_dict
    elif isinstance(obj, list):
        new_list = [_format_entry(x) for x in obj]
        return new_list

parser = argparse.ArgumentParser(description='Command Table Parser')
parser.add_argument('--commands', metavar='N', nargs='+', help='Filter by first level command (OR)')
parser.add_argument('--params', metavar='N', nargs='+', help='Filter by parameters (OR)')
args = parser.parse_args()
cmd_set_names = args.commands
param_names = args.params

config = Configuration([])
cmd_table = config.get_command_table()
cmd_list = []
if cmd_set_names is None :
    # if no command prefix specified, use all command table entries
    cmd_list = cmd_table.keys()
else:
    # if the command name matches a prefix, add it to the output list
    for name in cmd_table.keys():
        for prefix in cmd_set_names:
            if name.startswith(prefix):
                cmd_list.append(name)
                break

results = []
if param_names:
    for name in cmd_list:
        cmd_args = cmd_table[name]['arguments']
        match = False
        for arg in cmd_args:
            if match:
                break
            arg_name = re.sub('--','', arg['name']).split(' ')[0]
            if arg_name in param_names:
                results.append(name)
                match = True
else:
    results = cmd_list

result_dict = {}
for cmd_name in results:
    table_entry = cmd_table[cmd_name]
    json_entry = {key: _format_entry(table_entry[key]) for key in table_entry.keys() \
        if key not in IGNORE_ARGS}
    result_dict[cmd_name] = json_entry
print(json.dumps(result_dict, indent=2, sort_keys=True))
    