# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify the list of modules that should be included as part of the CLI install. """

from __future__ import print_function

import os
import sys
import json
import tempfile
import zipfile
import subprocess

from ..utilities.path import (get_repo_root, get_command_modules_paths)
from ..utilities.display import print_heading
from ..utilities.const import COMMAND_MODULE_PREFIX

REPO_ROOT = get_repo_root()
AZURE_CLI_PATH = os.path.join(REPO_ROOT, 'src', 'azure-cli')
AZURE_CLI_SETUP_PY = os.path.join(AZURE_CLI_PATH, 'setup.py')

# This is a list of modules that we do not want to be installed by default.
# Add your modules to this list if you don't want it to be installed when the CLI is installed.
MODULES_TO_EXCLUDE = ['azure-cli-taskhelp']

def get_cli_dependencies():
    dist_dir = tempfile.mkdtemp()
    tmp_dir = tempfile.mkdtemp()
    try:
        subprocess.check_call(['python', 'setup.py', 'bdist_wheel', '-d', dist_dir], cwd=AZURE_CLI_PATH)
        wheel_path = os.path.join(dist_dir, os.listdir(dist_dir)[0])
        zip_ref = zipfile.ZipFile(wheel_path, 'r')
        zip_ref.extractall(tmp_dir)
        zip_ref.close()
        dist_info_dir = [f for f in os.listdir(tmp_dir) if f.endswith('.dist-info')][0]
        whl_metadata_filepath = os.path.join(tmp_dir, dist_info_dir, 'metadata.json')
        with open(whl_metadata_filepath) as f:
            return json.load(f)['run_requires'][0]['requires']
    except subprocess.CalledProcessError as err:
        print(err, file=sys.stderr)

if __name__ == '__main__':
    errors_list = []
    cli_deps = get_cli_dependencies()
    all_command_modules = get_command_modules_paths(include_prefix=True)
    for modname, _ in all_command_modules:
        if modname in cli_deps and modname in MODULES_TO_EXCLUDE:
            errors_list.append("{} is a dependency of azure-cli BUT is marked as should be excluded.".format(modname))
        if modname not in cli_deps and modname not in MODULES_TO_EXCLUDE:
            errors_list.append("{} is not included to be installed by default! If this is a mistake, modify {}. "
                               "Otherwise, modify this script ({}) to exclude the module.".format(modname, AZURE_CLI_SETUP_PY, __file__))
    if errors_list:
        print_heading('Errors whilst verifying default modules list in {}!'.format(AZURE_CLI_SETUP_PY))
        print('\n'.join(errors_list), file=sys.stderr)
        sys.exit(1)
    else:
        print('Verified default modules list successfully.', file=sys.stderr)
