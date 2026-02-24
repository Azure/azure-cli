# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.nic._show_effective_route_table import ShowEffectiveRouteTable as _ShowEffectiveRouteTable
from azure.cli.command_modules.network._format import transform_effective_route_table


class NICShowEffectiveRouteTable(_ShowEffectiveRouteTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_transformer = transform_effective_route_table
