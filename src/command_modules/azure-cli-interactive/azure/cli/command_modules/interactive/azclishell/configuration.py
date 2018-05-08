# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function

import os

from prompt_toolkit import prompt
from six.moves import configparser
from azure.cli.core._help import PRIVACY_STATEMENT


SELECT_SYMBOL = {
    'outside': '#',
    'query': '??',
    'example': '::',
    'exit_code': '$',
    'scope': '%%',
    'unscope': '..'
}

GESTURE_INFO = {
    SELECT_SYMBOL['outside'] + "[cmd]": "use commands outside the application",
    # pylint: disable=line-too-long
    "[cmd] + [param] +" + "\"" + SELECT_SYMBOL['query'] + "[query]" + "\"": "Inject jmespath query from previous command",
    "\"" + SELECT_SYMBOL['query'] + "[query]" + "\"": "Jmespath query of the previous command",
    "[cmd] " + SELECT_SYMBOL['example'] + " [num]": "do a step by step tutorial of example",
    SELECT_SYMBOL['exit_code']: "get the exit code of the previous command",
    SELECT_SYMBOL['scope'] + '[cmd]': "set a scope, and scopes can be chained with spaces",
    SELECT_SYMBOL['scope'] + ' ' + SELECT_SYMBOL['unscope']: "go back a scope",
}

CONFIG_FILE_NAME = 'shell-config'
GESTURE_LENGTH = max(len(key) for key in GESTURE_INFO) + 1


def help_text(values):
    """ reformats the help text """
    result = ""
    for key in values:
        result += key + ' '.join('' for x in range(GESTURE_LENGTH - len(key))) +\
                        ': ' + values[key] + '\n'
    return result


SHELL_HELP = help_text(GESTURE_INFO)


class Configuration(object):
    """ configuration for program """
    BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                      '0': False, 'no': False, 'false': False, 'off': False,
                      'y': True, 'Y': True, 'n': False, 'N': False}

    """ Configuration information """
    def __init__(self, cli_config, style=None):
        self.config = configparser.ConfigParser({
            'firsttime': 'yes',
            'style': style if style else 'default'
        })
        self.cli_config = cli_config
        self.config.add_section('Help Files')
        self.config.add_section('Layout')
        self.config.set('Help Files', 'command', 'help_dump.json')
        self.config.set('Help Files', 'history', 'history.txt')
        self.config.set('Help Files', 'frequency', 'frequency.json')
        self.config.set('Layout', 'command_description', 'yes')
        self.config.set('Layout', 'param_description', 'yes')
        self.config.set('Layout', 'examples', 'yes')
        self.config_dir = os.getenv('AZURE_CONFIG_DIR') or os.path.expanduser(os.path.join('~', '.azure-shell'))

        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        if not os.path.exists(os.path.join(self.config_dir, CONFIG_FILE_NAME)):
            with open(os.path.join(self.config_dir, CONFIG_FILE_NAME), 'w') as config_file:
                self.config.write(config_file)
        else:
            with open(os.path.join(self.config_dir, CONFIG_FILE_NAME), 'r') as config_file:
                self.config.readfp(config_file)  # pylint: disable=deprecated-method
                self.update()

    def get_config_dir(self):
        return self.config_dir

    def get_history(self):
        """ returns the history """
        return self.config.get('Help Files', 'history')

    def get_help_files(self):
        """ returns where the command table is cached """
        return self.config.get('Help Files', 'command')

    def get_frequency(self):
        """ returns the name of the frequency file """
        return self.config.get('Help Files', 'frequency')

    def load(self, path):
        """ loads the configuration settings """
        self.config.read(path)

    def firsttime(self):
        """ sets it as already done"""
        self.config.set('DEFAULT', 'firsttime', 'no')
        if self.cli_config.getboolean('core', 'collect_telemetry', fallback=False):
            print(PRIVACY_STATEMENT)
        else:
            self.cli_config.set_value('core', 'collect_telemetry', ask_user_for_telemetry())

        self.update()

    def get_style(self):
        """ gets the last style they used """
        return self.config.get('DEFAULT', 'style')

    def has_feedback(self):
        """ returns whether user has given feedback """
        return self.cli_config.getboolean('core', 'given feedback', fallback='false')

    def set_feedback(self, value):
        """ sets the feedback in the config """
        self.cli_config.set_value('core', 'given feedback', value)

    def set_style(self, val):
        """ sets the style they used """
        self.set_val('DEFAULT', 'style', val)

    def set_val(self, direct, section, val):
        """ set the config values """
        if val is not None:
            self.config.set(direct, section, val)
            self.update()

    def update(self):
        """ updates the configuration settings """
        with open(os.path.join(self.config_dir, CONFIG_FILE_NAME), 'w') as config_file:
            self.config.write(config_file)


def ask_user_for_telemetry():
    """ asks the user for if we can collect telemetry """
    answer = " "
    while answer.lower() != 'yes' and answer.lower() != 'no':
        answer = prompt(u'\nDo you agree to sending telemetry (yes/no)? Default answer is yes: ')

        if answer == '':
            answer = 'yes'

    return answer
