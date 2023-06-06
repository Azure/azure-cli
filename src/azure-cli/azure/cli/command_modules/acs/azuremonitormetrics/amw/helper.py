# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.acs.azuremonitormetrics.amw.create import create_default_mac
from azure.cli.command_modules.acs.azuremonitormetrics.constants import MAC_API
from azure.cli.command_modules.acs.azuremonitormetrics.helper import sanitize_resource_id
from azure.cli.command_modules.acs._client_factory import get_resources_client
from azure.core.exceptions import HttpResponseError


def get_amw_region(cmd, azure_monitor_workspace_resource_id):
    # region of MAC can be different from region of RG so find the location of the azure_monitor_workspace_resource_id
    amw_subscription_id = azure_monitor_workspace_resource_id.split("/")[2]
    resources = get_resources_client(cmd.cli_ctx, amw_subscription_id)
    try:
        resource = resources.get_by_id(
            azure_monitor_workspace_resource_id, MAC_API)
        return resource.location.lower()
    except HttpResponseError as ex:
        raise ex


def get_azure_monitor_workspace_resource(cmd, cluster_subscription, cluster_region, raw_parameters):
    azure_monitor_workspace_resource_id = raw_parameters.get("azure_monitor_workspace_resource_id")
    if azure_monitor_workspace_resource_id is None or azure_monitor_workspace_resource_id == "":
        azure_monitor_workspace_resource_id, azure_monitor_workspace_location = create_default_mac(
            cmd,
            cluster_subscription,
            cluster_region
        )
    else:
        azure_monitor_workspace_resource_id = sanitize_resource_id(azure_monitor_workspace_resource_id)
        azure_monitor_workspace_location = get_amw_region(cmd, azure_monitor_workspace_resource_id)
    print(f"Using Azure Monitor Workspace (stores prometheus metrics) : {azure_monitor_workspace_resource_id}")
    return azure_monitor_workspace_resource_id, azure_monitor_workspace_location.lower()
