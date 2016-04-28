#!/usr/bin/env python
#
# This script will set up tab completion for the Azure CLI.
#
# Calling the script
#   e.g. python <filename> <path_to_cli_install> <path_to_config_file>
#           <path_to_config_file> is optional as a default will be used. (e.g. ~/.bashrc)
#
# - Optional Environment Variables Available
#     AZURE_CLI_DISABLE_PROMPTS  - Disable prompts during installation and use the defaults
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

DISABLE_PROMPTS = os.environ.get('AZURE_CLI_DISABLE_PROMPTS')

COMPLETION_FILENAME = 'az.completion'
DEFAULT_RC_FILE = os.path.expanduser(os.path.join('~', '.bashrc'))
REGISTER_PYTHON_ARGCOMPLETE = """

_python_argcomplete() {
    local IFS='\v'
    COMPREPLY=( $(IFS="$IFS"                   COMP_LINE="$COMP_LINE"                   COMP_POINT="$COMP_POINT"                   _ARGCOMPLETE_COMP_WORDBREAKS="$COMP_WORDBREAKS"                   _ARGCOMPLETE=1                   "$1" 8>&1 9>&2 1>/dev/null 2>/dev/null) )
    if [[ $? != 0 ]]; then
        unset COMPREPLY
    fi
}
complete -o nospace -o default -F _python_argcomplete "az"
"""

def prompt_input(message):
    return None if DISABLE_PROMPTS else input(message)

def create_tab_completion_file(filename):
    with open(filename, 'w') as completion_file:
        completion_file.write(REGISTER_PYTHON_ARGCOMPLETE)

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
    try:
        # use value from argv if available else fall back to prompt or default
        rc_file = sys.argv[2] if len(sys.argv) >= 3 else prompt_input('Path to rc file (default {}): '.format(DEFAULT_RC_FILE)) or DEFAULT_RC_FILE
    except EOFError:
        error_exit('Unable to prompt for input. Pass the rc file as an argument to this script.')
    rc_file_path = os.path.realpath(os.path.expanduser(rc_file))
    backup_rc(rc_file_path)
    line_to_add = "source '{}'".format(completion_file_path)
    modify_rc(rc_file_path, line_to_add)
    print('Tab completion enabled.')
    print('Run `exec -l $SHELL` to restart your shell.')

if __name__ == '__main__':
    main()
