# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import sys
import re
import argparse
from subprocess import check_call, CalledProcessError

from ..utilities.path import get_repo_root, get_all_module_paths

REGEX_COMPONENT_NAME = re.compile(r"([a-z\-]*)-([0-9])")

def error_exit(msg):
    print('ERROR: '+msg, file=sys.stderr)
    sys.exit(1)

def check_component_revisions(component_name, r_start, r_end):
    for comp_name, comp_path in get_all_module_paths():
        if comp_name == component_name:
            revision_range = "{}..{}".format(r_start, r_end)
            try:
                check_call(["git", "log",
                            "--pretty=format:'%C(yellow)%h %Cred%ad %Cblue%an%Cgreen%d %Creset%s'",
                            revision_range, "--", comp_path, ":(exclude)*/tests/*"],
                           cwd=get_repo_root())
            except CalledProcessError as e:
                error_exit(str(e))
            return
    raise error_exit("No component found with name '{}'".format(component_name))


def check_all_component_revisions(r_start, r_end):
    for comp_name, _ in get_all_module_paths():
        print('<<< {} >>>'.format(comp_name))
        check_component_revisions(comp_name, r_start, r_end)
        print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Check for changes made to a component since a git commit or tag. Empty "
                    "response means no changes.")
    parser.add_argument('--component', '-c',
                        help='Component name (e.g. azure-cli, azure-cli-vm, etc.). If not '
                             'specified and --git-revision-start doesn\'t start with the component '
                             'name, all component changes are shown.')
    parser.add_argument('--git-revision-start', '-s', required=True,
                        help="Git tag (or commit) to use as the start of the revision range. "
                             "(e.g. release-azure-cli-vm-0.1.0)")
    parser.add_argument('--git-revision-end', '-e', default='HEAD',
                        help='Git tag (or commit) to use as the end of the revision range.')
    args = parser.parse_args()
    if args.git_revision_start.startswith('azure-cli') and not args.component:
        args.component = re.match(REGEX_COMPONENT_NAME, args.git_revision_start).group(1)
    if args.component:
        check_component_revisions(args.component,
                                  args.git_revision_start,
                                  args.git_revision_end)
    else:
        check_all_component_revisions(args.git_revision_start,
                                      args.git_revision_end)
