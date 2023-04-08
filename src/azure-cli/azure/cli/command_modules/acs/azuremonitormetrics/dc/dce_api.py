import json
from azure.cli.command_modules.acs.azuremonitormetrics.constants import DC_API
from azure.cli.command_modules.acs.azuremonitormetrics.dc.defaults import get_default_dce_name
from azure.cli.command_modules.acs.azuremonitormetrics.constants import DC_API
from knack.util import CLIError


def create_dce(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, mac_region):
    from azure.cli.core.util import send_raw_request
    dce_name = get_default_dce_name(cmd, mac_region, cluster_name)
    dce_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Insights/dataCollectionEndpoints/{2}".format(cluster_subscription, cluster_resource_group_name, dce_name)
    try:
        dce_url = f"https://management.azure.com{dce_resource_id}?api-version={DC_API}"
        dce_creation_body = json.dumps({"name": dce_name,
                                        "location": mac_region,
                                        "kind": "Linux",
                                        "properties": {}})
        headers = ['User-Agent=azuremonitormetrics.create_dce']
        send_raw_request(cmd.cli_ctx, "PUT",
                         dce_url, body=dce_creation_body, headers=headers)
        error = None
        return dce_resource_id
    except CLIError as error:
        raise error