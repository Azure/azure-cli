import json
from azure.cli.command_modules.acs.azuremonitormetrics.deaults import get_default_region
from azure.cli.command_modules.acs.azuremonitormetrics.responseparsers.amwlocationresponseparser import parseResourceProviderResponseForLocations

from knack.util import CLIError

def get_supported_rp_locations(cmd, rp_name):
    from azure.cli.core.util import send_raw_request
    supported_locations = []
    headers = ['User-Agent=azuremonitormetrics.get_supported_rp_locations']
    association_url = f"https://management.azure.com/providers/{rp_name}?api-version={RP_LOCATION_API}"
    r = send_raw_request(cmd.cli_ctx, "GET", association_url, headers=headers)
    data = json.loads(r.text)
    supported_locations = parseResourceProviderResponseForLocations(data)
    return supported_locations

def get_default_mac_region(cmd, cluster_region):
    global first_supported_region
    if first_supported_region is not None and len(first_supported_region) != 0:
        return first_supported_region
    supported_locations = get_supported_rp_locations(cmd, 'Microsoft.Monitor')
    if cluster_region in supported_locations:
        return cluster_region
    if len(supported_locations) > 0:
        first_supported_region = supported_locations[0]
        return supported_locations[0]
    cloud_name = cmd.cli_ctx.cloud.name
    if cloud_name.lower() == 'azurechinacloud':
        raise CLIError("Azure China Cloud is not supported for the Azure Monitor Metrics addon")
    if cloud_name.lower() == 'azureusgovernment':
        return "usgovvirginia"
    # default to public cloud
    return get_default_region(cmd)


def get_default_mac_name_and_region(cmd, cluster_region):
    default_mac_region = get_default_mac_region(cmd, cluster_region)
    default_mac_name = "DefaultAzureMonitorWorkspace-" + default_mac_region
    default_mac_name = default_mac_name[0:43]
    return default_mac_name, default_mac_region
