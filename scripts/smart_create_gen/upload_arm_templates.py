from __future__ import print_function

import configparser
import json
import os
import re
import sys

import argparse

from _common import get_name_from_path, validate_src, parser

config = configparser.ConfigParser()
config.read('config.ini')

STORAGE_ACCOUNT_NAME = config['storage']['account']
TEMPLATE_CONTAINER_NAME = config['storage']['container']
STORAGE_ACCOUNT_KEY = config['storage']['key']
SUBSCRIPTION_ID = config['storage']['subscription']

def _upload_templates(name, api_version, path, dir=None):
    for item in os.listdir(path):
        item_path = os.path.join(path, item) 
        if os.path.isdir(item_path):
            temp_dir = '{}/{}'.format(dir, item) if dir else item
            _upload_templates(name, api_version, item_path, temp_dir)
        elif item.endswith('.json') and 'swagger' not in item:
            blob_src = os.path.join(path, item)
            if dir:
                blob_dest = 'Create{}_{}/{}/{}'.format(name, api_version, dir, item)
            else:
                blob_dest = 'Create{}_{}/{}'.format(name, api_version, item)
            cmd = 'az storage blob upload -n {0} --account-name {1} --type block --account-key {2} --container-name {3} --upload-from {4} --subscription {5}'.format(
                blob_dest, STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY, TEMPLATE_CONTAINER_NAME, blob_src, SUBSCRIPTION_ID
            )
            print('\nUPLOADING {}...'.format(blob_dest))
            os.system(cmd)

def upload_template_files(*args):

    print('\n== UPLOAD ARM TEMPLATES ==')

    args = parser.parse_args(args)

    api_version = args.api_version
    src = args.src
    name = get_name_from_path(src)
    
    _upload_templates(name, api_version, src)

if __name__ == '__main__':
    upload_template_files(*sys.argv[1:])