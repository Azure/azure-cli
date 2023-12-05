# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
from azure.cli.command_modules.acs.azuremonitormetrics.constants import DC_API
from azure.cli.command_modules.acs.azuremonitormetrics.dc.defaults import get_default_dce_name
from knack.util import CLIError


def create_dce(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, mac_region):
    from azure.cli.core.util import send_raw_request
    dce_name = get_default_dce_name(mac_region, cluster_name)
    dce_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Insights/dataCollectionEndpoints/{2}"\
        .format(cluster_subscription, cluster_resource_group_name, dce_name)
    try:
        armendpoint = cmd.cli_ctx.cloud.endpoints.resource_manager
        dce_url = f"{armendpoint}{dce_resource_id}?api-version={DC_API}"
        dce_creation_body = json.dumps({"name": dce_name,
                                        "location": mac_region,
                                        "kind": "Linux",
                                        "properties": {}})
        headers = ['User-Agent=azuremonitormetrics.create_dce']
        send_raw_request(cmd.cli_ctx, "PUT",
                         dce_url, body=dce_creation_body, headers=headers)
        return dce_resource_id
    except CLIError as error:
        raise error
