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
        self._file_chain = []
        self._load_file_chain()

    def _load_file_chain(self):
        current_dir = os.getcwd()
        while current_dir:
            self._add_to_file_chain(current_dir, self.dir_name, self.file_name)
            # Stop if already in root drive
            if current_dir == os.path.dirname(current_dir):
                break
            current_dir = os.path.dirname(current_dir)
        # add root to _file_chain if exists
        self._add_to_file_chain(current_dir, self.dir_name, self.file_name)

    def _add_to_file_chain(self, current_dir, dir_name, file_name):
        dir_path = os.path.join(current_dir, dir_name)
        file_path = os.path.join(dir_path, file_name)
        if os.path.isfile(file_path) and os.access(file_path, os.R_OK) and os.access(file_path, os.W_OK):
            self._file_chain.append(_ConfigFile(dir_path, file_path))

    def get(self, command, argument):
        for local_context in self._file_chain:
            command_parts = command.split(' ')
            while True:
                section = ' '.join(command_parts) if command_parts else ALL
                try:
                    return local_context.get(section, argument)
                except (configparser.NoSectionError, configparser.NoOptionError):
                    pass
                if not command_parts:
                    break
                command_parts = command_parts[:-1]
        return None

    def set(self, scopes, argument, value):
        if self._file_chain:
            local_context = self._file_chain[0]
            for scope in scopes:
                local_context.set_value(scope, argument, value)

    def is_on(self):
        return len(self._file_chain) > 0

    def turn_on(self):
        current_dir = os.getcwd()
        file_path = os.path.join(current_dir, self.dir_name, self.file_name)
        if not os.path.isfile(file_path):
            try:
                ensure_dir(os.path.dirname(file_path))
                with open(file_path, 'w'):
                    pass
                os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
                self._file_chain.clear()
                self._load_file_chain()
            except Exception:  # pylint: disable=broad-except
                raise CLIError('fail to turn on local context in {}.'.format(os.path.dirname(current_dir)))
            logger.warning('local context in current directory is turned on.')
        else:
            raise CLIError('local context is already enabled in current directory')

    def turn_off(self):
        if self.is_on():
            file_path = self._file_chain[0].config_path
            try:
                os.remove(file_path)
                parent_dir = os.path.dirname(file_path)
                shutil.rmtree(parent_dir)
                logger.warning('local context in %s is turned off.', os.path.dirname(parent_dir))
            except Exception:  # pylint: disable=broad-except
                raise CLIError('fail to turn off local context in {}.'.format(os.path.dirname(parent_dir)))

    def first_dir_path(self):
        if self.is_on():
            return os.path.dirname(os.path.dirname(self._file_chain[0].config_path))
        return None


class LocalContextAttribute(object):
    # pylint: disable=too-few-public-methods
    def __init__(self, name, actions, scopes=None):
        """ Local Context Attribute arguments

        :param name: Argument name in local context, should make sure they are consistent for STORE and USE places
        :type name: str
        :param actions: Which action should be taken for local context, value can be a list of STORE and USE
        :type actions: list
        :param scopes: The effective level of of this argument when saved to local context.
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
