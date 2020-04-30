# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import stat
import shutil
import configparser
import enum

from knack.log import get_logger
from knack.config import _ConfigFile
from knack.util import ensure_dir

ALL = 'ALL'   # effective level of local context, ALL means all commands can share this parameter value
LOCAL_CONTEXT_FILE = '.local_context_{}'
LOCAL_CONTEXT_CONFIG_SECTION = 'local_context'
LOCAL_CONTEXT_NOTICE = '; This file is used to store local context data.\n'\
                       '; DO NOT modify it manually unless you know it well.\n'
logger = get_logger(__name__)


class LocalContextAction(enum.Enum):
    SET = 1   # action for a parameter in local context, SET means its value will be saved to local context
    GET = 2   # action for a parameter in local context, GET means will read value from local context for this parameter


def _get_current_username(cli_ctx):
    from azure.cli.core._profile import Profile
    profile = Profile(cli_ctx=cli_ctx)
    username = None
    try:
        username = profile.get_current_account_user()
    except Exception:  # pylint: disable=broad-except
        pass
    return username


class AzCLILocalContext(object):  # pylint: disable=too-many-instance-attributes

    def __init__(self, cli_ctx):
        self.cli_ctx = cli_ctx
        self.config = cli_ctx.config
        self.dir_name = os.path.basename(self.config.config_dir)
        self.username = _get_current_username(cli_ctx)
        if self.username is not None:
            self.file_name = LOCAL_CONTEXT_FILE.format(self.username)
            self.is_on = self.config.getboolean(LOCAL_CONTEXT_CONFIG_SECTION, self.username, False)
        else:
            self.is_on = False

        self.current_dir = None
        try:
            self.current_dir = os.getcwd()
        except FileNotFoundError:
            logger.debug('The working directory has been deleted or recreated. Local context is ignored.')

        self._local_context_file = None
        if self.is_on and self.current_dir:
            self._load_local_context_file()

    def _load_local_context_file(self):
        current_dir = self.current_dir
        while current_dir:
            dir_path = os.path.join(current_dir, self.dir_name)
            file_path = os.path.join(dir_path, self.file_name)
            if os.path.isfile(file_path) and os.access(file_path, os.R_OK) and os.access(file_path, os.W_OK):
                logger.debug('Current effective local context working directory is %s', current_dir)
                self._local_context_file = _ConfigFile(dir_path, file_path, LOCAL_CONTEXT_NOTICE)
                break   # load only one local context
            # Stop if already in root drive
            if current_dir == os.path.dirname(current_dir):
                if self._local_context_file is None:
                    logger.debug('No effective local context found')
                break
            current_dir = os.path.dirname(current_dir)

    def effective_working_directory(self):
        return os.path.dirname(self._local_context_file.config_dir)

    def get(self, command, argument):
        if self.is_on and self.current_dir and self._local_context_file:
            command_parts = command.split()
            while True:
                section = ' '.join(command_parts) if command_parts else ALL
                try:
                    return self._local_context_file.get(section, argument)
                except (configparser.NoSectionError, configparser.NoOptionError):
                    pass
                if not command_parts:
                    break
                command_parts = command_parts[:-1]
        return None

    def set(self, scopes, argument, value):
        if self.is_on and self.current_dir:
            if self._local_context_file is None:
                file_path = os.path.join(self.current_dir, self.dir_name, self.file_name)
                if not os.path.isfile(file_path):
                    try:
                        ensure_dir(os.path.dirname(file_path))
                        with open(file_path, 'w'):
                            pass
                        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
                        self._local_context_file = None
                        self._load_local_context_file()
                        logger.warning('Initiate local context in %s', self.current_dir)
                    except Exception:  # pylint: disable=broad-except
                        logger.warning('fail to set value to local context')
            if self._local_context_file:
                for scope in scopes:
                    self._local_context_file.set_value(scope, argument, value)

    def turn_on(self):
        self.config.set_value(LOCAL_CONTEXT_CONFIG_SECTION, self.username, 'on')

    def turn_off(self):
        self.config.remove_option(LOCAL_CONTEXT_CONFIG_SECTION, self.username)

    def delete_file(self):
        try:
            os.remove(self._local_context_file.config_path)
            parent_dir = os.path.dirname(self._local_context_file.config_path)
            if not os.listdir(parent_dir):
                shutil.rmtree(parent_dir)
        except Exception:  # pylint: disable=broad-except
            return False
        return True

    def clear(self):
        self._local_context_file.clear()

    def delete(self, scopes, names=None):
        for scope in scopes:
            if names is None:
                self._local_context_file.remove_section(scope)
            else:
                for name in names:
                    self._local_context_file.remove_option(scope, name)

    def get_value(self, scopes=None, names=None):
        if scopes is None:
            scopes = self._local_context_file.sections()

        result = {}
        for scope in scopes:
            try:
                if names is None:
                    for name, value in self._local_context_file.items(scope):  # may raise NoSectionError
                        if scope not in result:
                            result[scope] = {}
                        result[scope][name] = value
                else:
                    for name in names:
                        value = self._local_context_file.get(scope, name)  # may raise NoOptionError
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
