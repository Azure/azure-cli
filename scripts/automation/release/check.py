# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import argparse
from subprocess import check_call

from ..utilities.path import get_repo_root, get_all_module_paths


def check_component_revisions(component_name, r_start, r_end):
    for comp_name, comp_path in get_all_module_paths():
        if comp_name == component_name:
            revision_range = "{}..{}".format(r_start, r_end)
            check_call(["git", "log",
                        "--pretty=format:'%C(yellow)%h %Cred%ad %Cblue%an%Cgreen%d %Creset%s'",
                        revision_range, "--", comp_path], cwd=get_repo_root())
            return
    raise ValueError("No component found with name '{}'".format(component_name))


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
                             'specified, all component changes are shown.')
    parser.add_argument('--git-revision-start', '-s', required=True,
                        help="Git tag (or commit) to use as the start of the revision range. "
                             "(e.g. release-azure-cli-vm-0.1.0)")
    parser.add_argument('--git-revision-end', '-e', default='HEAD',
                        help='Git tag (or commit) to use as the end of the revision range.')
    args = parser.parse_args()
    if args.component:
        check_component_revisions(args.component,
                                  args.git_revision_start,
                                  args.git_revision_end)
    else:
        check_all_component_revisions(args.git_revision_start,
                                      args.git_revision_end)
