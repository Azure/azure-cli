# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pkgutil
import importlib

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

_hiddenimports = collect_submodules('humanfriendly')
_data = []

mods_ns_pkg = importlib.import_module('azure.cli.command_modules')
command_modules = [modname for _, modname, _ in pkgutil.iter_modules(mods_ns_pkg.__path__)]
for command_module in command_modules:
    _hiddenimports.extend(collect_submodules('azure.cli.command_modules.{}'.format(command_module)))

    tests_module = 'azure.cli.command_modules.{}.tests'.format(command_module)
    tests = importlib.util.find_spec(tests_module)
    if tests is not None:
        _data.extend(collect_data_files(tests_module))
hiddenimports = _hiddenimports
datas = _data
