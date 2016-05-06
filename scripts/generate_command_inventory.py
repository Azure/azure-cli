import argparse
import json
import re
import sys

from azure.cli.application import Configuration

class Exporter(json.JSONEncoder):

    def default(self, o):#pylint: disable=method-hidden
        try:
            return super(Exporter, self).default(o)
        except TypeError:
            return str(o)

parser = argparse.ArgumentParser(description='Command Table Parser')
parser.add_argument('--commands', metavar='N', nargs='+', help='Filter by first level command (OR)')
parser.add_argument('--params', metavar='N', nargs='+', help='Filter by parameters (OR)')
args = parser.parse_args()
cmd_set_names = args.commands
param_names = args.params

config = Configuration([])
cmd_table = config.get_command_table()
cmd_list = [x['name'] for x in cmd_table.values()
             if cmd_set_names is None or (x['name'].split()[0]) in cmd_set_names]
results = []

if param_names:
    for name in cmd_list:
        cmd_args = [x for x in cmd_table.values() if name == x['name']][0]['arguments']
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

heading = '=== COMMANDS IN {} PACKAGE(S) WITH {} PARAMETERS ==='.format(
    cmd_set_names or 'ANY', param_names or 'ANY')
print('\n{}\n'.format(heading))
print('\n'.join(results))