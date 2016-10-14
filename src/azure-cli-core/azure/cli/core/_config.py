#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
import os
from six.moves import configparser

GLOBAL_CONFIG_DIR = os.path.expanduser(os.path.join('~', '.azure'))
GLOBAL_CONFIG_PATH = os.path.join(GLOBAL_CONFIG_DIR, 'config')
ENV_VAR_PREFIX = 'AZURE_'

def active_context():
    from azure.cli.core.context import get_active_context_name
    return get_active_context_name()

CONTEXT_CONFIG_DIR = os.path.expanduser(os.path.join('~', '.azure', 'context_config'))
ACTIVE_CONTEXT_CONFIG_PATH = os.path.join(CONTEXT_CONFIG_DIR, active_context())

_UNSET = object()
_ENV_VAR_FORMAT = ENV_VAR_PREFIX+'{section}_{option}'

class AzConfig(object):
    _BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def __init__(self):
        self.config_parser = configparser.SafeConfigParser()

    @staticmethod
    def env_var_name(section, option):
        return _ENV_VAR_FORMAT.format(section=section.upper(),
                                      option=option.upper())

    def has_option(self, section, option):
        if AzConfig.env_var_name(section, option) in os.environ:
            return True
        return self.config_parser.has_option(section, option)

    def get(self, section, option, fallback=_UNSET):
        try:
            env = AzConfig.env_var_name(section, option)
            return os.environ[env] if env in os.environ else self.config_parser.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is _UNSET:
                raise
            else:
                return fallback

    def getint(self, section, option, fallback=_UNSET):
        return int(self.get(section, option, fallback))

    def getfloat(self, section, option, fallback=_UNSET):
        return float(self.get(section, option, fallback))

    def getboolean(self, section, option, fallback=_UNSET):
        val = str(self.get(section, option, fallback))
        if val.lower() not in AzConfig._BOOLEAN_STATES: #pylint: disable=E1101
            raise ValueError('Not a boolean: {}'.format(val))
        return AzConfig._BOOLEAN_STATES[val.lower()] #pylint: disable=E1101

az_config = AzConfig()
az_config.config_parser.read([GLOBAL_CONFIG_PATH, ACTIVE_CONTEXT_CONFIG_PATH])
