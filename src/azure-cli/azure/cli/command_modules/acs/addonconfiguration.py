# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json

from azure.cli.command_modules.acs._client_factory import get_resource_groups_client, get_resources_client
from azure.cli.command_modules.acs._consts import (
    CONST_INGRESS_APPGW_ADDON_NAME,
    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID,
    CONST_INGRESS_APPGW_SUBNET_CIDR,
    CONST_INGRESS_APPGW_SUBNET_ID,
    CONST_MONITORING_ADDON_NAME,
    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID,
    CONST_VIRTUAL_NODE_ADDON_NAME,
)
from azure.cli.command_modules.acs._resourcegroup import get_rg_location
from azure.cli.command_modules.acs._roleassignments import add_role_assignment
from azure.cli.core.azclierror import AzCLIError, ClientRequestError, CLIError
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import send_raw_request
from azure.core.exceptions import HttpResponseError
from knack.log import get_logger
from msrestazure.tools import parse_resource_id, resource_id

logger = get_logger(__name__)
# mapping for azure public cloud
# log analytics workspaces cannot be created in WCUS region due to capacity limits
# so mapped to EUS per discussion with log analytics team
AzureCloudLocationToOmsRegionCodeMap = {
    "australiasoutheast": "ASE",
    "australiaeast": "EAU",
    "australiacentral": "CAU",
    "australiacentral2": "CBR2",
    "brazilsouth": "CQ",
    "brazilsoutheast": "BRSE",
    "canadacentral": "CCA",
    "canadaeast": "YQ",
    "centralindia": "CID",
    "centralus": "CUS",
    "eastasia": "EA",
    "eastus": "EUS",
    "eastus2": "EUS2",
    "eastus2euap": "EAP",
    "francecentral": "PAR",
    "francesouth": "MRS",
    "germanywestcentral": "DEWC",
    "japaneast": "EJP",
    "japanwest": "OS",
    "jioindiacentral": "JINC",
    "jioindiawest": "JINW",
    "koreacentral": "SE",
    "koreasouth": "PS",
    "northcentralus": "NCUS",
    "northeurope": "NEU",
    "norwayeast": "NOE",
    "norwaywest": "NOW",
    "qatarcentral": "QAC",
    "southafricanorth": "JNB",
    "southcentralus": "SCUS",
    "southindia": "MA",
    "southeastasia": "SEA",
    "swedencentral": "SEC",
    "switzerlandnorth": "CHN",
    "switzerlandwest": "CHW",
    "uaecentral": "AUH",
    "uaenorth": "DXB",
    "uksouth": "SUK",
    "ukwest": "WUK",
    "usgovvirginia": "USGV",
    "westcentralus": "WCUS",
    "westeurope": "WEU",
    "westus": "WUS",
    "westus2": "WUS2",
    "westus3": "USW3",
}


AzureCloudRegionToOmsRegionMap = {
    "australiacentral": "australiacentral",
    "australiacentral2": "australiacentral2",
    "australiaeast": "australiaeast",
    "australiasoutheast": "australiasoutheast",
    "brazilsouth": "brazilsouth",
    "brazilsoutheast": "brazilsoutheast",
    "canadacentral": "canadacentral",
    "canadaeast": "canadaeast",
    "centralus": "centralus",
    "centralindia": "centralindia",
    "eastasia": "eastasia",
    "eastus": "eastus",
    "eastus2": "eastus2",
    "francecentral": "francecentral",
    "francesouth": "francesouth",
    "germanywestcentral": "germanywestcentral",
    "germanynorth": "germanywestcentral",
    "japaneast": "japaneast",
    "japanwest": "japanwest",
    "jioindiacentral": "jioindiacentral",
    "jioindiawest": "jioindiawest",
    "koreacentral": "koreacentral",
    "koreasouth": "koreasouth",
    "northcentralus": "northcentralus",
    "northeurope": "northeurope",
    "norwayeast": "norwayeast",
    "norwaywest": "norwaywest",
    "qatarcentral": "qatarcentral",
    "southafricanorth": "southafricanorth",
    "southafricawest": "southafricanorth",
    "southcentralus": "southcentralus",
    "southeastasia": "southeastasia",
    "southindia": "southindia",
    "swedencentral": "swedencentral",
    "switzerlandnorth": "switzerlandnorth",
    "switzerlandwest": "switzerlandwest",
    "uaecentral": "uaecentral",
    "uaenorth": "uaenorth",
    "uksouth": "uksouth",
    "ukwest": "ukwest",
    "westcentralus": "westcentralus",
    "westeurope": "westeurope",
    "westindia": "centralindia",
    "westus": "westus",
    "westus2": "westus2",
    "westus3": "westus3",
    "eastus2euap": "eastus2euap",
    "centraluseuap": "eastus2euap",
}


# mapping for azure china cloud
# log analytics only support China East2 region
AzureChinaLocationToOmsRegionCodeMap = {
    "chinaeast": "EAST2",
    "chinaeast2": "EAST2",
    "chinanorth": "EAST2",
    "chinanorth2": "EAST2",
}


AzureChinaRegionToOmsRegionMap = {
    "chinaeast": "chinaeast2",
    "chinaeast2": "chinaeast2",
    "chinanorth": "chinaeast2",
    "chinanorth2": "chinaeast2",
}


# mapping for azure us governmner cloud
AzureFairfaxLocationToOmsRegionCodeMap = {
    "usgovvirginia": "USGV",
    "usgovarizona": "PHX",
}


AzureFairfaxRegionToOmsRegionMap = {
    "usgovvirginia": "usgovvirginia",
    "usgovtexas": "usgovvirginia",
    "usgovarizona": "usgovarizona",
}


# pylint: disable=too-many-locals
def ensure_default_log_analytics_workspace_for_monitoring(
    cmd, subscription_id, resource_group_name
):
    rg_location = get_rg_location(cmd.cli_ctx, resource_group_name)
    cloud_name = cmd.cli_ctx.cloud.name

    if cloud_name.lower() == "azurecloud":
        workspace_region = AzureCloudRegionToOmsRegionMap.get(
            rg_location, "eastus"
        )
        workspace_region_code = AzureCloudLocationToOmsRegionCodeMap.get(
            workspace_region, "EUS"
        )
    elif cloud_name.lower() == "azurechinacloud":
        workspace_region = AzureChinaRegionToOmsRegionMap.get(
            rg_location, "chinaeast2"
        )
        workspace_region_code = AzureChinaLocationToOmsRegionCodeMap.get(
            workspace_region, "EAST2"
        )
    elif cloud_name.lower() == "azureusgovernment":
        workspace_region = AzureFairfaxRegionToOmsRegionMap.get(
            rg_location, "usgovvirginia"
        )
        workspace_region_code = AzureFairfaxLocationToOmsRegionCodeMap.get(
            workspace_region, "USGV"
        )
    else:
        logger.error(
            "AKS Monitoring addon not supported in cloud : %s", cloud_name
        )

    default_workspace_resource_group = (
        "DefaultResourceGroup-" + workspace_region_code
    )
    default_workspace_name = "DefaultWorkspace-{0}-{1}".format(
        subscription_id, workspace_region_code
    )

    default_workspace_resource_id = (
        "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.OperationalInsights/workspaces/{2}".format(
            subscription_id,
            default_workspace_resource_group,
            default_workspace_name,
        )
    )
    resource_groups = get_resource_groups_client(cmd.cli_ctx, subscription_id)
    resources = get_resources_client(cmd.cli_ctx, subscription_id)

    # check if default RG exists
    if resource_groups.check_existence(default_workspace_resource_group):
        try:
            resource = resources.get_by_id(
                default_workspace_resource_id, "2015-11-01-preview"
            )
            return resource.id
        except HttpResponseError as ex:
            if ex.status_code != 404:
                raise ex
    else:
        resource_groups.create_or_update(
            default_workspace_resource_group, {"location": workspace_region}
        )

    GenericResource = cmd.get_models(
        "GenericResource", resource_type=ResourceType.MGMT_RESOURCE_RESOURCES
    )
    generic_resource = GenericResource(
        location=workspace_region, properties={"sku": {"name": "standalone"}}
    )

    async_poller = resources.begin_create_or_update_by_id(
        default_workspace_resource_id, "2015-11-01-preview", generic_resource
    )

    ws_resource_id = ""
    while True:
        result = async_poller.result(15)
        if async_poller.done():
            ws_resource_id = result.id
            break

    return ws_resource_id


def sanitize_loganalytics_ws_resource_id(workspace_resource_id):
    workspace_resource_id = workspace_resource_id.strip()
    if not workspace_resource_id.startswith("/"):
        workspace_resource_id = "/" + workspace_resource_id
    if workspace_resource_id.endswith("/"):
        workspace_resource_id = workspace_resource_id.rstrip("/")
    return workspace_resource_id


def get_existing_container_insights_extension_dcr_tags(cmd, dcr_url):
    tags = {}
    _MAX_RETRY_TIMES = 3
    for retry_count in range(0, _MAX_RETRY_TIMES):
        try:
            resp = send_raw_request(
                cmd.cli_ctx, "GET", dcr_url
            )
            json_response = json.loads(resp.text)
            if ("tags" in json_response) and (json_response["tags"] is not None):
                tags = json_response["tags"]
            break
        except CLIError as e:
            if "ResourceNotFound" in str(e):
                break
            if retry_count >= (_MAX_RETRY_TIMES - 1):
                raise e
    return tags


def getRegionCodeForAzureRegion(cmd, cluster_region):
    region_code = "EUS"
    cloud_name = cmd.cli_ctx.cloud.name
    if cloud_name.lower() == "azurecloud":
        region_code = AzureCloudLocationToOmsRegionCodeMap.get(
            cluster_region, "EUS"
        )
    elif cloud_name.lower() == "azurechinacloud":
        region_code = AzureChinaLocationToOmsRegionCodeMap.get(
            cluster_region, "EAST2"
        )
    elif cloud_name.lower() == "azureusgovernment":
        region_code = AzureFairfaxLocationToOmsRegionCodeMap.get(
            cluster_region, "USGV"
        )
    else:
        logger.error(
            "AKS Monitoring addon not supported in cloud : %s", cloud_name
        )
    return region_code


def sanitize_dcr_name(name):
    name = name[0:43]
    lastIndexAlphaNumeric = len(name) - 1
    while ((name[lastIndexAlphaNumeric].isalnum() is False) and lastIndexAlphaNumeric > -1):
        lastIndexAlphaNumeric = lastIndexAlphaNumeric - 1
    if lastIndexAlphaNumeric < 0:
        return ""
    return name[0:lastIndexAlphaNumeric + 1]


# pylint: disable=too-many-locals,too-many-branches,too-many-statements,line-too-long
def ensure_container_insights_for_monitoring(
    cmd,
    addon,
    cluster_subscription,
    cluster_resource_group_name,
    cluster_name,
    cluster_region,
    remove_monitoring=False,
    aad_route=False,
    create_dcr=False,
    create_dcra=False,
    enable_syslog=False,
):
    """
    Either adds the ContainerInsights solution to a LA Workspace OR sets up a DCR (Data Collection Rule) and DCRA
    (Data Collection Rule Association). Both let the monitoring addon send data to a Log Analytics Workspace.

    Set aad_route == True to set up the DCR data route. Otherwise the solution route will be used. Create_dcr and
    create_dcra have no effect if aad_route == False. If syslog data is to be collected set aad_route == True and
    enable_syslog == True

    Set remove_monitoring to True and create_dcra to True to remove the DCRA from a cluster. The association makes
    it very hard to delete either the DCR or cluster. (It is not obvious how to even navigate to the association from
    the portal, and it prevents the cluster and DCR from being deleted individually).
    """
    if not addon.enabled:
        return None

    # workaround for this addon key which has been seen lowercased in the wild
    for key in list(addon.config):
        if (
            key.lower() == CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID.lower() and
            key != CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID
        ):
            addon.config[
                CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID
            ] = addon.config.pop(key)

    workspace_resource_id = addon.config[
        CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID
    ]
    workspace_resource_id = sanitize_loganalytics_ws_resource_id(
        workspace_resource_id
    )

    # extract subscription ID and resource group from workspace_resource_id URL
    try:
        subscription_id = workspace_resource_id.split("/")[2]
    except IndexError:
        raise AzCLIError(
            "Could not locate resource group in workspace-resource-id URL."
        )

    # region of workspace can be different from region of RG so find the location of the workspace_resource_id
    if not remove_monitoring:
        resources = get_resources_client(cmd.cli_ctx, subscription_id)
        try:
            resource = resources.get_by_id(
                workspace_resource_id, "2015-11-01-preview"
            )
            location = resource.location
            # location can have spaces for example 'East US' hence remove the spaces
            location = location.replace(" ", "").lower()
        except HttpResponseError as ex:
            raise ex

    if aad_route:
        cluster_resource_id = (
            f"/subscriptions/{cluster_subscription}/resourceGroups/{cluster_resource_group_name}/"
            f"providers/Microsoft.ContainerService/managedClusters/{cluster_name}"
        )
        region_code = getRegionCodeForAzureRegion(cmd, cluster_region)
        dataCollectionRuleName = sanitize_dcr_name(f"MSCI-{region_code}-{cluster_name}")
        dcr_resource_id = (
            f"/subscriptions/{cluster_subscription}/resourceGroups/{cluster_resource_group_name}/"
            f"providers/Microsoft.Insights/dataCollectionRules/{dataCollectionRuleName}"
        )
        if create_dcr:
            # first get the association between region display names and region IDs (because for some reason
            # the "which RPs are available in which regions" check returns region display names)
            region_names_to_id = {}
            # retry the request up to two times
            for _ in range(3):
                try:
                    location_list_url = cmd.cli_ctx.cloud.endpoints.resource_manager + \
                        f"/subscriptions/{cluster_subscription}/locations?api-version=2019-11-01"
                    r = send_raw_request(cmd.cli_ctx, "GET", location_list_url)
                    # this is required to fool the static analyzer. The else statement will only run if an exception
                    # is thrown, but flake8 will complain that e is undefined if we don't also define it here.
                    error = None
                    break
                except AzCLIError as e:
                    error = e
            else:
                # This will run if the above for loop was not broken out of. This means all three requests failed
                raise error
            json_response = json.loads(r.text)
            for region_data in json_response["value"]:
                region_names_to_id[region_data["displayName"]] = region_data[
                    "name"
                ]

            # check if region supports DCRs and DCR-A
            for _ in range(3):
                try:
                    feature_check_url = cmd.cli_ctx.cloud.endpoints.resource_manager + \
                        f"/subscriptions/{cluster_subscription}/providers/Microsoft.Insights?api-version=2020-10-01"
                    r = send_raw_request(cmd.cli_ctx, "GET", feature_check_url)
                    error = None
                    break
                except AzCLIError as e:
                    error = e
            else:
                raise error
            json_response = json.loads(r.text)
            for resource in json_response["resourceTypes"]:
                if resource["resourceType"].lower() == "datacollectionrules":
                    region_ids = map(
                        lambda x: region_names_to_id[x], resource["locations"])
                    if location not in region_ids:
                        raise ClientRequestError(
                            f"Data Collection Rules are not supported for LA workspace region {location}")
                if resource["resourceType"].lower() == "datacollectionruleassociations":
                    region_ids = map(
                        lambda x: region_names_to_id[x], resource["locations"])
                    if cluster_region not in region_ids:
                        raise ClientRequestError(
                            f"Data Collection Rule Associations are not supported for cluster region {cluster_region}")
            dcr_url = cmd.cli_ctx.cloud.endpoints.resource_manager + \
                f"{dcr_resource_id}?api-version=2021-04-01"
            # get existing tags on the container insights extension DCR if the customer added any
            existing_tags = get_existing_container_insights_extension_dcr_tags(
                cmd, dcr_url)
            # create the DCR
            dcr_creation_body_without_syslog = json.dumps(
                {
                    "location": location,
                    "tags": existing_tags,
                    "properties": {
                        "dataSources": {
                            "extensions": [
                                {
                                    "name": "ContainerInsightsExtension",
                                    "streams": [
                                        "Microsoft-ContainerInsights-Group-Default"
                                    ],
                                    "extensionName": "ContainerInsights",
                                }
                            ]
                        },
                        "dataFlows": [
                            {
                                "streams": [
                                    "Microsoft-ContainerInsights-Group-Default"
                                ],
                                "destinations": ["la-workspace"],
                            }
                        ],
                        "destinations": {
                            "logAnalytics": [
                                {
                                    "workspaceResourceId": workspace_resource_id,
                                    "name": "la-workspace",
                                }
                            ]
                        },
                    },
                }
            )

            dcr_creation_body_with_syslog = json.dumps(
                {
                    "location": location,
                    "tags": existing_tags,
                    "properties": {
                        "dataSources": {
                            "syslog": [
                                {
                                    "streams": [
                                        "Microsoft-Syslog"
                                    ],
                                    "facilityNames": [
                                        "auth",
                                        "authpriv",
                                        "cron",
                                        "daemon",
                                        "mark",
                                        "kern",
                                        "local0",
                                        "local1",
                                        "local2",
                                        "local3",
                                        "local4",
                                        "local5",
                                        "local6",
                                        "local7",
                                        "lpr",
                                        "mail",
                                        "news",
                                        "syslog",
                                        "user",
                                        "uucp"
                                    ],
                                    "logLevels": [
                                        "Debug",
                                        "Info",
                                        "Notice",
                                        "Warning",
                                        "Error",
                                        "Critical",
                                        "Alert",
                                        "Emergency"
                                    ],
                                    "name": "sysLogsDataSource"
                                }
                            ],
                            "extensions": [
                                {
                                    "name": "ContainerInsightsExtension",
                                    "streams": [
                                        "Microsoft-ContainerInsights-Group-Default"
                                    ],
                                    "extensionName": "ContainerInsights",
                                }
                            ]
                        },
                        "dataFlows": [
                            {
                                "streams": [
                                    "Microsoft-ContainerInsights-Group-Default",
                                    "Microsoft-Syslog"
                                ],
                                "destinations": ["la-workspace"],
                            }
                        ],
                        "destinations": {
                            "logAnalytics": [
                                {
                                    "workspaceResourceId": workspace_resource_id,
                                    "name": "la-workspace",
                                }
                            ]
                        },
                    },
                }
            )

            for _ in range(3):
                try:
                    if enable_syslog:
                        send_raw_request(
                            cmd.cli_ctx, "PUT", dcr_url, body=dcr_creation_body_with_syslog
                        )
                    else:
                        send_raw_request(
                            cmd.cli_ctx, "PUT", dcr_url, body=dcr_creation_body_without_syslog
                        )
                    error = None
                    break
                except AzCLIError as e:
                    error = e
            else:
                raise error

        if create_dcra:
            # only create or delete the association between the DCR and cluster
            association_body = json.dumps(
                {
                    "location": cluster_region,
                    "properties": {
                        "dataCollectionRuleId": dcr_resource_id,
                        "description": "routes monitoring data to a Log Analytics workspace",
                    },
                }
            )
            association_url = cmd.cli_ctx.cloud.endpoints.resource_manager + \
                f"{cluster_resource_id}/providers/Microsoft.Insights/dataCollectionRuleAssociations/ContainerInsightsExtension?api-version=2021-04-01"
            for _ in range(3):
                try:
                    send_raw_request(
                        cmd.cli_ctx,
                        "PUT" if not remove_monitoring else "DELETE",
                        association_url,
                        body=association_body,
                    )
                    error = None
                    break
                except AzCLIError as e:
                    error = e
            else:
                raise error


def add_monitoring_role_assignment(result, cluster_resource_id, cmd):
    service_principal_msi_id = None
    is_useAADAuth = False
    # Check if monitoring addon enabled with useAADAuth = True, if it does, ignore role assignment
    # Check if service principal exists, if it does, assign permissions to service principal
    # Else, provide permissions to MSI
    if (
        (hasattr(result, "addon_profiles")) and
        (CONST_MONITORING_ADDON_NAME in result.addon_profiles) and
        hasattr(result.addon_profiles[CONST_MONITORING_ADDON_NAME], "config") and
        hasattr(result.addon_profiles[CONST_MONITORING_ADDON_NAME].config, "useAADAuth") and
        result.addon_profiles[CONST_MONITORING_ADDON_NAME].config.useAADAuth
    ):
        is_useAADAuth = True
    elif (
        hasattr(result, "service_principal_profile") and
        hasattr(result.service_principal_profile, "client_id") and
        result.service_principal_profile.client_id.lower() != "msi"
    ):
        logger.info("valid service principal exists, using it")
        service_principal_msi_id = result.service_principal_profile.client_id
        is_service_principal = True
    elif (
        (hasattr(result, "addon_profiles")) and
        (CONST_MONITORING_ADDON_NAME in result.addon_profiles) and
        (
            hasattr(
                result.addon_profiles[CONST_MONITORING_ADDON_NAME], "identity"
            )
        ) and
        (
            hasattr(
                result.addon_profiles[CONST_MONITORING_ADDON_NAME].identity,
                "object_id",
            )
        )
    ):
        logger.info("omsagent MSI exists, using it")
        service_principal_msi_id = result.addon_profiles[
            CONST_MONITORING_ADDON_NAME
        ].identity.object_id
        is_service_principal = False

    if is_useAADAuth:
        logger.info(
            "Monitoring Metrics Publisher role assignment not required for monitoring addon with managed identity auth")
    elif service_principal_msi_id is not None:
        if not add_role_assignment(
            cmd,
            "Monitoring Metrics Publisher",
            service_principal_msi_id,
            is_service_principal,
            scope=cluster_resource_id,
        ):
            logger.warning(
                "Could not create a role assignment for Monitoring addon. "
                "Are you an Owner on this subscription?"
            )
    else:
        logger.warning(
            "Could not find service principal or user assigned MSI for role"
            "assignment"
        )


def add_ingress_appgw_addon_role_assignment(result, cmd):
    service_principal_msi_id = None
    # Check if service principal exists, if it does, assign permissions to service principal
    # Else, provide permissions to MSI
    if (
        hasattr(result, "service_principal_profile") and
        hasattr(result.service_principal_profile, "client_id") and
        result.service_principal_profile.client_id != "msi"
    ):
        service_principal_msi_id = result.service_principal_profile.client_id
        is_service_principal = True
    elif (
        (hasattr(result, "addon_profiles")) and
        (CONST_INGRESS_APPGW_ADDON_NAME in result.addon_profiles) and
        (
            hasattr(
                result.addon_profiles[CONST_INGRESS_APPGW_ADDON_NAME],
                "identity",
            )
        ) and
        (
            hasattr(
                result.addon_profiles[CONST_INGRESS_APPGW_ADDON_NAME].identity,
                "object_id",
            )
        )
    ):
        service_principal_msi_id = result.addon_profiles[
            CONST_INGRESS_APPGW_ADDON_NAME
        ].identity.object_id
        is_service_principal = False

    if service_principal_msi_id is not None:
        config = result.addon_profiles[CONST_INGRESS_APPGW_ADDON_NAME].config
        if CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID in config:
            appgw_id = config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID]
            parsed_appgw_id = parse_resource_id(appgw_id)
            appgw_group_id = resource_id(
                subscription=parsed_appgw_id["subscription"],
                resource_group=parsed_appgw_id["resource_group"],
            )
            if not add_role_assignment(
                cmd,
                "Contributor",
                service_principal_msi_id,
                is_service_principal,
                scope=appgw_group_id,
            ):
                logger.warning(
                    "Could not create a role assignment for application gateway: %s "
                    "specified in %s addon. "
                    "Are you an Owner on this subscription?",
                    appgw_id,
                    CONST_INGRESS_APPGW_ADDON_NAME,
                )
        if CONST_INGRESS_APPGW_SUBNET_ID in config:
            subnet_id = config[CONST_INGRESS_APPGW_SUBNET_ID]
            if not add_role_assignment(
                cmd,
                "Network Contributor",
                service_principal_msi_id,
                is_service_principal,
                scope=subnet_id,
            ):
                logger.warning(
                    "Could not create a role assignment for subnet: %s "
                    "specified in %s addon. "
                    "Are you an Owner on this subscription?",
                    subnet_id,
                    CONST_INGRESS_APPGW_ADDON_NAME,
                )
        if CONST_INGRESS_APPGW_SUBNET_CIDR in config:
            if result.agent_pool_profiles[0].vnet_subnet_id is not None:
                parsed_subnet_vnet_id = parse_resource_id(
                    result.agent_pool_profiles[0].vnet_subnet_id
                )
                vnet_id = resource_id(
                    subscription=parsed_subnet_vnet_id["subscription"],
                    resource_group=parsed_subnet_vnet_id["resource_group"],
                    namespace="Microsoft.Network",
                    type="virtualNetworks",
                    name=parsed_subnet_vnet_id["name"],
                )
                if not add_role_assignment(
                    cmd,
                    "Contributor",
                    service_principal_msi_id,
                    is_service_principal,
                    scope=vnet_id,
                ):
                    logger.warning(
                        "Could not create a role assignment for virtual network: %s "
                        "specified in %s addon. "
                        "Are you an Owner on this subscription?",
                        vnet_id,
                        CONST_INGRESS_APPGW_ADDON_NAME,
                    )


def add_virtual_node_role_assignment(cmd, result, vnet_subnet_id):
    # Remove trailing "/subnets/<SUBNET_NAME>" to get the vnet id
    vnet_id = vnet_subnet_id.rpartition("/")[0]
    vnet_id = vnet_id.rpartition("/")[0]

    service_principal_msi_id = None
    is_service_principal = False
    os_type = "Linux"
    addon_name = CONST_VIRTUAL_NODE_ADDON_NAME + os_type
    # Check if service principal exists, if it does, assign permissions to service principal
    # Else, provide permissions to MSI
    if (
        hasattr(result, "service_principal_profile") and
        hasattr(result.service_principal_profile, "client_id") and
        result.service_principal_profile.client_id.lower() != "msi"
    ):
        logger.info("valid service principal exists, using it")
        service_principal_msi_id = result.service_principal_profile.client_id
        is_service_principal = True
    elif (
        (hasattr(result, "addon_profiles")) and
        (addon_name in result.addon_profiles) and
        (hasattr(result.addon_profiles[addon_name], "identity")) and
        (hasattr(result.addon_profiles[addon_name].identity, "object_id"))
    ):
        logger.info("virtual node MSI exists, using it")
        service_principal_msi_id = result.addon_profiles[
            addon_name
        ].identity.object_id
        is_service_principal = False

    if service_principal_msi_id is not None:
        if not add_role_assignment(
            cmd,
            "Contributor",
            service_principal_msi_id,
            is_service_principal,
            scope=vnet_id,
        ):
            logger.warning(
                "Could not create a role assignment for virtual node addon. "
                "Are you an Owner on this subscription?"
            )
    else:
        logger.warning(
            "Could not find service principal or user assigned MSI for role"
            "assignment"
        )
