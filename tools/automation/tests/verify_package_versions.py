# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import argparse
import subprocess

from ..utilities.path import get_all_module_paths, get_repo_root
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


def changes_require_version_bump(mod_name, mod_version, mod_path, base_repo=None, base_tag=None):
    revision_range = os.environ.get('TRAVIS_COMMIT_RANGE', None)
    if revision_range:
        cmd = ["git", "diff", revision_range, "--", mod_path, ":(exclude)*/tests/*"]
        print('Executing: {}'.format(' '.join(cmd)))
        changes = subprocess.check_output(cmd, cwd=mod_path, universal_newlines=True).strip()
        if changes:
            if is_available_on_pypi(mod_name, mod_version):
                print("There are changes to {} and the current version {} is already available on PyPI! "
                    "Bump the version.".format(mod_name, mod_version))
                print("Changes are as follows:")
                print(changes)
                return False
            elif base_repo and version_in_base_repo(base_repo, mod_path, mod_name, mod_version):
                print("There are changes to {} and the current version {} is already used at tag {}. "
                    "Bump the version.".format(mod_name, mod_version, base_tag))
                print("Changes are as follows:")
                print(changes)
                return False
    return True


def version_in_base_repo(base_repo, mod_path, mod_name, mod_version):
    base_repo_mod_path = mod_path.replace(get_repo_root(), base_repo)
    try:
        if mod_version == _get_mod_version(base_repo_mod_path):
            print('Version {} of {} is already used on in the base repo.'.format(mod_version, mod_name))
            return True
    except OSError:  # FileNotFoundError introduced in Python 3
        print('Module {} not in base repo. Skipping...'.format(mod_name), file=sys.stderr)
    except Exception as ex:
        # Print warning if unable to get module from base version (e.g. mod didn't exist there)
        print('Warning: Unable to get module version from base repo... skipping...', file=sys.stderr)
        print(str(ex), file=sys.stderr)
    return False


def _get_mod_version(mod_path):
    return subprocess.check_output(['python', 'setup.py', '--version'], cwd=mod_path,
                                   universal_newlines=True).strip()


def check_package_version(mod_name, mod_path, base_repo=None, base_tag=None):
    mod_version = _get_mod_version(mod_path)
    checks = []
    if mod_name in ['azure-cli', 'azure-cli-core']:
        checks.append(is_unreleased_version(mod_name, mod_version))
    checks.append(contains_no_plus_dev(mod_version))
    checks.append(changes_require_version_bump(mod_name, mod_version, mod_path, base_repo=base_repo, base_tag=base_tag))
    return all(checks)


def verify_all(base_repo=None, base_tag=None):
    all_paths = get_all_module_paths()
    all_ok = []
    failed_mods = []
    for p in all_paths:
        res = check_package_version(p[0], p[1], base_repo=base_repo, base_tag=base_tag)
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


def verify_one(mod_name, base_repo=None, base_tag=None):
    p = [path for name, path in get_all_module_paths() if name == mod_name]
    if not p:
        print('Module not found.', file=sys.stderr)
        sys.exit(1)
    res = check_package_version(mod_name, p[0], base_repo=base_repo, base_tag=base_tag)
    if not res:
        print_heading('Error whilst verifying version of {}!'.format(mod_name))
        print('See above for the full warning/errors.')
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Verify package versions")
    parser.add_argument('--module', '-m', required=False, help="The module you want to verify.")
    parser.add_argument('--base-repo', required=False, help="Path to directory containing the CLI repo with "\
                        "the base versions to compare against.")
    parser.add_argument('--base-tag', required=False, help="A tag that represents the base repo (e.g. the Git tag)")
    args = parser.parse_args()
    if args.module:
        verify_one(args.module, base_repo=args.base_repo, base_tag=args.base_tag)
    else:
        verify_all(base_repo=args.base_repo, base_tag=args.base_tag)
