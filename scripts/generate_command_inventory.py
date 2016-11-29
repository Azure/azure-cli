# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import json
import re
import sys

from azure.cli.core.application import Configuration

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

# ignore the params passed in now so they aren't used by the cli
sys.argv = sys.argv[:1]
config = Configuration([])
cmd_table = config.get_command_table()
cmd_list = [cmd_name for cmd_name in cmd_table.keys() if cmd_set_names is None or cmd_name.split()[0] in cmd_set_names]
results = []

if param_names:
    for name in cmd_list:
        cmd_name = [x for x in cmd_table.keys() if name == x][0]
        cmd_args = cmd_table[cmd_name]['arguments']
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
