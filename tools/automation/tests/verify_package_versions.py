# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import os
import sys
import argparse
import subprocess

from ..utilities.path import get_all_module_paths
from ..utilities.display import print_heading
from ..utilities.pypi import is_available_on_pypi

SETUP_PY_NAME = 'setup.py'


def is_unreleased_version(mod_name, mod_version):
    if is_available_on_pypi(mod_name, mod_version):
        print('Version {} of {} is already available on PyPI! Update the version.'.format(mod_version, mod_name))
        return False
    return True


def contains_no_plus_dev(mod_version):
    if '+dev' in mod_version:
        print("Version contains the invalid '+dev'. Actual version {}".format(mod_version))
        return False
    return True

def changes_require_version_bump(mod_name, mod_version, mod_path):
    revision_range = os.environ.get('TRAVIS_COMMIT_RANGE', None)
    if revision_range:
        cmd = ["git", "log", "--pretty=format:* %s", revision_range, "--", mod_path, ":(exclude)*/tests/*"]
        changes = subprocess.check_output(cmd, cwd=mod_path, universal_newlines=True).strip()
        if changes and is_available_on_pypi(mod_name, mod_version):
            print("There are changes to {} and the current version {} is already available on PyPI! Bump the version.".format(mod_name, mod_version))
            print("Changes are as follows:")
            print(changes)
            return False
        else:
            return True
    else:
        # There's no revision range so we'll ignore this check
        return True

def check_package_version(mod_name, mod_path):
    mod_version = subprocess.check_output('python setup.py --version'.split(), cwd=mod_path, universal_newlines=True).strip()
    checks = []
    if mod_name in ['azure-cli', 'azure-cli-core']:
        checks.append(is_unreleased_version(mod_name, mod_version))
    checks.append(contains_no_plus_dev(mod_version))
    checks.append(changes_require_version_bump(mod_name, mod_version, mod_path))
    return all(checks)


def verify_all():
    all_paths = get_all_module_paths()
    all_ok = []
    failed_mods = []
    for p in all_paths:
        res = check_package_version(p[0], p[1])
        if not res:
            failed_mods.append(p[0])
            print('Error(s) on {}'.format(p[0]))
        all_ok.append(res)
    if not all(all_ok):
        print('The following modules have invalid versions:')
        print('\n'.join(failed_mods))
        print('See above for the full warning/errors')
        sys.exit(1)
    else:
        print('Verified versions of all modules successfully.', file=sys.stderr)


def verify_one(mod_name):
    p = [path for name, path in get_all_module_paths() if name == mod_name]
    if not p:
        print('Module not found.', file=sys.stderr)
        sys.exit(1)
    res = check_package_version(mod_name, p[0])
    if not res:
        print_heading('Error whilst verifying version of {}!'.format(mod_name))
        print('See above for the full warning/errors.')
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Verify package versions")
    parser.add_argument('--module', '-m', required=False, help="The module you want to verify.")
    args = parser.parse_args()
    if args.module:
        verify_one(args.module)
    else:
        verify_all()
