# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import json
import os
import re
import sys

import argparse

from _common import get_config

config = get_config()
if not config:
    sys.exit(-1)

STORAGE_ACCOUNT_NAME = config['storage']['account']
TEMPLATE_CONTAINER_NAME = config['storage']['container']
STORAGE_ACCOUNT_KEY = config['storage']['key']
SUBSCRIPTION_ID = config['storage']['subscription']

uploads = []

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
            cmd = 'az storage blob upload -n {0} --account-name {1} --type block --account-key {2} --container-name {3} --file {4} --subscription {5}'.format(
                blob_dest, STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY, TEMPLATE_CONTAINER_NAME, blob_src, SUBSCRIPTION_ID
            )
            print('\nUPLOADING {}...'.format(blob_dest))
            uploads.append(cmd)

def upload_template_files(*args):

    print('\n== UPLOAD ARM TEMPLATES ==')
    
    parser = argparse.ArgumentParser(description='Upload ARM Templates')
    parser.add_argument('--name', metavar='NAME', required=True, help='Name of the thing being uploaded (in CamelCase)')
    parser.add_argument('--src', metavar='PATH', required=True, help='Path to the directory containing ARM templates to upload. Subdirectories will automatically be crawled.')
    parser.add_argument('--api-version', metavar='VERSION', required=True, help='API version for the templates being uploaded in yyyy-MM-dd format. (ex: 2016-07-01)')
    args = parser.parse_args(args)

    name = args.name
    api_version = args.api_version
    src = args.src
    
    _upload_templates(name, api_version, src)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=40) as executor:
        tasks = [executor.submit(lambda cmd: os.system(cmd), u) for u in uploads]
        for t in as_completed(tasks):
            t.result() # don't use the result but expose exceptions from the threads


if __name__ == '__main__':
    upload_template_files(*sys.argv[1:])
