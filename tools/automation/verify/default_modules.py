# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify the list of modules that should be included as part of the CLI install. """

import os
import sys
import glob

from automation.utilities.path import (get_repo_root, get_command_modules_paths)
from automation.utilities.display import print_heading

AZURE_CLI_PATH = os.path.join(get_repo_root(), 'src', 'azure-cli')
AZURE_CLI_SETUP_PY = os.path.join(AZURE_CLI_PATH, 'setup.py')


def get_cli_dependencies(build_folder):
    azure_cli_wheel = glob.glob(build_folder.rstrip('/') + '/azure_cli-*.whl')[0]
    print('Explore wheel file {}.'.format(azure_cli_wheel))

    # Read the run-time dependencies (``Requires-Dist``) straight from the spec
    # defined wheel ``METADATA`` via ``pkginfo`` instead of the legacy
    # ``metadata.json`` artifact, which only ``wheel==0.30.0`` writes into
    # ``.dist-info/`` (removed in wheel>=0.31.0, see pypa/wheel#195). This lets
    # the CLI wheel be built with any modern wheel/setuptools version.
    # ``requires_dist`` entries are full PEP 508 strings (e.g. ``azure-cli-foo==1.2.3``
    # or with markers); normalize them to bare distribution names so callers can
    # compare against module names directly.
    from pkginfo import Wheel
    from packaging.requirements import Requirement
    print('Load metadata from {}'.format(azure_cli_wheel))
    return [Requirement(r).name for r in (Wheel(azure_cli_wheel).requires_dist or [])]


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
