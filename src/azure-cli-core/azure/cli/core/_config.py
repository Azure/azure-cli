# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import stat
from six.moves import configparser

from azure.cli.core._environment import get_config_dir

GLOBAL_CONFIG_DIR = get_config_dir()
CONFIG_FILE_NAME = 'config'
GLOBAL_CONFIG_PATH = os.path.join(GLOBAL_CONFIG_DIR, CONFIG_FILE_NAME)
ENV_VAR_PREFIX = 'AZURE_'
DEFAULTS_SECTION = 'defaults'

_UNSET = object()
_ENV_VAR_FORMAT = ENV_VAR_PREFIX + '{section}_{option}'


def get_config_parser():
    import sys

    python_version = sys.version_info.major
    return configparser.ConfigParser() if python_version == 3 else configparser.SafeConfigParser()


class AzConfig(object):
    _BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def __init__(self):
        self.config_parser = get_config_parser()

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
        if val.lower() not in AzConfig._BOOLEAN_STATES:
            raise ValueError('Not a boolean: {}'.format(val))
        return AzConfig._BOOLEAN_STATES[val.lower()]


az_config = AzConfig()
az_config.config_parser.read(GLOBAL_CONFIG_PATH)


def set_global_config(config):
    if not os.path.isdir(GLOBAL_CONFIG_DIR):
        os.makedirs(GLOBAL_CONFIG_DIR)
    with open(GLOBAL_CONFIG_PATH, 'w') as configfile:
        config.write(configfile)
    os.chmod(GLOBAL_CONFIG_PATH, stat.S_IRUSR | stat.S_IWUSR)
    # reload az_config
    az_config.config_parser.read(GLOBAL_CONFIG_PATH)


def set_global_config_value(section, option, value):
    config = get_config_parser()
    config.read(GLOBAL_CONFIG_PATH)
    try:
        config.add_section(section)
    except configparser.DuplicateSectionError:
        pass
    config.set(section, option, value)
    set_global_config(config)
