# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.nic._list_effective_nsg import ListEffectiveNsg as _ListEffectiveNsg
from azure.cli.command_modules.network._format import transform_effective_nsg


class NICListEffectiveNsg(_ListEffectiveNsg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_transformer = transform_effective_nsg
