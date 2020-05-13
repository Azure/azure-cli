# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.mgmt.loganalytics.models import WorkspaceSkuNameEnum


def create_log_analytics_workspace(cmd, client, resource_group_name, workspace_name, location=None, tags=None,
                                   sku=WorkspaceSkuNameEnum.per_gb2018.value, retention_time=None,
                                   public_network_access_for_query=None, public_network_access_for_ingestion=None):
    from azure.mgmt.loganalytics.models import Workspace, WorkspaceSku
    from azure.cli.core.commands import LongRunningOperation
    workspace_client = client
    sku = WorkspaceSku(name=sku)
    workspace_instance = Workspace(location=location,
                                   tags=tags,
                                   sku=sku,
                                   retention_in_days=retention_time,
                                   public_network_access_for_query=public_network_access_for_query,
                                   public_network_access_for_ingestion=public_network_access_for_ingestion)
    return LongRunningOperation(cmd.cli_ctx)(workspace_client.create_or_update(resource_group_name,
                                                                               workspace_name,
                                                                               workspace_instance))


def update_log_analytics_workspace(instance, tags=None, retention_time=None,
                                   public_network_access_for_query=None, public_network_access_for_ingestion=None):
    if tags is not None:
        instance.tags = tags
    if retention_time is not None:
        instance.retention_in_days = retention_time
    if public_network_access_for_query is not None:
        instance.public_network_access_for_query = public_network_access_for_query
    if public_network_access_for_ingestion is not None:
        instance.public_network_access_for_ingestion = public_network_access_for_ingestion
    return instance


def list_log_analytics_workspace(client, resource_group_name=None):
    workspace_client = client
    if resource_group_name is not None:
        return workspace_client.list_by_resource_group(resource_group_name)
    return workspace_client.list()
