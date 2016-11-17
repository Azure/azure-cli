# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import configparser
import os
import re

def get_name_from_path(path):
    """ Parses a directory in 'mgmt_<name> ' format into the camel case name used by ARM. The
    directory name should be in snake case. """
    while path:
        path, item = os.path.split(path)
        if 'mgmt_' in item:
            return snake_to_camel(item.replace('mgmt_', '', 1))
    raise RuntimeError('You must specify a path with --src that includes a directory in the format \'mgmt_<name>\'')

def get_config():
    config = configparser.ConfigParser()
    CONFIG_PATH = os.path.join(os.getcwd(), 'config.ini')
    if os.path.isfile('config.ini'):
        config.read('config.ini')
        return config
    else:
        print("'config.ini' file not found. Creating an empty one. Please update it and re-run the script.")
        with open(CONFIG_PATH, 'w') as f:
            f.write("""[autorest]
path = AutoRest.exe

[storage]
account = FILL_IN
key = FILL_IN
container = FILL_IN
subscription = FILL_IN
""")
        return None

def to_snake_case(s):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def to_dash_case(s):
    return _to_snake_case(s).replace('_', '-')

def snake_to_camel(s):
    return ''.join([x.capitalize() for x in s.split('_')])
