# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
from azure.cli.command_modules.acs.azuremonitormetrics.responseparsers.amwlocationresponseparser import (
    parseResourceProviderResponseForLocations
)
from azure.cli.command_modules.acs.azuremonitormetrics.constants import RP_LOCATION_API


def get_default_region(cmd):
    cloud_name = cmd.cli_ctx.cloud.name
    if cloud_name.lower() == 'azurechinacloud':
        return "chinanorth3"
    if cloud_name.lower() == 'azureusgovernment':
        return "usgovvirginia"
    if cloud_name.lower() == 'ussec':
        return "ussecwest"
    if cloud_name.lower() == 'usnat':
        return "usnatwest"
    return "eastus"


def get_supported_rp_locations(cmd, rp_name, subscription):
    from azure.cli.core.util import send_raw_request
    supported_locations = []
    headers = ['User-Agent=azuremonitormetrics.get_supported_rp_locations']
    armendpoint = cmd.cli_ctx.cloud.endpoints.resource_manager
    association_url = f"{armendpoint}/subscriptions/{subscription}/providers/{rp_name}?api-version={RP_LOCATION_API}"
    r = send_raw_request(cmd.cli_ctx, "GET", association_url, headers=headers)
    data = json.loads(r.text)
    supported_locations = parseResourceProviderResponseForLocations(data)
    return supported_locations


def get_default_mac_region(cmd, cluster_region, subscription):
    supported_locations = get_supported_rp_locations(cmd, 'Microsoft.Monitor', subscription)
    if cluster_region == 'centraluseuap':
        return 'eastus2euap'
    if cluster_region in supported_locations:
        return cluster_region
    if len(supported_locations) > 0:
        return supported_locations[0]
    # default to public cloud
    return get_default_region(cmd)


def get_default_mac_name_and_region(cmd, cluster_region, subscription):
    default_mac_region = get_default_mac_region(cmd, cluster_region, subscription)
    default_mac_name = "DefaultAzureMonitorWorkspace-" + default_mac_region
    default_mac_name = default_mac_name[0:43]
    return default_mac_name, default_mac_region
