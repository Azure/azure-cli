# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import stat
import shutil
import configparser

from knack.log import get_logger
from knack.config import _ConfigFile
from knack.util import ensure_dir, CLIError

STORE = 'STORE'   # action for a parameter in local context, STORE means its value will be saved to local context
USE = 'USE'   # action for a parameter in local context, USE means will read value from local context for this parameter
ALL = 'ALL'   # effective level of local context, ALL means all commands can share this parameter value
logger = get_logger(__name__)


class AzCLILocalContext(object):

    def __init__(self, dir_name=None, file_name=None):
        self.dir_name = dir_name
        self.file_name = file_name
        self._local_context_file = None
        self._load_local_context_file()

    def _load_local_context_file(self):
        current_dir = os.getcwd()
        while current_dir:
            dir_path = os.path.join(current_dir, self.dir_name)
            file_path = os.path.join(dir_path, self.file_name)
            if os.path.isfile(file_path) and os.access(file_path, os.R_OK) and os.access(file_path, os.W_OK):
                self._local_context_file = _ConfigFile(dir_path, file_path)
                break   # load only one local context
            # Stop if already in root drive
            if current_dir == os.path.dirname(current_dir):
                if self._local_context_file is None:
                    logger.debug('local context is not turned on in %s and all its parent directories', current_dir)
                break
            current_dir = os.path.dirname(current_dir)

    def get(self, command, argument):
        if self.is_on():
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
        if self.is_on():
            for scope in scopes:
                self._local_context_file.set_value(scope, argument, value)

    def is_on(self):
        return self._local_context_file is not None

    def turn_on(self):
        current_dir = os.getcwd()
        file_path = os.path.join(current_dir, self.dir_name, self.file_name)
        if not os.path.isfile(file_path):
            try:
                ensure_dir(os.path.dirname(file_path))
                with open(file_path, 'w'):
                    pass
                os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
                self._local_context_file = None
                self._load_local_context_file()
            except Exception:  # pylint: disable=broad-except
                raise CLIError('fail to turn on local context in {}.'.format(current_dir))
            logger.warning('local context in %s is turned on.', current_dir)
        else:
            logger.warning('local context is already turned on in %s', current_dir)

    def turn_off(self):
        if self.is_on():
            file_path = self._local_context_file.config_path
            try:
                os.remove(file_path)
                parent_dir = os.path.dirname(file_path)
                if not os.listdir(parent_dir):
                    shutil.rmtree(parent_dir)
                self._local_context_file = None
                logger.warning('local context in %s is turned off.', os.path.dirname(parent_dir))
            except Exception:  # pylint: disable=broad-except
                raise CLIError('fail to turn off local context in {}.'.format(os.path.dirname(parent_dir)))

    def current_turn_on_dir(self):
        if self.is_on():
            return os.path.dirname(os.path.dirname(self._local_context_file.config_path))
        return None


class LocalContextAttribute(object):
    # pylint: disable=too-few-public-methods
    def __init__(self, name, actions, scopes=None):
        """ Local Context Attribute arguments

        :param name: Argument name in local context. Make sure it is consistent for STORE and USE.
        :type name: str
        :param actions: Which action should be taken for local context. Allowed values: STORE, USE
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
        if scopes is None and STORE in actions:
            scopes = [ALL]
        self.scopes = scopes
