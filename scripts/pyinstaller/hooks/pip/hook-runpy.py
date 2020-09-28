# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

_datas = collect_data_files('pip')

_hiddenimports = []
_hiddenimports.extend(collect_submodules('pip'))
_hiddenimports.extend(collect_submodules('distutils'))

hiddenimports = _hiddenimports
datas = _datas
