# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import fileinput
import os
import sys


class VersionPatcher(object):
    """Manages patching the version of a package to remove '+dev' from the version."""

    def __init__(self, use_version_patch, component_name, component_path):
        self.use_version_patch = use_version_patch
        self.component_name = component_name
        self.component_path = component_path
        self.setup_py = os.path.join(component_path, 'setup.py')
        self.backup_setup_py_version = None
        # These two modules also have version defined in the __init__.py file
        # These versions have to be kept in sync.
        if self.component_name == 'azure-cli':
            self.init_py_path = os.path.join(self.component_path, 'azure', 'cli', '__init__.py')
        elif self.component_name == 'azure-cli-core':
            self.init_py_path = os.path.join(self.component_path, 'azure', 'cli', 'core',
                                             '__init__.py')
        else:
            self.init_py_path = None
        self.backup_init_version = None

    def _patch_setup_py(self):
        for _, line in enumerate(fileinput.input(self.setup_py, inplace=1)):
            if line.startswith('VERSION'):
                self.backup_setup_py_version = line
                # apply version patch
                sys.stdout.write(line.replace('+dev', ''))
            else:
                sys.stdout.write(line)

    def _unpatch_setup_py(self):
        for _, line in enumerate(fileinput.input(self.setup_py, inplace=1)):
            if line.startswith('VERSION'):
                # restore original version
                sys.stdout.write(self.backup_setup_py_version)
            else:
                sys.stdout.write(line)

    def _patch_init_py(self):
        for _, line in enumerate(fileinput.input(self.init_py_path, inplace=1)):
            if line.startswith('__version__'):
                self.backup_init_version = line
                # apply init version patch
                sys.stdout.write(line.replace('+dev', ''))
            else:
                sys.stdout.write(line)

    def _unpatch_init_py(self):
        for _, line in enumerate(fileinput.input(self.init_py_path, inplace=1)):
            if line.startswith('__version__'):
                # restore original init version
                sys.stdout.write(self.backup_init_version)
            else:
                sys.stdout.write(line)

    def patch(self):
        if not self.use_version_patch:
            return
        self._patch_setup_py()
        if self.init_py_path:
            self._patch_init_py()

    def unpatch(self):
        if not self.use_version_patch:
            return
        self._unpatch_setup_py()
        if self.init_py_path:
            self._unpatch_init_py()
