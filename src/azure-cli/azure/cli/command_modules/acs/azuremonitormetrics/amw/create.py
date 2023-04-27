# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json

from azure.cli.command_modules.acs.azuremonitormetrics.constants import MAC_API
from azure.cli.command_modules.acs.azuremonitormetrics.amw.defaults import get_default_mac_name_and_region
from azure.cli.command_modules.acs._client_factory import get_resource_groups_client, get_resources_client
from azure.core.exceptions import HttpResponseError
from knack.util import CLIError


def create_default_mac(cmd, cluster_subscription, cluster_region):
    from azure.cli.core.util import send_raw_request
    default_mac_name, default_mac_region = get_default_mac_name_and_region(cmd, cluster_region)
    default_resource_group_name = "DefaultResourceGroup-{0}".format(default_mac_region)
    azure_monitor_workspace_resource_id = \
        "/subscriptions/{0}/resourceGroups/{1}/providers/microsoft.monitor/accounts/{2}"\
        .format(
            cluster_subscription,
            default_resource_group_name,
            default_mac_name
        )
    # Check if default resource group exists or not, if it does not then create it
    resource_groups = get_resource_groups_client(cmd.cli_ctx, cluster_subscription)
    resources = get_resources_client(cmd.cli_ctx, cluster_subscription)

    if resource_groups.check_existence(default_resource_group_name):
        try:
            resource = resources.get_by_id(azure_monitor_workspace_resource_id, MAC_API)
            # If MAC already exists then return from here
            return azure_monitor_workspace_resource_id, resource.location
        except HttpResponseError as ex:
            if ex.status_code != 404:
                raise ex
    else:
        resource_groups.create_or_update(default_resource_group_name, {"location": default_mac_region})
    association_body = json.dumps({"location": default_mac_region, "properties": {}})
    armendpoint = cmd.cli_ctx.cloud.endpoints.resource_manager
    association_url = f"{armendpoint}{azure_monitor_workspace_resource_id}?api-version={MAC_API}"
    try:
        headers = ['User-Agent=azuremonitormetrics.create_default_mac']
        send_raw_request(cmd.cli_ctx, "PUT", association_url,
                         body=association_body, headers=headers)
        return azure_monitor_workspace_resource_id, default_mac_region
    except CLIError as e:
        raise e
