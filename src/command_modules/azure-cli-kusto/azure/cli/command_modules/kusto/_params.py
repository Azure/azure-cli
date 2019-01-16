# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (name_type)
from azure.mgmt.kusto.models import AzureSkuName
from azure.cli.core.commands.parameters import (get_enum_type)


def load_arguments(self, _):

    # Kusto clusters
    sku_arg_type = CLIArgumentType(help='The name of the sku.',
                                   arg_type=get_enum_type(AzureSkuName))

    with self.argument_context('kusto cluster') as c:
        c.ignore('kusto_management_request_options')
        c.argument('cluster_name', arg_type=name_type, help='The name of the cluster.', id_part='name')
        c.argument('sku', arg_type=sku_arg_type)
        c.argument('capacity', type=int, help='The instance number of the VM.')

    # Kusto databases
    with self.argument_context('kusto database') as c:
        c.ignore('kusto_management_request_options')
        c.argument('cluster_name', help='The name of the cluster.', id_part='name')
        c.argument('database_name', arg_type=name_type, help='The name of the database.', id_part='child_name_1')
        c.argument('soft_delete_period_in_days', type=int, help='The number of days that data should be kept before it is unavailable to query.')
        c.argument('hot_cache_period_in_days', type=int, help='The number of days that data should be kept in cache, for fast queries.')

    # Kusto database list
    with self.argument_context('kusto database list') as c:
        c.argument('cluster_name', id_part=None)
