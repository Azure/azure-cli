# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import argparse
import os
import tempfile
from subprocess import check_call

from .version_patcher import VersionPatcher
from ..utilities.path import get_all_module_paths


def build(pkg_path, dest):
    """
    pkg_path - Full path to directory of the package to build
    dest - Destination for the built package
    """
    check_call(['python', 'setup.py', 'sdist', '-d', dest, 'bdist_wheel', '-d', dest], cwd=pkg_path)


def release(pkg_dir, repo):
    """Release all packages in a directory"""
    pkgs = [os.path.join(pkg_dir, f) for f in os.listdir(pkg_dir)]
    for pkg in pkgs:
        check_call(['twine', 'register', '--repository-url', repo, '--repository', repo, pkg])
        check_call(['twine', 'upload', '--repository-url', repo, '--repository', repo, pkg])


def run_build_release(component_name, repo, use_version_patch=True):
    """
    component_name - The full component name (e.g. azure-cli, azure-cli-core, azure-cli-vm, etc.)
    """
    for comp_name, comp_path in get_all_module_paths():
        if comp_name == component_name:
            pkg_dir = tempfile.mkdtemp()
            patcher = VersionPatcher(use_version_patch, component_name, comp_path)
            patcher.patch()
            build(comp_path, pkg_dir)
            patcher.unpatch()
            print("Built '{}' to '{}'".format(comp_name, pkg_dir))
            if repo:
                release(pkg_dir, repo)
            return
    raise ValueError("No component found with name '{}'".format(component_name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Automated build and release of a component. To only build, don't specify the"
                    " repo parameter. The environment variables TWINE_USERNAME and TWINE_PASSWORD "
                    "are required if releasing.")
    parser.add_argument('--component', '-c', required=True,
                        help='Component name (e.g. azure-cli, azure-cli-vm, etc.)')
    parser.add_argument('--no-version-patch', action='store_false',
                        help="By default, we patch the version number of the package to remove "
                             "'+dev' if it exists.")
    parser.add_argument('--repo', '-r',
                        help='Repository URL for release (e.g. https://pypi.python.org/pypi, '
                             'https://testpypi.python.org/pypi)')
    args = parser.parse_args()
    if args.repo:
        assert os.environ.get('TWINE_USERNAME') and os.environ.get('TWINE_PASSWORD'), \
            "Set TWINE_USERNAME and TWINE_PASSWORD environment variables to authentication with " \
            "PyPI repository."
    run_build_release(args.component,
                      args.repo,
                      args.no_version_patch)
