# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.route_filter.rule._list_service_communities import \
    ListServiceCommunities as _ListServiceCommunities
from azure.cli.command_modules.network._format import transform_service_community_table_output


class RouteFilterRuleListServiceCommunities(_ListServiceCommunities):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_transformer = transform_service_community_table_output
