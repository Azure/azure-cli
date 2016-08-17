#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
import os
from six.moves import configparser

GLOBAL_CONFIG_PATH = os.path.expanduser(os.path.join('~', '.azure', 'az_config'))
ACTIVE_ENV_CONFIG_PATH = os.path.expanduser(os.path.join('~', '.azure', 'env_config', 'default'))
ENV_VAR_PREFIX = 'AZURE_CLI_'

_UNSET = object()
_ENV_VAR_FORMAT = ENV_VAR_PREFIX+'{section}_{option}'

class AzConfigParser(configparser.SafeConfigParser, object):
    """A SafeConfigParser that checks environment variables first."""
    _BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    @staticmethod
    def env_var_name(section, option):
        return _ENV_VAR_FORMAT.format(section=section.upper(),
                                      option=option.upper())

    def has_option(self, section, option):
        if AzConfigParser.env_var_name(section, option) in os.environ:
            return True
        return super(AzConfigParser, self).has_option(section, option)

    def get(self, section, option, fallback=_UNSET): #pylint: disable=W0221
        try:
            env = AzConfigParser.env_var_name(section, option)
            return os.environ[env] if env in os.environ else super(AzConfigParser,
                                                                   self).get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is _UNSET:
                raise
            else:
                return fallback

    def getint(self, section, option, fallback=_UNSET): #pylint: disable=W0221
        return int(self.get(section, option, fallback))

    def getfloat(self, section, option, fallback=_UNSET): #pylint: disable=W0221
        return float(self.get(section, option, fallback))

    def getboolean(self, section, option, fallback=_UNSET): #pylint: disable=W0221
        val = self.get(section, option, fallback)
        if val.lower() not in AzConfigParser._BOOLEAN_STATES: #pylint: disable=E1101
            raise ValueError('Not a boolean: {}'.format(val))
        return AzConfigParser._BOOLEAN_STATES[val.lower()] #pylint: disable=E1101

az_config = AzConfigParser()
az_config.read([GLOBAL_CONFIG_PATH, ACTIVE_ENV_CONFIG_PATH])
