#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function
import os
from six.moves import input, configparser #pylint: disable=redefined-builtin
from azure.cli.commands import cli_command
import azure.cli._logging as _logging
from azure.cli._config import GLOBAL_CONFIG_PATH, ACTIVE_ENV_CONFIG_PATH, ENV_VAR_PREFIX
import azure.cli.command_modules.configure._help # pylint: disable=unused-import

logger = _logging.get_az_logger(__name__)

OUTPUT_LIST = [
    {'name': 'json', 'desc': 'JSON formatted output that most closely matches API responses'},
    {'name': 'jsonc', 'desc': 'Colored JSON formatted output that most closely matches API responses'}, #pylint: disable=line-too-long
    {'name': 'table', 'desc': 'Human-readable output format that focuses on clarity'},
    {'name': 'tsv', 'desc': 'Tab and Newline delimited, great for GREP, AWK, etc.'}
]

MESSAGES = {
    'intro': '\nWelcome to the Azure CLI! This command will guide you through logging in and '\
             'setting some default values.\n',
    'global_settings_loc': 'Your global settings can be found at {}',
    'active_env_settings_loc': 'Your current environment settings can be found at {}',
    'current_config_info': 'Your current configuration is as follows:\n',
    'env_vars_heading': 'Environment variables:',
    'global_settings_exists': 'Do you wish to change your global settings? (y/N): ',
    'prompt_global_output': 'What default output format would you like?\n'\
                            '{}\n'\
                            'Please enter a choice [{}]: ',
    'closing': '\nYou\'re all set! Here are some commands to try:\n'\
               ' $ az vm create --help\n'\
               ' $ az feedback\n',
}

def _prompt_global_output(global_config):
    try:
        config_output = global_config.get('core', 'output')
        default_output = [i for i, x in enumerate(OUTPUT_LIST) if x['name'] == config_output][0]+1
    except (IndexError, configparser.NoSectionError, configparser.NoOptionError):
        default_output = 1
    options = '\n'.join([' [{}] {} - {}'.format(i+1, x['name'], x['desc']) \
                        for i, x in enumerate(OUTPUT_LIST)])
    allowed_vals = list(range(1, len(OUTPUT_LIST)+1))
    while True:
        try:
            ans = int(input(MESSAGES['prompt_global_output'].format(options, default_output)) \
                            or default_output)
            if ans in allowed_vals:
                # array index is 0-based, user input is 1-based
                return ans-1
            raise ValueError
        except ValueError:
            logger.warning('Valid values are %s', allowed_vals)

def _prompt_global_settings_exist():
    while True:
        ans = input(MESSAGES['global_settings_exists'])
        if not ans or ans.lower() == 'n':
            return False
        if ans.lower() == 'y':
            return True

def _print_cur_configuration(file_config):
    for section in file_config.sections():
        print('[{}]'.format(section))
        for option in file_config.options(section):
            print('{} = {}'.format(option, file_config.get(section, option)))
        print()
    env_vars = [ev for ev in os.environ if ev.startswith(ENV_VAR_PREFIX)]
    if env_vars:
        print(MESSAGES['env_vars_heading'])
        print('\n'.join(['{} = {}'.format(ev, os.environ[ev]) for ev in env_vars]))
        print()

def _handle_global_configuration():
    print(MESSAGES['global_settings_loc'].format(GLOBAL_CONFIG_PATH))
    print(MESSAGES['active_env_settings_loc'].format(ACTIVE_ENV_CONFIG_PATH))
    # We don't want to use AzConfigParser as we don't want to use get values set by env vars.
    file_config = configparser.SafeConfigParser()
    config_exists = file_config.read([GLOBAL_CONFIG_PATH, ACTIVE_ENV_CONFIG_PATH])
    global_config = configparser.SafeConfigParser()
    global_config.read(GLOBAL_CONFIG_PATH)
    change_global_settings = None
    if config_exists:
        print(MESSAGES['current_config_info'])
        _print_cur_configuration(file_config)
        change_global_settings = _prompt_global_settings_exist()
    if not config_exists or change_global_settings:
        output_index = _prompt_global_output(global_config)
        try:
            global_config.add_section('core')
        except configparser.DuplicateSectionError:
            pass
        global_config.set('core', 'output', OUTPUT_LIST[output_index]['name'])
        with open(GLOBAL_CONFIG_PATH, 'wb') as configfile:
            global_config.write(configfile)

def handle_configure():
    try:
        print(MESSAGES['intro'])
        _handle_global_configuration()
        print(MESSAGES['closing'])
    except KeyboardInterrupt:
        # Catch to prevent stacktrace and print newline
        print()

cli_command('configure', handle_configure)
