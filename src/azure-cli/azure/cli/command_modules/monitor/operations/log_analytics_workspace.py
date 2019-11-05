# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.mgmt.loganalytics.models import SkuNameEnum


def create_log_analytics_workspace(cmd, client, resource_group_name, workspace_name, location=None, tags=None,
                                   sku=SkuNameEnum.per_gb2018.value, retention_time=None):
    from azure.mgmt.loganalytics.models import Workspace, Sku
    from azure.cli.core.commands import LongRunningOperation
    workspace_client = client
    sku = Sku(name=sku)
    workspace_instance = Workspace(location=location,
                                   tags=tags,
                                   sku=sku,
                                   retention_in_days=retention_time)
    return LongRunningOperation(cmd.cli_ctx)(workspace_client.create_or_update(resource_group_name,
                                                                               workspace_name,
                                                                               workspace_instance))


def update_log_analytics_workspace(instance, tags=None, retention_time=None):
    if tags is not None:
        instance.tags = tags
    if retention_time is not None:
        instance.retention_in_days = retention_time
    return instance


def list_log_analytics_workspace(client, resource_group_name=None):
    workspace_client = client
    if resource_group_name is not None:
        return workspace_client.list_by_resource_group(resource_group_name)
    return workspace_client.list()
