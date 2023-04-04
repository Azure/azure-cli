# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import uuid
# from sre_constants import FAILURE, SUCCESS

from azure-cli.azure.cli.command_modules.acs.azuremonitormetrics.addonput import addon_put
from azure.cli.command_modules.acs.azuremonitormetrics.responseparsers.amwlocationresponseparser import parseResourceProviderResponseForLocations

from azure.cli.core.azclierror import (
    UnknownError,
    InvalidArgumentValueError,
    ClientRequestError,
    CLIError
)
from .._client_factory import get_resources_client, get_resource_groups_client
from enum import Enum
from six import with_metaclass
from azure.core import CaseInsensitiveEnumMeta
from azure.core.exceptions import HttpResponseError

AKS_CLUSTER_API = "2023-01-01" # "2023-01-01"
MAC_API = "2023-04-03"
DC_API = "2022-06-01"
GRAFANA_API = "2022-08-01"
GRAFANA_ROLE_ASSIGNMENT_API = "2022-04-01"
RULES_API = "2023-03-01"
FEATURE_API = "2020-09-01"
RP_API = "2021-04-01"
ALERTS_API = "2023-01-01-preview"
RP_LOCATION_API = "2022-01-01"

class GrafanaLink(with_metaclass(CaseInsensitiveEnumMeta, str, Enum)):
    """
    Status of Grafana link to the Prometheus Addon
    """
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ALREADYPRESENT = "ALREADYPRESENT"
    NOPARAMPROVIDED = "NOPARAMPROVIDED"


class DC_TYPE(with_metaclass(CaseInsensitiveEnumMeta, str, Enum)):
    """
    Types of DC* objects
    """
    DCE = "DCE"
    DCR = "DCR"
    DCRA = "DCRA"


first_supported_region = ""


MapToClosestMACRegion = {
    "australiacentral": "eastus",
    "australiacentral2": "eastus",
    "australiaeast": "eastus",
    "australiasoutheast": "eastus",
    "brazilsouth": "eastus",
    "canadacentral": "eastus",
    "canadaeast": "eastus",
    "centralus": "centralus",
    "centralindia": "centralindia",
    "eastasia": "westeurope",
    "eastus": "eastus",
    "eastus2": "eastus2",
    "francecentral": "westeurope",
    "francesouth": "westeurope",
    "japaneast": "eastus",
    "japanwest": "eastus",
    "koreacentral": "westeurope",
    "koreasouth": "westeurope",
    "northcentralus": "eastus",
    "northeurope": "westeurope",
    "southafricanorth": "westeurope",
    "southafricawest": "westeurope",
    "southcentralus": "eastus",
    "southeastasia": "westeurope",
    "southindia": "centralindia",
    "uksouth": "westeurope",
    "ukwest": "westeurope",
    "westcentralus": "eastus",
    "westeurope": "westeurope",
    "westindia": "centralindia",
    "westus": "westus",
    "westus2": "westus2",
    "westus3": "westus",
    "norwayeast": "westeurope",
    "norwaywest": "westeurope",
    "switzerlandnorth": "westeurope",
    "switzerlandwest": "westeurope",
    "uaenorth": "westeurope",
    "germanywestcentral": "westeurope",
    "germanynorth": "westeurope",
    "uaecentral": "westeurope",
    "eastus2euap": "eastus2euap",
    "centraluseuap": "westeurope",
    "brazilsoutheast": "eastus",
    "jioindiacentral": "centralindia",
    "swedencentral": "westeurope",
    "swedensouth": "westeurope",
    "qatarcentral": "westeurope"
}

def check_azuremonitormetrics_profile(cmd, cluster_subscription, cluster_resource_group_name, cluster_name):
    from azure.cli.core.util import send_raw_request
    feature_check_url = f"https://management.azure.com/subscriptions/{cluster_subscription}/resourceGroups/{cluster_resource_group_name}/providers/Microsoft.ContainerService/managedClusters/{cluster_name}?api-version={AKS_CLUSTER_API}"
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
                raise CLIError(f"Azure Monitor Metrics is already enabled for this cluster. Please use `az aks update --disable-azuremonitormetrics -g {cluster_resource_group_name} -n {cluster_name}` and then try enabling.")


# DCR = 64, DCE = 44, DCRA = 64
# All DC* object names should end only in alpha numeric (after `length` trim)
# DCE remove underscore from cluster name
def sanitize_name(name, type, length):
    length = length - 1
    if type == DC_TYPE.DCE:
        name = name.replace("_", "")
    name = name[0:length]
    lastIndexAlphaNumeric = len(name) - 1
    while ((name[lastIndexAlphaNumeric].isalnum() is False) and lastIndexAlphaNumeric > -1):
        lastIndexAlphaNumeric = lastIndexAlphaNumeric - 1
    if (lastIndexAlphaNumeric < 0):
        return ""

    return name[0:lastIndexAlphaNumeric + 1]


def sanitize_resource_id(resource_id):
    resource_id = resource_id.strip()
    if not resource_id.startswith("/"):
        resource_id = "/" + resource_id
    if resource_id.endswith("/"):
        resource_id = resource_id.rstrip("/")
    return resource_id.lower()


def get_supported_rp_locations(cmd, rp_name):
    from azure.cli.core.util import send_raw_request
    supported_locations = []
    headers = ['User-Agent=azuremonitormetrics.get_supported_rp_locations']
    association_url = f"https://management.azure.com/providers/{rp_name}?api-version={RP_LOCATION_API}"
    r = send_raw_request(cmd.cli_ctx, "GET", association_url, headers=headers)
    data = json.loads(r.text)
    supported_locations = parseResourceProviderResponseForLocations(data)
    return supported_locations


def get_default_region(cmd):
    cloud_name = cmd.cli_ctx.cloud.name
    if cloud_name.lower() == 'azurechinacloud':
        raise CLIError("Azure China Cloud is not supported for the Azure Monitor Metrics addon")
    if cloud_name.lower() == 'azureusgovernment':
        return "usgovvirginia"
    return "eastus"

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

def get_default_mac_name(cmd, cluster_region):
    default_mac_name = "DefaultAzureMonitorWorkspace-" + get_default_mac_region(cmd, cluster_region)
    default_mac_name = default_mac_name[0:43]
    return default_mac_name


def create_default_mac(cmd, cluster_subscription, cluster_region):
    from azure.cli.core.util import send_raw_request
    default_mac_name = get_default_mac_name(cmd, cluster_region)
    default_resource_group_name = "DefaultResourceGroup-{0}".format(get_default_mac_region(cmd, cluster_region))
    azure_monitor_workspace_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/microsoft.monitor/accounts/{2}".format(cluster_subscription, default_resource_group_name, default_mac_name)
    # Check if default resource group exists or not, if it does not then create it
    resource_groups = get_resource_groups_client(cmd.cli_ctx, cluster_subscription)
    resources = get_resources_client(cmd.cli_ctx, cluster_subscription)

    if resource_groups.check_existence(default_resource_group_name):
        try:
            resources.get_by_id(azure_monitor_workspace_resource_id, MAC_API)
            # If MAC already exists then return from here
            return azure_monitor_workspace_resource_id
        except HttpResponseError as ex:
            if ex.status_code != 404:
                raise ex
    else:
        resource_groups.create_or_update(default_resource_group_name, {"location": get_default_mac_region(cmd, cluster_region)})
    association_body = json.dumps({"location": get_default_mac_region(cmd, cluster_region), "properties": {}})
    association_url = f"https://management.azure.com{azure_monitor_workspace_resource_id}?api-version={MAC_API}"
    try:
        headers = ['User-Agent=azuremonitormetrics.create_default_mac']
        send_raw_request(cmd.cli_ctx, "PUT", association_url,
                         body=association_body, headers=headers)
        return azure_monitor_workspace_resource_id
    except CLIError as e:
        raise e


def get_azure_monitor_workspace_resource_id(cmd, cluster_subscription, cluster_region, raw_parameters):
    azure_monitor_workspace_resource_id = raw_parameters.get("azure_monitor_workspace_resource_id")
    if azure_monitor_workspace_resource_id is None or azure_monitor_workspace_resource_id == "":
        azure_monitor_workspace_resource_id = create_default_mac(cmd, cluster_subscription, cluster_region)
    else:
        azure_monitor_workspace_resource_id = sanitize_resource_id(azure_monitor_workspace_resource_id)
    return azure_monitor_workspace_resource_id.lower()


def get_default_dce_name(cmd, mac_region, cluster_name):
    region = get_default_region(cmd)
    if mac_region in MapToClosestMACRegion:
        region = MapToClosestMACRegion[mac_region]
    default_dce_name = "MSProm-" + region + "-" + cluster_name
    return sanitize_name(default_dce_name, DC_TYPE.DCE, 44)


def get_default_dcr_name(cmd, mac_region, cluster_name):
    region = get_default_region(cmd)
    if mac_region in MapToClosestMACRegion:
        region = MapToClosestMACRegion[mac_region]
    default_dcr_name = "MSProm-" + region + "-" + cluster_name
    return sanitize_name(default_dcr_name, DC_TYPE.DCR, 64)


def get_default_dcra_name(cmd, cluster_region, cluster_name):
    region = get_default_region(cmd)
    if cluster_region in MapToClosestMACRegion:
        region = MapToClosestMACRegion[cluster_region]
    default_dcra_name = "ContainerInsightsMetricsExtension-" + region + "-" + cluster_name
    return sanitize_name(default_dcra_name, DC_TYPE.DCRA, 64)


def get_mac_region_and_check_support(cmd, azure_monitor_workspace_resource_id, cluster_region):
    from azure.cli.core.util import send_raw_request
    from azure.core.exceptions import HttpResponseError
    # region of MAC can be different from region of RG so find the location of the azure_monitor_workspace_resource_id
    mac_subscription_id = azure_monitor_workspace_resource_id.split("/")[2]
    resources = get_resources_client(cmd.cli_ctx, mac_subscription_id)
    try:
        resource = resources.get_by_id(
            azure_monitor_workspace_resource_id, MAC_API)
        mac_location = resource.location
    except HttpResponseError as ex:
        raise ex
    # first get the association between region display names and region IDs (because for some reason
    # the "which RPs are available in which regions" check returns region display names)
    region_names_to_id = {}
    # retry the request up to two times
    for _ in range(3):
        try:
            headers = ['User-Agent=azuremonitormetrics.get_mac_region_and_check_support.mac_subscription_location_support_check']
            location_list_url = f"https://management.azure.com/subscriptions/{mac_subscription_id}/locations?api-version=2019-11-01"
            r = send_raw_request(cmd.cli_ctx, "GET", location_list_url, headers=headers)

            # this is required to fool the static analyzer. The else statement will only run if an exception
            # is thrown, but flake8 will complain that e is undefined if we don"t also define it here.
            error = None
            break
        except CLIError as e:
            error = e
    else:
        # This will run if the above for loop was not broken out of. This means all three requests failed
        raise error
    json_response = json.loads(r.text)
    for region_data in json_response["value"]:
        region_names_to_id[region_data["displayName"]
                           ] = region_data["name"]
    # check if region supports DCR and DCRA
    for _ in range(3):
        try:
            feature_check_url = f"https://management.azure.com/subscriptions/{mac_subscription_id}/providers/Microsoft.Insights?api-version=2020-10-01"
            headers = ['User-Agent=azuremonitormetrics.get_mac_region_and_check_support.mac_subscription_dcr_dcra_regions_support_check']
            r = send_raw_request(cmd.cli_ctx, "GET", feature_check_url, headers=headers)
            error = None
            break
        except CLIError as e:
            error = e
    else:
        raise error
    json_response = json.loads(r.text)
    for resource in json_response["resourceTypes"]:
        region_ids = map(lambda x: region_names_to_id[x],
                         resource["locations"])  # map is lazy, so doing this for every region isn"t slow
        if resource["resourceType"].lower() == "datacollectionrules" and mac_location not in region_ids:
            raise ClientRequestError(
                f"Data Collection Rules are not supported for MAC region {mac_location}")
        elif resource[
                "resourceType"].lower() == "datacollectionruleassociations" and cluster_region not in region_ids:
            raise ClientRequestError(
                f"Data Collection Rule Associations are not supported for cluster region {cluster_region}")
    return mac_location


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


# pylint: disable=too-many-locals,too-many-branches,too-many-statements,line-too-long
def create_dcr(cmd, mac_region, azure_monitor_workspace_resource_id, cluster_subscription, cluster_resource_group_name, cluster_name, dce_resource_id):
    from azure.cli.core.util import send_raw_request
    dcr_name = get_default_dcr_name(cmd, mac_region, cluster_name)
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
    dcr_url = f"https://management.azure.com{dcr_resource_id}?api-version={DC_API}"
    try:
        headers = ['User-Agent=azuremonitormetrics.create_dcr']
        send_raw_request(cmd.cli_ctx, "PUT",
                         dcr_url, body=dcr_creation_body, headers=headers)
        error = None
        return dcr_resource_id
    except CLIError as error:
        raise error


def create_dcra(cmd, cluster_region, cluster_subscription, cluster_resource_group_name, cluster_name, dcr_resource_id):
    from azure.cli.core.util import send_raw_request
    cluster_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.ContainerService/managedClusters/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        cluster_name
    )
    dcra_name = get_default_dcra_name(cmd, cluster_region, cluster_name)
    dcra_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Insights/dataCollectionRuleAssociations/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        dcra_name
    )
    # only create or delete the association between the DCR and cluster
    association_body = json.dumps({"location": cluster_region,
                                   "properties": {
                                       "dataCollectionRuleId": dcr_resource_id,
                                       "description": "Promtheus data collection association between DCR, DCE and target AKS resource"
                                   }})
    association_url = f"https://management.azure.com{cluster_resource_id}/providers/Microsoft.Insights/dataCollectionRuleAssociations/{dcra_name}?api-version={DC_API}"
    try:
        headers = ['User-Agent=azuremonitormetrics.create_dcra']
        send_raw_request(cmd.cli_ctx, "PUT", association_url,
                         body=association_body, headers=headers)
        error = None
        return dcra_resource_id
    except CLIError as error:
        raise error


def link_grafana_instance(cmd, raw_parameters, azure_monitor_workspace_resource_id):
    from azure.cli.core.util import send_raw_request
    # GET grafana principal ID
    try:
        grafana_resource_id = raw_parameters.get("grafana_resource_id")
        if grafana_resource_id is None or grafana_resource_id == "":
            return GrafanaLink.NOPARAMPROVIDED
        grafana_resource_id = sanitize_resource_id(grafana_resource_id)
        grafanaURI = "https://management.azure.com{0}?api-version={1}".format(
            grafana_resource_id,
            GRAFANA_API
        )
        headers = ['User-Agent=azuremonitormetrics.link_grafana_instance']
        grafanaArmResponse = send_raw_request(cmd.cli_ctx, "GET", grafanaURI, body={}, headers=headers)
        servicePrincipalId = grafanaArmResponse.json()["identity"]["principalId"]
    except CLIError as e:
        raise CLIError(e)
    # Add Role Assignment
    try:
        MonitoringDataReader = "b0d8363b-8ddd-447d-831f-62ca05bff136"
        roleDefinitionURI = "https://management.azure.com{0}/providers/Microsoft.Authorization/roleAssignments/{1}?api-version={2}".format(
            azure_monitor_workspace_resource_id,
            uuid.uuid4(),
            GRAFANA_ROLE_ASSIGNMENT_API
        )
        roleDefinitionId = "{0}/providers/Microsoft.Authorization/roleDefinitions/{1}".format(
            azure_monitor_workspace_resource_id,
            MonitoringDataReader
        )
        association_body = json.dumps({"properties": {"roleDefinitionId": roleDefinitionId, "principalId": servicePrincipalId}})
        headers = ['User-Agent=azuremonitormetrics.add_role_assignment']
        send_raw_request(cmd.cli_ctx, "PUT", roleDefinitionURI, body=association_body, headers=headers)
    except CLIError as e:
        if e.response.status_code != 409:
            erroString = "Role Assingment failed. Please manually assign the `Monitoring Data Reader` role to the Azure Monitor Workspace ({0}) for the Azure Managed Grafana System Assigned Managed Identity ({1})".format(
                azure_monitor_workspace_resource_id,
                servicePrincipalId
            )
            print(erroString)
    # Setting up AMW Integration
    targetGrafanaArmPayload = grafanaArmResponse.json()
    if targetGrafanaArmPayload["properties"] is None:
        raise CLIError("Invalid grafana payload to add AMW integration")
    if "grafanaIntegrations" not in json.dumps(targetGrafanaArmPayload):
        targetGrafanaArmPayload["properties"]["grafanaIntegrations"] = {}
    if "azureMonitorWorkspaceIntegrations" not in json.dumps(targetGrafanaArmPayload):
        targetGrafanaArmPayload["properties"]["grafanaIntegrations"]["azureMonitorWorkspaceIntegrations"] = []
    amwIntegrations = targetGrafanaArmPayload["properties"]["grafanaIntegrations"]["azureMonitorWorkspaceIntegrations"]
    if amwIntegrations != [] and azure_monitor_workspace_resource_id in json.dumps(amwIntegrations).lower():
        return GrafanaLink.ALREADYPRESENT
    try:
        grafanaURI = "https://management.azure.com{0}?api-version={1}".format(
            grafana_resource_id,
            GRAFANA_API
        )
        targetGrafanaArmPayload["properties"]["grafanaIntegrations"]["azureMonitorWorkspaceIntegrations"].append({"azureMonitorWorkspaceResourceId": azure_monitor_workspace_resource_id})
        targetGrafanaArmPayload = json.dumps(targetGrafanaArmPayload)
        headers = ['User-Agent=azuremonitormetrics.setup_amw_grafana_integration', 'Content-Type=application/json']
        send_raw_request(cmd.cli_ctx, "PUT", grafanaURI, body=targetGrafanaArmPayload, headers=headers)
    except CLIError as e:
        raise CLIError(e)
    return GrafanaLink.SUCCESS


def put_rules(cmd, default_rule_group_id, default_rule_group_name, mac_region, azure_monitor_workspace_resource_id, cluster_name, default_rules_template, url, i):
    from azure.cli.core.util import send_raw_request
    body = json.dumps({
        "id": default_rule_group_id,
        "name": default_rule_group_name,
        "type": "Microsoft.AlertsManagement/prometheusRuleGroups",
        "location": mac_region,
        "properties": {
            "scopes": [
                azure_monitor_workspace_resource_id
            ],
            "enabled": True,
            "clusterName": cluster_name,
            "interval": "PT1M",
            "rules": default_rules_template[i]["properties"]["rulesArmTemplate"]["resources"][0]["properties"]["rules"]
        }
    })
    for _ in range(3):
        try:
            headers = ['User-Agent=azuremonitormetrics.put_rules.' + default_rule_group_name]
            send_raw_request(cmd.cli_ctx, "PUT", url,
                             body=body, headers=headers)
            error = None
            break
        except CLIError as e:
            error = e
    else:
        raise error


def delete_rule(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, default_rule_group_name):
    from azure.cli.core.util import send_raw_request
    default_rule_group_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.AlertsManagement/prometheusRuleGroups/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        default_rule_group_name
    )
    headers = ['User-Agent=azuremonitormetrics.delete_rule.' + default_rule_group_name]
    url = "https://management.azure.com{0}?api-version={1}".format(
        default_rule_group_id,
        RULES_API
    )
    send_raw_request(cmd.cli_ctx, "DELETE", url, headers=headers)


def get_recording_rules_template(cmd, azure_monitor_workspace_resource_id):
    from azure.cli.core.util import send_raw_request
    headers = ['User-Agent=azuremonitormetrics.get_recording_rules_template']
    url = f"https://management.azure.com{azure_monitor_workspace_resource_id}/providers/microsoft.alertsManagement/alertRuleRecommendations?api-version={ALERTS_API}"
    r = send_raw_request(cmd.cli_ctx, "GET", url, headers=headers)
    data = json.loads(r.text)
    return data['value']


def create_rules(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, azure_monitor_workspace_resource_id, mac_region, raw_parameters):
    # with urllib.request.urlopen("https://defaultrulessc.blob.core.windows.net/defaultrules/ManagedPrometheusDefaultRecordingRules.json") as url:
    #     default_rules_template = json.loads(url.read().decode())
    default_rules_template = get_recording_rules_template(cmd, azure_monitor_workspace_resource_id)
    default_rule_group_name = "NodeRecordingRulesRuleGroup-{0}".format(cluster_name)
    default_rule_group_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.AlertsManagement/prometheusRuleGroups/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        default_rule_group_name
    )
    url = "https://management.azure.com{0}?api-version={1}".format(
        default_rule_group_id,
        RULES_API
    )
    put_rules(cmd, default_rule_group_id, default_rule_group_name, mac_region, azure_monitor_workspace_resource_id, cluster_name, default_rules_template, url, 0)

    default_rule_group_name = "KubernetesRecordingRulesRuleGroup-{0}".format(cluster_name)
    default_rule_group_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.AlertsManagement/prometheusRuleGroups/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        default_rule_group_name
    )
    url = "https://management.azure.com{0}?api-version={1}".format(
        default_rule_group_id,
        RULES_API
    )
    put_rules(cmd, default_rule_group_id, default_rule_group_name, mac_region, azure_monitor_workspace_resource_id, cluster_name, default_rules_template, url, 1)

    enable_windows_recording_rules = raw_parameters.get("enable_windows_recording_rules")

    if enable_windows_recording_rules is True:
        default_rule_group_name = "NodeRecordingRulesRuleGroup-Win-{0}".format(cluster_name)
        default_rule_group_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.AlertsManagement/prometheusRuleGroups/{2}".format(
            cluster_subscription,
            cluster_resource_group_name,
            default_rule_group_name
        )
        url = "https://management.azure.com{0}?api-version={1}".format(
            default_rule_group_id,
            RULES_API
        )
        put_rules(cmd, default_rule_group_id, default_rule_group_name, mac_region, azure_monitor_workspace_resource_id, cluster_name, default_rules_template, url, 2)

        default_rule_group_name = "NodeAndKubernetesRecordingRulesRuleGroup-Win-{0}".format(cluster_name)
        default_rule_group_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.AlertsManagement/prometheusRuleGroups/{2}".format(
            cluster_subscription,
            cluster_resource_group_name,
            default_rule_group_name
        )
        url = "https://management.azure.com{0}?api-version={1}".format(
            default_rule_group_id,
            RULES_API
        )
        put_rules(cmd, default_rule_group_id, default_rule_group_name, mac_region, azure_monitor_workspace_resource_id, cluster_name, default_rules_template, url, 3)


def get_dce_from_dcr(cmd, dcrId):
    from azure.cli.core.util import send_raw_request
    association_url = f"https://management.azure.com{dcrId}?api-version={DC_API}"
    headers = ['User-Agent=azuremonitormetrics.get_dce_from_dcr']
    r = send_raw_request(cmd.cli_ctx, "GET", association_url, headers=headers)
    data = json.loads(r.text)
    return data['properties']['dataCollectionEndpointId']


def get_dc_objects_list(cmd, cluster_region, cluster_subscription, cluster_resource_group_name, cluster_name):
    try:
        from azure.cli.core.util import send_raw_request
        cluster_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.ContainerService/managedClusters/{2}".format(
            cluster_subscription,
            cluster_resource_group_name,
            cluster_name
        )
        association_url = f"https://management.azure.com{cluster_resource_id}/providers/Microsoft.Insights/dataCollectionRuleAssociations?api-version={DC_API}"
        headers = ['User-Agent=azuremonitormetrics.get_dcra']
        r = send_raw_request(cmd.cli_ctx, "GET", association_url, headers=headers)
        data = json.loads(r.text)
        dc_object_array = []
        for item in data['value']:
            dce_id = get_dce_from_dcr(cmd, item['properties']['dataCollectionRuleId'])
            dc_object_array.append({'name': item['name'], 'dataCollectionRuleId': item['properties']['dataCollectionRuleId'], 'dceId': dce_id})
        return dc_object_array
    except CLIError as e:
        error = e
        raise CLIError(error)


def delete_dc_objects_if_prometheus_enabled(cmd, dc_objects_list, cluster_subscription, cluster_resource_group_name, cluster_name):
    from azure.cli.core.util import send_raw_request
    cluster_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.ContainerService/managedClusters/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        cluster_name
    )
    for item in dc_objects_list:
        association_url = f"https://management.azure.com{item['dataCollectionRuleId']}?api-version={DC_API}"
        try:
            headers = ['User-Agent=azuremonitormetrics.get_dcr_if_prometheus_enabled']
            r = send_raw_request(cmd.cli_ctx, "GET", association_url, headers=headers)
            data = json.loads(r.text)
            if 'microsoft-prometheusmetrics' in [stream.lower() for stream in data['properties']['dataFlows'][0]['streams']]:
                # delete DCRA
                url = f"https://management.azure.com{cluster_resource_id}/providers/Microsoft.Insights/dataCollectionRuleAssociations/{item['name']}?api-version={DC_API}"
                headers = ['User-Agent=azuremonitormetrics.delete_dcra']
                send_raw_request(cmd.cli_ctx, "DELETE", url, headers=headers)
                # delete DCR
                url = f"https://management.azure.com{item['dataCollectionRuleId']}?api-version={DC_API}"
                headers = ['User-Agent=azuremonitormetrics.delete_dcr']
                send_raw_request(cmd.cli_ctx, "DELETE", url, headers=headers)
                # delete DCE
                url = f"https://management.azure.com{item['dceId']}?api-version={DC_API}"
                headers = ['User-Agent=azuremonitormetrics.delete_dce']
                send_raw_request(cmd.cli_ctx, "DELETE", url, headers=headers)
        except CLIError as e:
            error = e
            raise CLIError(error)


def delete_rules(cmd, cluster_subscription, cluster_resource_group_name, cluster_name):
    delete_rule(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, "NodeRecordingRulesRuleGroup-{0}".format(cluster_name))
    delete_rule(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, "KubernetesRecordingRulesRuleGroup-{0}".format(cluster_name))
    delete_rule(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, "NodeRecordingRulesRuleGroup-Win-{0}".format(cluster_name))
    delete_rule(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, "NodeAndKubernetesRecordingRulesRuleGroup-Win-{0}".format(cluster_name))


def link_azure_monitor_profile_artifacts(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, cluster_region, raw_parameters, create_flow):
    # MAC creation if required
    azure_monitor_workspace_resource_id = get_azure_monitor_workspace_resource_id(cmd, cluster_subscription, cluster_region, raw_parameters)
    # Get MAC region (required for DCE, DCR creation) and check support for DCE,DCR creation
    mac_region = get_mac_region_and_check_support(cmd, azure_monitor_workspace_resource_id, cluster_region)
    # DCE creation
    dce_resource_id = create_dce(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, mac_region)
    # DCR creation
    dcr_resource_id = create_dcr(cmd, mac_region, azure_monitor_workspace_resource_id, cluster_subscription, cluster_resource_group_name, cluster_name, dce_resource_id)
    # DCRA creation
    create_dcra(cmd, cluster_region, cluster_subscription, cluster_resource_group_name, cluster_name, dcr_resource_id)
    # Link grafana
    link_grafana_instance(cmd, raw_parameters, azure_monitor_workspace_resource_id)
    # create recording rules and alerts
    create_rules(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, azure_monitor_workspace_resource_id, mac_region, raw_parameters)
    # if aks cluster create flow -> do a PUT on the AKS cluster to enable the addon
    if create_flow:
        addon_put(cmd, cluster_subscription, cluster_resource_group_name, cluster_name)


def unlink_azure_monitor_profile_artifacts(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, cluster_region):
    ################ CHECK IF DCR IS LINKED WITH ANOTHER DCRA ##############################################
    # Remove DC* if prometheus is enabled
    dc_objects_list = get_dc_objects_list(cmd, cluster_region, cluster_subscription, cluster_resource_group_name, cluster_name)
    delete_dc_objects_if_prometheus_enabled(cmd, dc_objects_list, cluster_subscription, cluster_resource_group_name, cluster_name)
    # Delete rules (Conflict({"error":{"code":"InvalidResourceLocation","message":"The resource 'NodeRecordingRulesRuleGroup-<clustername>' already exists in location 'eastus2' in resource group '<clustername>'. A resource with the same name cannot be created in location 'eastus'. Please select a new resource name."}})
    delete_rules(cmd,  cluster_subscription, cluster_resource_group_name, cluster_name)


def post_request(cmd, subscription_id, rp_name, headers):
    from azure.cli.core.util import send_raw_request
    customUrl = "https://management.azure.com/subscriptions/{0}/providers/{1}/register?api-version={2}".format(
        subscription_id,
        rp_name,
        RP_API
    )
    try:
        send_raw_request(cmd.cli_ctx, "POST", customUrl, headers=headers)
    except CLIError as e:
        raise CLIError(e)


def rp_registrations(cmd, subscription_id):
    from azure.cli.core.util import send_raw_request
    # Get list of RP's for RP's subscription
    try:
        headers = ['User-Agent=azuremonitormetrics.get_mac_sub_list']
        customUrl = "https://management.azure.com/subscriptions/{0}/providers?api-version={1}&$select=namespace,registrationstate".format(
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


# pylint: disable=too-many-locals,too-many-branches,too-many-statements,line-too-long
def ensure_azure_monitor_profile_prerequisites(
    cmd,
    client,
    cluster_subscription,
    cluster_resource_group_name,
    cluster_name,
    cluster_region,
    raw_parameters,
    remove_azuremonitormetrics,
    create_flow=False
):
    cloud_name = cmd.cli_ctx.cloud.name
    if cloud_name.lower() == 'azurechinacloud':
        raise CLIError("Azure China Cloud is not supported for the Azure Monitor Metrics addon")

    if cloud_name.lower() == "azureusgovernment":
        grafana_resource_id = raw_parameters.get("grafana_resource_id")
        if grafana_resource_id is not None or grafana_resource_id != "":
            raise InvalidArgumentValueError("Azure US Government cloud does not support Azure Managed Grarfana yet. Please follow this documenation for enabling it via the public cloud : aka.ms/ama-grafana-link-ff")

    if (remove_azuremonitormetrics):
        unlink_azure_monitor_profile_artifacts(
            cmd,
            cluster_subscription,
            cluster_resource_group_name,
            cluster_name,
            cluster_region
        )
    else:
        # Check if already onboarded
        if create_flow == False:
            check_azuremonitormetrics_profile(cmd, cluster_subscription, cluster_resource_group_name, cluster_name)
        # Do RP registrations if required
        rp_registrations(cmd, cluster_subscription)
        link_azure_monitor_profile_artifacts(
            cmd,
            cluster_subscription,
            cluster_resource_group_name,
            cluster_name,
            cluster_region,
            raw_parameters,
            create_flow
        )
    return
