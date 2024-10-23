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
    import re
    from azure.mgmt.core.tools import parse_resource_id
    # Define the allowed characters in the final string
    allowed_chars = re.compile(r'[^a-zA-Z0-9]')

    # Parse the resource ID to extract details
    parsed_dict = parse_resource_id(azure_monitor_workspace_resource_id)
    resources = get_resources_client(cmd.cli_ctx, parsed_dict["subscription"])
    try:
        # Retrieve the resource information
        resource = resources.get_by_id(
            azure_monitor_workspace_resource_id, MAC_API)
        # Get the location and filter it to include only allowed characters
        location = resource.location.lower()
        filtered_location = allowed_chars.sub('', location)
        return filtered_location
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
