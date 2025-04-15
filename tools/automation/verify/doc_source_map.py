# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify the document source map. """

import os
import sys
import json

from ..utilities.path import (get_repo_root, get_command_modules_paths)
from ..utilities.display import print_heading
from ..utilities.const import COMMAND_MODULE_PREFIX

REPO_ROOT = get_repo_root()
DOC_MAP_NAME = 'doc_source_map.json'
HELP_FILE_NAME = '_help.py'
DOC_SOURCE_MAP_PATH = os.path.join('doc', 'sphinx', 'azhelpgen', DOC_MAP_NAME)


def _get_help_files_in_map(map_path):
    with open(map_path) as json_file:
        json_data = json.load(json_file)
        return list(json_data.values())


def _map_help_files_not_found(help_files_in_map):
    none_existent_files = []
    for f in help_files_in_map:
        if not os.path.isfile(os.path.join(REPO_ROOT, f)):
            none_existent_files.append(f)
    return none_existent_files


def _help_files_not_in_map(help_files_in_map):
    found_files = []
    not_in_map = []
    for name, path in get_command_modules_paths():
        name.replace(COMMAND_MODULE_PREFIX, '')
        help_file = os.path.join(path, 'azure', 'cli', 'command_modules', name, HELP_FILE_NAME)
        if os.path.isfile(help_file):
            found_files.append(help_file)
    for f in found_files:
        f_path = f.replace(REPO_ROOT + '/', '')
        if f_path not in help_files_in_map:
            not_in_map.append(f_path)
    return not_in_map


def verify_doc_source_map(*args):
    map_path = os.path.join(REPO_ROOT, DOC_SOURCE_MAP_PATH)
    help_files_in_map = _get_help_files_in_map(map_path)
    help_files_not_found = _map_help_files_not_found(help_files_in_map)
    hep_files_to_add_to_map = _help_files_not_in_map(help_files_in_map)

    if help_files_not_found or hep_files_to_add_to_map:
        print_heading('Errors whilst verifying {}!'.format(DOC_MAP_NAME))
        if help_files_not_found:
            print('\nThe following files are in {} but do not exist:'.format(DOC_MAP_NAME), file=sys.stderr)
            print('\n'.join(help_files_not_found), file=sys.stderr)
        if hep_files_to_add_to_map:
            print('\nThe following files should be added to {}:'.format(DOC_MAP_NAME), file=sys.stderr)
            print('\n'.join(hep_files_to_add_to_map), file=sys.stderr)
        sys.exit(1)
    else:
        print('Verified {} successfully.'.format(DOC_MAP_NAME), file=sys.stderr)
