# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
from knack.util import CLIError
from azure.cli.core.azclierror import (
    UnknownError
)
from azure.cli.command_modules.acs.azuremonitormetrics.constants import (
    RP_API,
    AKS_CLUSTER_API
)


def sanitize_resource_id(resource_id):
    resource_id = resource_id.strip()
    if not resource_id.startswith("/"):
        resource_id = "/" + resource_id
    if resource_id.endswith("/"):
        resource_id = resource_id.rstrip("/")
    return resource_id.lower()


def post_request(cmd, subscription_id, rp_name, headers):
    from azure.cli.core.util import send_raw_request
    armendpoint = cmd.cli_ctx.cloud.endpoints.resource_manager
    customUrl = "{0}/subscriptions/{1}/providers/{2}/register?api-version={3}".format(
        armendpoint,
        subscription_id,
        rp_name,
        RP_API,
    )
    try:
        send_raw_request(cmd.cli_ctx, "POST", customUrl, headers=headers)
    except CLIError as e:
        raise CLIError(e)


# pylint: disable=line-too-long
def rp_registrations(cmd, subscription_id):
    from azure.cli.core.util import send_raw_request
    # Get list of RP's for RP's subscription
    try:
        headers = ['User-Agent=azuremonitormetrics.get_mac_sub_list']
        armendpoint = cmd.cli_ctx.cloud.endpoints.resource_manager
        customUrl = "{0}/subscriptions/{1}/providers?api-version={2}&$select=namespace,registrationstate".format(
            armendpoint,
            subscription_id,
            RP_API
        )
        r = send_raw_request(cmd.cli_ctx, "GET", customUrl, headers=headers)
    except CLIError as e:
        raise CLIError(e)
    isInsightsRpRegistered = False
    isAlertsManagementRpRegistered = False
    isMoniotrRpRegistered = False
    isDashboardRpRegistered = False
    json_response = json.loads(r.text)
    values_array = json_response["value"]
    for value in values_array:
        if value["namespace"].lower() == "microsoft.insights" and value["registrationState"].lower() == "registered":
            isInsightsRpRegistered = True
        if value["namespace"].lower() == "microsoft.alertsmanagement" and value["registrationState"].lower() == "registered":
            isAlertsManagementRpRegistered = True
        if value["namespace"].lower() == "microsoft.monitor" and value["registrationState"].lower() == "registered":
            isAlertsManagementRpRegistered = True
        if value["namespace"].lower() == "microsoft.dashboard" and value["registrationState"].lower() == "registered":
            isAlertsManagementRpRegistered = True
    if isInsightsRpRegistered is False:
        headers = ['User-Agent=azuremonitormetrics.register_insights_rp']
        post_request(cmd, subscription_id, "microsoft.insights", headers)
    if isAlertsManagementRpRegistered is False:
        headers = ['User-Agent=azuremonitormetrics.register_alertsmanagement_rp']
        post_request(cmd, subscription_id, "microsoft.alertsmanagement", headers)
    if isMoniotrRpRegistered is False:
        headers = ['User-Agent=azuremonitormetrics.register_monitor_rp']
        post_request(cmd, subscription_id, "microsoft.monitor", headers)
    if isDashboardRpRegistered is False:
        headers = ['User-Agent=azuremonitormetrics.register_dashboard_rp']
        post_request(cmd, subscription_id, "microsoft.dashboard", headers)


# pylint: disable=line-too-long
def check_azuremonitormetrics_profile(cmd, cluster_subscription, cluster_resource_group_name, cluster_name):
    from azure.cli.core.util import send_raw_request
    armendpoint = cmd.cli_ctx.cloud.endpoints.resource_manager
    feature_check_url = f"{armendpoint}/subscriptions/{cluster_subscription}/resourceGroups/{cluster_resource_group_name}/providers/Microsoft.ContainerService/managedClusters/{cluster_name}?api-version={AKS_CLUSTER_API}"
    try:
        headers = ['User-Agent=azuremonitormetrics.check_azuremonitormetrics_profile']
        r = send_raw_request(cmd.cli_ctx, "GET", feature_check_url,
                             body={}, headers=headers)
    except CLIError as e:
        raise UnknownError(e)
    json_response = json.loads(r.text)
    values_array = json_response["properties"]
    if "azureMonitorProfile" in values_array:
        if "metrics" in values_array["azureMonitorProfile"]:
            if values_array["azureMonitorProfile"]["metrics"]["enabled"] is True:
                raise CLIError(f"Azure Monitor Metrics is already enabled for this cluster. Please use `az aks update --disable-azure-monitor-metrics -g {cluster_resource_group_name} -n {cluster_name}` and then try enabling.")
