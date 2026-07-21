# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
from knack.util import CLIError
from azure.cli.core.azclierror import (
    UnknownError
)
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
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


def post_request(cmd, rp_name):
    resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    try:
        resource_client.providers.register(rp_name)
    except Exception as e:
        raise CLIError(e)


def register_rps(cmd, subscription_id, rp_namespaces, user_agent):
    from azure.cli.core.util import send_raw_request
    try:
        headers = ['User-Agent=' + user_agent]
        armendpoint = cmd.cli_ctx.cloud.endpoints.resource_manager
        customUrl = "{0}/subscriptions/{1}/providers?api-version={2}&$select=namespace,registrationstate".format(
            armendpoint,
            subscription_id,
            RP_API
        )
        r = send_raw_request(cmd.cli_ctx, "GET", customUrl, headers=headers)
        json_response = json.loads(r.text)
        values_array = json_response["value"]

        for value in values_array:
            namespace = value["namespace"].lower()
            if namespace in rp_namespaces and value["registrationState"].lower() == "registered":
                rp_namespaces[namespace] = True

        for namespace, registered in rp_namespaces.items():
            if not registered:
                headers = ['User-Agent=azuremonitormetrics.register_{}_rp'.format(namespace.split('.')[1].lower())]
                post_request(cmd, namespace)
    except CLIError as e:
        raise CLIError(e)


def rp_registrations(cmd, cluster_subscription_id, raw_parameters):
    from azure.mgmt.core.tools import parse_resource_id
    cluster_rp_namespaces = {
        "microsoft.insights": False,
        "microsoft.alertsmanagement": False
    }
    cluster_user_agent = 'azuremonitormetrics.get_cluster_sub_rp_list'
    register_rps(cmd, cluster_subscription_id, cluster_rp_namespaces, cluster_user_agent)

    subscription_id = cluster_subscription_id
    azure_monitor_workspace_resource_id = raw_parameters.get("azure_monitor_workspace_resource_id")
    if azure_monitor_workspace_resource_id and azure_monitor_workspace_resource_id != "":
        parsed_dict = parse_resource_id(azure_monitor_workspace_resource_id)
        subscription_id = parsed_dict["subscription"]
    monitor_workspace_rp_namespaces = {
        "microsoft.insights": False,
        "microsoft.alertsmanagement": False,
        "microsoft.monitor": False
    }
    monitor_workspace_user_agent = 'azuremonitormetrics.get_monitor_workspace_rp_list'
    register_rps(cmd, subscription_id, monitor_workspace_rp_namespaces, monitor_workspace_user_agent)

    grafana_workspace_resource_id = raw_parameters.get("grafana_workspace_resource_id")
    if grafana_workspace_resource_id and grafana_workspace_resource_id != "":
        grafana_sub_id = grafana_workspace_resource_id.split("/")[2]
        grafana_rp_namespaces = {
            "microsoft.dashboard": False
        }
        grafana_user_agent = 'azuremonitormetrics.get_grafana_sub_rp_list'
        register_rps(cmd, grafana_sub_id, grafana_rp_namespaces, grafana_user_agent)


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
                return True
    return False
