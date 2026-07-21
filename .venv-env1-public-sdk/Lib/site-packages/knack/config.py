# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import stat
import configparser

from .util import ensure_dir

_UNSET = object()

CONFIG_FILE_ENCODING = 'utf-8'


def get_config_parser():
    return configparser.ConfigParser()  # keep this for backward compatibility


class CLIConfig(object):
    _BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    _DEFAULT_CONFIG_ENV_VAR_PREFIX = 'CLI'
    _DEFAULT_CONFIG_DIR = os.path.expanduser(os.path.join('~', '.{}'.format('cli')))
    _DEFAULT_CONFIG_FILE_NAME = 'config'
    _CONFIG_DEFAULTS_SECTION = 'defaults'

    def __init__(self, config_dir=None, config_env_var_prefix=None, config_file_name=None, use_local_config=None):
        """ Manages configuration options available in the CLI

        :param config_dir: The directory to store config files
        :type config_dir: str
        :param config_env_var_prefix: The prefix for config environment variables
        :type config_env_var_prefix: str
        :param config_file_name: The name given to the config file to be created
        :type config_file_name: str
        """
        config_dir = config_dir or CLIConfig._DEFAULT_CONFIG_DIR
        ensure_dir(config_dir)
        config_env_var_prefix = config_env_var_prefix or CLIConfig._DEFAULT_CONFIG_ENV_VAR_PREFIX
        env_var_prefix = '{}_'.format(config_env_var_prefix.upper())
        default_config_dir = os.path.expanduser(config_dir)
        self.config_dir = os.environ.get('{}CONFIG_DIR'.format(env_var_prefix), default_config_dir)
        configuration_file_name = config_file_name or CLIConfig._DEFAULT_CONFIG_FILE_NAME
        self.config_path = os.path.join(self.config_dir, configuration_file_name)
        self._env_var_format = '{}{}'.format(env_var_prefix, '{section}_{option}')
        self.defaults_section_name = CLIConfig._CONFIG_DEFAULTS_SECTION
        self.use_local_config = use_local_config
        self._config_file_chain = []

        current_dir = None
        try:
            current_dir = os.getcwd()
        except FileNotFoundError:
            from .log import get_logger
            logger = get_logger()
            logger.warning("The working directory has been deleted or recreated. "
                           "Local config is ignored.")

        config_dir_name = os.path.basename(self.config_dir)
        while current_dir:
            current_config_dir = os.path.join(current_dir, config_dir_name)
            # Stop if already in the default .azure
            if (os.path.normcase(os.path.normpath(current_config_dir)) ==
                    os.path.normcase(os.path.normpath(self.config_dir))):
                break
            if os.path.isdir(current_config_dir):
                self._config_file_chain.append(_ConfigFile(current_config_dir,
                                                           os.path.join(current_config_dir, configuration_file_name)))
            # Stop if already in root drive
            if current_dir == os.path.dirname(current_dir):
                break
            current_dir = os.path.dirname(current_dir)
        self._config_file_chain.append(_ConfigFile(self.config_dir, self.config_path))

    def env_var_name(self, section, option):
        return self._env_var_format.format(section=section.upper(),
                                           option=option.upper())

    def has_option(self, section, option):
        if self.env_var_name(section, option) in os.environ:
            return True
        config_files = self._config_file_chain if self.use_local_config else self._config_file_chain[-1:]
        return bool(next((f for f in config_files if f.has_option(section, option)), False))

    def get(self, section, option, fallback=_UNSET):
        env = self.env_var_name(section, option)
        if env in os.environ:
            return os.environ[env]
        last_ex = None
        for config in self._config_file_chain if self.use_local_config else self._config_file_chain[-1:]:
            try:
                return config.get(section, option)
            except (configparser.NoSectionError, configparser.NoOptionError) as ex:
                last_ex = ex

        if fallback is _UNSET:
            raise last_ex  # pylint:disable=raising-bad-type
        return fallback

    def sections(self):
        combined_sections = []
        # Go through the config chain and combine all sections
        for config in self._config_file_chain if self.use_local_config else self._config_file_chain[-1:]:
            sections = config.sections()
            for section in sections:
                if section not in combined_sections:
                    combined_sections.append(section)
        return combined_sections

    def items(self, section):
        import re
        # Only allow valid env vars, in all caps: CLI_SECTION_TEST_OPTION, CLI_SECTION__TEST_OPTION
        pattern = self.env_var_name(section, '([0-9A-Z_]+)')
        env_entries = []
        for k in os.environ:
            # Must be a full match, otherwise CLI_SECTION_T part in CLI_MYSECTION_Test_Option will match
            matched = re.fullmatch(pattern, k)
            if matched:
                # (name, value, ENV_VAR_NAME)
                item = (matched.group(1).lower(), os.environ[k], k)
                env_entries.append(item)

        # Prepare result with env entries first
        result = {c[0]: c for c in env_entries}
        # Add entries from config files if they do not exist yet
        for config in self._config_file_chain if self.use_local_config else self._config_file_chain[-1:]:
            try:
                entries = config.items(section)
                for name, value in entries:
                    if name not in result:
                        result[name] = (name, value, config.config_path)
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass
        return [{'name': name, 'value': value, 'source': source} for name, value, source in result.values()]

    def getint(self, section, option, fallback=_UNSET):
        return int(self.get(section, option, fallback))

    def getfloat(self, section, option, fallback=_UNSET):
        return float(self.get(section, option, fallback))

    def getboolean(self, section, option, fallback=_UNSET):
        val = str(self.get(section, option, fallback))
        if val.lower() not in CLIConfig._BOOLEAN_STATES:
            raise ValueError('Not a boolean: {}'.format(val))
        return CLIConfig._BOOLEAN_STATES[val.lower()]

    def set_value(self, section, option, value):
        if self.use_local_config:
            current_config_dir = os.path.join(os.getcwd(), os.path.basename(self.config_dir))
            config_file_path = os.path.join(current_config_dir, os.path.basename(self.config_path))
            if config_file_path == self._config_file_chain[0].config_path:
                self._config_file_chain[0].set_value(section, option, value)
            else:
                config = _ConfigFile(current_config_dir, config_file_path)
                config.set_value(section, option, value)
                self._config_file_chain.insert(0, config)
        else:
            self._config_file_chain[-1].set_value(section, option, value)

    def set_to_use_local_config(self, use_local_config):
        self.use_local_config = use_local_config

    def remove_option(self, section, option):
        for config in self._config_file_chain if self.use_local_config else self._config_file_chain[-1:]:
            if config.remove_option(section, option):
                return True
        return False


class _ConfigFile(object):
    _BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def __init__(self, config_dir, config_path, config_comment=None):
        """ Manage configuration options available in the CLI

        :param config_dir: The directory to store the config file
        :type config_dir: str
        :param config_path: The path of the config file
        :type config_path: str
        :param config_comment: The comment which will be written into the head of the config file
        :type config_comment: str

        When 'config_comment' is given, each line should start with # or ;. For details about INI file comment,
        see https://docs.python.org/3/library/configparser.html#supported-ini-file-structure
        """
        self.config_dir = config_dir
        self.config_path = config_path
        self.config_comment = config_comment
        self.config_parser = configparser.ConfigParser()
        if os.path.exists(config_path):
            self.config_parser.read(config_path, encoding=CONFIG_FILE_ENCODING)

    def items(self, section):
        return self.config_parser.items(section) if self.config_parser else []

    def sections(self):
        return self.config_parser.sections() if self.config_parser else []

    def has_option(self, section, option):
        return self.config_parser.has_option(section, option) if self.config_parser else False

    def get(self, section, option):
        if self.config_parser:
            return self.config_parser.get(section, option)
        raise configparser.NoOptionError(option, section)

    def getint(self, section, option):
        return int(self.get(section, option))

    def getfloat(self, section, option):
        return float(self.get(section, option))

    def getboolean(self, section, option):
        val = str(self.get(section, option))
        if val.lower() not in _ConfigFile._BOOLEAN_STATES:
            raise ValueError('Not a boolean: {}'.format(val))
        return _ConfigFile._BOOLEAN_STATES[val.lower()]

    def set(self, config):
        ensure_dir(self.config_dir)
        with open(self.config_path, 'w', encoding=CONFIG_FILE_ENCODING) as configfile:
            if self.config_comment:
                configfile.write(self.config_comment + '\n')
            config.write(configfile)
        os.chmod(self.config_path, stat.S_IRUSR | stat.S_IWUSR)
        self.config_parser.read(self.config_path)

    def set_value(self, section, option, value):
        config = configparser.ConfigParser()
        config.read(self.config_path)
        try:
            config.add_section(section)
        except configparser.DuplicateSectionError:
            pass
        config.set(section, option, value)
        self.set(config)

    def remove_option(self, section, option):
        existed = False
        if self.config_parser:
            try:
                existed = self.config_parser.remove_option(section, option)
                self.set(self.config_parser)
            except configparser.NoSectionError:
                pass
        return existed

    def remove_section(self, section):
        if self.config_parser and self.config_parser.remove_section(section):
            self.set(self.config_parser)
            return True
        return False

    def clear(self):
        if self.config_parser:
            for section in self.config_parser.sections():
                self.config_parser.remove_section(section)
            self.set(self.config_parser)
