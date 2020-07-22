# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from .._client_factory import cf_synapse_client_workspace_factory
from ..constant import SynapseSqlCreateMode
from azure.cli.core.util import sdk_no_wait, read_file_content
from azure.mgmt.synapse.models import SqlPool, SqlPoolPatchInfo, Sku


# Synapse sqlpool
def create_sql_pool(cmd, client, resource_group_name, workspace_name, sql_pool_name, performance_level, tags=None,
                    no_wait=False):
    workspace_client = cf_synapse_client_workspace_factory(cmd.cli_ctx)
    workspace_object = workspace_client.get(resource_group_name, workspace_name)
    location = workspace_object.location

    sku = Sku(name=performance_level)

    sql_pool_info = SqlPool(sku=sku, location=location, create_mode=SynapseSqlCreateMode.Default, tags=tags)

    return sdk_no_wait(no_wait, client.create, resource_group_name, workspace_name, sql_pool_name, sql_pool_info)


def update_sql_pool(cmd, client, resource_group_name, workspace_name, sql_pool_name, sku_name=None, tags=None):
    sku = Sku(name=sku_name)
    sql_pool_patch_info = SqlPoolPatchInfo(sku=sku, tags=tags)
    return client.update(resource_group_name, workspace_name, sql_pool_name, sql_pool_patch_info)
