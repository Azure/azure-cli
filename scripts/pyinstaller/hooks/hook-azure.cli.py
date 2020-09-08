# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pkgutil
import importlib

from PyInstaller.utils.hooks import collect_submodules

_hiddenimports = collect_submodules('humanfriendly')
_hiddenimports.extend(collect_submodules('pytest'))
_hiddenimports.extend(collect_submodules('xdist'))
_hiddenimports.extend(collect_submodules('azure.mgmt.keyvault'))
_hiddenimports.extend(collect_submodules('azure.multiapi'))

mods_ns_pkg = importlib.import_module('azure.cli.command_modules')
command_modules = [modname for _, modname, _ in pkgutil.iter_modules(mods_ns_pkg.__path__)]
for command_module in command_modules:
    all_packages = collect_submodules('azure.cli.command_modules.{}'.format(command_module))
    exclude_tests_packages = collect_submodules('azure.cli.command_modules.{}'.format(command_module), filter=lambda name: 'tests' not in name)
    print('{}\n{}\n{}\n\n'.format(command_module, str(all_packages), str(exclude_tests_packages)))
    _hiddenimports.extend(collect_submodules('azure.cli.command_modules.{}'.format(command_module), filter=lambda name: 'tests' not in name))
hiddenimports = _hiddenimports
