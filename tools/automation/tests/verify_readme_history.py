# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify the README and HISTORY files for each module so they format correctly on PyPI. """

from __future__ import print_function

import os
import sys
import argparse
import subprocess
from docutils import core, io

from ..utilities.path import get_all_module_paths
from ..utilities.display import print_heading

HISTORY_NAME = 'HISTORY.rst'
RELEASE_HISTORY_TITLE = 'Release History'


def exec_command(command, cwd=None, stdout=None, env=None):
    """Returns True in the command was executed successfully"""
    try:
        command_list = command if isinstance(command, list) else command.split()
        env_vars = os.environ.copy()
        if env:
            env_vars.update(env)
        subprocess.check_call(command_list, stdout=stdout, cwd=cwd, env=env_vars)
        return True
    except subprocess.CalledProcessError as err:
        print(err, file=sys.stderr)
        return False


def check_history_headings(mod_path):
    history_path = os.path.join(mod_path, HISTORY_NAME)

    source_path = None
    destination_path = None
    with open(history_path, 'r') as f:
        input_string = f.read()
        _, pub = core.publish_programmatically(
            source_class=io.StringInput, source=input_string,
            source_path=source_path,
            destination_class=io.NullOutput, destination=None,
            destination_path=destination_path,
            reader=None, reader_name='standalone',
            parser=None, parser_name='restructuredtext',
            writer=None, writer_name='null',
            settings=None, settings_spec=None, settings_overrides={},
            config_section=None, enable_exit_status=None)
        if pub.writer.document.children[0].rawsource == RELEASE_HISTORY_TITLE:
            return True
        else:
            print("Expected '{}' as first heading in HISTORY.rst".format(RELEASE_HISTORY_TITLE))
            return False


def check_readme_render(mod_path):
    checks = []
    checks.append(exec_command('python setup.py check -r -s', cwd=mod_path))
    checks.append(check_history_headings(mod_path))
    return all(checks)


def verify_all():
    all_paths = get_all_module_paths()
    all_ok = []
    failed_mods = []
    for p in all_paths:
        res = check_readme_render(p[1])
        if not res:
            failed_mods.append(p[0])
            print('Error(s) on {}'.format(p[0]))
        all_ok.append(res)
    if not all(all_ok):
        print_heading('Errors whilst verifying READMEs!')
        print('The following modules have invalid README/HISTORYs:')
        print('\n'.join(failed_mods))
        print('See above for the full warning/errors')
        print('note: Line numbers in the errors map to the long_description of your setup.py.')
        sys.exit(1)
    else:
        print('Verified READMEs of all modules successfully.', file=sys.stderr)


def verify_one(mod_name):
    p = [path for name, path in get_all_module_paths() if name == mod_name]
    assert p, 'Module not found.'
    res = check_readme_render(p[0])
    if not res:
        print_heading('Error whilst verifying README/HISTORY of {}!'.format(mod_name))
        print('See above for the full warning/errors.')
        print('note: Line numbers in the errors map to the long_description of your setup.py.')
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Verify the README and HISTORY files for each module so they format correctly on PyPI.")
    parser.add_argument('--module', '-m', required=False,
                        help="The module you want to run this script on. e.g. azure-cli-core.")
    args = parser.parse_args()
    if args.module:
        verify_one(args.module)
    else:
        verify_all()
