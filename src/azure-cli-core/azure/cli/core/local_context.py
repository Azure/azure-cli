# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import shutil
import configparser
import enum

from knack.log import get_logger
from knack.config import _ConfigFile

ALL = 'all'   # effective level of local context, ALL means all commands can share this parameter value
LOCAL_CONTEXT_FILE = '.local_context_{}'  # each user has a separate file, an example is .local_context_username
LOCAL_CONTEXT_ON_OFF_CONFIG_SECTION = 'local_context'
LOCAL_CONTEXT_NOTICE = '; This file is used to store local context data.\n'\
                       '; DO NOT modify it manually unless you know it well.\n'
logger = get_logger(__name__)


class LocalContextAction(enum.Enum):
    SET = 1   # action for a parameter in local context, SET means its value will be saved to local context
    GET = 2   # action for a parameter in local context, GET means will read value from local context for this parameter


def _get_current_system_username():
    try:
        import getpass
        return getpass.getuser()
    except Exception:  # pylint: disable=broad-except
        pass
    return None


class AzCLILocalContext(object):  # pylint: disable=too-many-instance-attributes

    def __init__(self, cli_ctx):
        self.cli_ctx = cli_ctx
        self.config = cli_ctx.config
        self.dir_name = os.path.basename(self.config.config_dir)
        self.username = None
        self.is_on = False
        self.current_dir = None

        # only used in get/set/effective_working_directory function, to avoid calling load files to many times.
        self._local_context_file = None

        self.initialize()

    def initialize(self):
        self.username = _get_current_system_username()
        self.is_on = self.config.getboolean(LOCAL_CONTEXT_ON_OFF_CONFIG_SECTION, self.username, False) \
            if self.username else False

        try:
            self.current_dir = os.getcwd()
        except FileNotFoundError:
            if self.is_on:
                logger.warning('The working directory has been deleted or recreated. Local context is ignored.')

        if self.is_on:
            self._local_context_file = self._get_local_context_file()

    def _get_local_context_file_name(self):
        return LOCAL_CONTEXT_FILE.format(self.username)

    def _load_local_context_files(self, recursive=False):
        local_context_files = []
        if self.username and self.current_dir:
            current_dir = self.current_dir
            while current_dir:
                dir_path = os.path.join(current_dir, self.dir_name)
                file_path = os.path.join(dir_path, self._get_local_context_file_name())
                if os.path.isfile(file_path) and os.access(file_path, os.R_OK) and os.access(file_path, os.W_OK):
                    local_context_files.append(_ConfigFile(dir_path, file_path, LOCAL_CONTEXT_NOTICE))
                    if not recursive:
                        break   # load only one local context
                # Stop if already in root drive
                if current_dir == os.path.dirname(current_dir):
                    break
                current_dir = os.path.dirname(current_dir)
        return local_context_files

    def _get_local_context_file(self):
        local_context_files = self._load_local_context_files(recursive=False)
        if len(local_context_files) == 1:
            return local_context_files[0]
        return None

    def effective_working_directory(self):
        return os.path.dirname(self._local_context_file.config_dir) if self._local_context_file else ''

    def get(self, command, argument):
        if self.is_on and self._local_context_file:
            command_parts = command.split()
            while True:
                section = ' '.join(command_parts) if command_parts else ALL
                try:
                    return self._local_context_file.get(section.lower(), argument)
                except (configparser.NoSectionError, configparser.NoOptionError):
                    pass
                if not command_parts:
                    break
                command_parts = command_parts[:-1]
        return None

    def set(self, scopes, argument, value):
        if self.is_on and self.username and self.current_dir:
            if self._local_context_file is None:
                file_path = os.path.join(self.current_dir, self.dir_name, self._get_local_context_file_name())
                dir_path = os.path.join(self.current_dir, self.dir_name)
                self._local_context_file = _ConfigFile(dir_path, file_path, LOCAL_CONTEXT_NOTICE)

            for scope in scopes:
                self._local_context_file.set_value(scope.lower(), argument, value)

    def turn_on(self):
        self.config.set_value(LOCAL_CONTEXT_ON_OFF_CONFIG_SECTION, self.username, 'on')
        self.is_on = self.config.getboolean(LOCAL_CONTEXT_ON_OFF_CONFIG_SECTION, self.username, False)
        self._local_context_file = self._get_local_context_file()

    def turn_off(self):
        self.config.remove_option(LOCAL_CONTEXT_ON_OFF_CONFIG_SECTION, self.username)
        self.is_on = self.config.getboolean(LOCAL_CONTEXT_ON_OFF_CONFIG_SECTION, self.username, False)
        self._local_context_file = None

    def delete_file(self, recursive=False):
        local_context_files = self._load_local_context_files(recursive=recursive)
        for local_context_file in local_context_files:
            try:
                os.remove(local_context_file.config_path)
                parent_dir = os.path.dirname(local_context_file.config_path)
                if not os.listdir(parent_dir):
                    shutil.rmtree(parent_dir)
                logger.warning('Local context persistence file in working directory %s is deleted.',
                               os.path.dirname(local_context_file.config_dir))
            except Exception:  # pylint: disable=broad-except
                logger.warning('Fail to delete local context persistence file in working directory %s',
                               os.path.dirname(local_context_file.config_dir))

    def clear(self, recursive=False):
        local_context_files = self._load_local_context_files(recursive=recursive)
        for local_context_file in local_context_files:
            local_context_file.clear()
            logger.warning('Local context information in working directory %s is cleared.',
                           os.path.dirname(local_context_file.config_dir))

    def delete(self, names=None):
        local_context_file = self._get_local_context_file()
        if local_context_file:
            for scope in local_context_file.sections():
                for name in names:
                    local_context_file.remove_option(scope, name)
        logger.warning('Local context value is deleted. You can run `az local-context show` to show all available '
                       'values.')

    def get_value(self, names=None):
        result = {}

        local_context_file = self._get_local_context_file()
        if not local_context_file:
            return result

        for scope in local_context_file.sections():
            try:
                if names is None:
                    for name, value in local_context_file.items(scope):  # may raise NoSectionError
                        if scope not in result:
                            result[scope] = {}
                        result[scope][name] = value
                else:
                    for name in names:
                        value = local_context_file.get(scope, name)  # may raise NoOptionError
                        if scope not in result:
                            result[scope] = {}
                        result[scope][name] = value
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass
        return result


class LocalContextAttribute(object):
    # pylint: disable=too-few-public-methods
    def __init__(self, name, actions, scopes=None):
        """ Local Context Attribute arguments

        :param name: Argument name in local context. Make sure it is consistent for SET and GET.
        :type name: str
        :param actions: Which action should be taken for local context. Allowed values: SET, GET
        :type actions: list
        :param scopes: The effective commands or command groups of this argument when saved to local context.
        :type scopes: list
        """
        self.name = name

        if isinstance(actions, str):
            actions = [actions]
        self.actions = actions

        if isinstance(scopes, str):
            scopes = [scopes]
        if scopes is None and LocalContextAction.SET in actions:
            scopes = [ALL]
        self.scopes = scopes
