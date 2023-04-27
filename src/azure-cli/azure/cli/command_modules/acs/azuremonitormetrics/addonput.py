# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
from azure.cli.command_modules.acs.azuremonitormetrics.constants import AKS_CLUSTER_API
from azure.cli.core.azclierror import (
    UnknownError,
    CLIError
)


# pylint: disable=line-too-long
def addon_put(cmd, cluster_subscription, cluster_resource_group_name, cluster_name):
    from azure.cli.core.util import send_raw_request
    armendpoint = cmd.cli_ctx.cloud.endpoints.resource_manager
    feature_check_url = f"{armendpoint}/subscriptions/{cluster_subscription}/resourceGroups/{cluster_resource_group_name}/providers/Microsoft.ContainerService/managedClusters/{cluster_name}?api-version={AKS_CLUSTER_API}"
    try:
        headers = ['User-Agent=azuremonitormetrics.addon_get']
        r = send_raw_request(cmd.cli_ctx, "GET", feature_check_url,
                             body={}, headers=headers)
    except CLIError as e:
        raise UnknownError(e)
    json_response = json.loads(r.text)
    if "azureMonitorProfile" in json_response["properties"]:
        if "metrics" in json_response["properties"]["azureMonitorProfile"]:
            if json_response["properties"]["azureMonitorProfile"]["metrics"]["enabled"] is False:
                # What if enabled doesn't exist
                json_response["properties"]["azureMonitorProfile"]["metrics"]["enabled"] = True
    try:
        headers = ['User-Agent=azuremonitormetrics.addon_put']
        body = json.dumps(json_response)
        r = send_raw_request(cmd.cli_ctx, "PUT", feature_check_url,
                             body=body, headers=headers)
    except CLIError as e:
        raise UnknownError(e)
