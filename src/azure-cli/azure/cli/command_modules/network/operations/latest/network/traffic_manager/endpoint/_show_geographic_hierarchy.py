# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.traffic_manager.endpoint._show_geographic_hierarchy import \
    ShowGeographicHierarchy as _ShowGeographicHierarchy
from azure.cli.command_modules.network._format import transform_geographic_hierachy_table_output


class TrafficManagerEndpointShowGeographicHierarchy(_ShowGeographicHierarchy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_transformer = transform_geographic_hierachy_table_output
