# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
from azure.cli.command_modules.acs.azuremonitormetrics.dc.defaults import get_default_dcr_name
from azure.cli.command_modules.acs.azuremonitormetrics.constants import (
    DC_API
)
from knack.util import CLIError


# pylint: disable=too-many-locals,too-many-branches,too-many-statements,line-too-long
def create_dcr(cmd, mac_region, azure_monitor_workspace_resource_id, cluster_subscription, cluster_resource_group_name, cluster_name, dce_resource_id):
    from azure.cli.core.util import send_raw_request
    dcr_name = get_default_dcr_name(mac_region, cluster_name)
    dcr_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Insights/dataCollectionRules/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        dcr_name
    )
    dcr_creation_body = json.dumps({"location": mac_region,
                                    "kind": "Linux",
                                    "properties": {
                                        "dataCollectionEndpointId": dce_resource_id,
                                        "dataSources": {"prometheusForwarder": [{"name": "PrometheusDataSource", "streams": ["Microsoft-PrometheusMetrics"], "labelIncludeFilter": {}}]},
                                        "dataFlows": [{"destinations": ["MonitoringAccount1"], "streams": ["Microsoft-PrometheusMetrics"]}],
                                        "description": "DCR description",
                                        "destinations": {
                                            "monitoringAccounts": [{"accountResourceId": azure_monitor_workspace_resource_id, "name": "MonitoringAccount1"}]}}})
    armendpoint = cmd.cli_ctx.cloud.endpoints.resource_manager
    dcr_url = f"{armendpoint}{dcr_resource_id}?api-version={DC_API}"
    try:
        headers = ['User-Agent=azuremonitormetrics.create_dcr']
        send_raw_request(cmd.cli_ctx, "PUT",
                         dcr_url, body=dcr_creation_body, headers=headers)
        return dcr_resource_id
    except CLIError as error:
        raise error
