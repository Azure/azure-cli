#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#
# This script will set up tab completion for the Azure CLI.
#
# Calling the script
#   e.g. python <filename> <path_to_cli_install> <path_to_rc_file>
#           <path_to_rc_file> is optional as a default will be used. (e.g. ~/.bashrc)
#
from __future__ import print_function
import os
import sys
import shutil

try:
    # Rename raw_input to input to support Python 2
    input = raw_input
except NameError:
    # Python 3 doesn't have raw_input
    pass

COMPLETION_FILENAME = 'az.completion'
REGISTER_PYTHON_ARGCOMPLETE = """

_python_argcomplete() {
    local IFS='\v'
    COMPREPLY=( $(IFS="$IFS"                   COMP_LINE="$COMP_LINE"                   COMP_POINT="$COMP_POINT"                   _ARGCOMPLETE_COMP_WORDBREAKS="$COMP_WORDBREAKS"                   _ARGCOMPLETE=1                   "$1" 8>&1 9>&2 1>/dev/null 2>/dev/null) )
    if [[ $? != 0 ]]; then
        unset COMPREPLY
    fi
}
complete -o nospace -F _python_argcomplete "az"
"""

USER_BASH_RC = os.path.expanduser(os.path.join('~', '.bashrc'))
USER_BASH_PROFILE = os.path.expanduser(os.path.join('~', '.bash_profile'))

def create_tab_completion_file(filename):
    with open(filename, 'w') as completion_file:
        completion_file.write(REGISTER_PYTHON_ARGCOMPLETE)

def _get_default_rc_file():
    bashrc_exists = os.path.isfile(USER_BASH_RC)
    bash_profile_exists = os.path.isfile(USER_BASH_PROFILE)
    if not bashrc_exists and bash_profile_exists:
        return USER_BASH_PROFILE
    return USER_BASH_RC if bashrc_exists else None

def backup_rc(rc_file):
    try:
        shutil.copyfile(rc_file, rc_file+'.backup')
        print("Backed up '{}' to '{}'".format(rc_file, rc_file+'.backup'))
    except (OSError, IOError):
        pass

def find_line_in_file(file_path, search_pattern):
    try:
        with open(file_path, 'r') as search_file:
            for line in search_file:
                if search_pattern in line:
                    return True
    except (OSError, IOError):
        pass
    return False

def modify_rc(rc_file_path, line_to_add):
    if not find_line_in_file(rc_file_path, line_to_add):
        with open(rc_file_path, 'a') as rc_file:
            rc_file.write('\n'+line_to_add+'\n')

def error_exit(message):
    print('ERROR: {}'.format(message), file=sys.stderr)
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        error_exit('Specify install location as argument.')

    completion_file_path = os.path.join(sys.argv[1], COMPLETION_FILENAME)
    create_tab_completion_file(completion_file_path)
    rc_file = _get_default_rc_file()
    if rc_file:
        print("Modifying '{}' to enable tab completion.".format(rc_file))
        rc_file_path = os.path.realpath(os.path.expanduser(rc_file))
        backup_rc(rc_file_path)
        line_to_add = "source '{}'".format(completion_file_path)
        modify_rc(rc_file_path, line_to_add)
        print('Tab completion set up complete.')
        print('** Run `exec -l $SHELL` to restart your shell. **')
        print("If tab completion is not activated, verify that '{}' is sourced by your shell.".format(rc_file))
    else:
        print("Unable to enable tab completion. No '{}' or '{}' file found.".format(USER_BASH_RC, USER_BASH_PROFILE))

if __name__ == '__main__':
    main()
