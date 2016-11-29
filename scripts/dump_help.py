# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import json
import os
import re
import subprocess
import sys

from azure.cli.core.application import Configuration

class Exporter(json.JSONEncoder):

    def default(self, o):#pylint: disable=method-hidden
        try:
            return super(Exporter, self).default(o)
        except TypeError:
            return str(o)

parser = argparse.ArgumentParser(description='Command Table Parser')
parser.add_argument('--commands', metavar='N', nargs='+', help='Filter by command scope')
args = parser.parse_args()
cmd_set_names = args.commands

# ignore the params passed in now so they aren't used by the cli
sys.argv = sys.argv[:1]
config = Configuration([])
cmd_table = config.get_command_table()
cmd_list = sorted([cmd_name for cmd_name in cmd_table.keys() if cmd_set_names is None or cmd_name.split()[0] in cmd_set_names])

for cmd in cmd_list:
    cmd_string = 'az {} -h'.format(cmd)
    os.system(cmd_string)
    print('\n===============================', flush=True)
