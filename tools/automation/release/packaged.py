# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import argparse
import os
import sys
import tempfile
import tarfile
import shutil
import json
from subprocess import check_call, check_output

from .version_patcher import VersionPatcher
from ..utilities.path import get_all_module_paths, get_repo_root

REPO_ROOT_DIR = get_repo_root()
COMPLETION_FILE = os.path.join(REPO_ROOT_DIR, 'packaged_releases', 'az.completion')
ARCHIVE_FILE_TMPL = 'azure-cli_packaged_{}'


class Patch(object):  # pylint: disable=too-few-public-methods
    def __init__(self, src_of_patch, path_to_patch):
        """
        - src: Relative path from the repo root
        - dest: Relative path to file to patch in the packaged release
        """
        self.src_of_patch = src_of_patch
        self.path_to_patch = path_to_patch

    def apply(self, working_dir):
        src = os.path.join(REPO_ROOT_DIR, self.src_of_patch)
        dest = os.path.join(working_dir, self.path_to_patch)
        shutil.copy(src, dest)


PATCHES = [
    ]


def error_exit(msg):
    print('ERROR: '+msg, file=sys.stderr)
    sys.exit(1)


def _gen_tag(c_name, c_version):
    return '{}-{}'.format(c_name, c_version)


def _verified_tags(components):
    available_tags = check_output(['git', 'tag'], cwd=REPO_ROOT_DIR)
    available_tags = str(available_tags, 'utf-8')
    available_tags = available_tags.split()
    for c_name, c_version in components:
        t = _gen_tag(c_name, c_version)
        if t not in available_tags:
            print('Tag {} not found.'.format(t))
            return False
    return True


def create_packaged_archive(version, components, archive_dest=None, use_version_patch=True):
    # Verify the components and versions by checking git tags
    if not _verified_tags(components):
        error_exit('Some components or versions are not valid.')
    working_dir = tempfile.mkdtemp()
    print('Using tmp directory {}'.format(working_dir))
    modules = {n: p for n, p in get_all_module_paths()}
    cur_git_commitish = check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO_ROOT_DIR).strip()
    for c_name, c_version in components:
        c_path = modules[c_name]
        git_tag = _gen_tag(c_name, c_version)
        check_call(['git', 'checkout', git_tag], cwd=REPO_ROOT_DIR)
        patcher = VersionPatcher(use_version_patch, c_name, c_path)
        patcher.patch()
        sub_dir = 'command_modules' if '/command_modules/' in c_path else ''
        shutil.copytree(c_path, os.path.join(working_dir, 'src', sub_dir, c_name))
        patcher.unpatch()
    check_call(['git', 'checkout', cur_git_commitish], cwd=REPO_ROOT_DIR)
    # Add completion file
    completion_dest = os.path.join(working_dir, 'az.completion')
    shutil.copy(COMPLETION_FILE, completion_dest)
    # Apply patches
    for patch in PATCHES:
        patch.apply(working_dir)
    # Build archive
    archive_filename = ARCHIVE_FILE_TMPL.format(version)
    archive_dest = os.path.expanduser(archive_dest) if archive_dest else os.getcwd()
    archive_path = os.path.join(archive_dest, archive_filename+'.tar.gz')
    with tarfile.open(archive_path, 'w:gz') as tar:
        tar.add(working_dir, arcname=archive_filename)
    print("Archive saved to {}".format(archive_path))
    print("Done.")


def _type_components_list(value):
    c_name, c_version = value.split('=', 1)
    if not c_name.startswith('azure-cli'):
        c_name = 'azure-cli-' + c_name
    return (c_name, c_version)


def _type_json_file(value):
    with open(os.path.expanduser(value)) as open_file:
        data = json.load(open_file)
        return [(k, data[k]) for k in data]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Automated generation of the packaged release archive.")

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('--components', '-c', nargs='+',
                       help="Space separated list in 'component=version' format. "
                            "(e.g. azure-cli=2.0.0 vm=2.0.0)",
                       type=_type_components_list)
    group.add_argument('--file-data', '-f',
                       help='Path to JSON file with commands in key/value format. '
                            '(e.g. {"azure-cli":"2.0.0", ...})',
                       type=_type_json_file)
    parser.add_argument('--version', '-v', required=True,
                        help="The version to name the packaged release.")
    parser.add_argument('--dest', '-d',
                        help="The destination directory to place the archive. "
                             "Defaults to current directory.")
    args = parser.parse_args()

    components_list = args.components or args.file_data
    create_packaged_archive(args.version, components_list, args.dest)
