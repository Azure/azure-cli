import os
import re

import argparse

def validate_src(path):
    if not os.path.isfile(path):
        raise RuntimeError('Your main template must be named \'azuredeploy.json\'. File not found.')    

def get_name_from_path(path):
    while path:
        path, item = os.path.split(path)
        if 'mgmt_' in item:
            snake_case = item.replace('mgmt_', '', 1).split('_')
            snake_case = [x.capitalize() for x in snake_case]
            return ''.join(snake_case)
    raise RuntimeError('You must specify a path with --src that includes a directory in the format \'mgmt_<name>\'')

def to_snake_case(s):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def to_dash_case(s):
    return _to_snake_case(s).replace('_', '-')    

parser = argparse.ArgumentParser(description='Smart Create')
parser.add_argument('--src', metavar='PATH', default=None, help='Path to the directory containing the main ARM template, which must be named \'azuredeploy.json\'. The path must include a directory name \'mgmt_<name>\'.')
parser.add_argument('--api-version', metavar='VERSION', required=True, help='API version for the template being generated in yyyy-MM-dd format. (ex: 2016-07-01)')
