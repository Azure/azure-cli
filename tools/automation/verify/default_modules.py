# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify the list of modules that should be included as part of the CLI install. """

import os
import sys
import json
import tempfile
import zipfile
import glob

from automation.utilities.path import (get_repo_root, get_command_modules_paths)
from automation.utilities.display import print_heading

AZURE_CLI_PATH = os.path.join(get_repo_root(), 'src', 'azure-cli')
AZURE_CLI_SETUP_PY = os.path.join(AZURE_CLI_PATH, 'setup.py')


def get_cli_dependencies(build_folder):
    azure_cli_wheel = glob.glob(build_folder.rstrip('/') + '/azure_cli-*.whl')[0]
    print('Explore wheel file {}.'.format(azure_cli_wheel))

    tmp_dir = tempfile.mkdtemp()

    zip_ref = zipfile.ZipFile(azure_cli_wheel, 'r')
    zip_ref.extractall(tmp_dir)
    zip_ref.close()

    dist_info_dir = [f for f in os.listdir(tmp_dir) if f.endswith('.dist-info')][0]
    whl_metadata_filepath = os.path.join(tmp_dir, dist_info_dir, 'metadata.json')
    with open(whl_metadata_filepath) as f:
        print('Load metadata file from {}'.format(whl_metadata_filepath))
        return json.load(f)['run_requires'][0]['requires']


def verify_default_modules(args):
    errors_list = []
    cli_deps = get_cli_dependencies(args.build_folder)
    all_command_modules = get_command_modules_paths(include_prefix=True)
    if not cli_deps:
        print('Unable to get the CLI dependencies for {}'.format(AZURE_CLI_SETUP_PY), file=sys.stderr)
        sys.exit(1)
    for modname, _ in all_command_modules:
        if modname not in cli_deps:
            errors_list.append("{} is not included to be installed by default! Modify {}.".format(modname, AZURE_CLI_SETUP_PY))
    if errors_list:
        print_heading('Errors whilst verifying default modules list in {}!'.format(AZURE_CLI_SETUP_PY))
        print('\n'.join(errors_list), file=sys.stderr)
        sys.exit(1)
    else:
        print('Verified default modules list successfully.', file=sys.stderr)
