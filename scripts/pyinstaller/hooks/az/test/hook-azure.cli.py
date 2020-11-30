# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pkgutil
import importlib

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

_datas = collect_data_files('pip')

_hiddenimports = []
_hiddenimports.extend(collect_submodules('humanfriendly'))
_hiddenimports.extend(collect_submodules('pip'))
_hiddenimports.extend(collect_submodules('distutils'))
_hiddenimports.append('fileinput')

_hiddenimports.extend(collect_submodules('pytest'))
_hiddenimports.extend(collect_submodules('unittest'))
# _hiddenimports.extend(collect_submodules('xdist'))

_hiddenimports.extend(collect_submodules('azure.mgmt.keyvault'))
_hiddenimports.extend(collect_submodules('azure.mgmt.authorization'))
_hiddenimports.extend(collect_submodules('azure.mgmt.resource'))
_hiddenimports.extend(collect_submodules('azure.multiapi'))
_hiddenimports.extend(collect_submodules('azure.cli.core', filter=lambda name: 'tests' not in name))

mods_ns_pkg = importlib.import_module('azure.cli.command_modules')
command_modules = [modname for _, modname, _ in pkgutil.iter_modules(mods_ns_pkg.__path__)]
for command_module in command_modules:
    _hiddenimports.extend(collect_submodules('azure.cli.command_modules.{}'.format(command_module), filter=lambda name: 'tests' not in name))

datas = _datas
hiddenimports = _hiddenimports
