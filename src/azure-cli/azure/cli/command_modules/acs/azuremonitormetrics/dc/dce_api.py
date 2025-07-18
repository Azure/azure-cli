# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.acs.azuremonitormetrics.constants import DC_API
from azure.cli.command_modules.acs.azuremonitormetrics.dc.defaults import get_default_dce_name
from knack.util import CLIError


def create_dce(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, mac_region):
    dce_name = get_default_dce_name(mac_region, cluster_name)
    dce_resource_id = (
        "/subscriptions/{0}/resourceGroups/{1}/providers/"
        "Microsoft.Insights/dataCollectionEndpoints/{2}"
    ).format(
        cluster_subscription,
        cluster_resource_group_name,
        dce_name
    )
    from azure.cli.command_modules.acs._client_factory import get_resources_client
    resources = get_resources_client(cmd.cli_ctx, cluster_subscription)
    try:
        resources.begin_create_or_update_by_id(
            dce_resource_id,
            DC_API,
            {
                "name": dce_name,
                "location": mac_region,
                "kind": "Linux",
                "properties": {}
            }
        )
        return dce_resource_id
    except Exception as error:
        raise CLIError(error)
