# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import pkgutil
from importlib import import_module

from PyInstaller.utils.hooks import collect_submodules

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SRC_DIR = os.path.join(BASE_DIR, 'src')
PATTERN = r'operations_tmpl=(?P<quote>[\'"])(?P<module>.+)#.+(?P=quote)'
EXCLUDE_SUFFIX = ['.{}', '.operations']

_hiddenimports = []
modules = []

mods_ns_pkg = import_module('azure.cli.command_modules')
command_modules = [modname for _, modname, _ in pkgutil.iter_modules(mods_ns_pkg.__path__)]
for command_module in command_modules:
    _hiddenimports.extend(collect_submodules('azure.cli.command_modules.{}'.format(command_module)))

hiddenimports = _hiddenimports
